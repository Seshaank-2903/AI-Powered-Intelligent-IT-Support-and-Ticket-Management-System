from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "company-ai-it-support"
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week

    # Database
    DATABASE_URL: str

    # Mistral
    MISTRAL_API_KEY: str
    MISTRAL_CHAT_MODEL: str = "mistral-small-latest"
    MISTRAL_EMBEDDING_MODEL: str = "mistral-embed"

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_PREFIX: str = "company_protocols"

    # Zulip
    ZULIP_SITE: str
    ZULIP_EMAIL: str
    ZULIP_API_KEY: str
    ZULIP_AI_SUPPORT_STREAM: str = "ai-support"
    ZULIP_IT_SUPPORT_STREAM: str = "it-support"
    ZULIP_IT_ADMIN_STREAM: str = "it-admin"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()
