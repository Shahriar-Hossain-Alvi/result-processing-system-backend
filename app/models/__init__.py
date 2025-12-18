# import models here so that alembic can find them

from .department_model import Department
from .semester_model import Semester
from .subject_model import Subject
from .student_model import Student
from .mark_model import Mark, ResultStatus
from .subject_offerings_model import SubjectOfferings
from .user_model import User, UserRole
