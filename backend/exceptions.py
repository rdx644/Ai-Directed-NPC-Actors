"""
Custom exception hierarchy for the NPC Actor System.

Provides structured, type-safe error handling with automatic HTTP status
mapping. All exceptions carry machine-readable error codes for consistent
API responses and structured logging.

Hierarchy:
    NPCSystemError (base)
    ├── EntityNotFoundError     → HTTP 404
    ├── ValidationError         → HTTP 422
    ├── AIGenerationError       → HTTP 503
    ├── ExternalServiceError    → HTTP 502
    │   ├── SecretManagerError
    │   ├── CloudStorageError
    │   └── CloudLoggingError
    ├── RateLimitError          → HTTP 429
    └── ConfigurationError      → HTTP 500
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("npc-system.exceptions")


class NPCSystemError(Exception):
    """
    Base exception for all NPC Actor System errors.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error identifier for API consumers.
        status_code: HTTP status code to return in API responses.
        details: Optional dict with additional context for debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "npc_system_error",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the exception for API response payloads."""
        result: dict[str, Any] = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class EntityNotFoundError(NPCSystemError):
    """Raised when a requested entity (attendee, character, etc.) does not exist."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
    ) -> None:
        super().__init__(
            message=f"{entity_type} not found: {entity_id}",
            error_code="entity_not_found",
            status_code=404,
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class AIGenerationError(NPCSystemError):
    """Raised when AI dialogue generation via Google Gemini fails."""

    def __init__(
        self,
        reason: str,
        *,
        model: str = "gemini-2.0-flash",
        fallback_used: bool = False,
    ) -> None:
        super().__init__(
            message=f"AI generation failed: {reason}",
            error_code="ai_generation_error",
            status_code=503,
            details={"model": model, "fallback_used": fallback_used},
        )


class ExternalServiceError(NPCSystemError):
    """Base exception for external Google Cloud service failures."""

    def __init__(
        self,
        service_name: str,
        reason: str,
        *,
        status_code: int = 502,
    ) -> None:
        super().__init__(
            message=f"{service_name} error: {reason}",
            error_code="external_service_error",
            status_code=status_code,
            details={"service": service_name},
        )


class SecretManagerError(ExternalServiceError):
    """Raised when Google Cloud Secret Manager operations fail."""

    def __init__(self, reason: str) -> None:
        super().__init__("Google Cloud Secret Manager", reason)


class CloudStorageError(ExternalServiceError):
    """Raised when Google Cloud Storage operations fail."""

    def __init__(self, reason: str) -> None:
        super().__init__("Google Cloud Storage", reason)


class CloudLoggingError(ExternalServiceError):
    """Raised when Google Cloud Logging operations fail."""

    def __init__(self, reason: str) -> None:
        super().__init__("Google Cloud Logging", reason)


class RateLimitError(NPCSystemError):
    """Raised when a client exceeds the configured rate limit."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(
            message="Rate limit exceeded. Please wait before retrying.",
            error_code="rate_limit_exceeded",
            status_code=429,
            details={"retry_after_seconds": retry_after},
        )


class ConfigurationError(NPCSystemError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(
            message=f"Configuration error for '{field}': {reason}",
            error_code="configuration_error",
            status_code=500,
            details={"field": field},
        )
