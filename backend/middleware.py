"""
Middleware stack for the NPC Actor System.

Provides production-grade middleware layers:
  - SecurityHeadersMiddleware: OWASP-recommended HTTP security headers
  - RateLimitMiddleware: Token-bucket rate limiting per client IP
  - RequestLoggingMiddleware: Structured request/response logging
  - ErrorHandlerMiddleware: Global exception handling with safe error responses

All middleware is designed to be composable and independently testable.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from backend.config import settings

logger = logging.getLogger("npc-system.middleware")


# ──────────────────────────────────────────────
#  Security Headers Middleware
# ──────────────────────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects OWASP-recommended security headers into every HTTP response.

    Headers applied:
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - X-XSS-Protection: 1; mode=block
      - Strict-Transport-Security (HSTS) in production
      - Content-Security-Policy
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: restricts browser feature access
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Content Security Policy — allow inline scripts for the prototype UI
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )

        # HSTS in production only
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


# ──────────────────────────────────────────────
#  Rate Limiting Middleware (Token Bucket)
# ──────────────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiter per client IP address.

    Protects against abuse and ensures fair resource usage.
    Returns HTTP 429 Too Many Requests when limit exceeded.

    Args:
        app: The ASGI application.
        requests_per_minute: Maximum requests per minute per IP.
        burst_size: Maximum burst size (bucket capacity).
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_size: int = 20,
    ) -> None:
        super().__init__(app)
        self.rate: float = requests_per_minute / 60.0  # tokens per second
        self.burst_size: int = burst_size
        # IP → (tokens_remaining, last_refill_timestamp)
        self._buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(burst_size), time.monotonic())
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For for proxied requests."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"

    def _consume_token(self, ip: str) -> bool:
        """Try to consume a token from the bucket. Returns True if allowed."""
        tokens, last_time = self._buckets[ip]
        now = time.monotonic()
        elapsed = now - last_time

        # Refill tokens based on elapsed time
        tokens = min(self.burst_size, tokens + elapsed * self.rate)

        if tokens >= 1.0:
            self._buckets[ip] = (tokens - 1.0, now)
            return True

        self._buckets[ip] = (tokens, now)
        return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks and static files
        path = request.url.path
        if path in ("/api/health",) or path.startswith(("/css/", "/js/")):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if not self._consume_token(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please wait before retrying.",
                    "retry_after_seconds": int(1 / self.rate) + 1,
                },
                headers={"Retry-After": str(int(1 / self.rate) + 1)},
            )

        response = await call_next(request)
        return response


# ──────────────────────────────────────────────
#  Request Logging Middleware
# ──────────────────────────────────────────────


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured request/response logging with correlation IDs.

    Logs:
      - Request method, path, client IP
      - Response status code and processing time
      - Unique request ID for correlation
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip logging for static files
        path = request.url.path
        if path.startswith(("/css/", "/js/")):
            return await call_next(request)

        request_id = str(uuid.uuid4())[:8]
        client_ip = request.headers.get(
            "X-Forwarded-For", request.client.host if request.client else "unknown"
        )

        start_time = time.monotonic()

        # Attach request ID to request state for downstream use
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {path} → 500 "
                f"({duration_ms:.1f}ms) IP={client_ip} ERROR={exc}"
            )
            raise

        duration_ms = (time.monotonic() - start_time) * 1000
        log_fn = logger.info if response.status_code < 400 else logger.warning
        log_fn(
            f"[{request_id}] {request.method} {path} → {response.status_code} "
            f"({duration_ms:.1f}ms) IP={client_ip}"
        )

        # Add correlation headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        return response


# ──────────────────────────────────────────────
#  Global Error Handler Middleware
# ──────────────────────────────────────────────


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler that returns safe, structured error responses.

    Prevents leaking internal details (stack traces, file paths) to clients.
    Logs full error details server-side for debugging.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(
                f"[{request_id}] Unhandled exception on {request.method} "
                f"{request.url.path}: {exc}"
            )

            # Safe error response — never expose internals
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": "An unexpected error occurred. Please try again.",
                    "request_id": request_id,
                },
            )


# ──────────────────────────────────────────────
#  Middleware Registration
# ──────────────────────────────────────────────


def register_middleware(app: FastAPI) -> None:
    """
    Register all middleware layers in the correct order.

    Order matters — outermost middleware executes first:
    1. ErrorHandler (outermost) — catches all exceptions
    2. RequestLogging — logs every request with timing
    3. SecurityHeaders — adds security headers to responses
    4. RateLimiting — protects against abuse
    """
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_rpm,
        burst_size=settings.rate_limit_burst,
    )
