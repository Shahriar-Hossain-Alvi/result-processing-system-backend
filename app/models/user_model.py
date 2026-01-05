from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, Boolean
from pydantic import EmailStr
import enum
from sqlalchemy import Enum as sqlEnum
from app.models.timestamp import TimestampMixin


class UserRole(enum.Enum):
    SUPER_ADMIN = 'super_admin'
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


"""
    Admins can create students/teachers/subjects/marks.
    Teachers can add marks only for subjects they teach.
"""


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[EmailStr] = mapped_column(
        String(100), nullable=False, unique=True)

    email: Mapped[EmailStr] = mapped_column(
        String(100), nullable=False, unique=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    mobile_number: Mapped[str] = mapped_column(
        String(11), nullable=True, default=None, unique=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    role: Mapped[UserRole] = mapped_column(
        sqlEnum(
            UserRole,
            name="userrole",
            # <-- This ensures the value ('admin') is used
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=UserRole.STUDENT
    )

    # relationship with student
    student: Mapped["Student"] = relationship(  # type: ignore
        back_populates="user", uselist=False)
    # normally sqlalchemy thinks the relationship is 1-N or N-1 so it creates a list using uselist=True
    # but we want 1-1 so we use uselist=False

    teacher: Mapped["Teacher"] = relationship(  # type: ignore
        back_populates="user", uselist=False)  # for 1-1

    # relationship with subject offerings
    subject_offerings: Mapped[list["SubjectOfferings"]] = relationship(  # type: ignore
        back_populates="taught_by")
