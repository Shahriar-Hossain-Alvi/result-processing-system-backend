from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.crud_operations.subject_service import create_subject, delete_subject, get_subject, get_subjects
from app.db.db import get_db_session
from app.schemas.subject_schema import SubjectCreateSchema, SubjectOutSchema
from app.schemas.user_schema import UserOutSchema


router = APIRouter(
    prefix="/subjects",
    tags=["subjects"]
)

# ensure admin
def ensure_admin(current_user: UserOutSchema):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")

# add new subject 
@router.post("/")
async def create_new_subject(
    subject_data: SubjectCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
):
    ensure_admin(current_user)

    try:
        return await create_subject(db, subject_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get all subjects
@router.get("/", response_model=list[SubjectOutSchema])
async def get_all_subjects(db: AsyncSession = Depends(get_db_session)):
    try:
        return await get_subjects(db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get single subject
@router.get("/{id}", response_model=SubjectOutSchema)
async def get_single_subject(
    id: int, 
    db: AsyncSession = Depends(get_db_session)):
    try:
        return await get_subject(db, id)
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
        return await delete_subject(db, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))