"""
AI Video Clipper — Application Configuration
=============================================
Membaca konfigurasi dari environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = ""
    
    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Paths
    UPLOAD_DIR: str = "../uploads"
    CLIPS_DIR: str = "../clips"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./videoclipper.db"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"
    
    # AI Models
    WHISPER_MODEL: str = "base"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Processing settings
    MAX_CLIPS: int = 5
    CLIP_MIN_DURATION: int = 30
    CLIP_MAX_DURATION: int = 90

    @field_validator("UPLOAD_DIR", "CLIPS_DIR", mode="before")
    @classmethod
    def resolve_paths(cls, v: str) -> str:
        """Resolve relative paths to absolute paths."""
        if not os.path.isabs(v):
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base, v.lstrip("../"))
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
