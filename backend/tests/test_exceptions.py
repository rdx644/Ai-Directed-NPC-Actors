"""
Tests for the custom exception hierarchy.

Validates:
    - Exception instantiation with correct fields
    - HTTP status code mapping
    - Serialization to API response format
    - Exception chaining and inheritance
"""

from __future__ import annotations

from backend.exceptions import (
    AIGenerationError,
    CloudLoggingError,
    CloudStorageError,
    ConfigurationError,
    EntityNotFoundError,
    ExternalServiceError,
    NPCSystemError,
    RateLimitError,
    SecretManagerError,
)


class TestNPCSystemError:
    """Base exception tests."""

    def test_basic_creation(self) -> None:
        """Base exception stores message and defaults."""
        err = NPCSystemError("Something went wrong")
        assert str(err) == "Something went wrong"
        assert err.message == "Something went wrong"
        assert err.error_code == "npc_system_error"
        assert err.status_code == 500
        assert err.details == {}

    def test_custom_fields(self) -> None:
        """Custom error_code, status_code, and details."""
        err = NPCSystemError(
            "Custom error",
            error_code="custom_err",
            status_code=418,
            details={"teapot": True},
        )
        assert err.error_code == "custom_err"
        assert err.status_code == 418
        assert err.details == {"teapot": True}

    def test_to_dict(self) -> None:
        """Serialization produces correct API response."""
        err = NPCSystemError(
            "Test error",
            error_code="test_err",
            details={"key": "value"},
        )
        result = err.to_dict()
        assert result["error"] == "test_err"
        assert result["message"] == "Test error"
        assert result["details"] == {"key": "value"}

    def test_to_dict_without_details(self) -> None:
        """Serialization omits empty details."""
        err = NPCSystemError("Simple error")
        result = err.to_dict()
        assert "details" not in result


class TestEntityNotFoundError:
    """Entity lookup failure tests."""

    def test_creation(self) -> None:
        err = EntityNotFoundError("Character", "char-001")
        assert err.status_code == 404
        assert err.error_code == "entity_not_found"
        assert "Character not found: char-001" in err.message
        assert err.details["entity_type"] == "Character"
        assert err.details["entity_id"] == "char-001"

    def test_inheritance(self) -> None:
        err = EntityNotFoundError("Attendee", "att-999")
        assert isinstance(err, NPCSystemError)
        assert isinstance(err, Exception)


class TestAIGenerationError:
    """AI generation failure tests."""

    def test_default_model(self) -> None:
        err = AIGenerationError("Rate limited")
        assert err.status_code == 503
        assert err.details["model"] == "gemini-2.0-flash"
        assert err.details["fallback_used"] is False

    def test_with_fallback(self) -> None:
        err = AIGenerationError("Timeout", fallback_used=True)
        assert err.details["fallback_used"] is True


class TestExternalServiceErrors:
    """External service error hierarchy tests."""

    def test_base_external_error(self) -> None:
        err = ExternalServiceError("TestService", "Connection refused")
        assert err.status_code == 502
        assert "TestService error" in err.message

    def test_secret_manager_error(self) -> None:
        err = SecretManagerError("Access denied")
        assert isinstance(err, ExternalServiceError)
        assert isinstance(err, NPCSystemError)
        assert "Secret Manager" in err.message

    def test_cloud_storage_error(self) -> None:
        err = CloudStorageError("Bucket not found")
        assert isinstance(err, ExternalServiceError)
        assert "Cloud Storage" in err.message

    def test_cloud_logging_error(self) -> None:
        err = CloudLoggingError("Write failed")
        assert isinstance(err, ExternalServiceError)
        assert "Cloud Logging" in err.message


class TestRateLimitError:
    """Rate limiting error tests."""

    def test_creation(self) -> None:
        err = RateLimitError(retry_after=30)
        assert err.status_code == 429
        assert err.details["retry_after_seconds"] == 30
        assert "Rate limit exceeded" in err.message


class TestConfigurationError:
    """Configuration error tests."""

    def test_creation(self) -> None:
        err = ConfigurationError("GEMINI_API_KEY", "Missing required key")
        assert err.status_code == 500
        assert err.details["field"] == "GEMINI_API_KEY"
        assert "GEMINI_API_KEY" in err.message
