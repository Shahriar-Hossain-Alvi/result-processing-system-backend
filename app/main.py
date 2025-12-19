# this project is using python 3.12 interpreter
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.routes import department_routes, login_logout, mark_routes, semester_routes, student_routes, subject_offering_route, subject_routes, user_routes, teacher_routes

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

# add the routes
app.include_router(teacher_routes.router, prefix="/api")
app.include_router(login_logout.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(student_routes.router, prefix="/api")
app.include_router(department_routes.router, prefix="/api")
app.include_router(semester_routes.router, prefix="/api")
app.include_router(subject_routes.router, prefix="/api")
app.include_router(subject_offering_route.router, prefix="/api")
app.include_router(mark_routes.router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
