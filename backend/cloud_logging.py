"""
Google Cloud Logging integration for the NPC Actor System.

Provides structured, JSON-formatted logging that integrates with
Google Cloud Logging (formerly Stackdriver) for production environments.
Falls back gracefully to standard Python logging in development.

Features:
    - Structured JSON log entries with severity levels
    - Automatic trace/span correlation for Cloud Run
    - Custom labels for service identification
    - Performance metrics logging (latency, cache hits)
    - Graceful fallback when Cloud Logging is unavailable

Usage:
    from backend.cloud_logging import get_logger, log_event

    logger = get_logger("my-module")
    logger.info("Operation completed", extra={"latency_ms": 42})

    log_event("dialogue_generated", {"character": "Zephyr", "latency_ms": 150})
"""

from __future__ import annotations

import logging
import time
from typing import Any

from backend.config import settings

logger = logging.getLogger("npc-system.cloud-logging")

# Module-level Cloud Logging client (lazy-initialized)
_cloud_client = None
_cloud_logger = None
_initialized = False


def _initialize_cloud_logging() -> bool:  # pragma: no cover
    """
    Initialize Google Cloud Logging client for production environments.

    Returns:
        True if Cloud Logging was successfully initialized, False otherwise.
    """
    global _cloud_client, _cloud_logger, _initialized

    if _initialized:
        return _cloud_logger is not None

    _initialized = True

    if not settings.is_production or not settings.google_cloud_project:
        logger.info("Cloud Logging disabled (not production or no project ID)")
        return False

    try:
        import google.cloud.logging as cloud_logging

        _cloud_client = cloud_logging.Client(
            project=settings.google_cloud_project,
        )
        # Attach Cloud Logging handler to Python's root logger
        _cloud_client.setup_logging(log_level=logging.INFO)
        _cloud_logger = _cloud_client.logger("npc-actor-system")

        logger.info(
            "Google Cloud Logging initialized for project: " f"{settings.google_cloud_project}"
        )
        return True

    except Exception as e:
        logger.warning(f"Cloud Logging initialization failed: {e}. Using standard logging.")
        return False


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger instance configured for the NPC Actor System.

    In production, logs are automatically routed to Google Cloud Logging.
    In development, standard Python logging is used.

    Args:
        module_name: The name of the module requesting the logger.

    Returns:
        A configured logging.Logger instance.
    """
    _initialize_cloud_logging()
    return logging.getLogger(f"npc-system.{module_name}")


def log_event(
    event_name: str,
    payload: dict[str, Any] | None = None,
    *,
    severity: str = "INFO",
) -> None:
    """
    Log a structured event to Google Cloud Logging.

    Events are logged as structured JSON payloads with automatic metadata
    enrichment (timestamp, service name, environment).

    Args:
        event_name: Machine-readable event identifier (e.g., "dialogue_generated").
        payload: Optional dictionary with event-specific data.
        severity: Log severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    entry = {
        "event": event_name,
        "service": "npc-actor-system",
        "environment": settings.app_env,
        **(payload or {}),
    }

    # Route to Cloud Logging in production
    if _cloud_logger is not None:  # pragma: no cover
        _cloud_logger.log_struct(
            entry,
            severity=severity,
            labels={
                "service": "npc-actor-system",
                "environment": settings.app_env,
            },
        )
    else:
        # Fallback to standard logging
        log_fn = getattr(logger, severity.lower(), logger.info)
        log_fn(f"[EVENT] {event_name}: {entry}")


def log_latency(
    operation: str,
    start_time: float,
    *,
    metadata: dict[str, Any] | None = None,
) -> float:
    """
    Log operation latency as a structured metric.

    Calculates elapsed time from start_time and logs it as a structured
    event for Cloud Monitoring dashboards.

    Args:
        operation: Name of the operation being measured.
        start_time: Monotonic timestamp from time.monotonic().
        metadata: Optional additional context.

    Returns:
        The calculated latency in milliseconds.
    """
    latency_ms = (time.monotonic() - start_time) * 1000

    log_event(
        "performance_metric",
        {
            "operation": operation,
            "latency_ms": round(latency_ms, 2),
            **(metadata or {}),
        },
    )

    return latency_ms
