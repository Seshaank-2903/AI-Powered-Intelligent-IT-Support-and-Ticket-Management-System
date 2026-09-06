import os
import logging
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

_mistral_client = None

def get_mistral_client() -> MistralClient | None:
    global _mistral_client
    if not _mistral_client and settings.MISTRAL_API_KEY:
        try:
            _mistral_client = MistralClient(api_key=settings.MISTRAL_API_KEY, max_retries=1, timeout=5)
            logger.info("Mistral client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral client: {e}")
    return _mistral_client

def get_embeddings(texts: list[str]) -> list[list[float]]:
    client = get_mistral_client()
    if not client:
        raise RuntimeError("Mistral client not configured.")
    
    response = client.embeddings(
        model=settings.MISTRAL_EMBEDDING_MODEL,
        input=texts
    )
    return [data.embedding for data in response.data]

def generate_chat_response(messages: list[dict], temperature: float = 0.3) -> str:
    client = get_mistral_client()
    if not client:
        raise RuntimeError("Mistral client not configured.")
    
    chat_messages = [
        ChatMessage(role=m["role"], content=m["content"]) for m in messages
    ]
    
    response = client.chat(
        model=settings.MISTRAL_CHAT_MODEL,
        messages=chat_messages,
        temperature=temperature
    )
    return response.choices[0].message.content
