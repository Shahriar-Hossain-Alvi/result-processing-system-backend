from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, Float, ForeignKey
from app.models.timestamp import TimestampMixin


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    subject_title: Mapped[str] = mapped_column(String(100), nullable=False)

    subject_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True)

    credits: Mapped[Float] = mapped_column(Float, nullable=False)

    # relationship with semester
    semester_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "semesters.id", ondelete="SET NULL"))  # set null if semester is deleted

    # one subject belongs to one semester
    semester: Mapped["Semester"] = relationship(
        back_populates="subjects")  # type: ignore

    # relationship with marks
    # one subject can have many marks
    marks: Mapped["Mark"] = relationship(
        back_populates="subject")  # type: ignore

    # relationship with subject_offerings
    # many subject can belong to many departments
    subject_offerings: Mapped[list["SubjectOfferings"]] = relationship(
        back_populates="subject")  # type: ignore
