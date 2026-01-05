from fastapi import HTTPException, Depends
from app.core.authenticated_user import get_current_user
from app.schemas.user_schema import UserOutSchema

# This functions already returns the current user, so passing current_user as get_current_user dependency will be redundant wherever this function is used

# ensure super admin


def ensure_super_admin(current_user: UserOutSchema = Depends(get_current_user)):
    if current_user.role.value != "super_admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return current_user

# ensure admin


def ensure_admin(current_user: UserOutSchema = Depends(get_current_user)):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return current_user

# ensure admin or teacher


def ensure_admin_or_teacher(current_user: UserOutSchema = Depends(get_current_user)):
    if current_user.role.value not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return current_user

# ensure admin or teacher


def ensure_student(current_user: UserOutSchema = Depends(get_current_user)):
    if current_user.role.value != "student":
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return current_user
