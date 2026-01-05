import re


def parse_integrity_error(error_msg: str) -> str:
    """
    Parse/Extract readable message from PostgreSQL IntegrityError
    example: 'Key (registration)=(213313316) already exists' 
    output: 'Registration 213313316 already exists'
    """
    # constraint name checks

    # --- Student Tables Constraints ---
    if "students_registration_key" in error_msg:
        # get the value using Regex
        match = re.search(r"Key \(registration\)=\((.*?)\)", error_msg)
        val = match.group(1) if match else ""
        return f"Registration number '{val}' already exists in our records."

    if "students_user_id_key" in error_msg:
        return "This user is already assigned to another student profile."

    # --- User Tables Constraints ---
    if "users_username_key" in error_msg:
        match = re.search(r"Key \(username\)=\((.*?)\)", error_msg)
        val = match.group(1) if match else ""
        return f"The username '{val}' is already registered."

    if "users_email_key" in error_msg:
        match = re.search(r"Key \(email\)=\((.*?)\)", error_msg)
        val = match.group(1) if match else ""
        return f"The email address '{val}' is already registered."

    if "users_mobile_number_key" in error_msg:
        return "This mobile number is already used for another user."

    # --- Teacher Tables Constraints ---
    if "teachers_user_id_key" in error_msg:
        return "This user is already assigned to another teacher profile."

    # --- Department Tables Constraints ---
    if "departments_department_name_key" in error_msg:
        match = re.search(r"Key \(department_name\)=\((.*?)\)", error_msg)
        val = match.group(1) if match else ""
        return f"A department named '{val}' already exists."

    # --- Semester Tables Constraints ---
    if "semesters_semester_name_key" in error_msg:
        match = re.search(r"Key \(semester_name\)=\((.*?)\)", error_msg)
        val = match.group(1) if match else ""
        return f"Semester name '{val}' already exists."

    if "semesters_semester_number_key" in error_msg:
        match = re.search(r"Key \(semester_number\)=\((.*?)\)", error_msg)
        val = match.group(1) if match else ""
        return f"Semester number '{val}' is already assigned."

    # --- Subject Tables Constraints ---
    if "subjects_subject_code_key" in error_msg:
        match = re.search(r"Key \(subject_code\)=\((.*?)\)", error_msg)
        val = match.group(1) if match else ""
        return f"A subject with code '{val}' already exists."

    # --- Mark Tables Constraints ---
    if "unique_mark_record" in error_msg:
        return "A mark entry already exists for this student in the selected subject and semester."

    # If no constraint name found (default message)
    return "This record already exists or violates a database constraint. Please check your data."
