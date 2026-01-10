import enum
from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy import Enum as sqlEnum
from app.models.timestamp import TimestampMixin


class LogLevel(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)

    level: Mapped[str] = mapped_column(
        sqlEnum(
            LogLevel,
            name="audit_log_level",
            native_enum=False,  # Added this to auto generate code in version file for enum
            # this is used to store the string values eg: "admin" instead of the Enum ADMIN in DB
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=LogLevel.INFO.value,  # python/sqlalchemy level default
        # DB level default, need the .value (not the Enum name)
        server_default=LogLevel.INFO.value
    )

    # ACTION: e.g., "LOGIN", "CREATE_USER", "DELETE_STUDENT"
    action: Mapped[str] = mapped_column(String(100))

    method: Mapped[str] = mapped_column(String(10))  # POST, GET, DELETE, etc.

    path: Mapped[str] = mapped_column(String(255))  # URL

    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)

    details: Mapped[str] = mapped_column(Text, nullable=True)  # Summary

    payload: Mapped[dict] = mapped_column(JSON, nullable=True)  # Request body
