from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from app.core.authenticated_user import get_current_user
from app.core.exceptions import DomainIntegrityError
from app.permissions import ensure_roles
from app.services.department_service import DepartmentService
from app.schemas.department_schema import DepartmentCreateSchema, DepartmentOutSchema, DepartmentUpdateSchema
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db_session
from app.schemas.user_schema import UserOutSchema


router = APIRouter(
    prefix="/departments",
    tags=["departments"]  # for swagger
)


# create department: used in Departments & Semester page to create department
@router.post("/")
async def create_new_department(
    department_data: DepartmentCreateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
):
    # attach action
    request.state.action = "CREATE DEPARTMENT"

    try:
        return await DepartmentService.create_department(department_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Create department Unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(status_code=500, detail="Internal Server Error")


# get all departments: used in Departments & Semester page to get all departments
@router.get("/", response_model=list[DepartmentOutSchema])
async def get_all_departments(
    current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await DepartmentService.get_departments(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get single department
# @router.get("/{id}", response_model=DepartmentOutSchema)
# async def get_single_department(
#     id: int,
#     db: AsyncSession = Depends(get_db_session),
#     current_user: UserOutSchema = Depends(get_current_user)
# ):

#     try:
#         return await DepartmentService.get_department(db, id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# update a department: used in Departments & Semester page to update department
@router.patch("/{id}")
async def update_single_department(
    id: int,
    department_data: DepartmentUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin"])),
):
    # attach action
    request.state.action = "UPDATE DEPARTMENT"

    try:
        return await DepartmentService.update_department(id, department_data, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update department Unexpected Error:", e)

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(status_code=500, detail=str(e))


# delete a department: used in Departments & Semester page to delete department by super admin
@router.delete("/{id}")
async def delete_single_department(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    authorized_user: UserOutSchema = Depends(ensure_roles(["super_admin"])),
):
    # attach action
    request.state.action = "DELETE DEPARTMENT"

    try:
        return await DepartmentService.delete_department(id, db, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Delete department Unexpected Error: {e}")

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(status_code=500, detail="Internal Server Error")
