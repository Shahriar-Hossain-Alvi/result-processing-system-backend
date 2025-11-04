from app.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, String

## Tables
# 1. students table = id, name, roll, registration, session, dept
# 2. results table = id, student_id, subject_id, semester_id, assignmet_mark, midterm_mark, final_mark, class_test_mark, total_mark grade(GPA)
# 3. semester = id, name, number
# 4. subject = id, name, subject_code, semester_id, dept_id, credits
# 5. Department = id, name

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dept_name = mapped_column(String(100), nullable=False, unique=True) # TODO: all department names must be unique and lowercased department_name = department_name.strip().lower()