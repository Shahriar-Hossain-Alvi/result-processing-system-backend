from fastapi import HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.integrity_error_parser import parse_integrity_error
from app.models import Semester
from app.schemas.semester_schema import SemesterCreateSchema, SemesterUpdateSchema
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from app.schemas.user_schema import UserOutSchema


class SemesterService:

    @staticmethod
    async def create_semester(
        semester_data: SemesterCreateSchema,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value,
            #     action="CREATE SEMESTER SUCCCESS",
            #     details=f"Semester: {new_semester.semester_name}, ID: {new_semester.id} created",
            #     created_by=authorized_user.id,
            #     payload={
            #         "payload_data": semester_data.model_dump()
            #     }
            # )

            return {
                "message": f"New Semester created successfully. ID: {new_semester.id}"
            }
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error while creating new Semester: {e}")

            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(
                f"Integrity error while creating new Semester: {readable_error}")

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value,
            #     action="CREATE SEMESTER ERROR",
            #     details=f"Semester creation failed. Error: {readable_error}",
            #     created_by=getattr(authorized_user, "id", None),
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #         "payload_data": semester_data.model_dump()
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def get_semesters(db: AsyncSession):
        statement = select(Semester).order_by(Semester.semester_number)
        result = await db.execute(statement)

        return result.scalars().all()

    @staticmethod
    async def get_semester(db: AsyncSession, semester_id: int):
        statement = select(Semester).where(Semester.id == semester_id)
        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def update_semester(
        semester_id: int,
        semester_update_data: SemesterUpdateSchema,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value,
            #     action="UPDATE SEMESTER SUCCCESS",
            #     details=f"Semester: {semester.semester_name} updated",
            #     created_by=authorized_user.id,
            #     payload={
            #         "payload_data": semester_update_data.model_dump(exclude_unset=True)
            #     }
            # )

            return {
                "message": f"Semester updated successfully. ID: {semester.id}"
            }
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error while updating semester: {e}")
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)
            logger.error(
                f"Integrity error while updating semester: {readable_error}")

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value,
            #     action="UPDATE SEMESTER ERROR",
            #     details=f"Semester update failed. Error: {readable_error}",
            #     created_by=getattr(authorized_user, "id", None),
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #         "payload_data": semester_update_data.model_dump()
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def delete_semester(
        semester_id: int,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.INFO.value,
            #     action="DELETE SEMESTER SUCCCESS",
            #     details=f"Semester: {semester.semester_name}, ID: {semester.id} deleted",
            #     created_by=authorized_user.id,
            #     payload={
            #         "payload_data": semester_id
            #     }
            # )

            return {"message": f"{semester.semester_name} semester deleted successfully"}
        except IntegrityError as e:
            await db.rollback()
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            # await create_audit_log_isolated(
            #     request=request, level=LogLevel.ERROR.value,
            #     action="DELETE SEMESTER ERROR",
            #     details=f"Semester deletion failed. Error: {readable_error}",
            #     created_by=getattr(authorized_user, "id", None),
            #     payload={
            #         "error": readable_error,
            #         "raw_error": error_msg,
            #         "payload_data": semester_id
            #     }
            # )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)
