from fastapi import HTTPException, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.integrity_error_parser import parse_integrity_error
from app.models import Department
from app.models.audit_log_model import LogLevel
from app.schemas.department_schema import DepartmentCreateSchema, DepartmentOutSchema, DepartmentUpdateSchema
from sqlalchemy.exc import IntegrityError

from app.schemas.user_schema import UserOutSchema
from app.services.audit_logging_service import create_audit_log


class DepartmentService:

    @staticmethod
    async def create_department(
        department_data: DepartmentCreateSchema,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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
            # refresh the object(get the new data)
            await db.refresh(new_department)

            await create_audit_log(
                db=db, request=request, level=LogLevel.INFO.value,
                action="CREATE DEPARTMENT SUCCCESS",
                details=f"New Department created successfully. ID: {new_department.id}",
                created_by=authorized_user.id
            )

            return {
                "message": f"New Department created successfully. ID: {new_department.id}"
            }
        except IntegrityError as e:
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            await create_audit_log(
                db=db, request=request, level=LogLevel.ERROR.value,
                action="CREATE DEPARTMENT ERROR",
                details=f"Error while creating new department: {readable_error}",
                created_by=authorized_user.id,
                payload={
                    "error": readable_error,
                    "raw_error": error_msg,
                    "payload_data": department_data.model_dump()
                }
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def get_departments(db: AsyncSession):
        statement = select(Department).order_by(Department.department_name)
        result = await db.execute(statement)

        return result.scalars().all()

    @staticmethod
    async def get_department(db: AsyncSession, department_id: int):
        statement = select(Department).where(Department.id == department_id)
        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def update_department(
        department_id: int,
        department_data: DepartmentUpdateSchema,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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

            await create_audit_log(
                db=db, request=request, level=LogLevel.INFO.value,
                action="UPDATE DEPARTMENT SUCCCESS",
                details=f"Department: {department.department_name} updated",
                created_by=authorized_user.id,
                payload={
                    "payload_data": department_data.model_dump(exclude_unset=True)
                }
            )

            return {
                "message": f"{department.department_name} department updated successfully. ID: {department.id}"
            }
        except IntegrityError as e:
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            await create_audit_log(
                db=db, request=request, level=LogLevel.ERROR.value,
                action="UPDATE DEPARTMENT ERROR",
                details=f"Department update failed. Error: {readable_error}",
                created_by=authorized_user.id,
                payload={
                    "error": readable_error,
                    "raw_error": error_msg,
                    "payload_data": department_data.model_dump()
                }
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    @staticmethod
    async def delete_department(
        department_id: int,
        request: Request,
        db: AsyncSession,
        authorized_user: UserOutSchema
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

            await create_audit_log(
                db=db, request=request, level=LogLevel.INFO.value,
                action="DELETE DEPARTMENT SUCCCESS",
                details=f"Department: {department.department_name}, ID: {department.id} deleted",
                created_by=authorized_user.id,
                payload={
                    "payload_data": department_id
                }
            )

            return {"message": f"{department.department_name} department deleted successfully"}
        except IntegrityError as e:
            # generally the PostgreSQL's error message will be in e.orig.args[0]
            error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
                e)

            # send the error message to the parser
            readable_error = parse_integrity_error(error_msg)

            await create_audit_log(
                db=db, request=request, level=LogLevel.ERROR.value,
                action="DELETE DEPARTMENT ERROR",
                details=f"Department deletion failed. Error: {readable_error}",
                created_by=authorized_user.id,
                payload={
                    "error": readable_error,
                    "raw_error": error_msg,
                    "payload_data": department_id
                }
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)
