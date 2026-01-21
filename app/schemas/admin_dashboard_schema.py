from pydantic import BaseModel, ConfigDict


class AdminDashboardBaseSchema(BaseModel):
    users: int
    admins: int
    teachers: int
    students: int
    departments: int
    semesters: int
    subjects: int
    assigned_courses: int
    marks: int
    audit_logs: int


class AdminDashboardResponseSchema(AdminDashboardBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)
