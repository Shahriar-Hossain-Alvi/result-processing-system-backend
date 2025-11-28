from app.schemas.marks_schema import MarksCreateSchema, MarksResponseSchema, MarksUpdateSchema
from app.schemas.user_schema import UserOutSchema
from app.services.marks_service import MarksService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db_session
from app.permissions.role_checks import ensure_admin_or_teacher, ensure_admin
from app.core.authenticated_user import get_current_user


router = APIRouter(
    prefix="/marks",
    tags=["marks"] # for swagger
)


# create marks
@router.post("/", 
    dependencies=[Depends(ensure_admin_or_teacher)],
    response_model=MarksResponseSchema
)
async def create_new_mark(
    mark_data: MarksCreateSchema,
    current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    
    return await MarksService.create_mark(db, mark_data, current_user)


# update marks
@router.patch("/{mark_id}",
    dependencies=[Depends(ensure_admin_or_teacher)],
    response_model=MarksResponseSchema              
)
async def update_a_mark(
    mark_id: int,
    mark_data: MarksUpdateSchema,
    current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):

    return await MarksService.update_mark(db, mark_data, mark_id, current_user)