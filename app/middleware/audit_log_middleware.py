from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.models.audit_log_model import LogLevel, AuditLog
from app.utils.audit_level_set import level_from_status
from app.db.sync_db import SyncSessionLocal


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        # Go to router -> service functions and get response. After that, save log
        response = await call_next(request)

        # Audit Logging
        method = request.method
        status = response.status_code

        # SKIP successful GET requests
        if method == "GET" and status < 400:
            return response

        if status >= 500:
            level = LogLevel.CRITICAL.value
        else:
            level = level_from_status(status)

        # attach payload from service functions integrity error, routers exceptions
        payload = getattr(request.state, "audit_payload", None)
        # user_id is attached from get_current_user
        user_id = getattr(request.state, "user_id", None)

        # action is attached from router before the try block
        action = getattr(
            request.state, "action",
            f"{request.method} {request.url.path}"
        )

        log = AuditLog(
            created_by=user_id,
            level=level,
            action=action,
            path=request.url.path,
            method=method,
            details=f"Log created by this users(USER ID:{user_id}) request in {method} method in Action: {action}. Status Code: {status}",
            ip_address=request.client.host if request.client else None,
            payload=payload,
        )

        with SyncSessionLocal() as session:
            try:
                session.add(log)
                session.commit()
            except Exception:
                session.rollback()

        return response
