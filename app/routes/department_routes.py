from fastapi import APIRouter, Depends, HTTPException
from app.core.authenticated_user import get_current_user
from app.permissions.role_checks import ensure_admin
from app.services.department_service import DepartmentService
from app.models.user_model import UserRole
from app.schemas.department_schema import DepartmentCreateSchema, DepartmentOutSchema, DepartmentUpdateSchema
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db_session
from app.schemas.user_schema import UserOutSchema
from app.utils.token_injector import inject_token


router = APIRouter(
    prefix="/departments",
    tags=["departments"]  # for swagger
)

# create department


@router.post("/")
async def create_new_department(
    department_data: DepartmentCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):

    try:
        return await DepartmentService.create_department(db, department_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get all departments
@router.get("/", response_model=list[DepartmentOutSchema])
async def get_all_departments(
    token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):

    try:
        return await DepartmentService.get_departments(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get single department
@router.get("/{id}", response_model=DepartmentOutSchema)
async def get_single_department(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    token_injection: None = Depends(inject_token),
    current_user: UserOutSchema = Depends(get_current_user)
):

    try:
        return await DepartmentService.get_department(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# update a department
@router.patch("/{id}")
async def update_single_department(
    id: int,
    department_data: DepartmentUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):

    try:
        return await DepartmentService.update_department(db, id, department_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# delete a department
@router.delete("/{id}")
async def delete_single_department(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):
    try:
        return await DepartmentService.delete_department(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
