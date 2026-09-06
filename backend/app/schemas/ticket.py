from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime

class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    visibility: Optional[str] = "NORMAL"

class TicketCreate(TicketBase):
    user_id: uuid.UUID
    company_id: uuid.UUID

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    visibility: Optional[str] = None
    resolution_source: Optional[str] = None

class TicketEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    actor_type: str
    actor_id: Optional[str] = None
    metadata_json: Optional[dict] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketResponse(TicketBase):
    id: uuid.UUID
    ticket_number: str
    company_id: uuid.UUID
    user_id: uuid.UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    status: str
    visibility: str = "NORMAL"
    resolution_source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    events: Optional[List[TicketEventResponse]] = []
    
    model_config = ConfigDict(from_attributes=True)
