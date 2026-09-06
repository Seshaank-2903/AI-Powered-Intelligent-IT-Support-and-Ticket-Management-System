from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.zulip.handlers import handle_incoming_message
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook")
async def zulip_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives outgoing webhooks from Zulip.
    """
    try:
        payload = await request.json()
        if payload.get("message"):
            msg = payload["message"]
            logger.info("Received webhook event for message ID: %s", msg.get("id"))
            handle_incoming_message(db, msg)
        elif "sender_email" in payload and "content" in payload:
            handle_incoming_message(db, payload)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing Zulip webhook: {e}")
        return {"status": "error", "message": str(e)}

