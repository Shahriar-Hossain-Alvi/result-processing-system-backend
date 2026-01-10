from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.integrity_error_parser import parse_integrity_error
from app.core.pw_hash import hash_password
from app.models.audit_log_model import LogLevel
from app.models.user_model import User
from app.models.teacher_model import Teacher
from app.models.department_model import Department
from app.schemas.teacher_schema import TeacherCreateSchema, TeacherUpdateByAdminSchema, TeacherUpdateSchema
from app.schemas.user_schema import UserOutSchema
from app.utils import check_existence
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError


class TeacherService:

    @staticmethod
    async def create_teacher(
        teacher_data: TeacherCreateSchema,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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

            # DB Log
            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value, created_by=authorized_user.id,
            #     action="CREATE TEACHER SUCCESS",
            #     details=f"New teacher created. Teacher ID: {new_teacher.id}, User ID: {new_user.id}."
            # )

            return {
                "message": f"Teacher created successfully. Teacher ID: {new_teacher.id}, User ID: {new_user.id}"
            }
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error while creating teacher: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(readable_error)

            # DB Log
            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value, created_by=getattr(
            #         authorized_user, "id", None),
            #     action="CREATE TEACHER DB ERROR",
            #     details=f"Integrity error: {readable_error}",
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #         "payload_data": teacher_data.model_dump(mode="json", exclude_none=True, exclude={"user": {"password"}})
            #     }
            # )

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
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value,
            #     action="UPDATE TEACHER SUCCCESS",
            #     details=f"Teacher: {teacher.name} updated. Teacher ID: {teacher.id} updated",
            #     created_by=authorized_user.id,
            #     payload={
            #         "payload_data": teacher_update_data.model_dump()
            #     }
            # )

            return {
                "message": f"Teacher updated successfully. Teacher ID: {teacher.id}"
            }
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error while updating teacher: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(readable_error)

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value,
            #     action="UPDATE TEACHER ERROR",
            #     details=f"Teacher update failed. Error: {readable_error}",
            #     created_by=getattr(authorized_user, "id", None),
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #         "payload_data": teacher_update_data.model_dump(exclude_unset=True)
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    # update teacher (self)

    @staticmethod
    async def update_teacher(
        teacher_id: int,
        teacher_update_data: TeacherUpdateSchema,
        request: Request,
        db: AsyncSession,
        current_user: UserOutSchema
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

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value,
            #     action="UPDATE TEACHER SUCCCESS",
            #     details=f"Teacher: {teacher.name}, ID: {teacher.id} updated",
            #     created_by=current_user.id,
            #     payload={
            #         "payload_data": teacher_update_data.model_dump(exclude_unset=True)
            #     }
            # )

            return teacher
        except IntegrityError as e:
            await db.rollback()
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value,
            #     action="UPDATE TEACHER ERROR",
            #     details=f"Teacher update failed. Error: {readable_error}",
            #     created_by=getattr(current_user, "id", None),
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #         "payload_data": teacher_update_data.model_dump()
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    # Delete Teachre
    async def delete_teacher(
        teacher_id: int,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
    ):
        teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))

        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        try:
            await db.delete(teacher)
            await db.commit()

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value,
            #     action="DELETE TEACHER SUCCCESS",
            #     details=f"Teacher: {teacher.name}, ID: {teacher.id} deleted",
            #     created_by=authorized_user.id,
            #     payload={
            #         "payload_data": teacher_id
            #     }
            # )

            return {"message": f"Teacher: {teacher.name} deleted successfully"}
        except IntegrityError as e:
            await db.rollback()
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value,
            #     action="DELETE TEACHER ERROR",
            #     details=f"Teacher deletion failed. Error: {readable_error}",
            #     created_by=getattr(authorized_user, "id", None),
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #         "payload_data": teacher_id
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)
