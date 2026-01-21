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


# used in create_admin router function and in create student_schema, create teacher schema
class UserCreateSchema(UserBaseSchema):
    password: str = "123456"


# used in update_single_user_by_admin router function
# TODO: create user profile to update these user data by self
class UserUpdateSchemaByAdmin(BaseModel):
    email: EmailStr | None = None
    username: EmailStr | None = None
    is_active: bool | None = None
    mobile_number: str | None = None


# TODO: create user profile to update users default password by self
# class UserPasswordUpdateSchema(BaseModel):
#     password: str


# used in get_logged_in_user router function and authorized_user depedency, get_current_user depedency
class UserOutSchema(UserBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    # this is required for response models.
    # pydantic expects DICTs or JSON but sqlalchemy returns objects.
    # So, from_attributes = True tells  pydantic to look for attributes on the source object (like user_object.id, user_object.username) rather than dictionary keys.
    # This allows the UserOutSchema to be initialized directly from a SQLAlchemy without having to convert it to a dictionary or throw an error


# below schemas are used in get_all_users router function for admins All User page and get_single_user router function for single user details page
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
    mobile_number: str | None
    created_at: datetime
    updated_at: datetime

    # optional profile data
    student: StudentResponseSchemaToGetAllUser | None = None
    teacher: TeacherResponseSchemaToGetAllUser | None = None

    model_config = ConfigDict(from_attributes=True)
