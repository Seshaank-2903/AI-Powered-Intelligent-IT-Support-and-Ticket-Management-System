from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.message import Message
from app.models.ticket import Ticket
from app.schemas.message import MessageResponse, MessageCreate
from app.core import security
from app.core.exceptions import AppException
from app.api.tickets import get_ticket
import uuid

router = APIRouter()

@router.get("/{ticket_id}/messages", response_model=List[MessageResponse])
def get_messages(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    # Reuse ticket access validation
    get_ticket(ticket_id, db, current_user)
    
    messages = db.query(Message).filter(Message.ticket_id == ticket_id).order_by(Message.created_at).all()
    return messages

@router.post("/{ticket_id}/messages", response_model=MessageResponse)
def create_message(
    ticket_id: uuid.UUID,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_user)
):
    ticket = get_ticket(ticket_id, db, current_user) # access validation
    
    msg = Message(
        ticket_id=ticket_id,
        sender_type=message_in.sender_type,
        sender_id=message_in.sender_id or str(current_user.id),
        message=message_in.message,
        source=message_in.source,
        metadata_json=message_in.metadata_json
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Auto-generate AI response if sender is USER and ticket is active
    if message_in.sender_type == "USER" and ticket.status not in ["RESOLVED", "CLOSED"]:
        try:
            from app.services.ticket_service import TicketService
            clean_content = message_in.message.strip().lower()

            if clean_content in ["solved", "yes", "fixed", "resolved"]:
                TicketService.update_status(db, ticket, "RESOLVED", actor_type="USER", actor_id=str(current_user.id))
            elif clean_content in ["not solved", "no", "unresolved", "not fixed"]:
                from app.ai.response_guard import generate_mistral_troubleshooting
                from app.services.knowledge_gap_service import KnowledgeGapService

                if ticket.status in ["PROTOCOL_ATTEMPTED", "PROTOCOL_RESPONSE", "WAITING_FOR_USER", "NEW"]:
                    prev_messages = db.query(Message).filter(Message.ticket_id == ticket.id, Message.sender_type == "BOT").all()
                    prev_text = "\n".join([m.message for m in prev_messages]) if prev_messages else ""

                    ai_response, source_type = generate_mistral_troubleshooting(
                        query=ticket.description or ticket.title,
                        previous_attempts=prev_text
                    )
                    bot_msg = Message(
                        ticket_id=ticket.id,
                        sender_type="BOT",
                        sender_id="AI_ASSISTANT",
                        message=ai_response,
                        source="MISTRAL"
                    )
                    db.add(bot_msg)
                    TicketService.update_status(db, ticket, "AI_TROUBLESHOOTING", actor_type="SYSTEM")
                else:
                    KnowledgeGapService.record_gap(db, ticket)
                    TicketService.update_status(db, ticket, "ESCALATED", actor_type="USER", actor_id=str(current_user.id))
            else:
                from app.rag.retrieval import retrieve_company_protocols
                from app.ai.response_guard import generate_protocol_response

                chunks = retrieve_company_protocols(str(ticket.company_id), message_in.message)
                ai_text, source_type = generate_protocol_response(message_in.message, chunks)
                bot_msg = Message(
                    ticket_id=ticket.id,
                    sender_type="BOT",
                    sender_id="AI_ASSISTANT",
                    message=ai_text,
                    source=source_type
                )
                db.add(bot_msg)
                ticket.status = "WAITING_FOR_USER"
                db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error auto-replying to user message: {e}")

    return msg
