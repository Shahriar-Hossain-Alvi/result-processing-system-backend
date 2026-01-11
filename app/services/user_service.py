from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.integrity_error_parser import parse_integrity_error
from app.models import User
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.schemas.user_schema import UserCreateSchema, UserOutSchema, UserUpdateSchemaByAdmin, UserUpdateSchemaByUser
from app.core import hash_password
from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload


class UserService:

    @staticmethod
    async def create_user(
        user_data: UserCreateSchema,  # validate user data from request
        request: Request,
        db: AsyncSession,  # db session will be passed from router file
        authorized_user: UserOutSchema
    ):

        # check for existing user
        statement = select(User).where(User.username == user_data.username)

        result = await db.execute(statement)
        is_exist = result.scalar_one_or_none()
        if (is_exist):
            logger.error("User already exist")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already exist")

        try:
            # hash password
            hashed_pwd = hash_password(user_data.password)

            # create user (sqlalchemy model/instance creation)
            new_user = User(
                # convert the pydantic object to dictionary and unpack it to match the model (keyword parameter unpacking)
                **user_data.model_dump(exclude={"password"}),
                hashed_password=hashed_pwd)

            db.add(new_user)  # add the new_user to db(session)
            await db.commit()  # commit the changes(adds to database)
            await db.refresh(new_user)  # refresh the object(get the new data)
            logger.success("New user created successfully")

            # DB Log
            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value, created_by=authorized_user.id,
            #     action="CREATE USER SUCCESS",
            #     details=f"New user created. User ID: {new_user.id}."
            # )

            return {"message": f"User created successfully. ID: {new_user.id}, username: {new_user.username}"}
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Error occurred while creating new user: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(f"Readable Error: {readable_error}")

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value, created_by=getattr(
            #         authorized_user, "id", None),
            #     action="CREATE USER DB ERROR",
            #     details=f"Integrity error: {readable_error}",
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #            "payload_data": user_data.model_dump(mode="json", exclude_none=True, exclude={"password"})
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def get_users(
        db: AsyncSession,
        user_role: str | None = None
    ):
        query = (
            select(User)
            .options(
                # User -> Teacher -> Department
                selectinload(User.teacher).selectinload(Teacher.department),

                # User -> Student -> Department & Semester
                selectinload(User.student).selectinload(Student.department),
                selectinload(User.student).selectinload(Student.semester),
            )
        ).order_by(User.id)

        if user_role:
            query = query.where(User.role == user_role)

        result = await db.execute(query)
        all_users = result.scalars().unique().all()  # unique

        return all_users

    @staticmethod
    async def get_user(db: AsyncSession, user_id: int):
        query = (
            select(User)
            .options(
                # User -> Teacher -> Department
                selectinload(User.teacher).selectinload(Teacher.department),

                # User -> Student -> Department & Semester
                selectinload(User.student).selectinload(Student.department),
                selectinload(User.student).selectinload(Student.semester),
            )
        )

        result = await db.execute(query.where(User.id == user_id))
        single_user = result.scalar_one_or_none()  # unique

        if not single_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return single_user

    @staticmethod
    async def update_user_by_admin(
        user_id: int,
        user_update_data_by_admin: UserUpdateSchemaByAdmin,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
    ):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        try:
            updated_user_data = user_update_data_by_admin.model_dump(
                exclude_unset=True)

            for key, value in updated_user_data.items():
                setattr(user, key, value)

            await db.commit()
            await db.refresh(user)

            # DB Log
            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value, created_by=authorized_user.id,
            #     action="UPDATE USER SUCCESS",
            #     details=f"User updated. User ID: {user.id}."
            # )

            return {
                "message": f"User updated successfully for username: {user.username}, role: {user.role.value}"
            }
        except IntegrityError as e:
            await db.rollback()
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value, created_by=getattr(
            #         authorized_user, "id", None),
            #     action="UPDATE USER DB ERROR",
            #     details=f"Integrity error: {readable_error}",
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #            "payload_data": user_update_data_by_admin.model_dump()
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def update_user_self(
        user_id: int,
        updated_password: UserUpdateSchemaByUser,
        request: Request,
        db: AsyncSession,
        current_user: UserOutSchema
    ):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You are not authorized to update this user")
        try:
            updated_hashed_password = hash_password(updated_password.password)

            user.hashed_password = updated_hashed_password

            await db.commit()
            await db.refresh(user)

            # DB Log
            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value, created_by=current_user.id,
            #     action="UPDATE USER SUCCESS",
            #     details=f"User updated. User ID: {user.id}."
            # )

            return user
        except IntegrityError as e:
            await db.rollback()
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value, created_by=getattr(
            #         current_user, "id", None),
            #     action="UPDATE USER DB ERROR",
            #     details=f"Integrity error: {readable_error}",
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #            "payload_data": user_id
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def delete_user(
        user_id: int,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
    ):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        try:
            await db.delete(user)
            await db.commit()

            # DB Log
            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value, created_by=authorized_user.id,
            #     action="DELETE USER SUCCESS",
            #     details=f"User deleted. User ID: {user.id}."
            # )

            return {
                "message": f"User: {user.username}, role: {user.role.value} deleted successfully"
            }
        except IntegrityError as e:
            await db.rollback()
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value, created_by=getattr(
            #         authorized_user, "id", None),
            #     action="DELETE USER DB ERROR",
            #     details=f"Integrity error: {readable_error}",
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #            "payload_data": user_id
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)
