from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.authenticated_user import get_current_user
from app.db.db import get_db_session
from app.models import User
from app.schemas.user_schema import UserCreateSchema, UserOutSchema, UserUpdateSchemaByAdmin, UserUpdateSchemaByUser
from app.core import hash_password
from fastapi import HTTPException, status


class UserService:

    @staticmethod
    async def create_user(
        user_data: UserCreateSchema,  # validate user data from request
        db: AsyncSession,  # db session will be passed from router file
    ):

        # check for existing user
        statement = select(User).where(User.username == user_data.username)

        result = await db.execute(statement)
        is_exist = result.scalar_one_or_none()
        if (is_exist):
            raise ValueError("User already exist")

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

        return new_user

    @staticmethod
    async def get_users(db: AsyncSession):
        statement = select(User)
        result = await db.execute(statement)

        return result.scalars().all()

    @staticmethod
    async def get_user(db: AsyncSession, user_id: int):
        result = await db.scalar(select(User).where(User.id == user_id))

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return result

    @staticmethod
    async def update_user_by_admin(db: AsyncSession, user_id: int, user_update_data_by_admin: UserUpdateSchemaByAdmin):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        updated_user_data = user_update_data_by_admin.model_dump(
            exclude_unset=True)

        for key, value in updated_user_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def update_user_self(
        db: AsyncSession,
        user_id: int,
        updated_password: UserUpdateSchemaByUser,
        current_user: UserOutSchema
    ):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You are not authorized to update this user")

        updated_hashed_password = hash_password(updated_password.password)

        user.hashed_password = updated_hashed_password

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await db.delete(user)
        await db.commit()

        return {
            "message": f"User: {user.username}, role: {user.role.value} deleted successfully"
        }
