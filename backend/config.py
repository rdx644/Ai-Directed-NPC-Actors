"""
Configuration management for the NPC Actor System.
Loads settings from environment variables with sensible defaults.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Google Services ---
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    # --- App Config ---
    app_env: str = os.getenv("APP_ENV", "development")
    app_port: int = int(os.getenv("APP_PORT", "8080"))
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")

    # --- Feature Modes ---
    database_mode: str = os.getenv("DATABASE_MODE", "memory")  # "memory" or "firestore"
    tts_mode: str = os.getenv("TTS_MODE", "browser")  # "browser" or "google"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def use_firestore(self) -> bool:
        return self.database_mode == "firestore"

    @property
    def use_google_tts(self) -> bool:
        return self.tts_mode == "google"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
