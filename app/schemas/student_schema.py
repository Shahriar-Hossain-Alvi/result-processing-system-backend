import re
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, datetime
from pydantic_partial import create_partial_model
from app.schemas.user_schema import UserCreateSchema, UserOutSchema


class StudentBaseSchema(BaseModel):
    name: str
    registration: str
    session: str = Field(..., examples=["2020-2021"])
    department_id: int | None = None
    semester_id: int | None = None
    # user_id: int # Don't need this because user and student will be created in same service function
    present_address: str = ""
    permanent_address: str = ""
    date_of_birth: date | None = None
    photo_url: str = ""
    photo_public_id: str = ""

    @field_validator("session")
    @classmethod
    def validate_session_format(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{4}$", v):
            raise ValueError(
                'Session must be in "YYYY-YYYY" format (e.g., 2020-2021)')
        return v


# used in create_student_record router function
class StudentCreateSchema(StudentBaseSchema):
    user: UserCreateSchema

# This is unused. Might not needed
# class StudentOutSchema(StudentBaseSchema):
#     id: int
#     created_at: datetime
#     updated_at: datetime
#     model_config = ConfigDict(from_attributes=True)

# TODO: create studet profile and use this schema to get students data
# class StudentResponseSchemaNested(StudentBaseSchema):
#     id: int
#     created_at: datetime
#     updated_at: datetime
#     user: UserOutSchema
#     model_config = ConfigDict(from_attributes=True)

# TODO: create studet profile to update users these data by self
# class StudentUpdateSchema(BaseModel):
#     name: str | None = None
#     present_address: str | None = None
#     permanent_address: str | None = None
#     date_of_birth: date | None = None
#     photo_url: str | None = None


# used in get_all_students_with_minimal_data for mark input
class DepartmentDataForMinimalStudent(BaseModel):
    id: int
    department_name: str
    model_config = ConfigDict(from_attributes=True)


# used in get_all_students_with_minimal_data for mark input
class SemesterDataForMinimalStudent(BaseModel):
    id: int
    semester_name: str
    semester_number: int
    model_config = ConfigDict(from_attributes=True)


# used in get_all_students_with_minimal_data for mark input
class StudentResponseSchemaForMarkInputSearch(BaseModel):
    id: int
    name: str
    registration: str
    session: str
    user_id: int
    department_id: int | None
    department: DepartmentDataForMinimalStudent | None
    semester_id: int | None
    semester: SemesterDataForMinimalStudent | None

    model_config = ConfigDict(from_attributes=True)


# used in update_single_student_by_admin router function
_Partial_Student = create_partial_model(StudentBaseSchema)


class StudentUpdateByAdminSchema(_Partial_Student):
    pass
