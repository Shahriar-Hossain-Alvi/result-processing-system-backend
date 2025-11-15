## Tables
1. users = id, username, email, hashed_password, is_active, role ✅
2. Department = id, dept_name ✅
3. semester = id, semester_name, semester_number ✅
4. students = id, name, registration, session, department_id, semester_id ✅
5. subject = id, subject_title, subject_code, semester_id, credits
6. marks = id, student_id, subject_id, semester_id, assignmet_mark, midterm_mark, final_mark, class_test_mark, GPA, total_mark grade(GPA), user_id(teacher_id/Admin_id)
7. subject_offerings = id, subject_id, department_id, taught_by


## Relationships
Department → Students                       | 1:N  | Each department has many students           
Department ↔ Subject (via subject_offerings)| M:N  | Subjects can belong to multiple departments 
Semester → Subjects                         | 1:N  | Each semester has many subjects             
Students → Marks                            | 1:N  | Each student can have many marks            
Subject → Marks                             | 1:N  | Each subject can have many marks            
Semester → Marks                            | 1:N  | multiple marks of different subjects belongs to one semester           
Users → Students                            | 1:1  | Each student has one user account           




after creation hooks

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
