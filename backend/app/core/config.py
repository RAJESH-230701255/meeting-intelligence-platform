"""Meeting Intelligence Platform — Core Configuration."""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://postgres:YOUR_POSTGRES_PASSWORD_HERE@localhost:5432/meeting_intelligence_db"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # AI Provider
    AI_PROVIDER: str = "mock"  # mock | openai | anthropic
    AI_MODEL: str = "gpt-4"

    # AI API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Speech-to-Text Provider
    SPEECH_PROVIDER: str = "mock"  # mock | whisper
    WHISPER_API_KEY: str = ""

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
