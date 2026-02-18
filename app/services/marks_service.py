from collections import defaultdict
from typing import Annotated, Any
from loguru import logger
from sqlalchemy import and_, join, select
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models import Mark, ResultStatus
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Query, Request, status
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
            # statement = statement.where(Mark.semester_id == target_semester_id)
        if target_department_id:
            filters.append(Student.department_id == target_department_id)
            # statement = statement.where(Student.department_id == target_department_id)
        if session:
            filters.append(Student.session == session)
            # statement = statement.where(Student.session == session)
        if result_status:
            filters.append(Mark.result_status == result_status)
            # statement = statement.where(Mark.result_status == result_status)
        # if is_challenged is not None:
        #     # if Result Status is 'challenged'
        #     if is_challenged:
        #         filters.append(Mark.result_status == ResultStatus.CHALLENGED)
        #     else:
        #         filters.append(
        #             Mark.result_challenge_payment_status != ResultStatus.CHALLENGED)

        if filters:
            statement = statement.where(and_(*filters))

        result = await db.execute(statement)
        marks = result.unique().scalars().all()  # remove duplicates using unique()

        return MarksService.group_marks_by_category(marks)

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

    # @staticmethod  # update a mark
    # async def update_mark(
    #     db: AsyncSession,
    #     update_data: MarksUpdateSchema,
    #     mark_id: int,
    #     current_user: UserOutSchema
    # ):
    #     mark = await db.scalar(select(Mark).where(Mark.id == mark_id))

    #     if not mark:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")

    #     user_role = current_user.role.value
    #     update_dict = update_data.model_dump(
    #         exclude_unset=True, exclude_none=True)

    #     # verify teacher role and is he teaching this subject
    #     is_teacher_authorized = False
    #     if user_role == "teacher":
    #         is_taught_by_this_teacher = await db.scalar(select(SubjectOfferings).where(
    #             and_(
    #                 SubjectOfferings.taught_by_id == current_user.id,
    #                 SubjectOfferings.subject_id == mark.subject_id
    #             )
    #         ))
    #         if is_taught_by_this_teacher:
    #             is_teacher_authorized = True
    #         else:
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN,
    #                 detail="You are not authorized to update mark for this subject.")

    #     # verify student role and only update "result_status" field from "published" to "challenged"
    #     if user_role == "student":
    #         if "result_status" in update_dict:
    #             new_status = update_dict["result_status"]

    #             # Challenge result when its published
    #             if new_status == ResultStatus.CHALLENGED and mark.result_status.value == ResultStatus.PUBLISHED:
    #                 mark.result_status = ResultStatus.CHALLENGED  # set result is challenged
    #                 mark.result_challenge_payment_status = False  # set payment status is pending
    #                 mark.challenged_at = datetime.now()  # set challenged date, need for payment
    #                 # show error if student tries to update more than 1 field
    #                 if len(update_dict) > 1:
    #                     raise HTTPException(
    #                         status_code=status.HTTP_403_FORBIDDEN,
    #                         detail="You are not authorized to update more than one field.")
    #             # show error if student tries to challenge when result_status is "unpublished", "resolved" or already "challenged"
    #             else:
    #                 raise HTTPException(
    #                     status_code=status.HTTP_403_FORBIDDEN,
    #                     detail="You can only challenge result once when it is published!")
    #         # show error if student tries to update other fields
    #         else:
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN, detail="you are not authorized to update this fields.")

    #     # if payment status is updating make sure user is admin
    #     if "result_challenge_payment_status" in update_dict:
    #         if (user_role != "admin"):
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN,
    #                 detail="Only admin can update payment status.")

    #         new_payment_status = update_dict["result_challenge_payment_status"]

    #         if mark.result_status.value == ResultStatus.CHALLENGED:
    #             # change payment status only if result is challenged
    #             mark.result_challenge_payment_status = new_payment_status
    #         else:
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN,
    #                 detail="You can only update payment status when result is challenged!")

    #     # Update rest of the updatable fields/Marks by admin/teacher
    #     if user_role in ["admin", "teacher"] and (user_role == "admin" or is_teacher_authorized):
    #         can_update_marks_data = (
    #             mark.result_status.value != ResultStatus.CHALLENGED or
    #             mark.result_challenge_payment_status is True
    #         )

    #         if can_update_marks_data:
    #             # compute or calculate marks if provided in update data
    #             mark_fields_updated = False
    #             for field in ["assignment_mark", "class_test_mark", "midterm_mark", "final_exam_mark"]:
    #                 if field in update_dict:
    #                     setattr(mark, field, update_dict[field])
    #                     mark_fields_updated = True

    #             if mark_fields_updated:
    #                 MarksService.compute_total_marks_and_gpa(mark)

    #                 # if result_status is challenged and mark is updated then resolve the status
    #                 if mark.result_status.value == ResultStatus.CHALLENGED:
    #                     mark.result_status = ResultStatus.RESOLVED

    #         elif (f in update_dict for f in ["assignment_mark", "class_test_mark", "midterm_mark", "final_exam_mark"]):
    #             # if tries to update marks when result is challenged and payment is pending
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN,
    #                 detail="Cannot update marks data while result is challenged and payment is pending."
    #             )

    #     if "result_status" in update_dict and user_role in ["admin", "teacher"]:
    #         new_status = update_dict["result_status"]
    #         if new_status == ResultStatus.CHALLENGED and user_role != "student":
    #             raise HTTPException(
    #                 status_code=status.HTTP_403_FORBIDDEN,
    #                 detail="Only student can challenge result."
    #             )
    #         mark.result_status = new_status
    #         # if update_data.assignment_mark is not None:
    #         #     mark.assignment_mark = update_data.assignment_mark

    #         # if update_data.class_test_mark is not None:
    #         #     mark.class_test_mark = update_data.class_test_mark

    #         # if update_data.midterm_mark is not None:
    #         #     mark.midterm_mark = update_data.midterm_mark

    #         # if update_data.final_exam_mark is not None:
    #         #     mark.final_exam_mark = update_data.final_exam_mark

    #         # MarksService.compute_total_marks_and_gpa(mark)
    #     try:
    #         await db.commit()
    #         await db.refresh(mark)

    #         return mark
    #     except IntegrityError as e:
    #         # generally the PostgreSQL's error message will be in e.orig.args[0]
    #         error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
    #             e)

    #         # send the error message to the parser
    #         readable_error = parse_integrity_error(error_msg)
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)

    # @staticmethod # delete a mark
    # async def delete_mark(db: AsyncSession, mark_id: int):
    #     mark = await db.scalar(select(Mark).where(Mark.id == mark_id))

    #     if not mark:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")

    #     await db.delete(mark)
    #     await db.commit()

    #     return mark
