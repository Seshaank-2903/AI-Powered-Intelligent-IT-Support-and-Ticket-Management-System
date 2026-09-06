from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.core import security
from app.core.exceptions import AppException

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN"]))
):
    # Only return users in the current admin's company
    users = db.query(User).filter(User.company_id == current_user.company_id).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "IT_AGENT"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException("NOT_FOUND", "User not found", 404)
    if user.company_id != current_user.company_id and current_user.role != "SUPER_ADMIN":
        raise AppException("FORBIDDEN", "Not allowed to view user from another company", 403)
    return user
