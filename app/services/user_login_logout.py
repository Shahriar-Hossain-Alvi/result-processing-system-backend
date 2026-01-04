from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Response
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import verify_password, create_access_token
from app.models import User
from app.core import settings


async def login_user(
    db: AsyncSession,
    username: str,
    password: str,
    response: Response
):
    # get user
    statement = select(User).where(User.username == username)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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

    return {
        "message": "Login successful",
        # "access_token": access_token,
    }  # this token will be stored in the browsers cookie and will be sent to backend for authentication with protected routes


async def logout_user(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )
    logger.success("Cookie deleted")

    return {"message": "Logout successful"}
