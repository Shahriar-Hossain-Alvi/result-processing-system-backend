from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user
from app.permissions.role_checks import ensure_admin
from app.services.user_service import UserService
from app.db.db import get_db_session
from app.schemas.user_schema import AllUsersWithDetailsResponseSchema, UserCreateSchema, UserOutSchema, UserUpdateSchemaByAdmin, UserUpdateSchemaByUser


router = APIRouter(
    prefix="/users",  # eg: /users/register, /users/:id
    tags=["users"]  # for swagger
)


# user(admin) register
@router.post("/register")
async def register_user(
    user_data: UserCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):

    try:
        return await UserService.create_user(user_data, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


# get logged in user
@router.get("/me", response_model=UserOutSchema)
async def get_logged_in_user(
        # token_injection: None = Depends(inject_token),
        current_user: UserOutSchema = Depends(get_current_user)):
    return current_user


# get all user
@router.get("/", response_model=list[AllUsersWithDetailsResponseSchema])
async def get_all_users(
    user_role: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):
    try:
        users = await UserService.get_users(db, user_role)
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", response_model=AllUsersWithDetailsResponseSchema)
async def get_single_user(
    id: int,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    # current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await UserService.get_user(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update single user by admin
@router.patch("/{id}", response_model=dict[str, str])
async def update_single_user_by_admin(
    id: int,
    user_data: UserUpdateSchemaByAdmin,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    # current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await UserService.update_user_by_admin(db, id, user_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update single user by self(password update)
@router.patch("/updatePassword/{id}", response_model=UserOutSchema)
async def update_single_user_by_self(
    id: int,
    user_data: UserUpdateSchemaByUser,
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user),
):
    try:
        return await UserService.update_user_self(db, id, user_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete single user
@router.delete("/{id}")
async def delete_a_user(
    id: int,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await UserService.delete_user(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
