from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import User
from app.models.teacher_model import Teacher
from app.models.department_model import Department
from app.schemas.teacher_schema import TeacherCreateSchema
from app.utils import check_existence
from fastapi import HTTPException, status


class TeacherService:

    @staticmethod
    async def create_teacher(
        db: AsyncSession,
        teacher_data: TeacherCreateSchema
    ):
        # check for existance in user table and throw error
        user = await check_existence(User, db, teacher_data.user_id, "User")

        if not user.role.value == "teacher":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="User is not a teacher. Cannot create teacher")

        # check for duplicate teacher
        teacher = await db.scalar(select(Teacher).where(Teacher.user_id == teacher_data.user_id))

        if (teacher):
            raise ValueError("Teacher already exist")

        # check if department exist
        await check_existence(Department, db, teacher_data.department_id, "Department")

        new_teacher = User(**teacher_data.model_dump())
        db.add(new_teacher)
        await db.commit()
        await db.refresh(new_teacher)

        return {
            "message": f"new_teacher created successfully. ID: {new_teacher.id}"
        }

    @staticmethod
    async def get_teachers(db: AsyncSession):
        teachers = await db.scalars(select(Teacher))
        return teachers.all()

    @staticmethod
    async def get_teacher(db: AsyncSession, teacher_id: int):
        teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))

        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

        return teacher
