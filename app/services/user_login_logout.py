from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import HTTPException, status, Response, Request
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import verify_password, create_access_token
from app.core.exceptions import DomainIntegrityError
from app.core.integrity_error_parser import parse_integrity_error
from app.models import User
from app.core import settings
from sqlalchemy.exc import IntegrityError


async def login_user(
    db: AsyncSession,
    username: str,
    password: str,
    response: Response,
    request: Request | None = None
):
    # get user
    statement = select(User).where(User.username == username)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials. Please check your credentials.")

    try:
        # verify password
        is_valid = verify_password(password, user.hashed_password)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials. Please check your credentials.")

        # deny login if account status is inactive
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is Deactivated. Please contact admin.")

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
        return {
            "message": "Login successful"
        }

    except IntegrityError as e:
        # Important: rollback as soon as an error occurs. It recovers the session from 'failed' state and puts it back in 'clean' state to save the Audit Log
        await db.rollback()

        # generally the PostgreSQL's error message will be in e.orig.args
        raw_error_message = str(e.orig) if e.orig else str(e)
        readable_error = parse_integrity_error(raw_error_message)

        logger.error(f"Error occurred while login: {e}")
        logger.error(f"Readable Error: {readable_error}")

        # attach audit payload safely
        if request:
            payload: dict[str, Any] = {
                "raw_error": raw_error_message,
                "readable_error": readable_error,
            }
            request.state.audit_payload = payload

        raise DomainIntegrityError(
            error_message=readable_error, raw_error=raw_error_message)


async def logout_user(response: Response):

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )
    logger.success("Cookie deleted")

    return {"message": "Logout successful"}
