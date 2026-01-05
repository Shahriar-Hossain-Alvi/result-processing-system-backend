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


class StudentCreateSchema(StudentBaseSchema):
    user: UserCreateSchema


class StudentOutSchema(StudentBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentResponseSchemaNested(StudentBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    user: UserOutSchema
    model_config = ConfigDict(from_attributes=True)


class StudentUpdateSchema(BaseModel):
    name: str | None = None
    present_address: str | None = None
    permanent_address: str | None = None
    date_of_birth: date | None = None
    photo_url: str | None = None


_Partial_Student = create_partial_model(StudentBaseSchema)


class StudentUpdateByAdminSchema(_Partial_Student):
    pass
