from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.permissions.role_checks import ensure_admin
from app.services.semester_service import SemesterService
from app.db.db import get_db_session
from app.schemas.semester_schema import SemesterCreateSchema, SemesterOutSchema, SemesterUpdateSchema
from app.schemas.user_schema import UserOutSchema
from app.utils.token_injector import inject_token


router = APIRouter(
    prefix="/semesters",
    tags=["semesters"]  # for swagger
)

# create semester


@router.post("/")
async def add__new_semester(
    semester_data: SemesterCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):

    try:
        return await SemesterService.create_semester(db, semester_data)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get all semester
@router.get("/", response_model=list[SemesterOutSchema])
async def get_all_semesters(db: AsyncSession = Depends(get_db_session)):
    try:
        return await SemesterService.get_semesters(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get single semester
@router.get("/{id}", response_model=SemesterOutSchema)
async def get_single_semester(id: int, db: AsyncSession = Depends(get_db_session)):
    try:
        return await SemesterService.get_semester(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# update a semester
@router.patch("/{id}")
async def update_single_semester(
    id: int,
    semester_data: SemesterUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):
    try:
        return await SemesterService.update_semester(db, id, semester_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# delete a semester
@router.delete("/{id}")
async def delete_single_semester(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    # token_injection: None = Depends(inject_token),
    authorized_user: UserOutSchema = Depends(ensure_admin),
):

    try:
        return await SemesterService.delete_semester(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
