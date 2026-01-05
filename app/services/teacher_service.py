from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.integrity_error_parser import parse_integrity_error
from app.core.pw_hash import hash_password
from app.models.user_model import User
from app.models.teacher_model import Teacher
from app.models.department_model import Department
from app.schemas.teacher_schema import TeacherCreateSchema, TeacherUpdateByAdminSchema, TeacherUpdateSchema
from app.schemas.user_schema import UserOutSchema
from app.utils import check_existence
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError


class TeacherService:

    @staticmethod
    async def create_teacher(
        db: AsyncSession,
        teacher_data: TeacherCreateSchema
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
            logger.error(f"Integrity error while creating teacher: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(readable_error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

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
        # all_teachers = await db.scalars(select(Teacher).options(joinedload(Teacher.department)).order_by(Teacher.department_id))

        # result = all_teachers.all()

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
        db: AsyncSession,
        teacher_id: int,
        teacher_data: TeacherUpdateByAdminSchema
    ):
        # check for teachers existence
        teacher = await check_existence(Teacher, db, teacher_id, "Teacher")
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        try:
            updated_teacher_data = teacher_data.model_dump(exclude_unset=True)

            for key, value in updated_teacher_data.items():
                setattr(teacher, key, value)

            await db.commit()
            await db.refresh(teacher)
            logger.success("Teacher updated successfully")
            return {
                "message": f"Teacher updated successfully. Teacher ID: {teacher.id}"
            }
        except IntegrityError as e:
            logger.error(f"Integrity error while updating teacher: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(readable_error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def update_teacher(
        db: AsyncSession,
        teacher_id: int,
        teacher_data: TeacherUpdateSchema
    ):
        # check for teachers existence
        teacher = await check_existence(Teacher, db, teacher_id, "Teacher")
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        try:
            updated_teacher_data = teacher_data.model_dump(exclude_unset=True)

            for key, value in updated_teacher_data.items():
                setattr(teacher, key, value)

            await db.commit()
            await db.refresh(teacher)

            return teacher
        except IntegrityError as e:
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def delete_teacher(db: AsyncSession, teacher_id: int):
        teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))

        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        await db.delete(teacher)
        await db.commit()

        return {"message": f"Teacher: {teacher.name} deleted successfully"}
