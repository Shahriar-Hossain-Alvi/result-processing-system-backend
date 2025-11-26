from functools import wraps
from typing import Callable, Literal
from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.jwt import decode_access_token
from app.models.user_model import User, UserRole
from app.schemas.user_schema import UserOutSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db_session, AsyncSessionLocal

# Define the OAuth2 scheme to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Define the allowed roles that can be passed to the decorator
AllowedRoles = Literal[
    # 'super_admin',
    'admin', 'teacher', 'student']


def permission(*required_roles: AllowedRoles):
    # 1. The main decorator function, which receives the target function (the FastAPI route)
    def decorator(func: Callable):

        # 2. @wraps is essential! It copies metadata (name, docstring, type hints) from the original function (func) to the wrapper, which FastAPI needs.

        @wraps(func)
        # 3. The asynchronous wrapper function that replaces the original route.
        #    It must accept 'request' and pass all *args and **kwargs.
        async def wrapper(request: Request, *args, **kwargs):

            # --- 4. Authentication: Check Token ---
            try:
                token = await oauth2_scheme(request)
            except HTTPException:
                raise

            # 5. Decode the token to get the user information.
            payload = decode_access_token(token)  # type: ignore

            if payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # username is set in the sub while token creation
            username = str(payload.get("sub"))

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )

            # --- 6. Fetch User ---
            async with AsyncSessionLocal() as db:
                try:
                    current_user = await db.scalar(select(User).where(User.username == username))

                    if not current_user:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found"
                        )
                except Exception as e:
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error during user fetch + " + str(e),
                    )

            # --- 7. Authorization: Check Roles ---

            # 8. If no roles are passed to the decorator (@permission(), it means only authentication is required.
            if not required_roles:
                # Authentication passed, proceed to execution.
                pass
            else:
                # 9. Check if the current user's role is in the list of required roles.
                current_users_role = current_user.role.value

                if current_users_role not in required_roles:
                    # 10. If the role doesn't match, deny access with 403 Forbidden.
                    required_list = ', '.join(required_roles)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {required_list}",
                    )

            # 9. Pass the current user to the route function as a keyword argument after authentication and authorization. so that it can be used in the route function
            kwargs["current_user"] = current_user

            # 10. If all checks pass, execute the original route function. This ensures the router code runs after successful validation.

            """
            when an user hits the /items/101 route, then FastAPI prepares the following arguments:
            1. request: Request Object
            2. item_id: 101
            3. db: AsyncSession Object
            all these arguments are passed to the decorators wrapper function.
            After that, the wrapper function accepts the request directly and stores/holds the remaining arguments(eg: item_id, db) in the *args and **kwargs.

            If we didn't use *args, then the arguments will be lost.

            After doing the Authentication and Authorization, the decorator passes the current_user and all the remaining arguments that it received/holds to the route function as a keyword argument.
            """

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
