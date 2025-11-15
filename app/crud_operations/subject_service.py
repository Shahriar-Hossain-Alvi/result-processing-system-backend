from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subject_model import Subject
from app.schemas.subject_schema import SubjectCreateSchema
from fastapi import HTTPException, status


async def create_subject(
        db: AsyncSession,
        subject_data: SubjectCreateSchema
):
    # check for existing subject
    subject = await db.scalar(select(Subject).where(Subject.subject_code == subject_data.subject_code))

    if subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Subject already exist")

    new_subject = Subject(**subject_data.model_dump())
    db.add(new_subject)
    await db.commit()
    await db.refresh(new_subject)

    return {
        "message": f"new_subject created successfully. ID: {new_subject.id}"
    }


async def get_subject(db: AsyncSession, subject_id: int):
    subject = await db.scalar(select(Subject).where(Subject.id == subject_id))

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    return subject


async def get_subjects(db: AsyncSession):
    subjects = await db.execute(select(Subject))

    return subjects.scalars().all()


async def delete_subject(
    db: AsyncSession,
    subject_id: int
):
    subject = await db.scalar(select(Subject).where(Subject.id == subject_id))

    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    await db.delete(subject)
    await db.commit()

    return {"message": f"{subject.subject_title} subject deleted successfully"}