"""
Security module for the NPC Actor System.

Provides:
  - Input sanitization and validation
  - API key authentication dependency
  - Field-level length constraints
  - Content filtering for generated dialogue
"""

from __future__ import annotations

import html
import logging
import re
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from backend.config import settings

logger = logging.getLogger("npc-system.security")

# ──────────────────────────────────────────────
#  Input Sanitization
# ──────────────────────────────────────────────

# Maximum allowed lengths for user-provided fields
FIELD_LIMITS: dict[str, int] = {
    "name": 100,
    "email": 254,
    "badge_id": 50,
    "company": 100,
    "role": 100,
    "personality_prompt": 2000,
    "backstory": 1000,
    "catchphrase": 200,
    "custom_context": 500,
    "context": 500,
    "notes": 500,
}

# Pattern for validating badge IDs (alphanumeric + hyphens)
BADGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{1,50}$")


def sanitize_string(value: str, field_name: str = "input") -> str:
    """
    Sanitize a string input by:
      1. Stripping leading/trailing whitespace
      2. Escaping HTML entities to prevent XSS
      3. Enforcing maximum length constraints
      4. Removing null bytes and control characters

    Args:
        value: The raw input string.
        field_name: Name of the field (for length limit lookup).

    Returns:
        The sanitized string.

    Raises:
        ValueError: If the input exceeds the maximum allowed length.
    """
    if not value:
        return value

    # Remove null bytes and control characters (except newline, tab)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)

    # Strip whitespace
    cleaned = cleaned.strip()

    # Enforce length limit
    max_length = FIELD_LIMITS.get(field_name, 1000)
    if len(cleaned) > max_length:
        raise ValueError(f"Field '{field_name}' exceeds maximum length of {max_length} characters")

    # Escape HTML entities to prevent stored XSS
    cleaned = html.escape(cleaned, quote=True)

    return cleaned


def sanitize_list(values: list[str], field_name: str = "list_item") -> list[str]:
    """Sanitize a list of strings, filtering empty values."""
    return [sanitize_string(v, field_name) for v in values if v and v.strip()]


def validate_badge_id(badge_id: str) -> str:
    """
    Validate a badge ID format.

    Args:
        badge_id: The badge ID to validate.

    Returns:
        The validated badge ID.

    Raises:
        ValueError: If the badge ID format is invalid.
    """
    if not BADGE_ID_PATTERN.match(badge_id):
        raise ValueError(
            "Badge ID must contain only alphanumeric characters, hyphens, and underscores"
        )
    return badge_id


def validate_email(email: str) -> str:
    """
    Basic email format validation.

    Args:
        email: The email address to validate.

    Returns:
        The validated email.

    Raises:
        ValueError: If the email format is invalid.
    """
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
    if not email_pattern.match(email):
        raise ValueError("Invalid email address format")
    if len(email) > FIELD_LIMITS["email"]:
        raise ValueError(f"Email exceeds maximum length of {FIELD_LIMITS['email']}")
    return email.lower().strip()


# ──────────────────────────────────────────────
#  API Key Authentication
# ──────────────────────────────────────────────

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> str | None:
    """
    Verify the API key for protected admin endpoints.

    In development mode, authentication is optional.
    In production, a valid API key is required.

    Args:
        api_key: The API key from the X-API-Key header.

    Returns:
        The validated API key, or None in development mode.

    Raises:
        HTTPException: 401 if the key is missing or invalid in production.
    """
    # Skip auth in development mode for easy prototyping
    if not settings.is_production:
        return api_key

    if not settings.admin_api_key:
        logger.warning("ADMIN_API_KEY not configured — admin endpoints are unprotected")
        return api_key

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not secrets.compare_digest(api_key, settings.admin_api_key):
        logger.warning("Invalid API key attempted")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )

    return api_key


# ──────────────────────────────────────────────
#  Content Safety Filter
# ──────────────────────────────────────────────

_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"<script\b", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
]


def filter_generated_content(text: str) -> str:
    """
    Filter AI-generated content to remove potentially unsafe patterns.

    Applies an additional safety layer on top of Gemini's built-in filters.

    Args:
        text: The generated text to filter.

    Returns:
        The filtered, safe text.
    """
    filtered = text
    for pattern in _BLOCKED_PATTERNS:
        filtered = pattern.sub("[filtered]", filtered)
    return filtered
