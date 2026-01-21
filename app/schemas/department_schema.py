from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DepartmentBaseSchema(BaseModel):
    department_name: str


# used in create_new_department router function
class DepartmentCreateSchema(DepartmentBaseSchema):
    pass


# used in get_all_departments router function
class DepartmentOutSchema(DepartmentBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    # this is required for response models.
    # pydantic expects DICTs or JSON but sqlalchemy returns objects.
    # So, from_attributes = True tells  pydantic to look for attributes on the source object (like user_object.id, user_object.username) rather than dictionary keys.
    # This allows the UserOutSchema to be initialized directly from a SQLAlchemy without having to convert it to a dictionary or throw an error


# used in update_department router function
class DepartmentUpdateSchema(DepartmentBaseSchema):
    pass
