from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class SubjectBaseSchema(BaseModel):
    subject_title: str = Field(..., max_length=100, examples=[
                               "Computer Science & Engineering"])
    subject_code: str = Field(..., max_length=20, examples=[
                              "CSE-123", "CSE-123456", "SWE-1234", "SWE-12345"])
    credits: float = Field(..., examples=[1.5, 3.0])
    semester_id: int

    @field_validator("subject_code")
    @classmethod
    def validate_subject_code(cls, v: str):
        # subject code should have 2-4 letter, then a dash(-), then 4-6 numbers
        pattern = r'^[A-Z]{3,5}-\d{3,6}$'
        if not re.match(pattern, v.upper()):
            raise ValueError(
                'Invalid Subject Code format. Example: Letter(3 to 5)-Number(3 to 6). Eg: CSE-123, CSE-123456, SWE-1234, SWE-12345')
        return v.upper()  # make the subject code uppercase


class SubjectCreateSchema(SubjectBaseSchema):
    pass


class SubjectOutSchema(SubjectBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SubjectUpdateSchema(BaseModel):
    subject_title: str | None = None
    subject_code: str | None = None
    credits: float | None = None
    semester_id: int | None = None
