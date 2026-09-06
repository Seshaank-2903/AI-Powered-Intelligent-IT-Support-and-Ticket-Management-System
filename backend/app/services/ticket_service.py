from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
from app.models.ticket import Ticket
from app.models.ticket_event import TicketEvent
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.core.exceptions import AppException

# State machine allowed transitions
ALLOWED_TRANSITIONS = {
    "NEW": ["CLASSIFYING", "PROTOCOL_SEARCH", "PROTOCOL_RESPONSE", "PROTOCOL_ATTEMPTED", "AI_TROUBLESHOOTING", "AI_ASSISTED", "WAITING_FOR_USER", "ESCALATED"],
    "CLASSIFYING": ["PROTOCOL_SEARCH", "PROTOCOL_RESPONSE", "PROTOCOL_ATTEMPTED", "AI_TROUBLESHOOTING", "AI_ASSISTED", "WAITING_FOR_USER", "ESCALATED"],
    "PROTOCOL_SEARCH": ["PROTOCOL_RESPONSE", "PROTOCOL_ATTEMPTED", "AI_TROUBLESHOOTING", "AI_ASSISTED", "WAITING_FOR_USER", "ESCALATED"],
    "PROTOCOL_RESPONSE": ["PROTOCOL_ATTEMPTED", "WAITING_FOR_USER", "AI_ASSISTED", "ESCALATED"],
    "PROTOCOL_ATTEMPTED": ["RESOLVED", "AI_ASSISTED", "WAITING_FOR_USER", "ESCALATED", "PROTOCOL_ATTEMPTED"],
    "AI_ASSISTED": ["RESOLVED", "WAITING_FOR_USER", "ESCALATED", "PROTOCOL_ATTEMPTED", "AI_ASSISTED"],
    "WAITING_FOR_USER": ["RESOLVED", "AI_TROUBLESHOOTING", "AI_ASSISTED", "PROTOCOL_ATTEMPTED", "WAITING_FOR_USER", "ESCALATED"],
    "AI_TROUBLESHOOTING": ["RESOLVED", "WAITING_FOR_USER", "AI_ASSISTED", "PROTOCOL_ATTEMPTED", "ESCALATED"],
    "ESCALATED": ["IT_IN_PROGRESS", "RESOLVED"],
    "IT_IN_PROGRESS": ["RESOLVED"],
    "RESOLVED": ["CLOSED"],
    "CLOSED": []
}

class TicketService:
    @staticmethod
    def generate_ticket_number(db: Session) -> str:
        # Get count for current year and format appropriately
        year = datetime.now().year
        count = db.query(Ticket).filter(Ticket.created_at >= datetime(year, 1, 1)).count() + 1
        return f"TKT-{year}-{count:06d}"

    @staticmethod
    def create_ticket(db: Session, ticket_in: TicketCreate) -> Ticket:
        ticket = Ticket(
            ticket_number=TicketService.generate_ticket_number(db),
            company_id=ticket_in.company_id,
            user_id=ticket_in.user_id,
            title=ticket_in.title,
            description=ticket_in.description,
            category=ticket_in.category,
            priority=ticket_in.priority,
            visibility=getattr(ticket_in, "visibility", "NORMAL") or "NORMAL",
            status="NEW"
        )
        db.add(ticket)
        db.flush() # flush to get ticket id

        # Add Event
        event = TicketEvent(
            ticket_id=ticket.id,
            event_type="CREATED",
            actor_type="SYSTEM"
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def update_status(db: Session, ticket: Ticket, new_status: str, actor_type: str, actor_id: Optional[str] = None) -> Ticket:
        current_status = ticket.status
        
        if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
            raise AppException("INVALID_TRANSITION", f"Cannot transition from {current_status} to {new_status}", 400)
        
        ticket.status = new_status
        if new_status == "CLOSED":
            ticket.closed_at = datetime.now(timezone.utc)
            
        # Log event
        event = TicketEvent(
            ticket_id=ticket.id,
            event_type=new_status,
            actor_type=actor_type,
            actor_id=actor_id
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket
