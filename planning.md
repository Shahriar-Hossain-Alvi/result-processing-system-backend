## Tables
1. students table = id, name, roll, registration, session, dept
2. results table = id, student_id, subject_id, semester_id, assignmet_mark, midterm_mark, final_mark, class_test_mark, total_mark grade(GPA)
3. semester = id, name, number
4. subject = id, name, subject_code, semester_id, dept_id, credits
5. Department = id, name

## Relationships
- Department → Students = 1:N
- Department → Subjects = 1:N
- Semester → Subjects = 1:N
- Semester → Marks = 1:N
- Student → Marks = 1:N
- Subject → Marks = 1:N



## Folder Structure
fastapi_backend/
│
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── routers/
│   │   ├── students.py
│   │   ├── subjects.py
│   │   ├── semesters.py
│   │   ├── departments.py
│   │   └── marks.py
│   └── __init__.py
│
├── requirements.txt
└── .env
