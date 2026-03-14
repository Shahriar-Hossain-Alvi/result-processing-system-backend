from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, ForeignKey
from app.models.timestamp import TimestampMixin


class SubjectOfferings(Base, TimestampMixin):
    __tablename__ = "subject_offerings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # relationship with teacher
    taught_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"))

    taught_by: Mapped["Teacher"] = relationship(  # type: ignore
        back_populates="subject_offerings")

    # relationship with subject
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), index=True)

    subject: Mapped["Subject"] = relationship(  # type: ignore
        back_populates="subject_offerings")

    # relationship with department
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="CASCADE"), index=True)

    department: Mapped["Department"] = relationship(  # type: ignore
        back_populates="subject_offerings")
