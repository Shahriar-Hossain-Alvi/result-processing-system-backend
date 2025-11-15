from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from app.core import settings

# access token
def create_access_token(
    subject: str, # username(email)
    expires_delta: Optional[timedelta] = None                   
    ) -> str: 
    
    # create JWT access token
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)) # set the expiration time


    payload = {
        "sub": str(subject),
        "iat": int(datetime.now(timezone.utc).timestamp()), # issued at time
        "exp": int(expire.timestamp()), # expiration time
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM) # this is the access token

    return token


def decode_access_token(token: str):
    
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) # returns the payload (sub, iat, exp)
    except ExpiredSignatureError:
        print("Expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"www-Authentication": "Bearer"},
        )

   