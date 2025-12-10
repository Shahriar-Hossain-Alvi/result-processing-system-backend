from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_login import login_user
from app.db.db import get_db_session
from app.schemas.jwt_schema import TokenSchema

# login router

router = APIRouter(prefix='/login', tags=['login'])



# login route setup with httponly cookies
@router.post("/", response_model=TokenSchema)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)):
    try:
        return await login_user(db, form_data.username, form_data.password, response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    