from collections import defaultdict
from typing import Annotated
from sqlalchemy import and_, join, select
from app.models.mark_model import Mark
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Query, status
from app.models.semester_model import Semester
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.subject_offerings_model import SubjectOfferings
from app.models.user_model import User
from app.schemas.marks_schema import MarksCreateSchema, MarksUpdateSchema
from app.schemas.user_schema import UserOutSchema
from app.utils import check_existence
from sqlalchemy.orm import joinedload


class MarksService:

    @staticmethod
    def compute_total_marks_and_gpa(mark_data: Mark):
        # calculate assignment mark, midterm mark, class test mark and convert it to 20%
        base_marks_for_in_course = 20

        total_in_course_marks_obtained_out_of_60 = (
            (mark_data.assignment_mark or 0) +
            (mark_data.midterm_mark or 0) +
            (mark_data.class_test_mark or 0)
        )

        converted_total_incourse_mark_obtained_out_of_20 = (
            total_in_course_marks_obtained_out_of_60*base_marks_for_in_course)/60

        total = (
            converted_total_incourse_mark_obtained_out_of_20 +
            (mark_data.final_exam_mark or 0)
        )

        mark_data.total_mark = total

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
        current_user: UserOutSchema
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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
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
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="You are not authorized to create a mark for this subject.")


        # if the user(teacher) is not different or the Admin, then create the mark 

        # create new_mark object but it does not have the total marks and gpa yet
        new_mark = Mark(
            **mark_data.model_dump()
        )

        # pass this new_mark object to the compute_total_marks_and_gpa function to get the total marks and gpa. It'll update the new_mark object
        MarksService.compute_total_marks_and_gpa(new_mark)

        db.add(new_mark)
        await db.commit()
        await db.refresh(new_mark)

        return new_mark



    # group marks by semester
    @staticmethod
    def group_marks_by_semester(marks):
        grouped = defaultdict(list)
        for m in marks:
            grouped[m.semester_id].append(m)

        return [{"semester_id": sem_id, "marks": items} for sem_id, items in grouped.items()]



    # get all marks for a subject with semester filtering, subject filtering
    @staticmethod
    async def get_all_marks_for_a_student(
        db: AsyncSession,
        student_id: int,
        semester_id: int | None = None,  # for filtering
        subject_id: int | None = None  # for filtering # TODO: (subject_id) this might not be needed
    ):

        stmt = select(Mark).where(Mark.student_id == student_id)

        if semester_id:
            # this part will be added to the existing statement if the semester_id is provided
            stmt = stmt.where(Mark.semester_id == semester_id)

        if subject_id:
            # this part will be added to the existing statement if the subject_id is provided
            stmt = stmt.where(Mark.subject_id == subject_id)

        marks = await db.scalars(stmt)

        return MarksService.group_marks_by_semester(marks)



    # get all students mark for a particular subject
    @staticmethod
    async def get_all_mark_for_a_subject(db: AsyncSession, subject_id: int):
        marks = await db.scalars(select(Mark).where(Mark.subject_id == subject_id))

        return marks



    # get result for a particular department and semester and session
    @staticmethod
    async def get_department_semester_result(
        db: AsyncSession,
        target_semester_id: int,
        target_department_id: int,
        session: str,
        # current_user: UserOutSchema
        # session: Annotated[str, Query("example: 2020-2021")]
    ):
        # Base query
        statement = select(Mark)\
            .join(Student, Student.id == Mark.student_id)\
            .join(Subject, Subject.id == Mark.subject_id)\
            .join(SubjectOfferings, SubjectOfferings.subject_id == Subject.id)\
            .where(
                and_(
                    Student.department_id == target_department_id,
                    Mark.semester_id == target_semester_id,
                    Student.session == session
                )
        )\
            #     .options(
        #         # The 'Mark' objects returned will now have 'mark.student' and 'mark.subject'
        #         # already loaded without further database hits.
        #         joinedload(Mark.student),
        #         joinedload(Mark.subject),
        # )

        # If teacher → restrict to subjects they teach
        # if current_user.role == "teacher":
        #     stmt = stmt.where(SubjectOffering.taught_by_id == current_user.id)

        res = await db.execute(statement)
        marks = res.scalars().all()

        return MarksService.group_marks_by_semester(marks)



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
        j = join(Subject, SubjectOfferings, Subject.id ==
                 SubjectOfferings.subject_id)

        statement = select(Subject).select_from(j).where(
            and_(
                Subject.semester_id == semester_id,
                SubjectOfferings.department_id == department_id
            )
        )

        # stmt = select(Subject)\
        #     .join(Subject.subject_offerings)\
        #     .where(
        #         and_(
        #             Subject.semester_id == semester_id,
        #             SubjectOfferings.department_id == department_id
        #         )
        #     )

        # restrict subject list for teachers
        if current_user.role.value == "teacher":
            statement = statement.where(
                SubjectOfferings.taught_by_id == current_user.id
            )

        result = await db.execute(statement)
        subjects = result.scalars().all()
        return subjects

    # update a mark

    @staticmethod
    async def update_mark(
        db: AsyncSession,
        update_data: MarksUpdateSchema,
        mark_id: int,
        current_user: UserOutSchema
    ):
        mark = await db.scalar(select(Mark).where(Mark.id == mark_id))

        if not mark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")


        # check if the user is teacher then his id is in the taught_by_id in subject_offerings
        if current_user.role.value == "teacher":
            is_taught_by_this_teacher = await db.scalar(select(SubjectOfferings).where(
                and_(
                    SubjectOfferings.taught_by_id == current_user.id,
                    SubjectOfferings.subject_id == mark.subject_id
                )
            ))

            if not is_taught_by_this_teacher:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="You are not authorized to update mark for this subject.")      
        

        if update_data.assignment_mark is not None:
            mark.assignment_mark = update_data.assignment_mark

        if update_data.class_test_mark is not None:
            mark.class_test_mark = update_data.class_test_mark

        if update_data.midterm_mark is not None:
            mark.midterm_mark = update_data.midterm_mark

        if update_data.final_exam_mark is not None:
            mark.final_exam_mark = update_data.final_exam_mark

        MarksService.compute_total_marks_and_gpa(mark)

        await db.commit()
        await db.refresh(mark)

        return mark

    # delete a mark

    @staticmethod
    async def delete_mark(db: AsyncSession, mark_id: int):
        mark = await db.scalar(select(Mark).where(Mark.id == mark_id))

        if not mark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")

        await db.delete(mark)
        await db.commit()

        return mark
