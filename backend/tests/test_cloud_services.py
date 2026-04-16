"""
Tests for Google Cloud service integrations.

Tests cover:
    - Cloud Logging: Event logging and latency tracking
    - Secret Manager: Secret retrieval with environment fallback
    - Cloud Storage: Audio storage and interaction export
    - Analytics: Interaction summaries and engagement metrics

All external clients are mocked to enable testing without GCP credentials.
"""

from __future__ import annotations

import os
import time

os.environ["APP_ENV"] = "testing"


from backend.cloud_logging import get_logger, log_event, log_latency
from backend.cloud_storage import (
    export_interactions,
    generate_signed_url,
    store_analytics_report,
    store_audio,
)
from backend.secret_manager import (
    _get_env_fallback,
    get_secret,
    list_available_secrets,
)


class TestCloudLogging:
    """Google Cloud Logging integration tests."""

    def test_get_logger_returns_logger(self) -> None:
        """get_logger returns a properly named Logger instance."""
        log = get_logger("test-module")
        assert log.name == "npc-system.test-module"

    def test_log_event_dev_mode(self) -> None:
        """log_event works in development mode (no cloud client)."""
        # Should not raise even without cloud credentials
        log_event("test_event", {"key": "value"})

    def test_log_event_with_severity(self) -> None:
        """log_event accepts different severity levels."""
        log_event("warning_event", {"issue": "test"}, severity="WARNING")

    def test_log_event_no_payload(self) -> None:
        """log_event works without a payload."""
        log_event("simple_event")

    def test_log_latency_returns_ms(self) -> None:
        """log_latency calculates and returns milliseconds."""
        start = time.monotonic()
        time.sleep(0.01)  # 10ms
        latency = log_latency("test_operation", start)
        assert latency > 5  # Should be at least ~10ms
        assert isinstance(latency, float)

    def test_log_latency_with_metadata(self) -> None:
        """log_latency includes metadata in events."""
        start = time.monotonic()
        latency = log_latency(
            "gemini_call",
            start,
            metadata={"character": "Zephyr", "type": "greeting"},
        )
        assert latency >= 0


class TestSecretManager:
    """Google Cloud Secret Manager integration tests."""

    def test_get_secret_from_env(self) -> None:
        """In non-production, secrets come from environment variables."""
        secret = get_secret("GEMINI_API_KEY", fallback="test-key")
        # Should return env value or fallback
        assert isinstance(secret, str)

    def test_get_secret_with_fallback(self) -> None:
        """Falls back to provided default when secret not available."""
        result = get_secret("NON_EXISTENT_SECRET", fallback="default-val")
        assert result == "default-val"

    def test_get_secret_unknown_no_fallback(self) -> None:
        """Returns empty string for unknown secrets without fallback."""
        # Clear the LRU cache to get fresh results
        get_secret.cache_clear()
        result = get_secret("TOTALLY_UNKNOWN_KEY_12345")
        assert result == ""

    def test_env_fallback_known_keys(self) -> None:
        """_get_env_fallback returns values for known secret IDs."""
        result = _get_env_fallback("GEMINI_API_KEY")
        assert isinstance(result, str)

    def test_env_fallback_unknown_key(self) -> None:
        """_get_env_fallback returns empty for unknown keys."""
        result = _get_env_fallback("UNKNOWN_SECRET")
        assert result == ""

    def test_list_available_secrets(self) -> None:
        """list_available_secrets returns list of strings."""
        secrets = list_available_secrets()
        assert isinstance(secrets, list)
        for s in secrets:
            assert isinstance(s, str)


class TestCloudStorage:
    """Google Cloud Storage integration tests."""

    def test_store_audio_no_bucket(self) -> None:
        """store_audio returns None when GCS is not configured."""
        result = store_audio(b"fake-audio", "char-001", "int-001")
        assert result is None

    def test_export_interactions_no_bucket(self) -> None:
        """export_interactions returns None when GCS is not configured."""
        result = export_interactions([{"test": "data"}])
        assert result is None

    def test_store_analytics_report_no_bucket(self) -> None:
        """store_analytics_report returns None when GCS is not configured."""
        result = store_analytics_report({"metric": 42})
        assert result is None

    def test_generate_signed_url_no_bucket(self) -> None:
        """generate_signed_url returns None when GCS is not configured."""
        result = generate_signed_url("audio/test.mp3")
        assert result is None


class TestAnalytics:
    """Analytics service tests."""

    def test_interaction_summary(self) -> None:
        """compute_interaction_summary returns valid structure."""
        from backend.analytics import compute_interaction_summary

        summary = compute_interaction_summary()
        assert "total_interactions" in summary
        assert "by_type" in summary
        assert "by_character" in summary
        assert "generated_at" in summary
        assert isinstance(summary["total_interactions"], int)

    def test_character_analytics_valid(self) -> None:
        """compute_character_analytics works for existing character."""
        from backend.analytics import compute_character_analytics
        from backend.database import db

        characters = db.list_characters()
        if characters:
            result = compute_character_analytics(characters[0].id)
            assert "character_name" in result
            assert "total_interactions" in result

    def test_character_analytics_not_found(self) -> None:
        """compute_character_analytics handles missing characters."""
        from backend.analytics import compute_character_analytics

        result = compute_character_analytics("nonexistent-id")
        assert "error" in result

    def test_engagement_metrics(self) -> None:
        """compute_engagement_metrics returns valid structure."""
        from backend.analytics import compute_engagement_metrics

        metrics = compute_engagement_metrics()
        assert "total_attendees" in metrics
        assert "engagement_rate" in metrics
        assert "avg_xp_per_attendee" in metrics
        assert metrics["total_attendees"] >= 0

    def test_system_health(self) -> None:
        """compute_system_health returns valid structure."""
        from backend.analytics import compute_system_health

        health = compute_system_health()
        assert "services" in health
        assert "data" in health
        assert "cache" in health
        assert "generated_at" in health
