from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models import ResultStatus, ResultChallengeStatus


class MarksBaseSchema(BaseModel):
    assignment_mark: float | None = None
    class_test_mark: float | None = None
    midterm_mark: float | None = None
    final_exam_mark: float | None = None
    student_id: int
    subject_id: int
    semester_id: int
    # result_status: ResultStatus = ResultStatus.UNPUBLISHED
    # result_challenge_status: ResultChallengeStatus = ResultChallengeStatus.NONE
    # result_challenge_payment_status: bool | None = None
    # challenged_at: datetime | None = None
    # result_challenge_payment_status: bool | None = None
    # challenge_payment_time: datetime | None = None
    # challenge_resolved_at: datetime | None = None


# used in create_new_mark router function
class MarksCreateSchema(MarksBaseSchema):
    pass


# used in update_a_mark router function
class MarksUpdateSchema(BaseModel):
    # student_id: int
    # subject_id: int
    assignment_mark: float | None = None
    class_test_mark: float | None = None
    midterm_mark: float | None = None
    final_exam_mark: float | None = None
    result_status: ResultStatus | None = None
    # also update the challenged_at for challenge and challenge_resolved_at for resolve
    result_challenge_status: ResultChallengeStatus | None = None
    # also update the challenge_payment_time
    result_challenge_payment_status: bool | None = None
    # challenged_at: datetime | None = None
    # challenge_payment_time: datetime | None = None
    # challenge_resolved_at: datetime | None = None


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
    registration: str
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
    result_status: ResultStatus
    result_challenge_status: ResultChallengeStatus
    result_challenge_payment_status: bool | None = None
    challenged_at: datetime | None = None
    challenge_payment_time: datetime | None = None
    challenge_resolved_at: datetime | None = None
    semester: PopulatedMarksStudentsCurrentSemesterResponseSchema
    subject: MinimalSubjectResponseSchema
    student: PopulatedMarksStudentResponseSchema
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# used in get_all_filtered_marks router function
class SemesterWiseAllSubjectsMarksWithPopulatedDataResponseSchema(BaseModel):
    department_name: str
    semester_name: str
    session: str
    marks: list[PopulatedMarksResponseSchema]
    model_config = ConfigDict(from_attributes=True)


# used in generate_single_students_single_semester_result router function
class MarkDetailsSchema(BaseModel):
    id: int
    assignment_mark: float
    class_test_mark: float
    midterm_mark: float
    final_exam_mark: float
    total_mark: float
    GPA: float
    # student_id: int
    # student: PopulatedMarksStudentResponseSchema
    # semester_id: int
    # semester: PopulatedMarksStudentsCurrentSemesterResponseSchema
    subject_id: int
    subject: MinimalSubjectResponseSchema
    model_config = ConfigDict(from_attributes=True)


# used in generate_single_students_single_semester_result router function
class GenerateSingleStudentsSingleSemesterResultResponseSchema(BaseModel):
    published_count: int
    total_subjects: int
    student_info: PopulatedMarksStudentResponseSchema | None = None
    semester_info: PopulatedMarksStudentsCurrentSemesterResponseSchema | None = None
    department_info: PopulatedMarksStudentsDepartmentResponseSchema | None = None
    result: list[MarkDetailsSchema] | None = None
    message: str | None = None
    model_config = ConfigDict(from_attributes=True)
