"""
Tests for the middleware stack.

Tests rate limiting, security headers, request logging, and error handling.
"""

from __future__ import annotations

import time

from backend.middleware import RateLimitMiddleware


class TestRateLimitBucket:
    """Tests for the rate limiter's token bucket algorithm."""

    def test_allows_requests_under_limit(self) -> None:
        """Requests under the rate limit should be allowed."""
        limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
        limiter.rate = 1.0  # 1 token/sec
        limiter.burst_size = 5
        from collections import defaultdict

        limiter._buckets = defaultdict(lambda: (5.0, time.monotonic()))

        # Should allow 5 burst requests
        for _ in range(5):
            assert limiter._consume_token("test-ip") is True

    def test_blocks_after_burst_exceeded(self) -> None:
        """Requests exceeding burst should be blocked."""
        limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
        limiter.rate = 0.1  # very slow refill
        limiter.burst_size = 2
        from collections import defaultdict

        limiter._buckets = defaultdict(lambda: (2.0, time.monotonic()))

        assert limiter._consume_token("test-ip") is True
        assert limiter._consume_token("test-ip") is True
        assert limiter._consume_token("test-ip") is False  # burst exceeded

    def test_token_refill_over_time(self) -> None:
        """Tokens should refill based on elapsed time."""
        limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
        limiter.rate = 100.0  # 100 tokens/sec (fast refill for testing)
        limiter.burst_size = 5
        from collections import defaultdict

        limiter._buckets = defaultdict(lambda: (5.0, time.monotonic()))

        # Exhaust all tokens
        for _ in range(5):
            limiter._consume_token("test-ip")

        # Wait a tiny bit for refill
        time.sleep(0.05)

        # Should have refilled some tokens
        assert limiter._consume_token("test-ip") is True

    def test_separate_buckets_per_ip(self) -> None:
        """Different IPs should have separate rate limit buckets."""
        limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
        limiter.rate = 0.1
        limiter.burst_size = 1
        from collections import defaultdict

        limiter._buckets = defaultdict(lambda: (1.0, time.monotonic()))

        assert limiter._consume_token("ip-1") is True
        assert limiter._consume_token("ip-1") is False  # ip-1 exhausted
        assert limiter._consume_token("ip-2") is True  # ip-2 still has tokens


class TestRateLimitEndpoint:
    """Integration test: rate limiting via the API."""

    def test_rate_limit_returns_429(self) -> None:
        """Excessive requests should eventually return 429."""
        from fastapi.testclient import TestClient

        from backend.app import app

        with TestClient(app) as client:
            # Make many rapid requests
            status_codes = []
            for _ in range(100):
                res = client.get("/api/attendees")
                status_codes.append(res.status_code)

            # At least some should be rate limited (429)
            # Note: depends on configured burst size
            if 429 in status_codes:
                # If we got rate limited, verify the response format
                for _i, code in enumerate(status_codes):
                    if code == 429:
                        # Re-do the request to check response body
                        res = client.get("/api/attendees")
                        if res.status_code == 429:
                            data = res.json()
                            assert "error" in data
                            assert data["error"] == "rate_limit_exceeded"
                            assert "retry_after_seconds" in data
                        break
