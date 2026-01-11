from typing import Any
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.core.pw_hash import hash_password
from app.models.user_model import User
from app.models.teacher_model import Teacher
from app.models.department_model import Department
from app.schemas.teacher_schema import TeacherCreateSchema, TeacherUpdateByAdminSchema, TeacherUpdateSchema
from app.utils import check_existence
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.utils.mask_sensitive_data import sanitize_payload


class TeacherService:

    @staticmethod
    async def create_teacher(
        teacher_data: TeacherCreateSchema,
        db: AsyncSession,
        request: Request | None = None
    ):
        # check for existance in user table
        existing_user = await db.scalar(select(User).where(User.username == teacher_data.user.username))

        if existing_user:
            logger.error("User with this email already exist")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="User with this email already exist")

        if not teacher_data.user.role.value == "teacher":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="User is not a teacher. Cannot create teacher.")

        # check if department exist
        if teacher_data.department_id:
            await check_existence(Department, db, teacher_data.department_id, "Department")

        try:
            # create user
            new_user_info = teacher_data.user.model_dump()
            raw_password = new_user_info.pop("password")

            new_user = User(
                **new_user_info,
                hashed_password=hash_password(raw_password)
            )

            db.add(new_user)
            await db.flush()  # This won't  add the user to the database yet but it'll generate a primary key for the user

            # create teacher
            new_teacher_info = teacher_data.model_dump(exclude={"user"})
            new_teacher = Teacher(
                **new_teacher_info,
                user_id=new_user.id
            )
            db.add(new_teacher)
            await db.commit()
            await db.refresh(new_teacher)
            logger.success("Teacher created successfully")

            return {
                "message": f"Teacher created successfully. Teacher ID: {new_teacher.id}, User ID: {new_user.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while creating teacher: {e}")
            logger.error(readable_error)
            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if teacher_data:
                    safe_data = sanitize_payload(
                        teacher_data.model_dump(
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
    async def get_teachers(db: AsyncSession):
        teachers = await db.scalars(select(Teacher))
        return teachers.all()

    @staticmethod
    async def get_teacher(db: AsyncSession, teacher_id: int):
        teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))

        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        return teacher

    @staticmethod
    async def grouped_teachers_by_department(
        db: AsyncSession
    ):
        all_teachers = await db.scalars(
            select(Department)
            .options(
                selectinload(
                    Department.teachers
                )
            ).order_by(Department.department_name)
        )

        result = all_teachers.all()

        return result

    @staticmethod
    async def update_teacher_by_admin(
        teacher_id: int,
        teacher_update_data: TeacherUpdateByAdminSchema,
        db: AsyncSession,
        request: Request | None = None,
    ):
        # check for teachers existence
        teacher = await check_existence(Teacher, db, teacher_id, "Teacher")
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        try:
            updated_teacher_data = teacher_update_data.model_dump(
                exclude_unset=True)

            for key, value in updated_teacher_data.items():
                setattr(teacher, key, value)

            await db.commit()
            await db.refresh(teacher)
            logger.success("Teacher updated successfully")

            return {
                "message": "Teacher updated successfully."
            }

        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating teacher(admin): {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if teacher_update_data:
                    payload["data"] = teacher_update_data.model_dump(
                        mode="json",
                        exclude_unset=True,
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    # update teacher (self)

    @staticmethod
    async def update_teacher(
        teacher_id: int,
        teacher_update_data: TeacherUpdateSchema,
        db: AsyncSession,
        request: Request | None = None
    ):
        # check for teachers existence
        teacher = await check_existence(Teacher, db, teacher_id, "Teacher")
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        try:
            updated_teacher_data = teacher_update_data.model_dump(
                exclude_unset=True)

            for key, value in updated_teacher_data.items():
                setattr(teacher, key, value)

            await db.commit()
            await db.refresh(teacher)

            return teacher
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating teacher(self): {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if teacher_update_data:
                    payload["data"] = teacher_update_data.model_dump(
                        mode="json",
                        exclude_unset=True,
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod
    # Delete Teachre
    async def delete_teacher(
        teacher_id: int,
        db: AsyncSession,
        request: Request | None = None,
    ):
        teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))

        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        try:
            await db.delete(teacher)
            await db.commit()

            return {"message": f"Teacher: {teacher.name} deleted successfully"}
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while deleting teacher: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )
