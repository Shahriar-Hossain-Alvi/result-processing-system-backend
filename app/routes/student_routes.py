from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.core.exceptions import DomainIntegrityError
from app.services.student_service import StudentService
from app.db.db import get_db_session
from app.permissions.role_checks import ensure_admin_or_teacher, ensure_admin, ensure_super_admin
from app.schemas.student_schema import StudentCreateSchema, StudentResponseSchemaNested, StudentUpdateByAdminSchema, StudentUpdateSchema
from app.schemas.user_schema import UserOutSchema

router = APIRouter(
    prefix="/students",
    tags=["students"]  # for swagger
)


# create student record
@router.post("/")
async def create_student_record(
        student_data: StudentCreateSchema,
        request: Request,
        db: AsyncSession = Depends(get_db_session),
        authorized_user: UserOutSchema = Depends(ensure_admin),
):
    # attach action
    request.state.action = "CREATE STUDENT"

    try:
        result = await StudentService.create_student(student_data, db, request)

        logger.success("Student created successfully FROM ROUTER")
        return {
            "message": f"Student created successfully. Student ID: {result.id}, User ID: {result.user_id}"
        }
    except DomainIntegrityError as de:
        # DB Log
        logger.error(f"Student created failed FROM ROUTER: {de}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Create student Unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# get all students
@router.get(
    "/",
    response_model=list[StudentResponseSchemaNested]
)
async def get_all_students(
    authorized_user: UserOutSchema = Depends(ensure_admin_or_teacher),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await StudentService.get_students(db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get single student
@router.get("/{id}", response_model=StudentResponseSchemaNested)
async def get_single_student(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user),
):
    try:
        return await StudentService.get_student(db, id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update a student (self)
@router.patch("/{id}")
async def update_single_student(
    id: int,
    student_data: StudentUpdateSchema,
    request: Request,
    current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    # attach action
    request.state.action = "UPDATE STUDENT BY SELF"

    if current_user.id != id:
        raise HTTPException(
            status_code=400, detail="You are not authorized to update this record.")

    try:
        return await StudentService.update_student(id, student_data, db, request)
    except DomainIntegrityError as de:
        # DB Log
        logger.error(f"Student update failed FROM ROUTER: {de}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update a student by admin
@router.patch("/updateByAdmin/{id}")
async def update_single_student_by_admin(
    id: int,
    student_data: StudentUpdateByAdminSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(ensure_admin)
):
    # attach action
    request.state.action = "UPDATE STUDENT BY ADMIN"

    try:
        return await StudentService.update_student_by_admin(id, student_data, db, request)
    except DomainIntegrityError as de:
        # DB Log
        logger.error(f"Student update failed FROM ROUTER: {de}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete a student
@router.delete("/{id}")
async def delete_single_student(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(ensure_super_admin)
):
    # attach action
    request.state.action = "DELETE STUDENT"

    try:
        return await StudentService.delete_student(id, db, request)
    except DomainIntegrityError as de:
        # DB Log
        logger.error(f"Student deletion failed FROM ROUTER: {de}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
