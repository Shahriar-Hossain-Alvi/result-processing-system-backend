# this project is using python 3.12 interpreter
from fastapi import FastAPI
import uvicorn

from app.routes import department_routes, login, semester_routes, student_routes, subject_routes, user_routes

app = FastAPI()


# add the routes
app.include_router(login.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(department_routes.router, prefix="/api")
app.include_router(semester_routes.router, prefix="/api")
app.include_router(student_routes.router, prefix="/api")
app.include_router(subject_routes.router, prefix="/api")



if __name__ == "__main__":
    # asyncio.run(init_db())
    uvicorn.run(app, host="0.0.0.0", port=8000)
