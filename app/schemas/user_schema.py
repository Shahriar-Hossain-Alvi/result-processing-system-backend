from pydantic import BaseModel, ConfigDict, EmailStr
from app.schemas.department_schema import DepartmentOutSchema
from app.schemas.semester_schema import SemesterOutSchema
from app.models import UserRole
from datetime import date, datetime


class UserBaseSchema(BaseModel):
    username: EmailStr = "student1@gmail.com"
    email: EmailStr = "student1@gmail.com"
    role: UserRole = UserRole.STUDENT
    is_active: bool = True
    mobile_number: str | None = None


class UserCreateSchema(UserBaseSchema):
    password: str = "123456"


class UserUpdateSchemaByAdmin(BaseModel):
    email: EmailStr | None = None
    username: EmailStr | None = None
    is_active: bool | None = None


class UserUpdateSchemaByUser(BaseModel):
    password: str


class UserOutSchema(UserBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    # this is required for response models.
    # pydantic expects DICTs or JSON but sqlalchemy returns objects.
    # So, from_attributes = True tells  pydantic to look for attributes on the source object (like user_object.id, user_object.username) rather than dictionary keys.
    # This allows the UserOutSchema to be initialized directly from a SQLAlchemy without having to convert it to a dictionary or throw an error


class StudentResponseSchemaToGetAllUser(BaseModel):
    id: int
    name: str
    registration: str
    session: str
    department: DepartmentOutSchema | None = None
    semester: SemesterOutSchema | None = None
    present_address: str
    permanent_address: str
    date_of_birth: date | None = None
    photo_url: str
    photo_public_id: str
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime
    updated_at: datetime


class TeacherResponseSchemaToGetAllUser(BaseModel):
    id: int
    name: str
    department: DepartmentOutSchema | None = None
    present_address: str
    permanent_address: str
    date_of_birth: date | None = None
    photo_url: str
    photo_public_id: str
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime
    updated_at: datetime


class AllUsersWithDetailsResponseSchema(BaseModel):
    id: int
    username: EmailStr
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # optional profile data
    student: StudentResponseSchemaToGetAllUser | None = None
    teacher: TeacherResponseSchemaToGetAllUser | None = None

    model_config = ConfigDict(from_attributes=True)
