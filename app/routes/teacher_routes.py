from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.permissions.role_checks import ensure_admin_or_teacher, ensure_admin
from app.db.db import get_db_session
from app.schemas.teacher_schema import TeacherCreateSchema, TeacherResponseSchemaNested
from app.schemas.user_schema import UserOutSchema
from app.utils.token_injector import inject_token
from app.services.teacher_service import TeacherService

router = APIRouter(prefix='/teacher', tags=['teachers'])

# create teacher record


@router.post("/")
async def create_student_record(
    teacher_data: TeacherCreateSchema,
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await TeacherService.create_teacher(db, teacher_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get single teacher
@router.get("/{id}", response_model=TeacherResponseSchemaNested)
async def get_single_teacher(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user),
):

    try:
        return await TeacherService.get_teacher(db, id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

#  get all teachers


@router.get("/", response_model=list[TeacherResponseSchemaNested])
async def get_all_teachers(
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await TeacherService.get_teachers(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
