from typing import Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import asc, desc, select, or_
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models import User
from app.models.department_model import Department
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.schemas.user_schema import UserCreateSchema, UserUpdateSchemaByAdmin
from app.core import hash_password
from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.utils.mask_sensitive_data import sanitize_payload


class UserService:

    @staticmethod
    async def create_user(
        user_data: UserCreateSchema,
        db: AsyncSession,
        request: Request | None = None
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

            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            logger.success("New user created successfully")

            return {"message": f"User created successfully. ID: {new_user.id}, username: {new_user.username}"}
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Error occurred while creating new user: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if user_data:
                    safe_data = sanitize_payload(
                        user_data.model_dump(
                            mode="json",
                            exclude={
                                "password",
                                "hashed_password",
                            },
                        )
                    )
                    payload["data"] = safe_data

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod
    async def get_users(
        db: AsyncSession,
        user_role: str | None = None,
        department_search: str | None = None,
        order_by_filter: str | None = None
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
        )

        if user_role:
            query = query.where(User.role == user_role)

        if department_search is not None and department_search != "":
            query = query.where(
                or_(
                    User.student.has(Student.department.has(
                        Department.department_name.ilike(f"%{department_search}%"))),
                    User.teacher.has(Teacher.department.has(
                        Department.department_name.ilike(f"%{department_search}%"))),
                )
            )

        if order_by_filter == "asc":
            query = query.order_by(asc(User.id))

        if order_by_filter == "desc":
            query = query.order_by(desc(User.id))

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
        db: AsyncSession,
        request: Request | None = None
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

            logger.success("User updated successfully")
            return {
                "message": f"User updated successfully for username: {user.username}, role: {user.role.value}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating user: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if user_update_data_by_admin:
                    payload["data"] = user_update_data_by_admin.model_dump(
                        mode="json",
                        exclude_unset=True,
                    )

                request.state.audit_payload = payload

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if user_update_data_by_admin:
                    payload["data"] = user_update_data_by_admin.model_dump(
                        mode="json",
                        exclude_unset=True,
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    # TODO: create profile page to update the default password
    # @staticmethod
    # async def update_user_self(
    #     user_id: int,
    #     updated_password: UserPasswordUpdateSchema,
    #     db: AsyncSession,
    #     request: Request | None = None
    # ):
    #     user = await db.scalar(select(User).where(User.id == user_id))

    #     if not user:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    #     try:
    #         updated_hashed_password = hash_password(updated_password.password)

    #         user.hashed_password = updated_hashed_password

    #         await db.commit()
    #         await db.refresh(user)
    #         logger.success("Password updated successfully")
    #         return {
    #             "message": f"Password updated successfully. Email/Username: {user.username}"
    #         }
    #     except IntegrityError as e:
    #         # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
    #         await db.rollback()

    #         # generally the PostgreSQL's error message will be in e.orig.args
    #         raw_error_message = str(e.orig) if e.orig else str(e)
    #         readable_error = parse_integrity_error(raw_error_message)

    #         logger.error(f"Integrity error while updating password: {e}")
    #         logger.error(f"Readable Error: {readable_error}")

    #         # attach audit payload safely
    #         if request:
    #             payload: dict[str, Any] = {
    #                 "raw_error": raw_error_message,
    #                 "readable_error": readable_error,
    #             }

    #             request.state.audit_payload = payload

    #         raise DomainIntegrityError(
    #             error_message=readable_error, raw_error=raw_error_message
    #         )

    # @staticmethod
    # async def delete_user(
    #     user_id: int,
    #     db: AsyncSession,
    #     request: Request | None = None
    # ):
    #     user = await db.scalar(select(User).where(User.id == user_id))

    #     if not user:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    #     try:
    #         await db.delete(user)
    #         await db.commit()

    #         logger.success("User deleted successfully")
    #         return {
    #             "message": f"User: {user.username}, role: {user.role.value} deleted successfully"
    #         }
    #     except IntegrityError as e:
    #         # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
    #         await db.rollback()

    #         # generally the PostgreSQL's error message will be in e.orig.args
    #         raw_error_message = str(e.orig) if e.orig else str(e)
    #         readable_error = parse_integrity_error(raw_error_message)

    #         logger.error(f"Integrity error while deleting user: {e}")
    #         logger.error(f"Readable Error: {readable_error}")

    #         # attach audit payload safely
    #         if request:
    #             payload: dict[str, Any] = {
    #                 "raw_error": raw_error_message,
    #                 "readable_error": readable_error,
    #             }

    #             request.state.audit_payload = payload

    #         raise DomainIntegrityError(
    #             error_message=readable_error, raw_error=raw_error_message
    #         )
