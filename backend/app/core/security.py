import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError  # type: ignore
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def get_current_user(db: Session = Depends(get_db), token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False))) -> User:
    if token:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active:
                    return user
        except JWTError:
            pass

    # Dev / Default User Fallback for unauthenticated requests
    user = db.query(User).filter(User.role == "SUPER_ADMIN").first()
    if not user:
        user = db.query(User).first()

    if not user:
        from app.models.company import Company
        company = db.query(Company).first()
        if not company:
            company = Company(id=uuid.UUID("00000000-0000-0000-0000-000000000001"), name="Acme Corp", slug="acme-corp")
            db.add(company)
            db.commit()

        user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            email="admin@acme.com",
            name="Admin User",
            company_id=company.id,
            role="SUPER_ADMIN"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "SUPER_ADMIN":
        raise AppException("FORBIDDEN", "The user doesn't have enough privileges", 403)
    return current_user

def require_role(roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles and current_user.role != "SUPER_ADMIN":
            raise AppException("FORBIDDEN", "The user doesn't have enough privileges", 403)
        return current_user
    return role_checker
