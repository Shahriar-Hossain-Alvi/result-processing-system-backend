from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.db.db import get_db_session
from app.permissions.role_checks import ensure_admin, ensure_admin_or_teacher
from app.schemas.subject_offering_schema import SubjectOfferingCreateSchema, SubjectOfferingResponseSchema, SubjectOfferingUpdateSchema
from app.schemas.subject_schema import SubjectOutSchema
from app.schemas.user_schema import UserOutSchema
from app.services.subject_offering_service import SubjectOfferingService
from app.utils.token_injector import inject_token


router = APIRouter(
    prefix="/subject_offering",
    tags=["subject_offering"]  # for swagger
)


@router.post("/")
async def create_new_subject_offering(
    sub_off_data: SubjectOfferingCreateSchema,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await SubjectOfferingService.create_subject_offering(sub_off_data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get offered subjects list for marking (Admin=All subjects, Teacher=subjects they teach)
@router.get("/offered_subjects", response_model=list[SubjectOutSchema])
async def get_offered_subjects_for_marking(
    semester_id: int,
    department_id: int,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await SubjectOfferingService.get_offered_subjects_for_marking(db, semester_id, department_id, authorized_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{subject_offering_id}", response_model=SubjectOfferingResponseSchema)
async def get_single_subject_offering(
    subject_offering_id: int,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await SubjectOfferingService.get_subject_offering(db, subject_offering_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=list[SubjectOfferingResponseSchema])
async def get_all_subject_offerings(
        # token_injection: None = Depends(inject_token),
        authorized_user: UserOutSchema = Depends(ensure_admin),
        db: AsyncSession = Depends(get_db_session)
):
    try:
        return await SubjectOfferingService.get_subject_offerings(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{subject_offering_id}", response_model=SubjectOfferingResponseSchema)
async def update_a_subject_offering(
    subject_offering_id: int,
    update_data: SubjectOfferingUpdateSchema,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
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
    authorized_user: UserOutSchema = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await SubjectOfferingService.delete_subject_offering(db, subject_offering_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
