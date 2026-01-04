from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

# Middleware will take token from the request and inject it to the header


class TokenInjectionFromCookieToHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # get token from cookie
        access_token = request.cookies.get("access_token")

        if access_token:
            # Set it to Authorization header
            if "authorization" not in request.headers:
                logger.info("Injecting token to header")
                # FastAPI/Starlette stores requests data in a special dictionary called scope
                headers = dict(request.scope['headers'])
                auth_header = f"Bearer {access_token}".encode(
                    # encode to bytes using latin-1 (Uvicorn or starlette uses latin-1 endoing for headers, not UTF-8)
                    'latin-1')
                headers[b'authorization'] = auth_header
                request.scope['headers'] = [(k, v) for k, v in headers.items()]

        response = await call_next(request)
        return response
