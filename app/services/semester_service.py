from typing import Any
from fastapi import HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models import Semester
from app.schemas.semester_schema import SemesterCreateSchema, SemesterUpdateSchema
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError


class SemesterService:

    @staticmethod  # create new semester
    async def create_semester(
        semester_data: SemesterCreateSchema,
        db: AsyncSession,
        request: Request | None = None,
    ):
        statement = select(Semester).where(
            or_(
                Semester.semester_name == semester_data.semester_name,
                Semester.semester_number == semester_data.semester_number
            )
        )
        result = await db.execute(statement)
        is_semester_exist = result.scalar_one_or_none()

        if (is_semester_exist):
            logger.error("Semester already exist")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Semester already exist")

        try:
            new_semester = Semester(**semester_data.model_dump())
            db.add(new_semester)
            await db.commit()
            await db.refresh(new_semester)
            logger.success("New Semester created successfully")

            return {
                "message": f"New Semester created successfully. ID: {new_semester.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while creating new Semester: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if semester_data:
                    payload["data"] = semester_data.model_dump(
                        mode="json")

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # get all semesters
    async def get_semesters(db: AsyncSession):
        statement = select(Semester).order_by(Semester.semester_number)
        result = await db.execute(statement)

        return result.scalars().all()

    # @staticmethod # get single semester
    # async def get_semester(db: AsyncSession, semester_id: int):
    #     statement = select(Semester).where(Semester.id == semester_id)
    #     result = await db.execute(statement)

    #     return result.scalar_one_or_none()

    @staticmethod  # update single semester
    async def update_semester(
        semester_id: int,
        semester_update_data: SemesterUpdateSchema,
        db: AsyncSession,
        request: Request | None = None
    ):
        statement = select(Semester).where(Semester.id == semester_id)
        result = await db.execute(statement)
        semester = result.scalar_one_or_none()

        if not semester:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")

        try:
            updated_semester_data = semester_update_data.model_dump(
                exclude_unset=True)  # convert to dictionary

            for key, value in updated_semester_data.items():
                setattr(semester, key, value)

            await db.commit()
            await db.refresh(semester)
            logger.success("Semester updated successfully")

            return {
                "message": f"Semester updated successfully. ID: {semester.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state.
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating semester: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if semester_update_data:
                    payload["data"] = semester_update_data.model_dump(
                        mode="json",
                        exclude_unset=True,
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # delete single semester by super admin
    async def delete_semester(
        semester_id: int,
        db: AsyncSession,
        request: Request | None = None,
    ):
        statement = select(Semester).where(Semester.id == semester_id)
        result = await db.execute(statement)
        semester = result.scalar_one_or_none()

        if not semester:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")
        try:
            await db.delete(semester)
            await db.commit()
            logger.success("Semester deleted successfully")

            return {"message": f"{semester.semester_name} semester deleted successfully"}
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while deleting semester: {e}")
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
