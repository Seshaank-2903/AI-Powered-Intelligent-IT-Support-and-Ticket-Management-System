from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class CompanyCreate(CompanyBase):
    slug: str

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
