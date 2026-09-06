from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.services.ticket_service import TicketService
from app.core import security
from app.core.exceptions import AppException
import uuid

router = APIRouter()

@router.post("/", response_model=TicketResponse)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    # Enforce company isolation
    if current_user.company_id != ticket_in.company_id and current_user.role != "SUPER_ADMIN":
        raise AppException("FORBIDDEN", "Cannot create ticket for another company", 403)
        
    ticket = TicketService.create_ticket(db, ticket_in)

    # Auto-create initial user message & AI response
    try:
        from app.models.message import Message
        from app.rag.retrieval import retrieve_company_protocols
        from app.ai.response_guard import generate_protocol_response

        msg_content = ticket.description or ticket.title
        user_msg = Message(
            ticket_id=ticket.id,
            sender_type="USER",
            sender_id=str(current_user.id),
            message=msg_content
        )
        db.add(user_msg)
        db.commit()

        # Search Protocols & Generate AI Reply
        chunks = retrieve_company_protocols(str(ticket.company_id), msg_content)
        ai_text, source_type = generate_protocol_response(msg_content, chunks)

        bot_msg = Message(
            ticket_id=ticket.id,
            sender_type="BOT",
            sender_id="AI_ASSISTANT",
            message=ai_text,
            source=source_type
        )
        db.add(bot_msg)

        if source_type == "PROTOCOL":
            ticket.resolution_source = "PROTOCOL"
        else:
            ticket.resolution_source = "MISTRAL"

        ticket.status = "WAITING_FOR_USER"
        db.commit()
        db.refresh(ticket)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating AI reply on ticket creation: {e}")

    return ticket

@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    query = db.query(Ticket)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(Ticket.company_id == current_user.company_id)
        if current_user.role == "EMPLOYEE":
            from sqlalchemy import or_
            query = query.filter(
                or_(Ticket.visibility != "CONFIDENTIAL", Ticket.user_id == current_user.id)
            )

    tickets = query.order_by(Ticket.created_at.desc()).all()

    result = []
    for t in tickets:
        resp = TicketResponse.model_validate(t)
        if t.user:
            resp.user_email = t.user.email
            resp.user_name = t.user.name or t.user.email.split("@")[0]
        result.append(resp)
    return result

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise AppException("NOT_FOUND", "Ticket not found", 404)
        
    if current_user.role != "SUPER_ADMIN":
        if ticket.company_id != current_user.company_id:
            raise AppException("FORBIDDEN", "Not allowed to access this ticket", 403)
        if current_user.role == "EMPLOYEE" and ticket.user_id != current_user.id:
            raise AppException("FORBIDDEN", "Not allowed to access this ticket", 403)
        if ticket.visibility == "CONFIDENTIAL" and current_user.role == "EMPLOYEE" and ticket.user_id != current_user.id:
            raise AppException("FORBIDDEN", "Not allowed to access this confidential ticket", 403)
            
    return ticket

@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: uuid.UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    ticket = get_ticket(ticket_id, db, current_user) # validates access
    
    if ticket_update.status and ticket_update.status != ticket.status:
        # Use state machine
        TicketService.update_status(
            db, 
            ticket, 
            ticket_update.status, 
            actor_type=current_user.role,
            actor_id=str(current_user.id)
        )
        
    # Apply other updates
    update_data = ticket_update.model_dump(exclude_unset=True)
    update_data.pop("status", None) # Already handled
    
    for field, value in update_data.items():
        setattr(ticket, field, value)
        
    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    ticket = get_ticket(ticket_id, db, current_user)
    # If ticket status is allowed to resolve
    if ticket.status in ["NEW", "CLASSIFYING", "PROTOCOL_SEARCH", "PROTOCOL_RESPONSE", "WAITING_FOR_USER", "AI_TROUBLESHOOTING", "ESCALATED", "IT_IN_PROGRESS"]:
        ticket.status = "RESOLVED"
        db.commit()
        db.refresh(ticket)
    return {"status": "RESOLVED", "ticket_number": ticket.ticket_number}

@router.post("/{ticket_id}/close")
def close_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    ticket = get_ticket(ticket_id, db, current_user)
    ticket.status = "CLOSED"
    db.commit()
    return {"status": "CLOSED"}

@router.post("/{ticket_id}/ai-respond")
def ai_respond_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    from app.rag.retrieval import retrieve_company_protocols
    from app.ai.response_guard import generate_protocol_response
    from app.models.message import Message

    ticket = get_ticket(ticket_id, db, current_user)
    query = f"{ticket.title} {ticket.description or ''}"

    # Perform RAG Retrieval
    chunks = retrieve_company_protocols(str(ticket.company_id), query)
    ai_text, source_type = generate_protocol_response(query, chunks)

    # Save BOT response message
    bot_msg = Message(
        ticket_id=ticket.id,
        sender_type="BOT",
        sender_id="AI_ASSISTANT",
        message=ai_text,
        source=source_type
    )
    db.add(bot_msg)

    # Extract protocol file names if available
    sources = []
    if chunks:
        sources = [c.get("metadata", {}).get("protocol_id", "Company Protocol") for c in chunks if c.get("metadata")]

    if source_type == "PROTOCOL":
        ticket.status = "PROTOCOL_RESPONSE"
        ticket.resolution_source = "PROTOCOL"
    else:
        ticket.status = "AI_TROUBLESHOOTING"
        ticket.resolution_source = "MISTRAL"

    ticket.status = "WAITING_FOR_USER"
    db.commit()
    db.refresh(ticket)

    return {
        "ticket_id": str(ticket.id),
        "ticket_number": ticket.ticket_number,
        "ai_response": ai_text,
        "source_type": source_type,
        "sources": list(set(sources)),
        "status": ticket.status
    }

@router.post("/{ticket_id}/feedback")
def ticket_feedback(
    ticket_id: uuid.UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    from app.services.knowledge_gap_service import KnowledgeGapService
    ticket = get_ticket(ticket_id, db, current_user)
    is_resolved = payload.get("resolved", False)

    if is_resolved:
        ticket.status = "RESOLVED"
        db.commit()
        return {"status": "RESOLVED", "message": "Ticket marked as resolved."}
    else:
        # Record knowledge gap and escalate
        KnowledgeGapService.record_gap(db, ticket)
        ticket.status = "ESCALATED"
        db.commit()
        return {"status": "ESCALATED", "message": "Issue escalated to IT support team. Knowledge gap logged."}

