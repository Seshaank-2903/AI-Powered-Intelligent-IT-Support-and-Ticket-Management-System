from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class KnowledgeGapBase(BaseModel):
    topic: str
    description: Optional[str] = None
    occurrence_count: int = 1
    status: str = "OPEN"

class KnowledgeGapResponse(KnowledgeGapBase):
    id: uuid.UUID
    company_id: uuid.UUID
    example_ticket_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class KnowledgeGapUpdate(BaseModel):
    status: Optional[str] = None
