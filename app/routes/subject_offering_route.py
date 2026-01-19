from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.db.db import get_db_session
from app.permissions import ensure_roles
from app.schemas.subject_offering_schema import AllSubjectOfferingsResponseSchema, SubjectOfferingCreateSchema, SubjectOfferingUpdateSchema
from app.schemas.subject_schema import MinimalSemesterResponseSchema
from app.schemas.user_schema import UserOutSchema
from app.services.subject_offering_service import SubjectOfferingService
from app.utils.token_injector import inject_token


router = APIRouter(
    prefix="/subject_offering",
    tags=["subject_offering"]  # for swagger
)


@router.post("/")
async def create_new_subject_offering(
    request: Request,
    sub_off_data: SubjectOfferingCreateSchema,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db_session),
):
    # attach action
    request.state.action = "CREATE SUBJECT OFFERING"
    try:
        return await SubjectOfferingService.create_subject_offering(sub_off_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Create subject offering unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/",
            response_model=list[AllSubjectOfferingsResponseSchema]
            )
async def get_all_subject_offerings(
    request: Request,
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await SubjectOfferingService.get_subject_offerings(db)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Create subject offering unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# get offered subjects list for marking (Admin=All subjects, Teacher=subjects they teach)


@router.get("/offered_subjects", response_model=list[MinimalSemesterResponseSchema])
async def get_offered_subjects_for_marking(
    semester_id: int,
    department_id: int,
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin", "teacher"])),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await SubjectOfferingService.get_offered_subjects_for_marking(db, semester_id, department_id, authorized_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{subject_offering_id}")
async def get_single_subject_offering(
    subject_offering_id: int,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin", "teacher"])),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await SubjectOfferingService.get_subject_offering(db, subject_offering_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{subject_offering_id}")
async def update_a_subject_offering(
    subject_offering_id: int,
    update_data: SubjectOfferingUpdateSchema,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await SubjectOfferingService.update_subject_offering(db, update_data, subject_offering_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{subject_offering_id}")
async def delete_a_subject_offering(
    subject_offering_id: int,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_roles(["super_admin"])),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await SubjectOfferingService.delete_subject_offering(db, subject_offering_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
