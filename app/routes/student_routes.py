from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.crud_operations.student_service import create_student, delete_student, get_student, get_students, update_student
from app.db.db import get_db_session
from app.schemas.student_schema import StudentCreateSchema, StudentOutSchema, StudentUpdateSchema
from app.schemas.user_schema import UserOutSchema

router = APIRouter(
    prefix="/students",
    tags=["students"] # for swagger
)


# ensure admin
def ensure_admin(current_user: UserOutSchema):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
# ensure admin or teacher
def ensure_admin_or_teacher(current_user: UserOutSchema):
    if current_user.role.value not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Unauthorized access")


# create student record
@router.post("/")
async def create_student_record(
        student_data: StudentCreateSchema,
        db: AsyncSession = Depends(get_db_session),
        current_user: UserOutSchema = Depends(get_current_user)
):
    ensure_admin(current_user)

    try:
        return await create_student(db, student_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get all students
@router.get("/", response_model=list[StudentOutSchema])
async def get_all_students(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
):
    ensure_admin_or_teacher(current_user)
    
    try:
        return await get_students(db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get single student
@router.get("/{id}", response_model=StudentOutSchema)
async def get_single_student(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user),
):
    try:
        return await get_student(db, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update a student 
@router.patch("/{id}", response_model=StudentOutSchema)
async def update_single_student(
    id: int,
    student_data: StudentUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
):
    
    ensure_admin(current_user)
    
    try:
        return await update_student(db, id, student_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# delete a student 
@router.delete("/{id}")
async def delete_single_student(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
):
    
    ensure_admin(current_user)
    
    try:
        return await delete_student(db, id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
