# import models here so that alembic can find them

from .department_model import Department
from .semester_model import Semester
from .subject_model import Subject
from .student_model import Student
from .mark_model import Mark, ResultStatus, ResultChallengeStatus
from .subject_offerings_model import SubjectOfferings
from .user_model import User, UserRole
from .teacher_model import Teacher
from .audit_log_model import AuditLog
