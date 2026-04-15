"""
Configuration management for the NPC Actor System.

Loads settings from environment variables with sensible defaults.
Validates required fields and provides computed properties for feature flags.

Environment Variables:
    GEMINI_API_KEY: Google Gemini API key (required for AI dialogue)
    GOOGLE_CLOUD_PROJECT: GCP project ID (for TTS & Firestore)
    APP_ENV: Application environment (development/production)
    APP_PORT: Server port (default: 8080)
    APP_HOST: Server bind address (default: 0.0.0.0)
    DATABASE_MODE: Storage backend (memory/firestore)
    TTS_MODE: Text-to-speech backend (browser/google)
    ADMIN_API_KEY: API key for admin endpoint authentication
    RATE_LIMIT_RPM: Rate limit requests per minute (default: 60)
    RATE_LIMIT_BURST: Rate limit burst size (default: 20)
    ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins
    LOG_LEVEL: Logging level (default: INFO)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

load_dotenv()

logger = logging.getLogger("npc-system.config")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses pydantic-settings for automatic validation and type coercion.
    """

    # --- Google Services ---
    gemini_api_key: str = ""
    google_cloud_project: str = ""

    # --- App Config ---
    app_env: str = "development"
    app_port: int = 8080
    app_host: str = "0.0.0.0"
    log_level: str = "INFO"

    # --- Feature Modes ---
    database_mode: str = "memory"
    tts_mode: str = "browser"

    # --- Security ---
    admin_api_key: str = ""
    allowed_origins: str = ""
    rate_limit_rpm: int = 60
    rate_limit_burst: int = 20

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Ensure app_env is a recognized value."""
        allowed = {"development", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got '{v}'")
        return v

    @field_validator("database_mode")
    @classmethod
    def validate_db_mode(cls, v: str) -> str:
        """Ensure database_mode is a recognized value."""
        allowed = {"memory", "firestore"}
        if v not in allowed:
            raise ValueError(f"database_mode must be one of {allowed}, got '{v}'")
        return v

    @field_validator("tts_mode")
    @classmethod
    def validate_tts_mode(cls, v: str) -> str:
        """Ensure tts_mode is a recognized value."""
        allowed = {"browser", "google"}
        if v not in allowed:
            raise ValueError(f"tts_mode must be one of {allowed}, got '{v}'")
        return v

    @field_validator("rate_limit_rpm")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        """Ensure rate limit is within a sensible range."""
        if v < 1 or v > 10000:
            raise ValueError("rate_limit_rpm must be between 1 and 10000")
        return v

    @property
    def is_production(self) -> bool:
        """Check if the application is running in production mode."""
        return self.app_env == "production"

    @property
    def use_firestore(self) -> bool:
        """Check if Firestore should be used as the database backend."""
        return self.database_mode == "firestore"

    @property
    def use_google_tts(self) -> bool:
        """Check if Google Cloud TTS should be used for speech synthesis."""
        return self.tts_mode == "google"

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated allowed origins for CORS configuration."""
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        # In development, allow common local origins
        if not self.is_production:
            return ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:3000"]
        return []

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def _create_settings() -> Settings:
    """Factory function with error handling for settings creation."""
    try:
        return Settings()
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        # Return defaults that allow the app to at least start
        return Settings(app_env="development")


settings = _create_settings()
