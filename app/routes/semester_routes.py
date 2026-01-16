from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.permissions import ensure_roles
from app.services.semester_service import SemesterService
from app.db.db import get_db_session
from app.schemas.semester_schema import SemesterCreateSchema, SemesterOutSchema, SemesterUpdateSchema
from app.schemas.user_schema import UserOutSchema


router = APIRouter(
    prefix="/semesters",
    tags=["semesters"]  # for swagger
)


# create semester: used in Departments & Semester page to create semester
@router.post("/")
async def add__new_semester(
    semester_data: SemesterCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
):
    # attach action
    request.state.action = "CREATE SEMESTER"

    try:
        return await SemesterService.create_semester(semester_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Semester creation unexpected error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(status_code=500, detail="Internal Server Error")


# get all semester: used in Departments & Semester page to get all semester
@router.get("/", response_model=list[SemesterOutSchema])
async def get_all_semesters(db: AsyncSession = Depends(get_db_session)):
    try:
        return await SemesterService.get_semesters(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get single semester
# @router.get("/{id}", response_model=SemesterOutSchema)
# async def get_single_semester(id: int, db: AsyncSession = Depends(get_db_session)):
#     try:
#         return await SemesterService.get_semester(db, id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# update a semester: used in Departments & Semester page to update semester
@router.patch("/{id}")
async def update_single_semester(
    id: int,
    semester_data: SemesterUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
):
    # attach action
    request.state.action = "UPDATE SEMESTER"

    try:
        return await SemesterService.update_semester(id, semester_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Semester update unexpected error: {e}")
        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(status_code=500, detail="Internal Server Error")


# delete a semester: used in Departments & Semester page to delete semester by super admin
@router.delete("/{id}")
async def delete_single_semester(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(ensure_roles(["super_admin"])),
):
    # attach action
    request.state.action = "DELETE SEMESTER"

    try:
        return await SemesterService.delete_semester(id, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Semester delete unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
