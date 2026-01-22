from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.core.exceptions import DomainIntegrityError
from app.permissions import ensure_roles
from app.db.db import get_db_session
from app.schemas.teacher_schema import TeacherCreateSchema, TeacherResponseSchemaForSubjectOfferingSearch, TeacherUpdateByAdminSchema
from app.schemas.user_schema import UserOutSchema
from app.services.teacher_service import TeacherService

router = APIRouter(prefix='/teachers', tags=['teachers'])


# create teacher record: used in Add User page to create teacher (User table + Teacher table data)
@router.post("/")
async def create_teacher_record(
    teacher_data: TeacherCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"]))
):
    # attach action
    request.state.action = "CREATE TEACHER"

    try:
        return await TeacherService.create_teacher(teacher_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical("Create teacher unexpected Error: ", e)

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


#  get all teachers
# @router.get("/", response_model=list[TeacherResponseSchema])
# async def get_all_teachers(
#     authorized_user: UserOutSchema = Depends(
#         ensure_roles(["super_admin", "admin", "teacher"])),
#     db: AsyncSession = Depends(get_db_session),
# ):
#     try:
#         return await TeacherService.get_teachers(db)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# get all teachers with minimal data for course allocation(Subject Offering)
@router.get("/all", response_model=list[TeacherResponseSchemaForSubjectOfferingSearch])
async def get_all_teachers_with_minimal_data(
    request: Request,
    search: str | None = None,
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db_session)

):
    try:
        return await TeacherService.get_all_teachers_with_minimal_data(db, search, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(
            "Get all teacher with minimal data unexpected Error: ", e)

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# @router.get("/all_faculty", response_model=list[TeachersDepartmentWiseGroupResponse])
# async def get_all_faculty(
#     db: AsyncSession = Depends(get_db_session)
# ):

#     try:
#         return await TeacherService.grouped_teachers_by_department(db)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# get single teacher
# @router.get("/{id}", response_model=TeacherResponseSchema)
# async def get_single_teacher(
#     id: int,
#     db: AsyncSession = Depends(get_db_session),
#     current_user: UserOutSchema = Depends(get_current_user),
# ):

#     try:
#         return await TeacherService.get_teacher(db, id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update teacher by self
# @router.patch("/{id}", response_model=TeacherResponseSchema)
# async def update_teacher(
#         id: int,
#         teacher_update_data: TeacherUpdateSchema,
#         request: Request,
#         db: AsyncSession = Depends(get_db_session),
#         current_user: UserOutSchema = Depends(get_current_user)
# ):
#     # attach action
#     request.state.action = "UPDATE TEACHER BY SELF"

#     if id != current_user.id:
#         raise HTTPException(
#             status_code=400, detail="You are not authorized to update this record.")

#     try:
#         return await TeacherService.update_teacher(id, teacher_update_data, db, request)
#     except DomainIntegrityError as de:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=de.error_message
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         # attach audit payload
#         if request:
#             request.state.audit_payload = {
#                 "raw_error": str(e),
#                 "exception_type": type(e).__name__,
#             }

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# update teacher data by admin: Used in SingleUserDetails page to update teacher tables data by admin
@router.patch("/updateByAdmin/{id}")
async def update_teacher_by_admin(
        id: int,
        teacher_update_data: TeacherUpdateByAdminSchema,
        request: Request,
        db: AsyncSession = Depends(get_db_session),
        authorized_user: UserOutSchema = Depends(
            ensure_roles(["super_admin", "admin"]))
):
    # attach action
    request.state.action = "UPDATE TEACHER BY ADMIN"

    try:
        return await TeacherService.update_teacher_by_admin(id, teacher_update_data, db, request)
    except DomainIntegrityError as de:
        logger.error(f"Teacher update failed FROM ROUTER(by admin): {de}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Update teacher by admin Unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete teacher
# @router.delete("/{id}")
# async def delete_a_teacher(
#     id: int,
#     request: Request,
#     db: AsyncSession = Depends(get_db_session),
#     authorized_user: UserOutSchema = Depends(ensure_roles(["super_admin"]))
# ):
#     # attach action
#     request.state.action = "DELETE TEACHER"

#     try:
#         return await TeacherService.delete_teacher(id, db, request)
#     except DomainIntegrityError as de:
#         logger.error(f"Teacher delete failed FROM ROUTER: {de}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=de.error_message
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.critical(f"Delete teacher Unexpected Error: {e}")

#         # attach audit payload
#         if request:
#             request.state.audit_payload = {
#                 "raw_error": str(e),
#                 "exception_type": type(e).__name__,
#             }

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
