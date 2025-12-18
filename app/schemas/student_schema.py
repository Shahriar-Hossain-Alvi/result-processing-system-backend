from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.user_schema import UserOutSchema


class StudentBaseSchema(BaseModel):
    name: str
    registration: str
    session: str
    department_id: int
    semester_id: int
    user_id: int
    present_address: str = ""
    permanent_address: str = ""
    date_of_birth: datetime | None = None
    mobile_number: str = ""
    photo_url: str = ""


class StudentCreateSchema(StudentBaseSchema):
    pass


class StudentOutSchema(StudentBaseSchema):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StudentResponseSchemaNested(StudentBaseSchema):
    id: int
    user: UserOutSchema
    model_config = ConfigDict(from_attributes=True)


class StudentUpdateSchema(BaseModel):
    name: str | None = None
    registration: str | None = None
    session: str | None = None
    department_id: int | None = None
    semester_id: int | None = None
    present_address: str | None = None
    permanent_address: str | None = None
    date_of_birth: datetime | None = None
    mobile_number: str | None = None
    photo_url: str | None = None
