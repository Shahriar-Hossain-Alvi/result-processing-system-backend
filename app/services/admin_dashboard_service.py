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
            # 1. Build a single query that wraps multiple subqueries
            query = select(
                select(func.count(User.id)).scalar_subquery().label("users"),
                select(func.count(User.id)).where(User.role.in_(
                    ["admin", "super_admin"])).scalar_subquery().label("admins"),
                select(func.count(Teacher.id)
                       ).scalar_subquery().label("teachers"),
                select(func.count(Student.id)
                       ).scalar_subquery().label("students"),
                select(func.count(Department.id)
                       ).scalar_subquery().label("departments"),
                select(func.count(Semester.id)
                       ).scalar_subquery().label("semesters"),
                select(func.count(Subject.id)
                       ).scalar_subquery().label("subjects"),
                select(func.count(SubjectOfferings.id)
                       ).scalar_subquery().label("assigned_courses"),
                select(func.count(Mark.id)).scalar_subquery().label("marks")
            )

            # 2. Execute the query
            result = await db.execute(query)

            # 3. Fetch the first row
            row = result.fetchone()

            # 4. Critical Check: If row is None, return zeros instead of crashing
            if row is None:
                return {k: 0 for k in ["users", "admins", "teachers", "students", "departments", "semesters", "subjects", "assigned courses", "marks"]}

            # 5. Return the mapped data
            return {
                "users": row.users,
                "admins": row.admins,
                "teachers": row.teachers,
                "students": row.students,
                "departments": row.departments,
                "semesters": row.semesters,
                "subjects": row.subjects,
                "assigned courses": row.assigned_courses,
                "marks": row.marks
            }

        # helper function to get count of any model/table
        # async def get_count(model):
        #     query = select(func.count(model.id))
        #     result = await db.execute(query)
        #     return result.scalar() or 0

        # # Count all users
        # total_users = await get_count(User)

        # # Count total admin
        # admin_count_result = await db.execute(select(func.count(User.id)).where(
        #     or_(
        #         User.role == "admin",
        #         User.role == "super_admin"
        #     )
        # ))

        # total_admins = admin_count_result.scalar() or 0

        # # direct counts from other tables
        # counts = {
        #     "users": total_users,
        #     "admins": total_admins,
        #     "teachers": await get_count(Teacher),
        #     "students": await get_count(Student),
        #     "departments": await get_count(Department),
        #     "semesters": await get_count(Semester),
        #     "subjects": await get_count(Subject),
        #     "assigned courses": await get_count(SubjectOfferings),
        #     "marks": await get_count(Mark)
        # }

        # return counts

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


# @staticmethod
# async def get_all_table_data_count(db: AsyncSession, request: Request | None = None):
#     try:
#         # We fetch all counts in one single SQL execution
#         query = select(
#             select(func.count(User.id)).scalar_subquery().label("users"),
#             select(func.count(User.id)).where(User.role.in_(
#                 ["admin", "super_admin"])).scalar_subquery().label("admins"),
#             select(func.count(Teacher.id)).scalar_subquery().label("teachers"),
#             select(func.count(Student.id)).scalar_subquery().label("students"),
#             select(func.count(Department.id)
#                    ).scalar_subquery().label("departments"),
#             select(func.count(Semester.id)).scalar_subquery().label("semesters"),
#             select(func.count(Subject.id)).scalar_subquery().label("subjects"),
#             select(func.count(SubjectOfferings.id)
#                    ).scalar_subquery().label("assigned_courses"),
#             select(func.count(Mark.id)).scalar_subquery().label("marks")
#         )

#         result = await db.execute(query)
#         row = result.fetchone()

#         return {
#             "users": row[0],
#             "admins": row[1],
#             "teachers": row[2],
#             "students": row[3],
#             "departments": row[4],
#             "semesters": row[5],
#             "subjects": row[6],
#             "assigned courses": row[7],
#             "marks": row[8]
#         }
#     except Exception as e:
#         await db.rollback()
        # ... your existing error handling ...
