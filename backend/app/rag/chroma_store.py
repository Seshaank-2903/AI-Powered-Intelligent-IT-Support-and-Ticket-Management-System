import os
import chromadb
from chromadb.config import Settings
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_chroma_client = None
CHROMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db"))

def get_chroma_client():
    global _chroma_client
    if not _chroma_client:
        try:
            os.makedirs(CHROMA_DIR, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
            logger.info(f"Using Chroma PersistentClient at '{CHROMA_DIR}'.")
        except Exception as e:
            logger.error(f"Error initializing Chroma PersistentClient: {e}")
            os.makedirs(CHROMA_DIR, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _chroma_client

def get_collection():
    client = get_chroma_client()
    if not client:
        raise RuntimeError("Chroma client not configured.")
    
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_PREFIX,
        metadata={"hnsw:space": "cosine"}
    )
