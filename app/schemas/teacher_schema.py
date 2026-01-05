from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from app.schemas.user_schema import UserCreateSchema, UserOutSchema
from pydantic_partial import create_partial_model


class TeacherBaseSchema(BaseModel):
    name: str
    department_id: int | None = None
    # user_id: int # Don't need this because user and teacher will be created in same service function
    present_address: str = ""
    permanent_address: str = ""
    date_of_birth: date | None = None
    photo_url: str = ""
    photo_public_id: str = ""


class TeacherCreateSchema(TeacherBaseSchema):
    user: UserCreateSchema


class TeacherResponseSchema(TeacherBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class TeacherResponseSchemaNested(TeacherResponseSchema):
    id: int
    user: UserOutSchema
    model_config = ConfigDict(from_attributes=True)


class TeachersPublicDataResponse(BaseModel):
    name: str
    photo_url: str
    model_config = ConfigDict(from_attributes=True)


class TeachersDepartmentWiseGroupResponse(BaseModel):
    department_name: str
    teachers: list[TeachersPublicDataResponse]
    model_config = ConfigDict(from_attributes=True)


# 1. dynamic partial base beacuse directly using create_partial_model is giving warning in service functions parameter
_PartialTeacher = create_partial_model(TeacherBaseSchema)


class TeacherUpdateByAdminSchema(_PartialTeacher):
    pass


class TeacherUpdateSchema(BaseModel):
    name: str | None = None
    present_address: str | None = None
    permanent_address: str | None = None
    date_of_birth: date | None = None
    photo_url: str | None = None
