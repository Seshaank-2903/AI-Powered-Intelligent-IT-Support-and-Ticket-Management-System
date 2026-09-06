from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime

class ProtocolBase(BaseModel):
    title: str
    description: Optional[str] = None
    version: Optional[str] = "1.0"

class ProtocolCreate(ProtocolBase):
    company_id: uuid.UUID

class ProtocolUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None

class ProtocolResponse(ProtocolBase):
    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
