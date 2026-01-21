from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user
from app.core.exceptions import DomainIntegrityError
from app.permissions import ensure_roles
from app.services.user_service import UserService
from app.db.db import get_db_session
from app.schemas.user_schema import AllUsersWithDetailsResponseSchema, UserCreateSchema, UserOutSchema, UserUpdateSchemaByAdmin


router = APIRouter(
    prefix="/users",  # eg: /users/, /users/:id
    tags=["users"]  # for swagger
)


# create admin: used in AddUser page to create admin
@router.post("/create_admin")
async def create_admin(
    user_data: UserCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"]))
):
    # attach action
    request.state.action = "CREATE USER BY ADMIN"

    try:
        return await UserService.create_user(user_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"User creation unexpected error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(status_code=500, detail="Internal Server Error")


# get logged in user: used to fetch users details after login from AuthProvider
@router.get("/me", response_model=UserOutSchema)
async def get_logged_in_user(
        current_user: UserOutSchema = Depends(get_current_user)):
    logger.success("User logged in successfully")
    return current_user


# get all user: used in AllUser page. Show all users with populated data
@router.get("/", response_model=list[AllUsersWithDetailsResponseSchema])
async def get_all_users(
    user_role: str | None = None,
    department_search: str | None = None,
    order_by_filter: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"]))
):
    try:
        users = await UserService.get_users(db, user_role, department_search, order_by_filter)
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get single user details: used in SingleUserDetails page(admin panel). Show specific users all info(user table + teacher/student table data)
@router.get("/{id}", response_model=AllUsersWithDetailsResponseSchema)
async def get_single_user(
    id: int,
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await UserService.get_user(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update single user by admin: used in singleUserDetails page to update user tables data by admin
@router.patch("/{id}")
async def update_single_user_by_admin(
    id: int,
    user_data: UserUpdateSchemaByAdmin,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"]))
):
    # attach action
    request.state.action = "UPDATE USER BY ADMIN"

    try:
        return await UserService.update_user_by_admin(id, user_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"User update by admin unexpected error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(status_code=500, detail="Internal Server Error")


# TODO: create profile page to update the default password
# update single user by self(password update)
# @router.patch("/updatePassword/{id}")
# async def update_single_user_by_self(
#     id: int,
#     user_data: UserPasswordUpdateSchema,
#     request: Request,
#     db: AsyncSession = Depends(get_db_session),
#     current_user: UserOutSchema = Depends(get_current_user),
# ):
#     # attach action
#     request.state.action = "UPDATE USER PASSWORD(self)"

#     if id != current_user.id:
#         raise HTTPException(
#             status_code=400, detail="You are not authorized to update this record.")

#     try:
#         return await UserService.update_user_self(id, user_data, db, request)
#     except DomainIntegrityError as de:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=de.error_message
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.critical(f"User password update(self) unexpected error: {e}")

#         # attach audit payload
#         if request:
#             request.state.audit_payload = {
#                 "raw_error": str(e),
#                 "exception_type": type(e).__name__,
#             }
#         raise HTTPException(status_code=500, detail="Internal Server Error")


# delete single user: user in
# @router.delete("/{id}")
# async def delete_a_user(
#     id: int,
#     request: Request,
#     db: AsyncSession = Depends(get_db_session),
#     authorized_user: UserOutSchema = Depends(ensure_roles(["super_admin"]))
# ):
#     # attach action
#     request.state.action = "DELETE USER"

#     try:
#         return await UserService.delete_user(id, db, request)
#     except DomainIntegrityError as de:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=de.error_message
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.critical(f"User delete unexpected error: {e}")

#         # attach audit payload
#         if request:
#             request.state.audit_payload = {
#                 "raw_error": str(e),
#                 "exception_type": type(e).__name__,
#             }
#         raise HTTPException(status_code=500, detail="Internal Server Error")
