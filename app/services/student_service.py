from typing import Any
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.core.pw_hash import hash_password
from app.models.department_model import Department
from app.models.semester_model import Semester
from app.models.student_model import Student
from app.models.user_model import User
from app.schemas.student_schema import StudentCreateSchema, StudentUpdateByAdminSchema, StudentUpdateSchema
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from app.utils import check_existence
from app.utils import delete_image_from_cloudinary
from app.utils.mask_sensitive_data import sanitize_payload


class StudentService:

    @staticmethod
    async def create_student(
            student_data: StudentCreateSchema,
            db: AsyncSession,
            request: Request | None = None,
    ):
        # check for existance in user table
        existing_user = await db.scalar(select(User).where(User.username == student_data.user.username))

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="User with this email already exist")

        if not student_data.user.role.value == "student":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="User is not a student. Cannot create student")

        # check if department exist
        if student_data.department_id:
            await check_existence(Department, db, student_data.department_id, "Department")

        # check if semester exist
        if student_data.semester_id:
            await check_existence(Semester, db, student_data.semester_id, "Semester")

        try:
            # create user
            new_user_info = student_data.user.model_dump(mode="json")
            raw_password = new_user_info.pop("password")

            new_user = User(
                **new_user_info,
                hashed_password=hash_password(raw_password)
            )

            db.add(new_user)
            await db.flush()  # This won't add the user to the database yet but it'll generate a primary key for the user

            # create student
            new_student_info = student_data.model_dump(exclude={"user"})
            new_student = Student(
                **new_student_info,
                user_id=new_user.id
            )
            db.add(new_student)
            await db.commit()
            await db.refresh(new_student)

            logger.success("New student created successfully")

            return new_student
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while creating student: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if student_data:
                    safe_data = sanitize_payload(
                        student_data.model_dump(
                            mode="json",
                            exclude={
                                "user": {
                                    "password",
                                    "hashed_password",
                                }
                            },
                        )
                    )
                    payload["data"] = safe_data

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod
    async def get_students(
            db: AsyncSession
    ):
        students = await db.scalars(select(Student).options(joinedload(Student.user)))

        return students.all()

    @staticmethod
    async def get_student(
            db: AsyncSession,
            student_id: int
    ):

        stmt = select(Student).where(Student.id == student_id).options(
            joinedload(Student.user)  # Eager load user
        )

        student = await db.scalar(stmt)

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        return student

    # update student by admin

    @staticmethod
    async def update_student_by_admin(
            student_id: int,
            student_update_data: StudentUpdateByAdminSchema,
            db: AsyncSession,
            request: Request | None = None,
    ):
        # check for existing student
        student = await check_existence(Student, db, student_id, "Student")

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        try:
            updated_student_data = student_update_data.model_dump(
                exclude_unset=True)  # convert to dictionary

            if "photo_public_id" in updated_student_data:
                new_public_id = updated_student_data["photo_public_id"]
                old_public_id = student.photo_public_id

                if old_public_id and old_public_id != new_public_id:
                    await delete_image_from_cloudinary(old_public_id)
                    logger.success(
                        "Old studet profile picture deleted from Cloudinary")

            for key, value in updated_student_data.items():
                # apply the updated data in the student object(from DB)
                setattr(student, key, value)

            await db.commit()
            await db.refresh(student)
            logger.success("Student updated successfully")

            return {
                "message": f"Student updated successfully. Student ID: {student.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers 	the 	session from 'failed' state and puts it back in 'clean' state to 	save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating student: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if student_update_data:
                    payload["data"] = student_update_data.model_dump(
                        mode="json", exclude_unset=True)

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod
    # update student (self)
    async def update_student(
            student_id: int,
            student_update_data: StudentUpdateSchema,
            db: AsyncSession,
            request: Request | None = None,
    ):
        # check for existing student
        student = await db.scalar(select(Student).where(Student.id == student_id))
        # TODO: When a student is updating their profile picture, delete the old one from Cloudinary using the photo public_id
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        try:
            updated_student_data = student_update_data.model_dump(
                exclude_unset=True)  # convert to dictionary

            for key, value in updated_student_data.items():
                # apply the updated data in the student object(from DB)
                setattr(student, key, value)

            await db.commit()
            await db.refresh(student)

            return {
                "message": f"Student updated successfully. Student ID: {student.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to 	save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating student(self): {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if student_update_data:
                    payload["data"] = student_update_data.model_dump(
                        mode="json", exclude_unset=True)

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod
    async def delete_student(
            student_id: int,
            db: AsyncSession,
            request: Request | None = None
    ):

        student = await db.scalar(select(Student).where(Student.id == student_id))

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        try:
            await db.delete(student)
            await db.commit()

            return {"message": f"{student.name} student deleted successfully"}
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to 	save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while deleting student: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                request.state.audit_payload = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }
            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )
