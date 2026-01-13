from typing import Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models.subject_model import Subject
from app.models.subject_offerings_model import SubjectOfferings
from app.schemas.subject_schema import SubjectCreateSchema
from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from app.schemas.user_schema import UserOutSchema


class SubjectService:

    @staticmethod
    async def create_subject(
            subject_data: SubjectCreateSchema,
            db: AsyncSession,
            request: Request | None = None
    ):
        capitalized_subject_code = subject_data.subject_code.upper().strip()

        # check for existing subject
        subject = await db.scalar(select(Subject).where(Subject.subject_code == capitalized_subject_code))

        if subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Subject already exist")

        try:
            new_subject = Subject(
                **subject_data.model_dump(exclude={"subject_code"}), subject_code=capitalized_subject_code)

            db.add(new_subject)
            await db.commit()
            await db.refresh(new_subject)
            logger.success("New subject created successfully")
            return {
                "message": f"new_subject created successfully. ID: {new_subject.id}. Name: {new_subject.subject_title}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

           # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while creating subject: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if subject_data:
                    payload["data"] = subject_data.model_dump(mode="json")

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod
    async def get_subject(db: AsyncSession, subject_id: int):
        subject = await db.scalar(select(Subject).where(Subject.id == subject_id))

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

        return subject

    @staticmethod
    async def get_subjects(db: AsyncSession):
        subjects = await db.execute(select(Subject))

        return subjects.scalars().all()

    @staticmethod
    async def delete_subject(
        subject_id: int,
        db: AsyncSession,
        request: Request | None = None
    ):
        subject = await db.scalar(select(Subject).where(Subject.id == subject_id))

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

        try:
            await db.delete(subject)
            await db.commit()
            logger.success("Subject deleted successfully")
            return {"message": f"Subject: {subject.subject_title} deleted successfully"}
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while deleting subject: {e}")
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

    @staticmethod
    async def get_subject_by_code(
            db: AsyncSession,
            subject_code: str
    ):
        capitalized_subject_code = subject_code.upper().strip()

        subject = await db.scalar(select(Subject).where(Subject.subject_code == capitalized_subject_code))

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

        return subject
