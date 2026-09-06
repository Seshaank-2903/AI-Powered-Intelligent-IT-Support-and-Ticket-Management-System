import logging
from typing import Optional, List, Dict, Any
from app.zulip.client import get_zulip_client
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_message(to: str, content: str, message_type: str = "stream", topic: Optional[str] = None) -> Optional[dict]:
    """
    Sends a message to a Zulip stream or private user.
    """
    client = get_zulip_client()
    if not client:
        logger.warning(f"Zulip client not initialized. Cannot send message to {to}.")
        return None

    request: Dict[str, Any] = {
        "type": message_type,
        "to": [to] if message_type == "private" and isinstance(to, str) else to,
        "content": content,
    }

    if message_type == "stream":
        request["topic"] = topic or "General"

    try:
        response = client.send_message(request)
        if response.get("result") != "success":
            logger.error(f"Error sending Zulip message to {to}: {response}")
        else:
            logger.info(f"Successfully sent Zulip message to {to} (type: {message_type})")
        return response
    except Exception as e:
        logger.error(f"Exception sending Zulip message: {e}")
        return None

def escalate_to_it(
    ticket_number: str,
    employee_name: str,
    employee_email: str,
    issue_desc: str,
    company_protocol_attempted: str = "None / Protocol Search Executed",
    protocol_result: str = "Issue not resolved.",
    ai_troubleshooting_attempted: str = "Mistral AI Troubleshooting",
    ai_result: str = "Issue still unresolved.",
    status: str = "ESCALATED",
    priority: str = "MEDIUM"
) -> Optional[dict]:
    """
    Sends an escalation message to #it-support stream with exact requested format.
    """
    content = f"""🚨 **IT SUPPORT ESCALATION**

**Ticket:** `{ticket_number}`

**Employee:** {employee_name} ({employee_email})

**Issue:**
{issue_desc}

**Protocol Attempt:**
{company_protocol_attempted}

**Result:**
{protocol_result}

**AI Troubleshooting:**
{ai_troubleshooting_attempted}

**Result:**
{ai_result}

**Status:**
{status}

**Action Required:**
IT team investigation"""
    return send_message(
        to=settings.ZULIP_IT_SUPPORT_STREAM,
        content=content.strip(),
        message_type="stream",
        topic=f"Escalation: {ticket_number}"
    )

def escalate_to_it_private(
    to_email: str,
    ticket_number: str,
    employee_name: str,
    employee_email: str,
    issue_desc: str,
    company_protocol_attempted: str = "None / Protocol Search Executed",
    protocol_result: str = "Issue not resolved.",
    ai_troubleshooting_attempted: str = "Mistral AI Troubleshooting",
    ai_result: str = "Issue still unresolved.",
    status: str = "ESCALATED",
    priority: str = "MEDIUM"
) -> Optional[dict]:
    """
    Sends a PRIVATE escalation message to authorized IT support personnel.
    Never posts confidential details to public #it-support stream.
    """
    content = f"""🔒 **CONFIDENTIAL IT SUPPORT TICKET**

**Ticket:** `{ticket_number}`

**Employee:** {employee_name} ({employee_email})

**Issue:**
{issue_desc}

**Protocol Attempt:**
{company_protocol_attempted}

**Result:**
{protocol_result}

**AI Troubleshooting:**
{ai_troubleshooting_attempted}

**Result:**
{ai_result}

**Status:**
{status}

**Action Required:**
IT investigation"""
    return send_message(
        to=to_email,
        content=content.strip(),
        message_type="private"
    )

def notify_admin(event_type: str, ticket_number: str, details: str) -> Optional[dict]:
    """
    Sends important ticket event notifications to #it-admin stream.
    """
    content = f"📢 **IT Admin Event: {event_type}**\n**Ticket:** `{ticket_number}`\n**Details:** {details}"
    return send_message(
        to=settings.ZULIP_IT_ADMIN_STREAM,
        content=content,
        message_type="stream",
        topic=f"Admin Alert: {ticket_number}"
    )

def ask_if_resolved(to: str, message_type: str = "stream", topic: Optional[str] = None) -> Optional[dict]:
    """
    Prompts the employee if their issue was resolved.
    """
    content = "Was your issue resolved? Please reply with **Solved** or **Not Solved**."
    return send_message(to=to, content=content, message_type=message_type, topic=topic)

