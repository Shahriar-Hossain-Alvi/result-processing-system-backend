from fastapi import APIRouter, Depends, HTTPException, Response, Request, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainIntegrityError
from app.models.audit_log_model import LogLevel
from app.services.user_login_logout import login_user, logout_user
from app.db.db import get_db_session
from app.utils.token_injector import inject_token

# login router

router = APIRouter(prefix='/auth', tags=['login'])


# login route setup with httponly cookies
@router.post("/login")
async def login(
        request: Request,
        response: Response,
        background_tasks: BackgroundTasks,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db_session)):
    try:
        result = await login_user(db, form_data.username, form_data.password, response)

        # background_tasks.add_task(
        #     create_audit_log_isolated,
        #     request=request, level="info", created_by=result["user_data"].id,
        #     action="LOGIN ATTEMPT",
        #     details=f"User {result["user_data"].username} logged in successfully"
        # )
        return {
            "message": result["message"]
        }
    except DomainIntegrityError as de:
        # DB Log
        # background_tasks.add_task(
        #     create_audit_log_isolated,
        #     request=request, level=LogLevel.ERROR.value,
        #     action="LOGIN ATTEMPT INTEGRITY ERROR",
        #     details=f"Integrity error for user {form_data.username}",
        #     payload={
        #         "error": de.error_message,
        #         "raw_error": de.raw_error,
        #         "payload_data": form_data.username
        #     }
        # )
        logger.error(f"Integrity error while login {str(de)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical("Unexpected Error: ", e)
        # DB Log
        # background_tasks.add_task(
        #     create_audit_log_isolated,
        #     request=request, level=LogLevel.CRITICAL.value,
        #     action="LOGIN USER SYSTEM ERROR",
        #     details=f"System error: {str(e)}",
        #     payload={
        #         "raw_error": str(e),
        #         "payload_data": form_data.username
        #     }
        # )
        logger.critical("LOGIN FAILED FROM ROUTER")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
):
    try:
        return await logout_user(response)
    except DomainIntegrityError as de:
        # DB Log
        # background_tasks.add_task(
        #     create_audit_log_isolated,
        #     request=request,
        #     level=LogLevel.ERROR.value,
        #     action="LOGOUT ATTEMPT INTEGRITY ERROR",
        #     details=f"Logout failed",
        # )
        logger.error(f"Integrity error while login {str(de)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=de.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical("Unexpected Error: ", e)
        # DB Log
        # background_tasks.add_task(
        #     create_audit_log_isolated,
        #     request=request, level=LogLevel.CRITICAL.value,
        #     action="LOGOUT USER SYSTEM ERROR",
        #     details=f"System error: {str(e)}",
        #     payload={
        #         "raw_error": str(e),
        #     }
        # )
        logger.critical("LOGIN FAILED FROM ROUTER")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
