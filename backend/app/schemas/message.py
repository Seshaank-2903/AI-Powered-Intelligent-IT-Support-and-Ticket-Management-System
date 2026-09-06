from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class MessageBase(BaseModel):
    sender_type: str
    sender_id: Optional[str] = None
    message: str
    source: Optional[str] = None
    metadata_json: Optional[dict] = None

class MessageCreate(MessageBase):
    ticket_id: uuid.UUID

class MessageResponse(MessageBase):
    id: uuid.UUID
    ticket_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
