from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authenticated_user import get_current_user
from app.db.db import get_db_session
from app.permissions.role_checks import ensure_admin, ensure_admin_or_teacher
from app.schemas.subject_offering_schema import SubjectOfferingCreateSchema, SubjectOfferingResponseSchema, SubjectOfferingUpdateSchema
from app.schemas.subject_schema import SubjectOutSchema
from app.schemas.user_schema import UserOutSchema
from app.services.subject_offering_service import SubjectOfferingService


router = APIRouter(
    prefix="/subject_offering",
    tags=["subject_offering"] # for swagger
)

# TODO: add token_injection in secured routes

@router.post("/", dependencies=[Depends(ensure_admin)])
async def create_new_subject_offering(
    sub_off_data: SubjectOfferingCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    
    return await SubjectOfferingService.create_subject_offering(sub_off_data, db)


# get offered subjects list for marking (Admin=All subjects, Teacher=subjects they teach)
@router.get("/offered_subjects", dependencies=[Depends(ensure_admin_or_teacher)], 
            response_model=list[SubjectOutSchema])
async def get_offered_subjects_for_marking(
    semester_id: int,
    department_id: int,
    current_user: UserOutSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    return await SubjectOfferingService.get_offered_subjects_for_marking(db, semester_id, department_id, current_user)


@router.get("/{subject_offering_id}", response_model=SubjectOfferingResponseSchema)
async def get_single_subject_offering(
    subject_offering_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    return await SubjectOfferingService.get_subject_offering(db, subject_offering_id)


@router.get("/", response_model=list[SubjectOfferingResponseSchema])
async def get_all_subject_offerings(db: AsyncSession = Depends(get_db_session)):
    return await SubjectOfferingService.get_subject_offerings(db)


@router.patch("/{subject_offering_id}", response_model=SubjectOfferingResponseSchema,
dependencies=[Depends(ensure_admin)])
async def update_a_subject_offering(
    subject_offering_id: int,
    update_data: SubjectOfferingUpdateSchema,
    db: AsyncSession = Depends(get_db_session)
):  
    return await SubjectOfferingService.update_subject_offering(db, update_data, subject_offering_id)


@router.delete("/{subject_offering_id}", dependencies=[Depends(ensure_admin)])
async def delete_a_subject_offering(
    subject_offering_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    return await SubjectOfferingService.delete_subject_offering(db, subject_offering_id)




# TODO: add this subject_offering to db after deploying or creating the frontend
"""
Subject Offerings for Tourism 1st Semester
  {"taught_by_id": 16, "subject_id": 1, "department_id": 6},
  {"taught_by_id": 17, "subject_id": 2, "department_id": 6},
  {"taught_by_id": 18, "subject_id": 3, "department_id": 6},
  {"taught_by_id": 19, "subject_id": 13, "department_id": 6},
  {"taught_by_id": 16, "subject_id": 14, "department_id": 6},
  {"taught_by_id": 17, "subject_id": 15, "department_id": 6},
  {"taught_by_id": 18, "subject_id": 16, "department_id": 6},
  {"taught_by_id": 19, "subject_id": 17, "department_id": 6}
"""