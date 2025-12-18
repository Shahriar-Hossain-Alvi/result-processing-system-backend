from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, Boolean
from pydantic import EmailStr
import enum
from sqlalchemy import Enum as sqlEnum

# For creating an admin account only


class UserRole(enum.Enum):
    # SUPER_ADMIN = 'super_admin'
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


"""
    Admins can create students/teachers/subjects/marks.
    Teachers can add marks only for subjects they teach.
"""


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[EmailStr] = mapped_column(
        String(100), nullable=False, unique=True)

    email: Mapped[EmailStr] = mapped_column(
        String(100), nullable=False, unique=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

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
    student: Mapped["Student"] = relationship(
        back_populates="user", uselist=False)  # type: ignore
    # normally sqlalchemy thinks the relationship is 1-N or N-1 so it creates a list using uselist=True
    # but we want 1-1 so we use uselist=False

    # TODO: create a relationship with teacher table

    # relationship with subject offerings
    subject_offerings: Mapped[list["SubjectOfferings"]] = relationship(
        back_populates="taught_by")  # type: ignore
