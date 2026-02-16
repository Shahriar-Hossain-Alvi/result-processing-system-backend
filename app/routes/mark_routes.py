from loguru import logger
from app.core.exceptions import DomainIntegrityError
from app.schemas.marks_schema import MarksCreateSchema, MarksResponseSchema, MarksUpdateSchema, SemesterWiseAllSubjectsMarksResponseSchema, SemesterWiseAllSubjectsMarksWithPopulatedDataResponseSchema
from app.schemas.user_schema import UserOutSchema
from app.services.marks_service import MarksService
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db_session
from app.permissions import ensure_roles
from app.core.authenticated_user import get_current_user


router = APIRouter(
    prefix="/marks",
    tags=["marks"]  # for swagger
)


# create marks: used in Insert and Update marks page to add marks for a student
@router.post("/")
async def create_new_mark(
    request: Request,
    mark_data: MarksCreateSchema,
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin", "teacher"])),
    db: AsyncSession = Depends(get_db_session),
):
    # attach action
    request.state.action = "INSERT MARK"
    try:
        return await MarksService.create_mark(db, mark_data, authorized_user, request)
    except DomainIntegrityError as de:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Create mark unexpected Error: {e}")
        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get result department wise with semester and session
@router.get(
    "/get_all_marks_with_filters",
    response_model=list[SemesterWiseAllSubjectsMarksWithPopulatedDataResponseSchema]
)
async def get_all_filtered_marks(
    request: Request,
    semester_id: int | None = None,
    department_id: int | None = None,
    session: str | None = None,
    result_status: str | None = None,
    authorized_user: UserOutSchema = Depends(
        ensure_roles(["super_admin", "admin", "teacher"])),
    db: AsyncSession = Depends(get_db_session),

):
    try:
        return await MarksService.get_all_marks_with_filters(db, authorized_user, semester_id, department_id, session, result_status)
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Get all marks unexpected Error: {e}")
        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update marks
# @router.patch("/{mark_id}", response_model=MarksResponseSchema)
# async def update_a_mark(
#     mark_id: int,
#     mark_data: MarksUpdateSchema,
#     authorized_user: UserOutSchema = Depends(
#         ensure_roles(["super_admin", "admin", "teacher"])),
#     db: AsyncSession = Depends(get_db_session),
# ):

#     try:
#         return await MarksService.update_mark(db, mark_data, mark_id, authorized_user)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete marks
# @router.delete("/{mark_id}", response_model=MarksResponseSchema)
# async def delete_a_mark(
#     mark_id: int,
#     authorized_user: UserOutSchema = Depends(ensure_roles(["super_admin"])),
#     db: AsyncSession = Depends(get_db_session),
# ):
#     try:
#         return await MarksService.delete_mark(db, mark_id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# get all subjects marks for a student
# @router.get("/student/{student_id}", response_model=list[SemesterWiseAllSubjectsMarksResponseSchema])
# async def get_all_subjects_marks_for_a_student(
#     student_id: int,
#     semester_id: int | None = Query(None),
#     subject_id: int | None = Query(None),
#     db: AsyncSession = Depends(get_db_session),
#     current_user: UserOutSchema = Depends(get_current_user),
# ):
#     try:
#         return await MarksService.get_all_marks_for_a_student(db, student_id, semester_id, subject_id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
