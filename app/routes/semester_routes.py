from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.crud_operations.semester_service import create_semester, delete_semester, get_semester, get_semesters, update_semester
from app.db.db import get_db_session
from app.schemas.semester_schema import SemesterCreateSchema, SemesterOutSchema, SemesterUpdateSchema
from app.schemas.user_schema import UserOutSchema


router = APIRouter(
    prefix="/semesters",
    tags=["semesters"] # for swagger
)


# create semester
@router.post("/")
async def add__new_semester(
    semester_data: SemesterCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
):
    if(current_user.role.value != "admin"):
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    
    try: 
        return await create_semester(db, semester_data)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# get all semester
@router.get("/", response_model=list[SemesterOutSchema])
async def get_all_semesters(db: AsyncSession = Depends(get_db_session)):
    try:
        return await get_semesters(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# get single semester
@router.get("/{id}", response_model=SemesterOutSchema)
async def get_single_semester(id: int, db: AsyncSession = Depends(get_db_session)):
    try:
        return await get_semester(db, id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  

# update a semester
@router.patch("/{id}", response_model=SemesterOutSchema)
async def update_single_semester(
    id: int,
    semester_data: SemesterUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
): 
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")

    try:
        return await update_semester(db, id, semester_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
# delete a semester
@router.delete("/{id}")
async def delete_single_semester(
    id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: UserOutSchema = Depends(get_current_user)
    ):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    try:
        return await delete_semester(db, id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))