from sqlalchemy.orm import DeclarativeBase

# declarative base. It will be used to create tables for models
class Base(DeclarativeBase):
    pass

from app.models import Department