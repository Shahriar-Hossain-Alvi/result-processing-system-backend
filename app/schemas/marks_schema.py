from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models import ResultStatus


class MarksBaseSchema(BaseModel):
    assignment_mark: float | None = None
    class_test_mark: float | None = None
    midterm_mark: float | None = None
    final_exam_mark: float | None = None
    student_id: int
    subject_id: int
    semester_id: int
    result_status: ResultStatus = ResultStatus.UNPUBLISHED
    result_challenge_payment_status: None | bool = None
    challenged_at: datetime | None = None


# used in create_new_mark router function
class MarksCreateSchema(MarksBaseSchema):
    pass


class MarksUpdateSchema(BaseModel):
    assignment_mark: float | None = None
    class_test_mark: float | None = None
    midterm_mark: float | None = None
    final_exam_mark: float | None = None
    result_status: ResultStatus | None = None
    result_challenge_payment_status: bool | None = None
    challenged_at: datetime | None = None


class MarksResponseSchema(MarksBaseSchema):
    id: int
    total_mark: float
    GPA: float
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SemesterWiseAllSubjectsMarksResponseSchema(BaseModel):
    semester_id: int
    marks: list[MarksResponseSchema]
    model_config = ConfigDict(from_attributes=True)


# used in get_all_filtered_marks router function
class PopulatedMarksStudentsCurrentSemesterResponseSchema(BaseModel):
    id: int
    semester_name: str
    semester_number: int
    model_config = ConfigDict(from_attributes=True)


# used in get_all_filtered_marks router function
class PopulatedMarksStudentsDepartmentResponseSchema(BaseModel):
    id: int
    department_name: str
    model_config = ConfigDict(from_attributes=True)


# used in get_all_filtered_marks router function
class PopulatedMarksStudentResponseSchema(BaseModel):
    id: int
    user_id: int
    name: str
    registration: int
    session: str
    department_id: int
    department: PopulatedMarksStudentsDepartmentResponseSchema
    semester_id: int
    semester: PopulatedMarksStudentsCurrentSemesterResponseSchema
    model_config = ConfigDict(from_attributes=True)


# used in get_all_filtered_marks router function
class MinimalSubjectResponseSchema(BaseModel):
    id: int
    subject_title: str
    subject_code: str
    credits: float
    model_config = ConfigDict(from_attributes=True)


# used in get_all_filtered_marks router function
class PopulatedMarksResponseSchema(MarksBaseSchema):
    id: int
    total_mark: float
    GPA: float
    subject: MinimalSubjectResponseSchema
    student: PopulatedMarksStudentResponseSchema
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# used in get_all_filtered_marks router function
class SemesterWiseAllSubjectsMarksWithPopulatedDataResponseSchema(BaseModel):
    semester_id: int
    marks: list[PopulatedMarksResponseSchema]
    model_config = ConfigDict(from_attributes=True)
