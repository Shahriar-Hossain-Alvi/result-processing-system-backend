from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.integrity_error_parser import parse_integrity_error
from app.core.pw_hash import hash_password
from app.models.department_model import Department
from app.models.semester_model import Semester
from app.models.student_model import Student
from app.models.user_model import User
from app.schemas.student_schema import StudentCreateSchema, StudentUpdateByAdminSchema, StudentUpdateSchema
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from app.schemas.user_schema import UserOutSchema
from app.utils import check_existence


class StudentService:

    @staticmethod
    async def create_student(
            db: AsyncSession,
            student_data: StudentCreateSchema
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
            new_user_info = student_data.user.model_dump()
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

            return {
                "message": f"Student created successfully. Student ID: {new_student.id}, User ID: {new_user.id}"
            }
        except IntegrityError as e:
            logger.error(f"Integrity error while creating student: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(readable_error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

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

    @staticmethod
    async def update_student_by_admin(
            db: AsyncSession,
            student_id: int,
            student_update_data: StudentUpdateByAdminSchema
    ):
        # check for existing student
        student = await db.scalar(select(Student).where(Student.id == student_id))

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
            logger.success("Student updated successfully")
            return {
                "message": f"Student updated successfully. Student ID: {student.id}"
            }
        except IntegrityError as e:
            logger.error(f"Integrity error while updating student: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(readable_error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def update_student(
            db: AsyncSession,
            student_id: int,
            student_update_data: StudentUpdateSchema
    ):
        # check for existing student
        student = await db.scalar(select(Student).where(Student.id == student_id))

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        updated_student_data = student_update_data.model_dump(
            exclude_unset=True)  # convert to dictionary

        for key, value in updated_student_data.items():
            # apply the updated data in the student object(from DB)
            setattr(student, key, value)

        await db.commit()
        await db.refresh(student)

        return student

    @staticmethod
    async def delete_student(
            db: AsyncSession,
            student_id: int
    ):
        student = await StudentService.get_student(db, student_id)

        await db.delete(student)
        await db.commit()

        return {"message": f"{student.name} student deleted successfully"}
