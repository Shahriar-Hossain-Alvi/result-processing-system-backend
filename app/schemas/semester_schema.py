from pydantic import BaseModel, ConfigDict, field_validator

class SemesterBaseSchema(BaseModel):
    semester_name: str
    semester_number: int
    
    @field_validator("semester_name", mode='before')
    @classmethod
    def lowercase_semester_name(cls, value):
        return value.lower().strip()

class SemesterCreateSchema(SemesterBaseSchema):
    pass

    
class SemesterOutSchema(SemesterBaseSchema):
    id: int 
    model_config = ConfigDict(from_attributes=True)

class SemesterUpdateSchema(SemesterBaseSchema):
    semester_name: str | None = None # type: ignore
    semester_number: int | None = None # type: ignore