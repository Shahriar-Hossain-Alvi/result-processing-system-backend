from collections import defaultdict
from typing import Annotated, Any
from loguru import logger
from sqlalchemy import and_, func, join, select
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models import Mark, ResultStatus
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Query, Request, status
from app.models.mark_model import ResultChallengeStatus
from app.models.semester_model import Semester
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.subject_offerings_model import SubjectOfferings
from app.models.teacher_model import Teacher
from app.models.user_model import User
from app.schemas.marks_schema import MarksCreateSchema, MarksUpdateSchema
from app.schemas.user_schema import UserOutSchema
from app.utils import check_existence
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy.exc import IntegrityError


class MarksService:

    @staticmethod
    def compute_total_marks_and_gpa(mark_data: Mark):
        assignment = getattr(mark_data, "assignment_mark", 0) or 0
        midterm = getattr(mark_data, "midterm_mark", 0) or 0
        class_test = getattr(mark_data, "class_test_mark", 0) or 0
        final = getattr(mark_data, "final_exam_mark", 0) or 0

        # calculate incourse mark
        total_in_course_in_60 = float(
            assignment + midterm + class_test)

        # convert incourse mark to 20%
        converted_incourse_to_20 = (
            total_in_course_in_60*20)/60

        # Total marks (incourse + final)
        total = float(converted_incourse_to_20 + final)

        # Rounding off to 2 decimal places
        mark_data.total_mark = round(total, 2)

        # calculate gpa
        if total >= 80:
            mark_data.GPA = 4.0
        elif total >= 75:
            mark_data.GPA = 3.75
        elif total >= 70:
            mark_data.GPA = 3.5
        elif total >= 65:
            mark_data.GPA = 3.25
        elif total >= 60:
            mark_data.GPA = 3.0
        elif total >= 55:
            mark_data.GPA = 2.75
        elif total >= 50:
            mark_data.GPA = 2.5
        elif total >= 45:
            mark_data.GPA = 2.25
        elif total >= 40:
            mark_data.GPA = 2.0
        else:
            mark_data.GPA = 0

        return mark_data

    # create marks
    @staticmethod
    async def create_mark(
        db: AsyncSession,
        mark_data: MarksCreateSchema,
        current_user: UserOutSchema,
        request: Request | None = None
    ):
        # check if a mark for this subject+student+semester already exist

        stmt = select(Mark).where(
            and_(
                Mark.student_id == mark_data.student_id,
                Mark.subject_id == mark_data.subject_id,
                Mark.semester_id == mark_data.semester_id
            )
        )

        result = await db.execute(stmt)
        existing_mark = result.scalar_one_or_none()

        if existing_mark:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A mark already exist for this student, subject, semester.")

        # check if the student exists, throws error if not
        await check_existence(Student, db, mark_data.student_id, "Student")

        # check if the subject exists, throws error if not
        await check_existence(Subject, db, mark_data.subject_id, "Subject")

        # check if the semester exists, throws error if not
        await check_existence(Semester, db, mark_data.semester_id, "Semester")

        # check if the person is a teacher and their subject is the same as the subject of the mark
        if current_user.role.value == "teacher":
            is_taught_by_this_teacher = await db.scalar(select(SubjectOfferings).where(
                and_(
                    SubjectOfferings.taught_by_id == current_user.id,
                    SubjectOfferings.subject_id == mark_data.subject_id
                )
            ))

            if not is_taught_by_this_teacher:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to create a mark for this subject.")

        # if the user(teacher) is not different or the Admin, then create the mark
        # create new_mark object but it does not have the total marks and gpa yet
        new_mark = Mark(
            **mark_data.model_dump()
        )

        # pass this new_mark object to the compute_total_marks_and_gpa function to get the total marks and gpa. It'll update the new_mark object
        MarksService.compute_total_marks_and_gpa(new_mark)

        try:
            db.add(new_mark)
            await db.commit()
            await db.refresh(new_mark)

            return {"message": f"Mark inserted successfully. Total Mark: {new_mark.total_mark} GPA: {new_mark.GPA}"}
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while inserting mark: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if mark_data:
                    mark_data.model_dump(
                        mode="json"
                    )
                    payload["data"] = mark_data

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # group marks by semester
    def group_marks_by_category(marks):
        # create a dictionary where the key will be department name, semester name and session
        grouped = defaultdict(list)

        for m in marks:
            category_key = (
                m.student.department.department_name,
                m.semester.semester_name,
                m.student.session
            )
            grouped[category_key].append(m)

        # convert the data in a list of dictionaries
        result = []
        for key, items in grouped.items():
            dept_name, sem_name, session_name = key

            result.append({
                "department_name": dept_name,
                "semester_name": sem_name,
                "session": session_name,
                "marks": items
            })

        return result

    @staticmethod  # get result for a particular department and semester and session
    async def get_all_marks_with_filters(
        db: AsyncSession,
        current_user: UserOutSchema,
        target_semester_id: int | None = None,
        target_department_id: int | None = None,
        session: str | None = None,
        result_status: str | None = None
    ):
        # Base query with joins (Mark, Student, Subject table)
        statement = select(Mark).join(Student).join(Subject)

        # options with joinedloads to reduce the number of queries/Database Hits
        statement = statement.options(
            # Mark -> Student -> Department = get the department info
            joinedload(Mark.student).joinedload(Student.department),
            # Mark -> Student -> Semester = get the current semester info
            joinedload(Mark.student).joinedload(Student.semester),
            # Mark -> Subject = get the subject info
            joinedload(Mark.subject)
        ).order_by(Subject.subject_title)

        # If teacher → restrict to subjects they teach
        if current_user.role == "teacher":
            teacher_res = await db.execute(select(Teacher.id).where(Teacher.user_id == current_user.id))
            teacher_id = teacher_res.scalar_one_or_none()

            if not teacher_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found"
                )
            statement = statement.join(
                SubjectOfferings,
                and_(
                    SubjectOfferings.subject_id == Mark.subject_id,
                    SubjectOfferings.department_id == Student.department_id,
                )
            ).where(SubjectOfferings.taught_by_id == teacher_id)

        # If filters are present
        filters = []
        if target_semester_id:
            filters.append(Mark.semester_id == target_semester_id)
        if target_department_id:
            filters.append(Student.department_id == target_department_id)
        if session:
            filters.append(Student.session == session)
        if result_status:
            filters.append(Mark.result_status == result_status)
        if filters:
            statement = statement.where(and_(*filters))

        result = await db.execute(statement)
        marks = result.unique().scalars().all()  # remove duplicates using unique()

        return MarksService.group_marks_by_category(marks)

    @staticmethod  # update a mark
    async def update_mark(
        db: AsyncSession,
        update_data: MarksUpdateSchema,
        mark_id: int,
        current_user: UserOutSchema,
        request: Request | None = None
    ):
        # check if mark exists
        mark = await db.scalar(select(Mark).where(Mark.id == mark_id))

        if not mark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Mark data not found")

        user_role = current_user.role.value
        update_dict = update_data.model_dump(exclude_unset=True)
        logger.success(f"update_dict: {update_dict}")

        # verify teacher role and is he teaching this subject
        is_teacher_authorized = False
        if user_role == "teacher":
            is_taught_by_this_teacher = await db.scalar(select(SubjectOfferings).where(
                and_(
                    SubjectOfferings.taught_by_id == current_user.id,
                    SubjectOfferings.subject_id == mark.subject_id
                )
            ))
            if not is_taught_by_this_teacher:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to update mark for this subject.")
            is_teacher_authorized = True

        # verify student role and only update "result_challenge_status" field from "none" to "challenged". Student can challenge only once. If the result_challenge_status is already "challenged" or "resolved", raise error
        if user_role == "student":
            if set(update_dict.keys()) == {"result_challenge_status"}:
                if (update_dict["result_challenge_status"] == ResultChallengeStatus.CHALLENGED
                    and mark.result_status == ResultStatus.PUBLISHED
                        and mark.result_challenge_status == ResultChallengeStatus.NONE):
                    # set result is challenged
                    mark.result_challenge_status = ResultChallengeStatus.CHALLENGED
                    mark.result_challenge_payment_status = False  # set payment status is pending
                    mark.challenged_at = datetime.now()  # set challenged date, need for payment
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Result is not published/Already challenged once.")
            elif set(update_dict.keys()) != {"result_challenge_status"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bad Request."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You can only challenge result once!")

        # Payment update (admin and super admin only)
        if "result_challenge_payment_status" in update_dict:
            new_payment_status = update_dict["result_challenge_payment_status"]

            if new_payment_status != mark.result_challenge_payment_status:
                if user_role not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not authorized to update payment status."
                    )

                if mark.result_challenge_status == ResultChallengeStatus.CHALLENGED:
                    mark.result_challenge_payment_status = update_dict["result_challenge_payment_status"]
                    if update_dict["result_challenge_payment_status"] == True:
                        mark.challenge_payment_time = datetime.now()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Result must be in challenge status to update payment status."
                )

        # Mark update
        if user_role in ["admin", "super_admin", "teacher"] and (user_role != "teacher" or is_teacher_authorized):
            # update result status if provided
            if "result_status" in update_dict:
                mark.result_status = update_dict["result_status"]

            # update result challenge status if provided
            if "result_challenge_status" in update_dict:
                mark.result_challenge_status = update_dict["result_challenge_status"]

                # if the sent challenged status is Resolved, add the resolved date
                if update_dict["result_challenge_status"] == ResultChallengeStatus.RESOLVED:
                    mark.challenge_resolved_at = datetime.now()

            mark_fields = ["assignment_mark", "class_test_mark",
                           "midterm_mark", "final_exam_mark"]

            # check if any mark data is being updated
            actual_mark_updates = [f for f in mark_fields if f in update_dict]

            if actual_mark_updates:
                # condition check before mark update
                is_challenged = mark.result_challenge_status == ResultChallengeStatus.CHALLENGED
                is_paid = mark.result_challenge_payment_status is True
                can_update_marks = (
                    (not is_challenged)  # update normally if not challenged
                    # update if challenged and paid
                    or (is_challenged and is_paid)
                )

                if not can_update_marks:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Result is challenged & Payment is due. Cannot update marks.")

                # now update marks
                for field in actual_mark_updates:
                    setattr(mark, field, update_dict[field])

                # calculate gpa
                MarksService.compute_total_marks_and_gpa(mark)

                # Resolve challenge status (if marks updated when challenged and paid)
                if mark.result_challenge_status == ResultChallengeStatus.CHALLENGED and is_paid:
                    mark.result_challenge_status = ResultChallengeStatus.RESOLVED
                    mark.challenge_resolved_at = datetime.now()

        try:
            await db.commit()
            await db.refresh(mark)

            return {
                "message": f"Mark status updated",
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while updating mark: {e}")
            logger.error(f"Readable Error: {readable_error}")

            # attach audit payload safely
            if request:
                payload: dict[str, Any] = {
                    "raw_error": raw_error_message,
                    "readable_error": readable_error,
                }

                if update_data:
                    payload["data"] = update_data.model_dump(mode="json")

                request.state.audit_payload = payload

            raise DomainIntegrityError(
                error_message=readable_error, raw_error=raw_error_message
            )

    @staticmethod  # delete a mark
    async def delete_mark(
        db: AsyncSession,
        mark_id: int,
        request: Request | None = None,
    ):
        try:
            mark = await db.scalar(select(Mark).where(Mark.id == mark_id))

            if not mark:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")

            await db.delete(mark)
            await db.commit()

            return {
                "message": f"Mark deleted successfully for id: {mark_id}"
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(
                f"Integrity error while deleting a students mark: {e}")
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

    @staticmethod  # generate and show results to a student when all subjects are marked
    async def generate_results(
        db: AsyncSession,
        registration: str,
        semester_id: int,
        department_id: int,
        request: Request | None = None
    ):
        try:
            # fetch student
            student_stmt = select(Student).where(
                Student.registration == registration)
            student = (await db.execute(student_stmt)).scalar_one_or_none()

            if not student:
                return {
                    "message": "Student not found",
                    "total_subjects": 0,
                    "published_count": 0
                }

            # check if the student is from selected department
            if student.department_id != department_id:
                return {
                    "message": "This student doesn't belong to this department",
                    "total_subjects": 0,
                    "published_count": 0
                }

            # get total offered subject for a semester in a department
            total_offered_subjects_stmt = select(func.count(SubjectOfferings.id)).join(Subject, SubjectOfferings.subject_id == Subject.id).where(
                and_(
                    SubjectOfferings.department_id == department_id,
                    Subject.semester_id == semester_id
                )
            )

            total_offered = (await db.execute(total_offered_subjects_stmt)).scalar() or 0

            if total_offered == 0:
                return {
                    "published_count": 0,
                    "total_subjects": total_offered,
                    "message": "No subjects offered in this semester yet"
                }

            # get the published marks for the student
            published_marks_stmt = select(Mark).where(
                and_(
                    Mark.student_id == student.id,
                    Mark.semester_id == semester_id,
                    Mark.result_status == ResultStatus.PUBLISHED
                )
            ).options(
                joinedload(Mark.subject),
                # joinedload(Mark.student),
                joinedload(Mark.student).joinedload(Student.department),
                joinedload(Mark.semester)
            )

            published_marks = await db.execute(published_marks_stmt)
            result = published_marks.scalars().all()

            if len(result) < total_offered:
                return {
                    "published_count": len(result),
                    "total_subjects": total_offered,
                    "message": "Result is under processing. Please try again later",
                }

            first_record = result[0]
            student_info = first_record.student
            semester_info = first_record.semester
            department_info = first_record.student.department

            return {
                "is_published": True,
                "published_count": len(result),
                "total_subjects": total_offered,
                "student_info": student_info,
                "semester_info": semester_info,
                "department_info": department_info,
                "result": result,
            }
        except IntegrityError as e:
            # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state
            await db.rollback()

            # generally the PostgreSQL's error message will be in e.orig.args
            raw_error_message = str(e.orig) if e.orig else str(e)
            readable_error = parse_integrity_error(raw_error_message)

            logger.error(f"Integrity error while creating student: {e}")
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

    # @staticmethod  # get all marks for a subject with semester filtering, subject filtering
    # async def get_all_marks_for_a_student(
    #     db: AsyncSession,
    #     student_id: int,
    #     semester_id: int | None = None,  # for filtering
    #     subject_id: int | None = None  # for filtering
    # ):
    #     stmt = select(Mark).where(Mark.student_id == student_id)
    #     if semester_id:
    #         # this part will be added to the existing statement if the semester_id is provided
    #         stmt = stmt.where(Mark.semester_id == semester_id)
    #     if subject_id:
    #         # this part will be added to the existing statement if the subject_id is provided
    #         stmt = stmt.where(Mark.subject_id == subject_id)
    #     marks = await db.scalars(stmt)
    #     return MarksService.group_marks_by_semester(marks)
    # @staticmethod  # get all students mark for a particular subject
    # async def get_all_mark_for_a_subject(db: AsyncSession, subject_id: int):
    #     marks = await db.scalars(select(Mark).where(Mark.subject_id == subject_id))
    #     return marks
