from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Response, Request
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import verify_password, create_access_token
from app.core.integrity_error_parser import parse_integrity_error
from app.models import User
from app.core import settings
from app.models.audit_log_model import LogLevel
from app.services.audit_logging_service import create_audit_log
from sqlalchemy.exc import IntegrityError


async def login_user(
    db: AsyncSession,
    username: str,
    password: str,
    response: Response,
    request: Request
):
    # get user
    statement = select(User).where(User.username == username)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        # verify password
        is_valid = verify_password(password, user.hashed_password)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # after validating the user, create access token
        access_token = create_access_token(user.username)

        # set the httponly cookie
        response.set_cookie(
            key="access_token",  # cookie name
            value=access_token,
            httponly=True,  # prevents access from javascript in the browser
            samesite="lax",  # CSRF defense
            expires=datetime.now(
                timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        logger.success("Login successful")

        await create_audit_log(
            db=db, request=request, level="info", created_by=user.id,
            action="LOGIN ATTEMPT",
            details=f"User {user.username} logged in successfully"
        )
        return {
            "message": "Login successful"
        }

    except IntegrityError as e:
        logger.error(f"Error occurred while login: {e}")
        # generally the PostgreSQL's error message will be in e.orig.args[0]
        error_msg = str(e.orig.args[0]) if e.orig.args else str(  # type: ignore
            e)

        # send the error message to the parser
        readable_error = parse_integrity_error(error_msg)
        logger.error(f"Readable Error: {readable_error}")

        await create_audit_log(
            db=db, request=request, level=LogLevel.ERROR.value, created_by=user.id,
            action="LOGIN ATTEMPT",
            details=f"Login failed for user {user.username}",
            payload={
                "error": readable_error,
                "raw_error": error_msg,
                "payload_data": username
            }
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=readable_error)


async def logout_user(request: Request, response: Response, db: AsyncSession):
    try:
        response.delete_cookie(
            key="access_token",
            httponly=True,
            samesite="lax"
        )
        logger.success("Cookie deleted")

        return {"message": "Logout successful"}
    except Exception as e:
        logger.error(f"Error occurred while logout: {e}")

        await create_audit_log(
            db=db,
            request=request,
            level=LogLevel.ERROR.value,
            action="LOGOUT ATTEMPT",
            details=f"Logout failed",
        )

        raise HTTPException(status_code=500, detail=str(e))
