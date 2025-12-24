from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey, DateTime
from datetime import datetime


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship with Department
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        # set null if department is deleted
        "departments.id", ondelete="SET NULL"), nullable=True)

    department: Mapped["Department"] = relationship(  # type: ignore
        back_populates="teachers")

    # Relationship with user table
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        # delete teachers record if user is deleted
        "users.id", ondelete="CASCADE"), unique=True)

    user: Mapped["User"] = relationship(  # type: ignore
        back_populates="teacher")

    # Teachers personal information
    present_address: Mapped[str] = mapped_column(
        String(200), nullable=False, default="")

    permanent_address: Mapped[str] = mapped_column(
        String(200), nullable=False, default="")

    date_of_birth: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    mobile_number: Mapped[str] = mapped_column(
        String(11), nullable=False, default=""
    )

    photo_url: Mapped[str] = mapped_column(
        String(400), nullable=False, default=""
    )

    photo_public_id: Mapped[str] = mapped_column(
        String(300), nullable=False, default=""
    )
