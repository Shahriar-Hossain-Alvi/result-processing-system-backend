from typing import Any
from loguru import logger
from sqlalchemy import and_, select
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
        teacher = await check_existence(Teacher, db, sub_off_data.taught_by_id, "Teacher")

        # if teacher.role.value != "teacher":
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST, detail="Not a teacher")

        # validate department id
        await check_existence(Department, db, sub_off_data.department_id, "Department")

        # department = await db.scalar(select(Department).where(Department.id == sub_off_data.department_id))

        # if not department:
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        # validate subject id
        await check_existence(Subject, db, sub_off_data.subject_id, "Subject")

        # subject = await db.scalar(select(Subject).where(Subject.id == sub_off_data.subject_id))

        # if not subject:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

        """
        # Pseudo-code logic for validation
        existing_count = await db.scalar(
            select(func.count(SubjectOfferings.id))
            .join(Subject)
            .where(
                SubjectOfferings.department_id == current_dept_id,
                Subject.semester_id == current_semester_id
            )
        )

        if existing_count >= 7:
            raise HTTPException(detail="This department already has 7 subjects in this semester.")
        """

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

    @staticmethod
    async def get_subject_offering(db: AsyncSession, subject_offering_id: int):
        subject_offering = await db.scalar(select(SubjectOfferings).where(SubjectOfferings.id == subject_offering_id))

        if not subject_offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")

        return subject_offering

    # get all subject offerings

    @staticmethod
    async def get_subject_offerings(db: AsyncSession):
        try:
            query = select(SubjectOfferings).options(
                selectinload(SubjectOfferings.department),
                selectinload(SubjectOfferings.subject).selectinload(
                    Subject.semester),
                selectinload(SubjectOfferings.taught_by).selectinload(
                    Teacher.department)
            )

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

    # update subject offering

    @staticmethod
    async def update_subject_offering(db: AsyncSession, update_data: SubjectOfferingUpdateSchema, subject_offering_id: int):

        # check for existing subject offering
        subject_offering = await db.scalar(select(SubjectOfferings).where(SubjectOfferings.id == subject_offering_id))

        if not subject_offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")

        updated_data = update_data.model_dump(exclude_unset=True)

        # check if taught_by exists
        if "taught_by_id" in updated_data:
            await check_existence(User, db, updated_data["taught_by_id"], "Teacher")

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
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def delete_subject_offering(db: AsyncSession, subject_offering_id: int):
        subject_offering = await db.scalar(select(SubjectOfferings).where(SubjectOfferings.id == subject_offering_id))

        if not subject_offering:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject offering not found")

        await db.delete(subject_offering)
        await db.commit()

        return {
            "message": f"Subject offering deleted successfully. ID: {subject_offering.id}"
        }

    # get offered subjects for marking
    # admin -> see all subjects for marking
    # teacher -> see only the subjects they teach

    @staticmethod
    async def get_offered_subjects_for_marking(
        db: AsyncSession,
        semester_id: int,
        department_id: int,
        current_user: UserOutSchema
    ):
        stmt = select(Subject)\
            .join(Subject.subject_offerings)\
            .where(
                and_(
                    Subject.semester_id == semester_id,
                    SubjectOfferings.department_id == department_id
                )
        )

        # restrict subject list for teachers
        if current_user.role.value == "teacher":
            stmt = stmt.where(
                SubjectOfferings.taught_by_id == current_user.id
            )

        result = await db.execute(stmt)
        subjects = result.scalars().all()
        return subjects
