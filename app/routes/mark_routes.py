from app.schemas.marks_schema import MarksCreateSchema, MarksResponseSchema, MarksUpdateSchema, SemesterWiseAllSubjectsMarksResponseSchema, SemesterWiseAllSubjectsMarksWithPopulatedDataResponseSchema
from app.schemas.user_schema import UserOutSchema
from app.services.marks_service import MarksService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db_session
from app.permissions.role_checks import ensure_admin_or_teacher, ensure_admin
from app.core.authenticated_user import get_current_user
from app.utils.token_injector import inject_token


router = APIRouter(
    prefix="/marks",
    tags=["marks"]  # for swagger
)


# create marks
@router.post("/", response_model=MarksResponseSchema)
async def create_new_mark(
    mark_data: MarksCreateSchema,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await MarksService.create_mark(db, mark_data, authorized_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# update marks


@router.patch("/{mark_id}", response_model=MarksResponseSchema)
async def update_a_mark(
    mark_id: int,
    mark_data: MarksUpdateSchema,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await MarksService.update_mark(db, mark_data, mark_id, authorized_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# delete marks


@router.delete("/{mark_id}", response_model=MarksResponseSchema)
async def delete_a_mark(
    mark_id: int,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await MarksService.delete_mark(db, mark_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# get all subjects marks for a student


@router.get("/student/{student_id}", response_model=list[SemesterWiseAllSubjectsMarksResponseSchema])
async def get_all_subjects_marks_for_a_student(
    student_id: int,
    semester_id: int | None = Query(None),
    subject_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user),
):
    try:
        return await MarksService.get_all_marks_for_a_student(db, student_id, semester_id, subject_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# get result department wise with semester and session


@router.get(
    "/department_wise_result",
    response_model=list[SemesterWiseAllSubjectsMarksWithPopulatedDataResponseSchema]
)
async def get_department_wise_result(
    semester_id: int,
    department_id: int,
    session: str,
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),

):
    try:
        return await MarksService.get_department_semester_result(db, semester_id, department_id, session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
