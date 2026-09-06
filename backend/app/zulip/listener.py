import time
import signal
import sys
import logging
import app.models
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.zulip.client import get_zulip_client, check_zulip_connection
from app.zulip.handlers import handle_incoming_message

# Ensure DB tables exist
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass


logger = logging.getLogger(__name__)

running = True

def signal_handler(sig, frame):
    global running
    logger.info(f"Received signal {sig}. Gracefully shutting down Zulip listener...")
    running = False
    sys.exit(0)

def process_zulip_event(event: dict):
    """
    Event callback executed for every incoming Zulip event.
    """
    if event.get("type") == "message" and "message" in event:
        msg = event["message"]
        db = SessionLocal()
        try:
            handle_incoming_message(db, msg)
        except Exception as e:
            logger.error(f"Error handling Zulip message event: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

def start_listener():
    """
    Main loop running Zulip client event listener with automatic reconnection logic.
    """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Zulip Generic Bot Real-time Event Listener...")

    retry_delay = 2
    max_delay = 60

    while running:
        client = get_zulip_client()
        if not client:
            logger.error("Zulip client is not configured properly. Retrying in 10s...")
            time.sleep(10)
            continue

        try:
            logger.info("Connecting to Zulip event stream...")
            # call_on_each_event blocks while listening to event stream
            client.call_on_each_event(
                process_zulip_event,
                event_types=["message"]
            )
            # Reset delay on clean loop exit
            retry_delay = 2
        except Exception as e:
            logger.error(f"Zulip listener stream interrupted: {e}")
            logger.info(f"Reconnecting in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    start_listener()
