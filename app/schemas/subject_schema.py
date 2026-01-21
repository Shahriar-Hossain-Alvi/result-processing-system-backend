from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

from pydantic_partial import create_partial_model


class SubjectBaseSchema(BaseModel):
    subject_title: str = Field(..., max_length=100, examples=[
                               "Computer Science & Engineering"])
    subject_code: str = Field(..., max_length=20, examples=[
                              "CSE-123", "CSE-123456", "SWE-1234", "SWE-12345"])
    credits: float = Field(..., examples=[1.5, 3.0])
    semester_id: int
    is_general: bool = False

    @field_validator("subject_code")
    @classmethod
    def validate_subject_code(cls, v: str):
        # subject code should have 2-4 letter, then a dash(-), then 4-6 numbers
        pattern = r'^[A-Z]{3,5}-\d{3,6}$'
        if not re.match(pattern, v.upper()):
            raise ValueError(
                'Invalid Subject Code format. Example: Letter(3 to 5)-Number(3 to 6). Eg: CSE-123, CSE-123456, SWE-1234, SWE-12345')
        return v.upper()  # make the subject code uppercase


# used in create_new_subject router function
class SubjectCreateSchema(SubjectBaseSchema):
    pass


# used in get_all_subjects router function
class MinimalSemesterResponseSchema(BaseModel):
    semester_name: str
    semester_number: int


class SubjectWithSemesterResponseSchema(SubjectBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    semester: MinimalSemesterResponseSchema

    model_config = ConfigDict(from_attributes=True)


# used in update_subject_by_admin router function
_Partial_Subject = create_partial_model(SubjectBaseSchema)


class SubjectUpdateSchema(_Partial_Subject):
    pass
