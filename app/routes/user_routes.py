from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user
from app.permissions.role_checks import ensure_admin
from app.services.user_service import UserService
from app.db.db import get_db_session
from app.schemas.user_schema import UserCreateSchema, UserOutSchema, UserUpdateSchemaByAdmin, UserUpdateSchemaByUser
from app.utils import inject_token


router = APIRouter(
    prefix="/users",  # eg: /users/register, /users/:id
    tags=["users"]  # for swagger
)

# TODO: add token_injection in secured routes


# user register
@router.post("/register")
async def register_user(user_data: UserCreateSchema, db: AsyncSession = Depends(get_db_session)):
    try:
        new_user = await UserService.create_user(db, user_data)

        return {"message": f"User created successfully. ID: {new_user.id}"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get logged in user
@router.get("/me", response_model=UserOutSchema)
async def get_logged_in_user(
    token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user)):
    return current_user


# get all user
@router.get("/", response_model=list[UserOutSchema])
async def get_all_users(db: AsyncSession = Depends(get_db_session)):
    try:
        users = await UserService.get_users(db)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get single user
@router.get("/{id}", response_model=UserOutSchema)
async def get_single_user(id: int, db: AsyncSession = Depends(get_db_session)):
    try:
        return await UserService.get_user(db, id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update single user by admin
@router.patch("/{id}", response_model=UserOutSchema, dependencies=[Depends(ensure_admin)])
async def update_single_user_by_admin(
    id: int,
    user_data: UserUpdateSchemaByAdmin,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await UserService.update_user_by_admin(db, id, user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update single user by self(password update)
@router.patch("/updatePassword/{id}", response_model=UserOutSchema)
async def update_single_user_by_self(
    id: int,
    user_data: UserUpdateSchemaByUser,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user),
):
    try:
        return await UserService.update_user_self(db, id, user_data, current_user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete single user
@router.delete("/{id}", dependencies=[Depends(ensure_admin)])
async def delete_a_user(
    id: int,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await UserService.delete_user(db, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
