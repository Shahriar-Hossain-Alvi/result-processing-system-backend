from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.jwt import decode_access_token
from app.db.db import get_db_session
from app.models import User


# token_url is only used for swagger documentation. OAuth2PasswordBearer looks for token in Authorization header(Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
        request: Request,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db_session)) -> User:  # type: ignore

    # this will extract the (sub, iat, exp) from the token
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = str(payload.get("sub"))  # get the username from sub

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    statement = select(User).where(User.username == username)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials")

    # attach user_id to request.state
    request.state.user_id = user.id

    return user
