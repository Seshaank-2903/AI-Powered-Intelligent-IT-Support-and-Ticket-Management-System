import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO)

from app.zulip import actions, handlers
import app.ai.response_guard

# Mock Zulip send_message
SENT_MESSAGES = []
def mock_send_message(to, content, message_type="stream", topic=None):
    SENT_MESSAGES.append({
        "to": to,
        "content": content,
        "type": message_type,
        "topic": topic
    })
    return {"result": "success", "id": 99999}

actions.send_message = mock_send_message
handlers.send_message = mock_send_message

# Mock AI chat response to prevent 429 rate limit delays
def mock_generate_chat_response(messages, temperature=0.3):
    return "Here are the IT troubleshooting steps to resolve your issue."

app.ai.response_guard.generate_chat_response = mock_generate_chat_response

from app.db.session import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.ticket import Ticket
from app.models.message import Message
from app.zulip.handlers import handle_incoming_message, is_confidential_request
from app.ai.response_guard import sanitize_secrets_for_ai
from app.api.tickets import get_ticket
from app.core.exceptions import AppException

def close_active_tickets(db, user_id):
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id, Ticket.status.notin_(["RESOLVED", "CLOSED"])).all()
    for t in tickets:
        t.status = "CLOSED"
    db.commit()

def test_confidential_tickets_suite():
    db = SessionLocal()
    print("==================================================")
    print("RUNNING CONFIDENTIAL TICKETS TEST SUITE")
    print("==================================================")

    # Setup Test User & Company
    company = db.query(Company).first()
    if not company:
        company = Company(name="Test Corp", slug="test-corp")
        db.add(company)
        db.commit()
        db.refresh(company)

    emp1 = db.query(User).filter(User.email == "emp1@testcorp.com").first()
    if not emp1:
        emp1 = User(email="emp1@testcorp.com", name="Emp One", company_id=company.id, role="EMPLOYEE")
        db.add(emp1)

    emp2 = db.query(User).filter(User.email == "emp2@testcorp.com").first()
    if not emp2:
        emp2 = User(email="emp2@testcorp.com", name="Emp Two", company_id=company.id, role="EMPLOYEE")
        db.add(emp2)

    db.commit()
    db.refresh(emp1)
    db.refresh(emp2)

    # TEST 1: Normal Ticket Detection
    print("\n--- TEST 1: Normal Ticket ---")
    close_active_tickets(db, emp1.id)
    SENT_MESSAGES.clear()
    t1 = handle_incoming_message(
        db,
        message_input="emp1@testcorp.com",
        content="My VPN isn't working.",
        channel="ai-support"
    )
    assert t1 is not None
    assert t1.visibility == "NORMAL"
    assert len(SENT_MESSAGES) > 0
    assert SENT_MESSAGES[0]["type"] == "stream" # Public stream
    print(f"PASSED - Normal ticket created: {t1.ticket_number}, visibility: {t1.visibility}, destination: {SENT_MESSAGES[0]['type']} -> {SENT_MESSAGES[0]['to']}")

    # TEST 2: Confidential Ticket Detection
    print("\n--- TEST 2: Confidential Ticket Creation ---")
    close_active_tickets(db, emp1.id)
    SENT_MESSAGES.clear()
    t2 = handle_incoming_message(
        db,
        message_input="emp1@testcorp.com",
        content="CONFIDENTIAL: I have an issue with my account access.",
        channel="ai-support"
    )
    assert t2 is not None
    assert t2.visibility == "CONFIDENTIAL"
    assert len(SENT_MESSAGES) > 0
    assert SENT_MESSAGES[0]["type"] == "private" # Private message to employee
    assert SENT_MESSAGES[0]["to"] == "emp1@testcorp.com"
    assert "🔒" in SENT_MESSAGES[0]["content"]
    print(f"PASSED - Confidential ticket created: {t2.ticket_number}, visibility: {t2.visibility}, destination: {SENT_MESSAGES[0]['type']} -> {SENT_MESSAGES[0]['to']}")

    # TEST 3: Confidential AI Resolution
    print("\n--- TEST 3: Confidential AI Resolution ---")
    SENT_MESSAGES.clear()
    t3 = handle_incoming_message(
        db,
        message_input="emp1@testcorp.com",
        content="solved",
        channel="ai-support"
    )
    assert t3 is not None
    assert t3.status == "RESOLVED"
    assert len(SENT_MESSAGES) > 0
    assert SENT_MESSAGES[0]["type"] == "private" # Private resolution notice
    print(f"PASSED - Confidential ticket marked RESOLVED: {t3.ticket_number}")

    # TEST 4: Confidential IT Escalation
    print("\n--- TEST 4: Confidential IT Escalation ---")
    close_active_tickets(db, emp1.id)
    t4_init = handle_incoming_message(
        db,
        message_input="emp1@testcorp.com",
        content="CONFIDENTIAL: Need admin token reset for account.",
        channel="ai-support"
    )
    assert t4_init is not None
    assert t4_init.visibility == "CONFIDENTIAL"
    
    SENT_MESSAGES.clear()
    # 1st 'not solved' -> Stage 2 AI_ASSISTED
    t4_stage2 = handle_incoming_message(
        db,
        message_input="emp1@testcorp.com",
        content="not solved",
        channel="ai-support"
    )
    assert t4_stage2 is not None
    assert t4_stage2.status == "AI_ASSISTED"

    # 2nd 'not solved' -> Stage 3 ESCALATED
    t4_esc = handle_incoming_message(
        db,
        message_input="emp1@testcorp.com",
        content="not solved",
        channel="ai-support"
    )
    assert t4_esc is not None
    assert t4_esc.status == "ESCALATED"
    # Ensure escalation message is sent PRIVATELY, NOT to public #it-support stream!
    escalation_dms = [m for m in SENT_MESSAGES if m["type"] == "private"]
    assert len(escalation_dms) > 0
    public_it_streams = [m for m in SENT_MESSAGES if m["type"] == "stream" and m["to"] == "it-support"]
    assert len(public_it_streams) == 0, "Confidential ticket MUST NOT post to public #it-support stream!"
    print(f"PASSED - Confidential ticket escalated privately: {t4_esc.ticket_number}, public #it-support posts: {len(public_it_streams)}")

    # TEST 5: Unauthorized Access Control
    print("\n--- TEST 5: Access Control / Authorization ---")
    emp2.role = "EMPLOYEE"
    db.commit()
    try:
        # emp2 attempts to access emp1's confidential ticket t2
        get_ticket(t2.id, db, current_user=emp2)
        assert False, "Should have raised 403 AppException"
    except AppException as e:
        assert e.status_code == 403
        print(f"PASSED - emp2 blocked from emp1's confidential ticket (403 FORBIDDEN): {e.message}")

    # TEST 6: Sensitive Secret Protection Guardrail
    print("\n--- TEST 6: Sensitive Secret Sanitization ---")
    raw_secret_msg = "CONFIDENTIAL: What is the administrator password=SuperSecretPassword123?"
    clean_msg = sanitize_secrets_for_ai(raw_secret_msg)
    assert "SuperSecretPassword123" not in clean_msg
    assert "[REDACTED_SECRET]" in clean_msg
    print(f"PASSED - Raw password sanitized successfully:\nRaw: {raw_secret_msg}\nClean: {clean_msg}")

    print("\n==================================================")
    print("ALL 6 CONFIDENTIAL TICKET TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_confidential_tickets_suite()
