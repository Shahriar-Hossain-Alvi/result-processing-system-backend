from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.subject_schema import SubjectBaseSchema


class SubjectOfferingBase(BaseModel):
    taught_by_id: int
    subject_id: int
    department_id: int


class SubjectOfferingCreateSchema(SubjectOfferingBase):
    pass


class SubjectOfferingUpdateSchema(BaseModel):
    taught_by_id: int | None = None
    subject_id: int | None = None
    department_id: int | None = None


# Get All Subject Offerings
class SubjectOfferingDepartmentResponseSchema(BaseModel):
    id: int
    department_name: str
    model_config = ConfigDict(from_attributes=True)


class SubjectOfferingSemesterResponseSchema(BaseModel):
    id: int
    semester_name: str
    model_config = ConfigDict(from_attributes=True)


class SubjectOfferingSubjectResponseSchema(BaseModel):
    id: int
    subject_title: str
    subject_code: str
    credits: float
    is_general: bool
    semester: SubjectOfferingSemesterResponseSchema
    model_config = ConfigDict(from_attributes=True)


class SubjectOfferingTaughtByResponseSchema(BaseModel):
    id: int
    name: str
    department_id: int
    department: SubjectOfferingDepartmentResponseSchema

    model_config = ConfigDict(from_attributes=True)


class AllSubjectOfferingsResponseSchema(SubjectOfferingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    taught_by: SubjectOfferingTaughtByResponseSchema
    department: SubjectOfferingDepartmentResponseSchema
    subject: SubjectOfferingSubjectResponseSchema

    model_config = ConfigDict(from_attributes=True)
