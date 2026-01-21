from typing import Any
from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models import User
from app.models import Department, Mark, Semester, Student, Subject, SubjectOfferings, Teacher
from sqlalchemy.exc import IntegrityError
from fastapi import Request


class AdminDashboardService:

    @staticmethod
    async def get_all_table_data_count(
        db: AsyncSession,
        request: Request | None = None
    ):

        try:
            # helper function to get count of any model/table
            async def get_count(model):
                query = select(func.count(model.id))
                result = await db.execute(query)
                return result.scalar() or 0

            # Count all users
            total_users = await get_count(User)

            # Count total admin
            admin_count_result = await db.execute(select(func.count(User.id)).where(
                or_(
                    User.role == "admin",
                    User.role == "super_admin"
                )
            ))

            total_admins = admin_count_result.scalar() or 0

            # direct counts from other tables
            counts = {
                "users": total_users,
                "admins": total_admins,
                "teachers": await get_count(Teacher),
                "students": await get_count(Student),
                "departments": await get_count(Department),
                "semesters": await get_count(Semester),
                "subjects": await get_count(Subject),
                "assigned courses": await get_count(SubjectOfferings),
                "marks": await get_count(Mark)
            }

            return counts

        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while getting all table count: {e}")
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
