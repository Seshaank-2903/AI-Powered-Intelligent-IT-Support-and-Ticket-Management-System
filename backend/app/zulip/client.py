import zulip
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

_zulip_client = None

def get_zulip_client() -> zulip.Client | None:
    """
    Returns an initialized Zulip Client singleton instance.
    Never exposes or logs credentials.
    """
    global _zulip_client
    if _zulip_client is None:
        if not settings.ZULIP_API_KEY or not settings.ZULIP_EMAIL or not settings.ZULIP_SITE:
            logger.warning("Zulip configuration is incomplete. Skipping Zulip client initialization.")
            return None
        try:
            _zulip_client = zulip.Client(
                email=settings.ZULIP_EMAIL,
                api_key=settings.ZULIP_API_KEY,
                site=settings.ZULIP_SITE
            )
            logger.info("Zulip client initialized successfully for site: %s", settings.ZULIP_SITE)
        except Exception as e:
            logger.error("Failed to initialize Zulip client: %s", str(e))
            return None
    return _zulip_client

def check_zulip_connection() -> bool:
    """
    Validates connection to Zulip API.
    """
    client = get_zulip_client()
    if not client:
        return False
    try:
        res = client.get_profile()
        return res.get("result") == "success"
    except Exception as e:
        logger.error("Zulip connection check failed: %s", str(e))
        return False

