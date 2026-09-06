from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket
from app.models.knowledge_gap import KnowledgeGap
from app.schemas.analytics import AnalyticsOverview
import logging
import uuid

logger = logging.getLogger(__name__)

class AnalyticsService:
    @staticmethod
    def get_overview(db: Session, company_id: Optional[uuid.UUID] = None) -> AnalyticsOverview:
        # Base query for tickets
        ticket_query = db.query(Ticket)
        gap_query = db.query(KnowledgeGap)
        
        if company_id:
            ticket_query = ticket_query.filter(Ticket.company_id == company_id)
            gap_query = gap_query.filter(KnowledgeGap.company_id == company_id)

        total_tickets = ticket_query.count()
        open_tickets = ticket_query.filter(Ticket.status.notin_(["RESOLVED", "CLOSED"])).count()
        resolved_tickets = ticket_query.filter(Ticket.status == "RESOLVED").count()
        escalated_tickets = ticket_query.filter(Ticket.status == "ESCALATED").count()
        
        # Calculate rates
        protocol_resolutions = ticket_query.filter(Ticket.resolution_source == "PROTOCOL").count()
        ai_resolutions = ticket_query.filter(Ticket.resolution_source == "MISTRAL").count()
        
        protocol_rate = (protocol_resolutions / total_tickets * 100) if total_tickets > 0 else 0.0
        ai_rate = ((protocol_resolutions + ai_resolutions + resolved_tickets) / total_tickets * 100) if total_tickets > 0 else 0.0
        if ai_rate > 100.0: ai_rate = 100.0
        escalation_rate = (escalated_tickets / total_tickets * 100) if total_tickets > 0 else 0.0
        
        # Gaps
        open_gaps = gap_query.filter(KnowledgeGap.status == "OPEN").count()

        return AnalyticsOverview(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            escalated_tickets=escalated_tickets,
            protocol_resolution_rate=round(protocol_rate, 2),
            ai_resolution_rate=round(ai_rate, 2),
            escalation_rate=round(escalation_rate, 2),
            average_resolution_time_hours=0.0, # Placeholder, requires complex time diff aggregation
            open_knowledge_gaps=open_gaps
        )
