import logging
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.company import Company
from app.models.ticket import Ticket
from app.models.message import Message
from app.services.ticket_service import TicketService, ALLOWED_TRANSITIONS
from app.services.knowledge_gap_service import KnowledgeGapService
from app.zulip.actions import send_message, escalate_to_it, escalate_to_it_private, notify_admin
from app.core.config import settings
from app.rag.retrieval import retrieve_company_protocols
from app.ai.response_guard import generate_protocol_response, generate_mistral_troubleshooting

logger = logging.getLogger(__name__)

PROCESSED_ZULIP_MSG_IDS = set()

def is_confidential_request(content: str) -> bool:
    if not content:
        return False
    c = content.strip().lower()
    conf_keywords = [
        "confidential", "confidential:", "confidential ticket", 
        "[confidential]", "🔒 confidential", "private:", "secret:",
        "private", "privately", "sensitive", "security", "privacy",
        "another employee", "other employee", "account info", "account information",
        "salary", "payroll", "credentials leak", "data leak", "incident", "breach"
    ]
    return any(kw in c for kw in conf_keywords)

def handle_incoming_message(
    db: Session,
    message_input: Union[Dict[str, Any], str],
    content: Optional[str] = None,
    zulip_message_id: Optional[Union[int, str]] = None,
    channel: Optional[str] = None,
    topic: Optional[str] = None,
    sender_id: Optional[Union[int, str]] = None,
    sender_name: Optional[str] = None
) -> Optional[Ticket]:
    """
    Processes an incoming message from Zulip.
    Extracts message metadata, enforces bot & channel filtering, prevents duplicates,
    identifies employee & company, executes tenant-isolated RAG search,
    handles user feedback ("Solved"/"Not Solved"), escalates to #it-support, and notifies #it-admin.
    """
    # 1. Standardize input payload extraction
    if isinstance(message_input, dict):
        msg_dict = message_input
        zulip_msg_id = msg_dict.get("id")
        sender_id = msg_dict.get("sender_id")
        sender_email = msg_dict.get("sender_email", "")
        sender_name = msg_dict.get("sender_full_name") or sender_email
        msg_type = msg_dict.get("type", "stream")
        
        if msg_type == "stream":
            display_recip = msg_dict.get("display_recipient")
            if isinstance(display_recip, str):
                channel_name = display_recip
            elif isinstance(display_recip, list) and len(display_recip) > 0:
                first_rec = display_recip[0]
                if isinstance(first_rec, dict) and "stream_name" in first_rec:
                    channel_name = first_rec["stream_name"]
                elif isinstance(first_rec, str):
                    channel_name = first_rec
                else:
                    channel_name = msg_dict.get("stream_name") or settings.ZULIP_AI_SUPPORT_STREAM
            else:
                channel_name = msg_dict.get("stream_name") or settings.ZULIP_AI_SUPPORT_STREAM
        else:
            channel_name = "private"

        topic_name = msg_dict.get("subject") or msg_dict.get("topic") or "General"
        msg_content = msg_dict.get("content", "")
    else:
        sender_email = message_input
        msg_content = content or ""

        zulip_msg_id = zulip_message_id
        channel_name = channel or settings.ZULIP_AI_SUPPORT_STREAM
        topic_name = topic or "General"
        msg_type = "private" if channel_name == "private" else "stream"

    if not sender_email or not msg_content:
        logger.warning("Empty sender email or message content. Skipping message processing.")
        return None

    # 2. BOT & SELF-MESSAGE FILTERING (Prevents echo loops)
    if isinstance(message_input, dict):
        client_name = str(message_input.get("client", "")).lower()
        sender_type = str(message_input.get("sender_type", "")).lower()
        is_bot = message_input.get("is_bot", False)
        
        # Ignore actual bot user accounts
        if is_bot or sender_type in ["bot", "2"] or "bot@" in sender_email.lower() or "-bot@" in sender_email.lower():
            logger.info(f"Ignoring bot user event ({sender_email}).")
            return None

        # Ignore outgoing automated bot response signatures to prevent echo loops
        if "zulippython" in client_name and ("**Ticket TKT-" in msg_content or "🔒 **Confidential" in msg_content or "Was your issue resolved?" in msg_content or "marked as resolved" in msg_content):
            logger.info(f"Ignoring bot outgoing response event ({sender_email}).")
            return None
    elif sender_email and ("bot@" in sender_email.lower() or "-bot@" in sender_email.lower()):
        logger.info(f"Ignoring message from bot email ({sender_email}).")
        return None


    # 3. CHANNEL FILTERING (#ai-support for employees, #it-support for IT agents)
    if msg_type == "stream":
        ai_stream = settings.ZULIP_AI_SUPPORT_STREAM.lower()
        it_stream = settings.ZULIP_IT_SUPPORT_STREAM.lower()
        if channel_name.lower() not in [ai_stream, it_stream]:
            logger.info(f"Ignoring message from unrelated stream: '{channel_name}'.")
            return None

    # 4. DUPLICATE ZULIP MESSAGE ID PREVENTION
    if zulip_msg_id is not None:
        target_id_str = str(zulip_msg_id)
        if target_id_str in PROCESSED_ZULIP_MSG_IDS:
            logger.warning(f"Duplicate Zulip message ID detected ({target_id_str}). Skipping processing.")
            return None
        PROCESSED_ZULIP_MSG_IDS.add(target_id_str)

    # 5. EMPLOYEE & COMPANY IDENTIFICATION (Auto-provision if needed)
    user = db.query(User).filter(User.email == sender_email).first()
    if not user and sender_id:
        user = db.query(User).filter(User.zulip_user_id == str(sender_id)).first()

    if not user:
        logger.info(f"User with email '{sender_email}' not found. Provisioning new employee record.")
        company = db.query(Company).first()
        if not company:
            company = Company(name="Default Company", slug="default-company", description="Auto-created default company")
            db.add(company)
            db.commit()
            db.refresh(company)

        user = User(
            email=sender_email,
            name=sender_name or sender_email.split("@")[0],
            company_id=company.id,
            zulip_user_id=str(sender_id) if sender_id else None,
            role="EMPLOYEE"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Determine outgoing reply destination
    reply_to = channel_name if msg_type == "stream" else sender_email
    reply_type = msg_type
    reply_topic = topic_name if msg_type == "stream" else None

    # 6. IT TEAM STREAM WORKFLOW (#it-support)
    if msg_type == "stream" and channel_name.lower() == settings.ZULIP_IT_SUPPORT_STREAM.lower():
        # Look up ticket number from topic or content
        import re
        tkt_match = re.search(r'TKT-\d{4}-\d{5,6}', f"{topic_name} {msg_content}")
        if tkt_match:
            ticket_num = tkt_match.group(0)
            it_ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_num).first()
            if it_ticket:
                clean_it = msg_content.strip().lower()
                
                # Save IT Agent Message
                it_msg = Message(
                    ticket_id=it_ticket.id,
                    sender_type="IT_AGENT",
                    sender_id=str(user.id),
                    message=msg_content,
                    metadata_json={"zulip_message_id": zulip_msg_id, "channel": channel_name, "topic": topic_name}
                )
                db.add(it_msg)
                db.commit()

                if clean_it in ["resolved", "solved", "fixed", "done", "close"]:
                    TicketService.update_status(db, it_ticket, "RESOLVED", actor_type="IT_AGENT", actor_id=str(user.id))
                    # If confidential, notify employee privately. Else notify in #ai-support
                    if it_ticket.visibility == "CONFIDENTIAL":
                        send_message(
                            to=it_ticket.user.email,
                            content=f"Your confidential ticket `{it_ticket.ticket_number}` has been resolved by the IT Support Team.",
                            message_type="private"
                        )
                    else:
                        send_message(
                            to=settings.ZULIP_AI_SUPPORT_STREAM,
                            content=f"Your ticket `{it_ticket.ticket_number}` has been resolved by the IT Support Team.",
                            message_type="stream",
                            topic=it_ticket.title or "General"
                        )
                    send_message(to=reply_to, content=f"Ticket `{it_ticket.ticket_number}` marked as RESOLVED.", message_type=reply_type, topic=reply_topic)
                elif it_ticket.status == "ESCALATED":
                    TicketService.update_status(db, it_ticket, "IT_IN_PROGRESS", actor_type="IT_AGENT", actor_id=str(user.id))
                    dest_to = user.email if it_ticket.visibility == "CONFIDENTIAL" else reply_to
                    dest_type = "private" if it_ticket.visibility == "CONFIDENTIAL" else reply_type
                    dest_topic = None if it_ticket.visibility == "CONFIDENTIAL" else reply_topic
                    send_message(to=dest_to, content=f"Ticket `{it_ticket.ticket_number}` updated to **IT_IN_PROGRESS**.", message_type=dest_type, topic=dest_topic)
                return it_ticket
        return None

    # 7. ACTIVE TICKET MULTI-STAGE WORKFLOW (#ai-support)
    active_ticket = db.query(Ticket).filter(
        Ticket.user_id == user.id,
        Ticket.status.notin_(["RESOLVED", "CLOSED"])
    ).order_by(Ticket.created_at.desc()).first()

    clean_content = msg_content.strip().lower()

    if active_ticket:
        # Automatically update active ticket visibility to CONFIDENTIAL if confidential keyword detected
        if is_confidential_request(msg_content):
            active_ticket.visibility = "CONFIDENTIAL"
            db.commit()

        # Check confidentiality
        is_conf = active_ticket.visibility == "CONFIDENTIAL"
        dest_to = sender_email if is_conf else reply_to
        dest_type = "private" if is_conf else reply_type
        dest_topic = None if is_conf else reply_topic

        # Save employee follow-up message
        user_msg = Message(
            ticket_id=active_ticket.id,
            sender_type="USER",
            sender_id=str(user.id),
            message=msg_content,
            metadata_json={"zulip_message_id": zulip_msg_id, "channel": channel_name, "topic": topic_name}
        )
        db.add(user_msg)
        db.commit()

        if clean_content in ["solved", "yes", "fixed", "resolved"]:
            TicketService.update_status(db, active_ticket, "RESOLVED", actor_type="USER", actor_id=str(user.id))
            res_reply = f"Ticket `{active_ticket.ticket_number}` marked as resolved. Have a great day!"
            send_message(to=dest_to, content=res_reply, message_type=dest_type, topic=dest_topic)
            admin_msg = f"User {user.name} marked confidential ticket as resolved." if is_conf else f"User {user.name} ({user.email}) marked issue as resolved."
            notify_admin("TICKET_RESOLVED", active_ticket.ticket_number, admin_msg)
            return active_ticket

        elif clean_content in ["not solved", "no", "unresolved", "not fixed"]:
            # Check current stage of the SAME ticket
            if active_ticket.status in ["PROTOCOL_ATTEMPTED", "WAITING_FOR_USER", "NEW"]:
                # Stage 1 failed -> Move SAME ticket to Stage 2: Mistral AI Troubleshooting
                from app.ai.response_guard import generate_mistral_troubleshooting
                
                prev_messages = db.query(Message).filter(Message.ticket_id == active_ticket.id, Message.sender_type == "BOT").all()
                prev_text = "\n".join([m.message for m in prev_messages]) if prev_messages else ""

                ai_response, source_type = generate_mistral_troubleshooting(
                    query=active_ticket.description or active_ticket.title,
                    previous_attempts=prev_text
                )

                bot_msg = Message(
                    ticket_id=active_ticket.id,
                    sender_type="BOT",
                    sender_id="AI_ASSISTANT",
                    message=ai_response,
                    source="MISTRAL"
                )
                db.add(bot_msg)
                TicketService.update_status(db, active_ticket, "AI_ASSISTED", actor_type="SYSTEM")

                reply_msg = f"Here are additional troubleshooting steps for ticket `{active_ticket.ticket_number}`:\n\n{ai_response}\n\nWas your issue resolved? Please reply with **Solved** or **Not Solved**."
                send_message(to=dest_to, content=reply_msg, message_type=dest_type, topic=dest_topic)
                return active_ticket

            else:
                # Stage 2 failed -> Escalate the SAME ticket
                KnowledgeGapService.record_gap(db, active_ticket)
                TicketService.update_status(db, active_ticket, "ESCALATED", actor_type="USER", actor_id=str(user.id))

                ticket_messages = db.query(Message).filter(Message.ticket_id == active_ticket.id).order_by(Message.created_at).all()
                
                protocol_sources = [m.message for m in ticket_messages if m.source == "PROTOCOL"]
                protocol_attempted = protocol_sources[0] if protocol_sources else "Company protocol search executed."

                ai_sources = [m.message for m in ticket_messages if m.source == "MISTRAL"]
                ai_attempted = ai_sources[0] if ai_sources else "Mistral AI general troubleshooting."

                if is_conf:
                    # Private Escalation for Confidential Ticket
                    escalate_to_it_private(
                        to_email=settings.ZULIP_EMAIL,
                        ticket_number=active_ticket.ticket_number,
                        employee_name=user.name,
                        employee_email=user.email,
                        issue_desc=active_ticket.description or active_ticket.title,
                        company_protocol_attempted=protocol_attempted,
                        protocol_result="Issue not resolved.",
                        ai_troubleshooting_attempted=ai_attempted,
                        ai_result="Issue still unresolved.",
                        status="ESCALATED",
                        priority=active_ticket.priority or "MEDIUM"
                    )
                    emp_notice = f"The issue could not be resolved automatically.\n\nConfidential Ticket `{active_ticket.ticket_number}` has been raised privately to the IT Support Team.\n\nThe IT team will continue troubleshooting your issue."
                    send_message(to=dest_to, content=emp_notice, message_type="private")
                    notify_admin("CONFIDENTIAL_TICKET_ESCALATED", active_ticket.ticket_number, f"Confidential ticket escalated for user {user.email}.")
                else:
                    # Send Escalation Card to #it-support stream
                    escalate_to_it(
                        ticket_number=active_ticket.ticket_number,
                        employee_name=user.name,
                        employee_email=user.email,
                        issue_desc=active_ticket.description or active_ticket.title,
                        company_protocol_attempted=protocol_attempted,
                        protocol_result="Issue not resolved.",
                        ai_troubleshooting_attempted=ai_attempted,
                        ai_result="Issue still unresolved.",
                        status="ESCALATED",
                        priority=active_ticket.priority or "MEDIUM"
                    )
                    emp_notice = f"The issue could not be resolved automatically.\n\nTicket `{active_ticket.ticket_number}` has been raised to the IT Support Team.\n\nThe IT team will continue troubleshooting your issue."
                    send_message(to=reply_to, content=emp_notice, message_type=reply_type, topic=reply_topic)
                    notify_admin("TICKET_ESCALATED", active_ticket.ticket_number, f"Escalated to IT Support for {user.name} ({user.email}).")
                return active_ticket
        else:
            # Employee sent a question or problem description -> Search Protocols & AI
            chunks = retrieve_company_protocols(str(user.company_id), msg_content)
            ai_response, source_type = generate_protocol_response(msg_content, chunks)

            bot_msg = Message(
                ticket_id=active_ticket.id,
                sender_type="BOT",
                sender_id="AI_ASSISTANT",
                message=ai_response,
                source=source_type
            )
            db.add(bot_msg)
            db.commit()

            target_status = "PROTOCOL_ATTEMPTED" if source_type == "PROTOCOL" else "AI_ASSISTED"
            if target_status in ALLOWED_TRANSITIONS.get(active_ticket.status, []):
                TicketService.update_status(db, active_ticket, target_status, actor_type="SYSTEM")

            reply_msg = f"**Ticket {active_ticket.ticket_number}:**\n\n{ai_response}\n\nWas your issue resolved? Please reply with **Solved** or **Not Solved**."
            send_message(to=dest_to, content=reply_msg, message_type=dest_type, topic=dest_topic)
            if is_conf and msg_type == "stream":
                stream_notice = f"🔒 **Confidential Ticket `{active_ticket.ticket_number}` updated.** A private Direct Message has been sent to you with the response."
                send_message(to=reply_to, content=stream_notice, message_type=reply_type, topic=reply_topic)
            return active_ticket

    # 8. NEW TICKET CREATION & PROTOCOL-FIRST WORKFLOW
    from app.schemas.ticket import TicketCreate
    is_confidential = is_confidential_request(msg_content) or msg_type == "private"
    visibility_val = "CONFIDENTIAL" if is_confidential else "NORMAL"

    ticket_in = TicketCreate(
        title=f"IT Request: {msg_content[:40]}",
        description=msg_content,
        user_id=user.id,
        company_id=user.company_id,
        visibility=visibility_val
    )
    new_ticket = TicketService.create_ticket(db, ticket_in)
    
    # Save initial user message
    user_msg = Message(
        ticket_id=new_ticket.id,
        sender_type="USER",
        sender_id=str(user.id),
        message=msg_content,
        metadata_json={"zulip_message_id": zulip_msg_id, "channel": channel_name, "topic": topic_name}
    )
    db.add(user_msg)
    db.commit()

    # Search Company Protocols (RAG)
    chunks = retrieve_company_protocols(str(user.company_id), msg_content)
    ai_response, source_type = generate_protocol_response(msg_content, chunks)
    
    if source_type == "PROTOCOL":
        # Protocol Found -> Stage 1
        TicketService.update_status(db, new_ticket, "PROTOCOL_ATTEMPTED", actor_type="SYSTEM")
    else:
        # Protocol NOT Found -> Move directly to Stage 2: Mistral AI
        TicketService.update_status(db, new_ticket, "AI_ASSISTED", actor_type="SYSTEM")

    bot_msg = Message(
        ticket_id=new_ticket.id,
        sender_type="BOT",
        sender_id="AI_ASSISTANT",
        message=ai_response,
        source=source_type
    )
    db.add(bot_msg)
    db.commit()

    if is_confidential:
        dest_to = sender_email
        dest_type = "private"
        dest_topic = None
        prefix = f"🔒 **Confidential ticket created.**\n\nTicket: `{new_ticket.ticket_number}`\n\nThis ticket is confidential. Further communication about this issue will be sent privately.\n\n"
        full_message = f"{prefix}{ai_response}\n\nWas your issue resolved? Please reply with **Solved** or **Not Solved**."
        
        # Send private DM to employee
        send_message(to=dest_to, content=full_message, message_type=dest_type, topic=dest_topic)
        
        # If created from a stream, post a safe notice in stream acknowledging private DM
        if msg_type == "stream":
            stream_notice = f"🔒 **Confidential request detected.** Ticket `{new_ticket.ticket_number}` created. A private Direct Message has been sent to you to continue troubleshooting."
            send_message(to=reply_to, content=stream_notice, message_type=reply_type, topic=reply_topic)
    else:
        dest_to = reply_to
        dest_type = reply_type
        dest_topic = reply_topic
        full_message = f"**Ticket {new_ticket.ticket_number} created.**\n\n{ai_response}\n\nWas your issue resolved? Please reply with **Solved** or **Not Solved**."
        send_message(to=dest_to, content=full_message, message_type=dest_type, topic=dest_topic)
    
    return new_ticket
