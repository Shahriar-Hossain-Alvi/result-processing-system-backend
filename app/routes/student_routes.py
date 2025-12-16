from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.services.student_service import StudentService
from app.db.db import get_db_session
from app.permissions.role_checks import ensure_admin_or_teacher, ensure_admin
from app.schemas.student_schema import StudentCreateSchema, StudentOutSchema, StudentResponseSchemaNested, StudentUpdateSchema
from app.schemas.user_schema import UserOutSchema
from app.utils.token_injector import inject_token

router = APIRouter(
    prefix="/students",
    tags=["students"]  # for swagger
)

# create student record


@router.post("/")
async def create_student_record(
        student_data: StudentCreateSchema,
        token_injection: None = Depends(inject_token),
        authorized_user: UserOutSchema = Depends(ensure_admin),
        db: AsyncSession = Depends(get_db_session),
):

    try:
        return await StudentService.create_student(db, student_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get all students
@router.get(
    "/",
    response_model=list[StudentOutSchema]
)
async def get_all_students(
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await StudentService.get_students(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get single student
@router.get("/{id}", response_model=StudentResponseSchemaNested)
async def get_single_student(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user),
):
    try:
        return await StudentService.get_student(db, id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update a student
@router.patch("/{id}", response_model=StudentOutSchema)
async def update_single_student(
    id: int,
    student_data: StudentUpdateSchema,
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await StudentService.update_student(db, id, student_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete a student
@router.delete("/{id}")
async def delete_single_student(
    id: int,
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await StudentService.delete_student(db, id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
