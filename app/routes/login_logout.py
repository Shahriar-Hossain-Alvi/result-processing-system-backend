from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.services.user_login_logout import login_user, logout_user
from app.db.db import get_db_session


# login router
router = APIRouter(prefix='/auth', tags=['login'])


# login route setup with httponly cookies
@router.post("/login")
async def login(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db_session)):

    # attach action
    request.state.action = "LOGIN USER"

    try:
        return await login_user(db, form_data.username, form_data.password, response, request)
    except DomainIntegrityError as de:
        logger.error(f"Integrity error while login {str(de)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical("Unexpected Error: ", e)
        logger.critical("LOGIN FAILED FROM ROUTER")
        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
):
    # attach action
    request.state.action = "LOGOUT USER"
    try:
        return await logout_user(response)
    except DomainIntegrityError as de:
        logger.error(f"Integrity error while login {str(de)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical("Unexpected Error: ", e)

        # attach audit payload
        if request:
            request.state.audit_payload = {
                "raw_error": str(e),
                "exception_type": type(e).__name__,
            }

        logger.critical("LOGIN FAILED FROM ROUTER")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
