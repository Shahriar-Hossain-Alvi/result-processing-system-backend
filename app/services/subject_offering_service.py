import time
from typing import Any
from loguru import logger
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models.department_model import Department
from app.models.subject_model import Subject
from app.models.subject_offerings_model import SubjectOfferings
from app.models.teacher_model import Teacher
from app.models.user_model import User
from app.schemas.subject_offering_schema import SubjectOfferingCreateSchema, SubjectOfferingUpdateSchema
from fastapi import HTTPException, Request, status
from app.schemas.user_schema import UserOutSchema
from app.utils import check_existence
from sqlalchemy.exc import IntegrityError


class SubjectOfferingService:

    # create subject offering
    @staticmethod
    async def create_subject_offering(
        sub_off_data: SubjectOfferingCreateSchema,
        db: AsyncSession,
        request: Request | None = None
    ):
        # validate teacher id and role
        await check_existence(Teacher, db, sub_off_data.taught_by_id, "Teacher")

        # validate department id
        await check_existence(Department, db, sub_off_data.department_id, "Department")

        # validate subject id
        await check_existence(Subject, db, sub_off_data.subject_id, "Subject")

        #  check if same subject offering exists
        is_exists = await db.scalar(select(SubjectOfferings).where(
            and_(
                SubjectOfferings.department_id == sub_off_data.department_id,
                SubjectOfferings.subject_id == sub_off_data.subject_id,
                SubjectOfferings.subject_id == sub_off_data.subject_id
            )
        ))

        if is_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Same subject offering already exists with this Teacher, Department and Subject.")

        # One semester can have maximum 7 subjects in a department
        current_semester_id = await db.scalar(select(Subject.semester_id).where(Subject.id == sub_off_data.subject_id))
        current_dept_id = await db.scalar(select(Department.id).where(Department.id == sub_off_data.department_id))

        if not current_semester_id or not current_dept_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subject or department")

        existing_count = await db.scalar(
            select(func.count(SubjectOfferings.id))
            .join(Subject)
            .where(
                SubjectOfferings.department_id == current_dept_id,
                Subject.semester_id == current_semester_id
            )
        )

        if existing_count is not None and existing_count >= 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This department already has 7 subjects in this semester. Cannot add more.")

        try:
            offered_subject = SubjectOfferings(
                **sub_off_data.model_dump()
            )

            db.add(offered_subject)
            await db.commit()
            await db.refresh(offered_subject)
            logger.success("Subject offering created successfully")
            return {
                "message": f"Subject offering created successfully. ID: {offered_subject.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(
                f"Integrity error while creating new subject offering: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if sub_off_data:
                    payload["data"] = sub_off_data.model_dump(
                        mode="json"
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    # get single subject offering
    # @staticmethod
    # async def get_subject_offering(db: AsyncSession, subject_offering_id: int):
    #     subject_offering = await db.scalar(select(SubjectOfferings).where(SubjectOfferings.id == subject_offering_id))

    #     if not subject_offering:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")

    #     return subject_offering

    @staticmethod  # get all subject offerings in Assign Course page
    async def get_subject_offerings(
        db: AsyncSession,
        order_by_filter: str | None = None,
        filter_by_department: int | None = None,
        search: str | None = None
    ):
        query = select(SubjectOfferings).options(
            selectinload(SubjectOfferings.department),
            selectinload(SubjectOfferings.subject).selectinload(
                Subject.semester),
            selectinload(SubjectOfferings.taught_by).selectinload(
                Teacher.department)
        )

        if order_by_filter == "asc":
            query = query.order_by(asc(SubjectOfferings.id))

        if order_by_filter == "desc":
            query = query.order_by(desc(SubjectOfferings.id))

        if filter_by_department is not None:
            query = query.where(
                SubjectOfferings.department_id == filter_by_department)

        # Search by teacher name
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    SubjectOfferings.taught_by.has(
                        Teacher.name.ilike(search_filter))
                )
            )

        try:
            result = await db.execute(query)
            subject_offerings = result.scalars().unique().all()

            return subject_offerings
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(
                f"Integrity error while creating new subject offering: {e}")
            logger.error(f"Readable Error: {readable_error}")

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # update subject offering
    async def update_subject_offering(
        subject_offering_id: int,
        update_data: SubjectOfferingUpdateSchema,
        db: AsyncSession,
        request: Request | None = None
    ):

        # check for existing subject offering
        subject_offering = await db.scalar(select(SubjectOfferings).where(SubjectOfferings.id == subject_offering_id))

        if not subject_offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")

        updated_data = update_data.model_dump(exclude_unset=True)

        # check if taught_by exists
        if "taught_by_id" in updated_data and updated_data["taught_by_id"] is not None:
            await check_existence(Teacher, db, updated_data["taught_by_id"], "Teacher")

        # check if department exists
        if "department_id" in updated_data:
            await check_existence(Department, db, updated_data["department_id"], "Department")

        # check if subject exists
        if "subject_id" in updated_data:
            await check_existence(Subject, db, updated_data["subject_id"], "Subject")

        for key, value in updated_data.items():
            setattr(subject_offering, key, value)

        try:
            db.add(subject_offering)
            await db.commit()
            await db.refresh(subject_offering)

            return subject_offering
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(
                f"Integrity error while updating subject offering: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if update_data:
                    payload["data"] = update_data.model_dump(
                        mode="json",
                        exclude_unset=True,
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # delete subject offering
    async def delete_subject_offering(
        db: AsyncSession,
        subject_offering_id: int,
        request: Request | None = None
    ):
        try:
            subject_offering = await db.scalar(select(SubjectOfferings).where(SubjectOfferings.id == subject_offering_id))

            if not subject_offering:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")

            await db.delete(subject_offering)
            await db.commit()
            logger.success(
                f"Subject offering deleted successfully. ID: {subject_offering.id}")
            return {
                "message": f"Subject offering deleted successfully. ID: {subject_offering.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(
                f"Integrity error while deleting subject offering: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    # get offered subjects for marking
    # admin -> see all subjects for marking
    # teacher -> see only the subjects they teach
    # @staticmethod
    # async def get_offered_subjects_for_marking(
    #     db: AsyncSession,
    #     semester_id: int,
    #     department_id: int,
    #     current_user: UserOutSchema
    # ):
    #     stmt = select(Subject)\
    #         .join(Subject.subject_offerings)\
    #         .where(
    #             and_(
    #                 Subject.semester_id == semester_id,
    #                 SubjectOfferings.department_id == department_id
    #             )
    #     )

    #     # restrict subject list for teachers
    #     if current_user.role.value == "teacher":
    #         stmt = stmt.where(
    #             SubjectOfferings.taught_by_id == current_user.id
    #         )

    #     result = await db.execute(stmt)
    #     subjects = result.scalars().all()
    #     return subjects
