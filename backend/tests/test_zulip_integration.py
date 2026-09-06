import pytest
from unittest.mock import MagicMock, patch
from app.core.config import settings
from app.zulip.client import check_zulip_connection, get_zulip_client
from app.zulip.actions import send_message, escalate_to_it, notify_admin
from app.zulip.handlers import handle_incoming_message
from app.models.ticket import Ticket
from app.models.message import Message
from app.models.user import User
from app.models.company import Company

# 1. Zulip Authentication Test
def test_zulip_authentication(monkeypatch):
    mock_client = MagicMock()
    mock_client.get_profile.return_value = {"result": "success", "email": settings.ZULIP_EMAIL}
    
    with patch("app.zulip.client.get_zulip_client", return_value=mock_client):
        assert check_zulip_connection() is True

# 2. Sending a Zulip Message Test
def test_send_zulip_message(monkeypatch):
    mock_client = MagicMock()
    mock_client.send_message.return_value = {"result": "success", "id": 1234}
    
    with patch("app.zulip.actions.get_zulip_client", return_value=mock_client):
        res = send_message(to="ai-support", content="Test message", message_type="stream", topic="General")
        assert res is not None
        assert res.get("result") == "success"
        mock_client.send_message.assert_called_once()

# 3. Receiving a Zulip Message Test
def test_receive_zulip_message(db, setup_test_data, monkeypatch):
    company, user = setup_test_data
    
    # Mock RAG and AI responses
    monkeypatch.setattr("app.zulip.handlers.retrieve_company_protocols", lambda cid, query: [])
    monkeypatch.setattr("app.zulip.handlers.generate_protocol_response", lambda query, chunks: ("Try restarting your router.", "MISTRAL"))
    monkeypatch.setattr("app.zulip.handlers.send_message", lambda **kwargs: {"result": "success"})
    monkeypatch.setattr("app.zulip.handlers.notify_admin", lambda *args, **kwargs: {"result": "success"})

    payload = {
        "id": 101,
        "sender_id": 42,
        "sender_email": user.email,
        "sender_full_name": user.name,
        "type": "stream",
        "display_recipient": "ai-support",
        "subject": "Internet Drop",
        "content": "My internet keeps dropping."
    }

    ticket = handle_incoming_message(db, payload)
    assert ticket is not None
    assert ticket.user_id == user.id
    assert ticket.company_id == company.id
    assert ticket.ticket_number.startswith("TKT-")

# 4. Ignoring Bot Messages Test
def test_ignore_bot_messages(db, setup_test_data, monkeypatch):
    bot_payload = {
        "id": 102,
        "sender_id": 99,
        "sender_email": "bot@companyaitickets.zulipchat.com",
        "sender_full_name": "AI Support Bot",
        "sender_type": "bot",
        "type": "stream",
        "display_recipient": "ai-support",
        "subject": "Auto-Reply",
        "content": "I am an automated response."
    }

    ticket = handle_incoming_message(db, bot_payload)
    assert ticket is None

# 5. Ignoring Unrelated Channels Test
def test_ignore_unrelated_channels(db, setup_test_data, monkeypatch):
    company, user = setup_test_data

    unrelated_payload = {
        "id": 103,
        "sender_id": 42,
        "sender_email": user.email,
        "sender_full_name": user.name,
        "type": "stream",
        "display_recipient": "random-chat",
        "subject": "Lunch Plans",
        "content": "Anyone want pizza?"
    }

    ticket = handle_incoming_message(db, unrelated_payload)
    assert ticket is None

# 6. Duplicate Message Prevention Test
def test_duplicate_message_prevention(db, setup_test_data, monkeypatch):
    company, user = setup_test_data

    monkeypatch.setattr("app.zulip.handlers.retrieve_company_protocols", lambda cid, query: [])
    monkeypatch.setattr("app.zulip.handlers.generate_protocol_response", lambda query, chunks: ("Step 1", "PROTOCOL"))
    monkeypatch.setattr("app.zulip.handlers.send_message", lambda **kwargs: {"result": "success"})
    monkeypatch.setattr("app.zulip.handlers.notify_admin", lambda *args, **kwargs: {"result": "success"})

    payload = {
        "id": 5555,
        "sender_id": 42,
        "sender_email": user.email,
        "sender_full_name": user.name,
        "type": "stream",
        "display_recipient": "ai-support",
        "subject": "Printer issue",
        "content": "Printer is jammed."
    }

    # First attempt should succeed and create a ticket
    ticket1 = handle_incoming_message(db, payload)
    assert ticket1 is not None

    # Second attempt with same zulip_message_id (5555) should be ignored
    ticket2 = handle_incoming_message(db, payload)
    assert ticket2 is None

# 7. Ticket Creation from Zulip Test
def test_ticket_creation_from_zulip(db, setup_test_data, monkeypatch):
    company, user = setup_test_data

    monkeypatch.setattr("app.zulip.handlers.retrieve_company_protocols", lambda cid, query: [])
    monkeypatch.setattr("app.zulip.handlers.generate_protocol_response", lambda query, chunks: ("Protocol steps...", "PROTOCOL"))
    monkeypatch.setattr("app.zulip.handlers.send_message", lambda **kwargs: {"result": "success"})
    monkeypatch.setattr("app.zulip.handlers.notify_admin", lambda *args, **kwargs: {"result": "success"})

    payload = {
        "id": 201,
        "sender_id": 42,
        "sender_email": user.email,
        "sender_full_name": user.name,
        "type": "stream",
        "display_recipient": "ai-support",
        "subject": "VPN Error",
        "content": "Cannot connect to VPN."
    }

    ticket = handle_incoming_message(db, payload)
    assert ticket is not None
    assert ticket.ticket_number.startswith("TKT-")
    assert ticket.status in ["PROTOCOL_ATTEMPTED", "AI_ASSISTED"]
    assert ticket.company_id == company.id

# 8. Multi-Stage Escalation to #it-support Test
def test_escalation_to_it_support(db, setup_test_data, monkeypatch):
    company, user = setup_test_data

    escalated_calls = []
    def mock_escalate(*args, **kwargs):
        escalated_calls.append(kwargs)
        return {"result": "success"}

    monkeypatch.setattr("app.zulip.handlers.retrieve_company_protocols", lambda cid, query: [])
    monkeypatch.setattr("app.zulip.handlers.generate_protocol_response", lambda query, chunks: ("Try resetting password", "PROTOCOL"))
    monkeypatch.setattr("app.zulip.handlers.generate_mistral_troubleshooting", lambda query, prev: ("Try advanced restart", "MISTRAL"))
    monkeypatch.setattr("app.zulip.handlers.send_message", lambda **kwargs: {"result": "success"})
    monkeypatch.setattr("app.zulip.handlers.escalate_to_it", mock_escalate)
    monkeypatch.setattr("app.zulip.handlers.notify_admin", lambda *args, **kwargs: {"result": "success"})

    # Step A: Initial ticket creation message (Stage 1: Protocol Attempt)
    payload_initial = {
        "id": 301,
        "sender_id": 42,
        "sender_email": user.email,
        "sender_full_name": user.name,
        "type": "stream",
        "display_recipient": "ai-support",
        "subject": "Locked Out",
        "content": "Account locked out."
    }

    ticket = handle_incoming_message(db, payload_initial)
    assert ticket is not None
    assert ticket.status == "PROTOCOL_ATTEMPTED"

    # Step B: User responds "Not Solved" -> Moves to Stage 2: Mistral AI
    payload_reply1 = {
        "id": 302,
        "sender_id": 42,
        "sender_email": user.email,
        "sender_full_name": user.name,
        "type": "stream",
        "display_recipient": "ai-support",
        "subject": "Locked Out",
        "content": "Not Solved"
    }

    stage2_ticket = handle_incoming_message(db, payload_reply1)
    assert stage2_ticket is not None
    assert stage2_ticket.status == "AI_ASSISTED"
    assert stage2_ticket.ticket_number == ticket.ticket_number

    # Step C: User responds "Not Solved" again -> Moves to Stage 3: Escalated to IT
    payload_reply2 = {
        "id": 303,
        "sender_id": 42,
        "sender_email": user.email,
        "sender_full_name": user.name,
        "type": "stream",
        "display_recipient": "ai-support",
        "subject": "Locked Out",
        "content": "Not Solved"
    }

    escalated_ticket = handle_incoming_message(db, payload_reply2)
    assert escalated_ticket is not None
    assert escalated_ticket.status == "ESCALATED"
    assert len(escalated_calls) == 1
    assert escalated_calls[0]["ticket_number"] == ticket.ticket_number
