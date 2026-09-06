from datetime import timedelta
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserAuthResponse

router = APIRouter()

@router.post("/login", response_model=Token, tags=["Auth"])
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.hashed_password:
        raise AppException("AUTH_FAILED", "Incorrect email or password", 400)
    if not security.verify_password(form_data.password, user.hashed_password):
        raise AppException("AUTH_FAILED", "Incorrect email or password", 400)
    if not user.is_active:
        raise AppException("INACTIVE_USER", "Inactive user", 400)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserAuthResponse, tags=["Auth"])
def read_current_user(
    current_user: User = Depends(security.get_current_user)
) -> UserAuthResponse:
    """
    Get current user.
    """
    return UserAuthResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        company_id=current_user.company_id
    )
