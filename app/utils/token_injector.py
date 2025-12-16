from fastapi import Request, HTTPException, status
from starlette.datastructures import MutableHeaders


async def inject_token(request: Request):
    """
    Reads the access_token from the cookie and injects it into the 
    Authorization: Bearer header to satisfy OAuth2PasswordBearer.
    """

    # get the cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if access_token:
        # if token exists, create a mutable header object
        mutable_headers = MutableHeaders(request._headers)

        # inject the header
        mutable_headers["Authorization"] = f"Bearer {access_token}"

        # update the request headers
        request._headers = mutable_headers

        # The function must return None or some data, but we are primarily modifying the request headers in place.

        return None
