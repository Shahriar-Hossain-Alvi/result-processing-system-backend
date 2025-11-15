from pydantic import BaseModel, ConfigDict


class SubjectBaseSchema(BaseModel):
    subject_name: str
    subject_code: str
    credits: float
    semester_id: int

class SubjectCreateSchema(SubjectBaseSchema):
    pass


class SubjectOutSchema(SubjectBaseSchema):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SubjectUpdateSchema(BaseModel):
    subject_name: str | None = None
    subject_code: str | None = None
    credits: float | None = None
    semester_id: int | None = None