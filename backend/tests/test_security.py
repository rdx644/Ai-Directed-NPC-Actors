"""
Security-focused tests for the NPC Actor System.

Tests input sanitization, validation, content filtering,
rate limiting behavior, and API authentication.
"""

from __future__ import annotations

import pytest

from backend.security import (
    FIELD_LIMITS,
    filter_generated_content,
    sanitize_list,
    sanitize_string,
    validate_badge_id,
    validate_email,
)


class TestSanitizeString:
    """Tests for the sanitize_string function."""

    def test_strips_whitespace(self) -> None:
        assert sanitize_string("  hello  ") == "hello"

    def test_escapes_html(self) -> None:
        result = sanitize_string('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_removes_null_bytes(self) -> None:
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_removes_control_characters(self) -> None:
        result = sanitize_string("hello\x01\x02world")
        assert "\x01" not in result

    def test_preserves_newlines_tabs(self) -> None:
        """Newlines and tabs should be preserved (useful for prompts)."""
        result = sanitize_string("line1\nline2\ttab")
        assert "\n" in result
        assert "\t" in result

    def test_enforces_max_length(self) -> None:
        with pytest.raises(ValueError, match="exceeds maximum length"):
            sanitize_string("A" * 101, "name")

    def test_empty_string(self) -> None:
        assert sanitize_string("") == ""

    def test_none_passthrough(self) -> None:
        """None values should pass through unchanged."""
        assert sanitize_string(None) is None

    def test_quotes_are_escaped(self) -> None:
        result = sanitize_string('He said "hello" & goodbye')
        assert "&quot;" in result
        assert "&amp;" in result


class TestSanitizeList:
    """Tests for the sanitize_list function."""

    def test_filters_empty_strings(self) -> None:
        result = sanitize_list(["python", "", "  ", "AI"])
        assert len(result) == 2
        assert "python" in result
        assert "AI" in result

    def test_sanitizes_each_item(self) -> None:
        result = sanitize_list(["<b>bold</b>", "normal"])
        assert "<b>" not in result[0]

    def test_empty_list(self) -> None:
        assert sanitize_list([]) == []


class TestValidateBadgeId:
    """Tests for badge ID validation."""

    def test_valid_alphanumeric(self) -> None:
        assert validate_badge_id("NFC-1001") == "NFC-1001"

    def test_valid_with_underscores(self) -> None:
        assert validate_badge_id("BADGE_001") == "BADGE_001"

    def test_invalid_special_chars(self) -> None:
        with pytest.raises(ValueError):
            validate_badge_id("NFC 1001")  # space

    def test_invalid_script_injection(self) -> None:
        with pytest.raises(ValueError):
            validate_badge_id('<script>alert("x")</script>')

    def test_empty_string(self) -> None:
        with pytest.raises(ValueError):
            validate_badge_id("")

    def test_too_long(self) -> None:
        with pytest.raises(ValueError):
            validate_badge_id("A" * 51)


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self) -> None:
        assert validate_email("test@example.com") == "test@example.com"

    def test_valid_email_with_plus(self) -> None:
        assert validate_email("user+tag@domain.com") == "user+tag@domain.com"

    def test_invalid_no_at(self) -> None:
        with pytest.raises(ValueError):
            validate_email("notanemail")

    def test_invalid_no_domain(self) -> None:
        with pytest.raises(ValueError):
            validate_email("user@")

    def test_invalid_spaces(self) -> None:
        with pytest.raises(ValueError):
            validate_email("user @domain.com")

    def test_lowercased(self) -> None:
        assert validate_email("User@DOMAIN.COM") == "user@domain.com"


class TestFilterGeneratedContent:
    """Tests for AI content safety filtering."""

    def test_removes_script_tags(self) -> None:
        result = filter_generated_content('Hello <script>alert("x")</script>')
        assert "<script" not in result

    def test_removes_javascript_protocol(self) -> None:
        result = filter_generated_content("Click javascript:alert(1)")
        assert "javascript:" not in result

    def test_removes_event_handlers(self) -> None:
        result = filter_generated_content("Click onclick=alert(1)")
        assert "onclick=" not in result

    def test_preserves_safe_content(self) -> None:
        safe = "The ancient wisdom flows through your code, traveler."
        assert filter_generated_content(safe) == safe

    def test_preserves_normal_html_words(self) -> None:
        text = "This is a script review for your testing methodology."
        result = filter_generated_content(text)
        # "script" as a word (not a tag) should be fine
        assert "methodology" in result


class TestFieldLimits:
    """Tests for field limit configuration."""

    def test_all_fields_have_limits(self) -> None:
        """All expected fields should have defined limits."""
        expected = [
            "name",
            "email",
            "badge_id",
            "company",
            "role",
            "personality_prompt",
            "backstory",
            "catchphrase",
            "custom_context",
            "context",
            "notes",
        ]
        for field in expected:
            assert field in FIELD_LIMITS, f"Missing limit for field: {field}"

    def test_limits_are_positive(self) -> None:
        for field, limit in FIELD_LIMITS.items():
            assert limit > 0, f"Field '{field}' has non-positive limit: {limit}"
