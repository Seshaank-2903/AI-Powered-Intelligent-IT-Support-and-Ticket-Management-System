from pydantic import BaseModel, ConfigDict

class AnalyticsOverview(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    escalated_tickets: int
    protocol_resolution_rate: float
    ai_resolution_rate: float
    escalation_rate: float
    average_resolution_time_hours: float
    open_knowledge_gaps: int

    model_config = ConfigDict(from_attributes=True)
