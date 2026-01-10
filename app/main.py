# this project is using python 3.12 interpreter
from fastapi import FastAPI
import uvicorn
from app.core.logging_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.audit_log_middleware import AuditMiddleware
from app.middleware.inject_token import TokenInjectionFromCookieToHeaderMiddleware
from app.routes import department_routes, login_logout, mark_routes, semester_routes, student_routes, subject_offering_route, subject_routes, user_routes, teacher_routes

# setup logging
setup_logging()

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# request comes here and follows the middlewares top to bottom (req -> middleware -> router)
# 1 when request IN
app.add_middleware(TokenInjectionFromCookieToHeaderMiddleware)
app.add_middleware(AuditMiddleware)  # 2 when request IN
# response comes here and follows the middlewares bottom to top (router -> middleware -> res)

# add the routes
app.include_router(login_logout.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(teacher_routes.router, prefix="/api")
app.include_router(student_routes.router, prefix="/api")
app.include_router(department_routes.router, prefix="/api")
app.include_router(semester_routes.router, prefix="/api")
app.include_router(subject_routes.router, prefix="/api")
app.include_router(subject_offering_route.router, prefix="/api")
app.include_router(mark_routes.router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
