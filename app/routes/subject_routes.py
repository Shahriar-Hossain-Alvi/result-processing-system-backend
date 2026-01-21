from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.core.exceptions import DomainIntegrityError
from app.permissions import ensure_roles
from app.services.subject_service import SubjectService
from app.db.db import get_db_session
from app.schemas.subject_schema import SubjectCreateSchema, SubjectUpdateSchema, SubjectWithSemesterResponseSchema
from app.schemas.user_schema import UserOutSchema


router = APIRouter(
    prefix="/subjects",
    tags=["subjects"]
)


# create subject: used in subjects page
@router.post("/")
async def create_new_subject(
    subject_data: SubjectCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"]))
):
    # attach action
    request.state.action = "CREATE SUBJECT"

    try:
        return await SubjectService.create_subject(subject_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Create subject Unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# get all subjects
@router.get("/", response_model=list[SubjectWithSemesterResponseSchema])
async def get_all_subjects(
        current_user: UserOutSchema = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session),
        subject_credits: float | None = None,
        semester_id: int | None = None,
        search: str | None = None,
        order_by_filter: str | None = None
):

    try:
        return await SubjectService.get_subjects(db, subject_credits, semester_id, search, order_by_filter)
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Get all subject Unexpected Error: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# get single subject
# @router.get("/{id}")
# async def get_single_subject(
#         id: int,
#         current_user: UserOutSchema = Depends(get_current_user),
#         db: AsyncSession = Depends(get_db_session)):
#     try:
#         return await SubjectService.get_subject(db, id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.critical(f"Get single subject Unexpected Error: {e}")

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# get subject by code
# @router.get("/subject/{code}")
# async def get_single_subject_by_code(
#     subject_code: str,
#     current_user: UserOutSchema = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db_session)
# ):
#     try:
#         return await SubjectService.get_subject_by_code(db, subject_code)
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.critical(f"Get subject by code Unexpected Error: {e}")

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# update subject by admin
@router.patch("/{id}")
async def update_subject_by_admin(
    id: int,
    subject_update_data: SubjectUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"]))
):
    # attach action
    request.state.action = "UPDATE SUBJECT BY ADMIN"

    try:
        return await SubjectService.update_subject_by_admin(id, subject_update_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# delete subject
@router.delete("/{id}")
async def delete_single_subject(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(ensure_roles(["super_admin"]))
):
    # attach action
    request.state.action = "DELETE SUBJECT"

    try:
        return await SubjectService.delete_subject(id, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
