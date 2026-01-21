from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.subject_schema import SubjectBaseSchema


class SubjectOfferingBase(BaseModel):
    taught_by_id: int
    subject_id: int
    department_id: int

#  used in create_new_subject_offering router function


class SubjectOfferingCreateSchema(SubjectOfferingBase):
    pass


# used in update_subject_offering router function (admin, super admin)
class SubjectOfferingUpdateSchema(BaseModel):
    taught_by_id: int | None = None
    subject_id: int | None = None
    department_id: int | None = None


# Get All Subject Offerings: below schemas are used in get_all_subject_offerings router function
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


class AllSubjectOfferingsResponseSchema(BaseModel):
    id: int
    taught_by_id: int | None
    subject_id: int
    department_id: int
    created_at: datetime
    updated_at: datetime
    taught_by: SubjectOfferingTaughtByResponseSchema | None
    department: SubjectOfferingDepartmentResponseSchema
    subject: SubjectOfferingSubjectResponseSchema

    model_config = ConfigDict(from_attributes=True)
