from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class SemesterBaseSchema(BaseModel):
    semester_name: str
    semester_number: int

    @field_validator("semester_name", mode='before')
    @classmethod
    def lowercase_semester_name(cls, value):
        return value.lower().strip()


# used in create_semester router function
class SemesterCreateSchema(SemesterBaseSchema):
    pass


# used in get_all_semesters router function
class SemesterOutSchema(SemesterBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# used update_single_semester router function
class SemesterUpdateSchema(SemesterBaseSchema):
    semester_name: str | None = None  # type: ignore
    semester_number: int | None = None  # type: ignore
