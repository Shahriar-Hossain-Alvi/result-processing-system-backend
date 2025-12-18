from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, Float, ForeignKey, UniqueConstraint, Boolean, DateTime
import enum
from sqlalchemy import Enum as sqlEnum


class ResultStatus(enum.Enum):
    PUBLISHED = "published"  # no color
    UNPUBLISHED = "unpublished"  # warning color
    RESOLVED = "resolved"  # success color
    CHALLENGED = "challedged"  # error color


class Mark(Base):
    __tablename__ = "marks"

    # a student can have only one mark for a subject in a semester
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "semester_id",
            name="unique_mark_record"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    assignment_mark: Mapped[float | None] = mapped_column(Float, default=0.0)

    midterm_mark: Mapped[float | None] = mapped_column(Float, default=0.0)

    class_test_mark: Mapped[float | None] = mapped_column(Float, default=0.0)

    final_exam_mark: Mapped[float | None] = mapped_column(Float, default=0.0)

    total_mark: Mapped[float | None] = mapped_column(Float, default=0.0)

    GPA: Mapped[float | None] = mapped_column(Float, default=0.0)

    result_status: Mapped[ResultStatus] = mapped_column(
        sqlEnum(
            ResultStatus,
            name="result_status",  # enum name in database
            # "values_callable" uses the value inside the "value" in DB instead of using the capitalized name(keys)
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=ResultStatus.UNPUBLISHED,
        server_default=ResultStatus.UNPUBLISHED.value
    )

    # Challenge Payment Status (Three-State: NULL, False, True)
    # NULL: No challenge initiated (default).
    # False: Challenge initiated, payment pending.
    # True: Payment confirmed, teacher can resolve.
    result_challenge_payment_status: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, default=None
    )

    # Challenge Initiation Timestamp
    challenged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # relationship with student
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"))

    student: Mapped["Student"] = relationship(
        back_populates="marks")  # type: ignore

    # TODO: add a field to store the submitted_by id(admin/teachers id)

    # relationship with subject
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"))

    subject: Mapped["Subject"] = relationship(
        back_populates="marks")  # type: ignore

    # relationship with semester
    semester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("semesters.id", ondelete="CASCADE"))

    semester: Mapped["Semester"] = relationship(
        back_populates="marks")  # type: ignore
