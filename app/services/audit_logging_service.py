from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log_model import AuditLog


async def create_audit_log(
    db: AsyncSession,
    action: str,  # CREATE USER / UPDATE USER / DELETE USER
    request: Request | None = None,
    level: str = "info",  # info for success, error for error
    details: str | None = None,  # custom message
    # user id (who sent the request eg; ID from get_current_user or authoried user)
    created_by: int | None = None,
    payload: dict | None = None
):
    new_log = AuditLog(
        created_by=created_by,
        level=level,
        action=action,
        method=request.method if request else None,
        path=request.url.path if request else None,
        ip_address=request.client.host if request else None,  # type: ignore
        details=details,
        payload=payload
    )

    db.add(new_log)
    await db.commit()
