from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Date, Integer, String, ForeignKey, DateTime
from datetime import datetime, date
from app.models.timestamp import TimestampMixin


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    registration: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True)

    session: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship with Department
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        # set null if department is deleted
        "departments.id", ondelete="SET NULL"), nullable=True)

    department: Mapped["Department"] = relationship(  # type: ignore
        back_populates="students")

    # Relationship with semester
    semester_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        # set null if semester is deleted
        "semesters.id", ondelete="SET NULL"), nullable=True)

    # each student has one semester (current semester)
    semester: Mapped["Semester"] = relationship(  # type: ignore
        back_populates="students")

    # Relationship with user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        # delete student record if user is deleted
        "users.id", ondelete="CASCADE"), unique=True)

    user: Mapped["User"] = relationship(  # type: ignore
        back_populates="student")

    # relationship with marks
    # one student can have many marks
    marks: Mapped[list["Mark"]] = relationship(  # type: ignore
        back_populates="student")

    # Students personal information
    present_address: Mapped[str] = mapped_column(
        String(200), nullable=False, default="")

    permanent_address: Mapped[str] = mapped_column(
        String(200), nullable=False, default="")

    date_of_birth: Mapped[date | None] = mapped_column(
        Date, nullable=True, default=None
    )

    photo_url: Mapped[str] = mapped_column(
        String(400), nullable=False, default=""
    )

    photo_public_id: Mapped[str] = mapped_column(
        String(300), nullable=False, default=""
    )
