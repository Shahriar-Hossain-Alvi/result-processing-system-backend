from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.permissions.role_checks import ensure_admin, ensure_admin_or_teacher
from app.services.subject_service import SubjectService
from app.db.db import get_db_session
from app.schemas.subject_schema import SubjectCreateSchema, SubjectOutSchema
from app.schemas.user_schema import UserOutSchema


router = APIRouter(
    prefix="/subjects",
    tags=["subjects"]
)

# TODO: add token_injection in secured routes

# add new subject 
@router.post("/")
async def create_new_subject(
    subject_data: SubjectCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
):
    ensure_admin(current_user)

    try:
        return await SubjectService.create_subject(db, subject_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get all subjects
@router.get("/", response_model=list[SubjectOutSchema])
async def get_all_subjects(db: AsyncSession = Depends(get_db_session)):
    try:
        return await SubjectService.get_subjects(db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get single subject
@router.get("/{id}", response_model=SubjectOutSchema)
async def get_single_subject(
    id: int, 
    db: AsyncSession = Depends(get_db_session)):
    try:
        return await SubjectService.get_subject(db, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get subject by code
@router.get("/subject/{code}", response_model=SubjectOutSchema)
async def get_single_subject_by_code(
    subject_code: str, 
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await SubjectService.get_subject_by_code(db, subject_code)   
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# delete subject 
@router.delete("/{id}")
async def delete_single_subject(  
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
):
    ensure_admin(current_user)

    try:
        return await SubjectService.delete_subject(db, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
