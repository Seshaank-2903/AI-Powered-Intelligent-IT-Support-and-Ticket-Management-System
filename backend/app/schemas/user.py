from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
import uuid
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = None
    role: str = "EMPLOYEE"
    is_active: bool = True
    zulip_user_id: Optional[str] = None

class UserCreate(UserBase):
    company_id: uuid.UUID
    password: Optional[str] = None

class UserResponse(UserBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
