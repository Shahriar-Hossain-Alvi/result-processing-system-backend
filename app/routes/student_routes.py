from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.services.student_service import StudentService
from app.db.db import get_db_session
from app.permissions.role_checks import ensure_admin_or_teacher, ensure_admin, ensure_super_admin
from app.schemas.student_schema import StudentCreateSchema, StudentOutSchema, StudentResponseSchemaNested, StudentUpdateByAdminSchema, StudentUpdateSchema
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
        request: Request,
        # token_injection: None = Depends(inject_token),
        db: AsyncSession = Depends(get_db_session),
        authorized_user: UserOutSchema = Depends(ensure_admin),
):

    try:
        return await StudentService.create_student(student_data, request, db, authorized_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected Error: ", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get all students
@router.get(
    "/",
    response_model=list[StudentResponseSchemaNested]
)
async def get_all_students(
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await StudentService.get_students(db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected Error: ", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get single student
@router.get("/{id}", response_model=StudentResponseSchemaNested)
async def get_single_student(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user),
):
    try:
        return await StudentService.get_student(db, id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected Error: ", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update a student (self)
@router.patch("/{id}")
async def update_single_student(
    id: int,
    student_data: StudentUpdateSchema,
    request: Request,
    # token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    if current_user.id != id:
        raise HTTPException(
            status_code=400, detail="You are not authorized to update this record.")

    try:
        return await StudentService.update_student(id, student_data, request, db, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected Error: ", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update a student by admin
@router.patch("/updateByAdmin/{id}")
async def update_single_student_by_admin(
    id: int,
    student_data: StudentUpdateByAdminSchema,
    request: Request,
    # token_injection: None = Depends(inject_token),
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(ensure_admin)
):

    try:
        return await StudentService.update_student_by_admin(id, student_data, request, db, authorized_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected Error: ", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete a student
@router.delete("/{id}")
async def delete_single_student(
    id: int,
    request: Request,
    # token_injection: None = Depends(inject_token),
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(ensure_super_admin)
):

    try:
        return await StudentService.delete_student(id, request, db, authorized_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected Error: ", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
