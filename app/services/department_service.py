from typing import Any
from fastapi import HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models import Department
from app.schemas.department_schema import DepartmentCreateSchema, DepartmentUpdateSchema
from sqlalchemy.exc import IntegrityError


class DepartmentService:

    @staticmethod  # create department
    async def create_department(
        department_data: DepartmentCreateSchema,
        db: AsyncSession,
        request: Request | None = None,
    ):
        lowercase_department_name = department_data.department_name.lower().strip()

        # check for existing department
        statement = select(Department).where(
            Department.department_name == lowercase_department_name)
        result = await db.execute(statement)
        is_exist = result.scalar_one_or_none()

        if (is_exist):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exist")

        try:
            new_department = Department(
                department_name=lowercase_department_name)

            db.add(new_department)  # add the new_department to db(session)
            await db.commit()
            await db.refresh(new_department)

            logger.success("New department created successfully")
            return {
                "message": f"New Department created successfully. ID: {new_department.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while creating department: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if department_data:
                    payload["data"] = department_data.model_dump(
                        mode="json",
                        exclude_unset=True
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # get all departments
    async def get_departments(db: AsyncSession):
        statement = select(Department).order_by(Department.department_name)
        result = await db.execute(statement)

        return result.scalars().all()

    # @staticmethod # get single department
    # async def get_department(db: AsyncSession, department_id: int):
    #     statement = select(Department).where(Department.id == department_id)
    #     result = await db.execute(statement)

    #     return result.scalar_one_or_none()

    @staticmethod  # update department
    async def update_department(
        department_id: int,
        department_data: DepartmentUpdateSchema,
        db: AsyncSession,
        request: Request | None = None,
    ):
        statement = select(Department).where(Department.id == department_id)
        result = await db.execute(statement)
        department = result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        try:
            lowercase_department_name = department_data.department_name.lower().strip()

            department.department_name = lowercase_department_name

            await db.commit()
            await db.refresh(department)

            logger.success("Department updated successfully")
            return {
                "message": f"{department.department_name} department updated successfully. ID: {department.id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating department: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if department_data:
                    payload["data"] = department_data.model_dump(
                        mode="json",
                        exclude_unset=True
                    )

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # delete department by super admin
    async def delete_department(
        department_id: int,
        db: AsyncSession,
        request: Request | None = None
    ):

        statement = select(Department).where(Department.id == department_id)
        result = await db.execute(statement)
        department = result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        try:
            await db.delete(department)
            await db.commit()

            logger.success("Department deleted successfully")

            return {"message": f"{department.department_name} department deleted successfully"}
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while deleting department: {e}")
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
