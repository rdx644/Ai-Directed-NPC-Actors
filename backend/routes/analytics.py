"""
Analytics API routes for the NPC Actor System.

Provides REST endpoints for real-time analytics, engagement metrics,
and data export capabilities that integrate with Google Cloud services.

Endpoints:
    GET  /api/analytics/summary      — Interaction summary dashboard
    GET  /api/analytics/characters   — Per-character performance analytics
    GET  /api/analytics/engagement   — Attendee engagement metrics
    GET  /api/analytics/health       — System health for Cloud Monitoring
    POST /api/analytics/export       — Export interaction data to Cloud Storage
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from backend.analytics import (
    compute_character_analytics,
    compute_engagement_metrics,
    compute_interaction_summary,
    compute_system_health,
)
from backend.cloud_logging import log_event
from backend.cloud_storage import export_interactions
from backend.database import db

logger = logging.getLogger("npc-system.routes.analytics")

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_analytics_summary() -> dict[str, Any]:
    """
    Get a comprehensive summary of all system interactions.

    Returns aggregated metrics including interaction counts by type,
    character popularity rankings, and recent activity feed.
    Integrates with Google Cloud Logging for metric event tracking.
    """
    summary = compute_interaction_summary()

    log_event(
        "analytics_summary_requested",
        {
            "total_interactions": summary["total_interactions"],
        },
    )

    return summary


@router.get("/characters")
async def get_character_analytics() -> list[dict[str, Any]]:
    """
    Get analytics for all active NPC characters.

    Returns per-character metrics including interaction counts,
    unique attendee engagement, and quest generation statistics.
    """
    characters = db.list_characters()
    analytics = [compute_character_analytics(c.id) for c in characters]

    log_event(
        "character_analytics_requested",
        {
            "character_count": len(analytics),
        },
    )

    return analytics


@router.get("/characters/{character_id}")
async def get_single_character_analytics(
    character_id: str,
) -> dict[str, Any]:
    """
    Get detailed analytics for a specific NPC character.

    Args:
        character_id: The character identifier to analyze.

    Returns:
        Character-specific interaction and engagement metrics.
    """
    return compute_character_analytics(character_id)


@router.get("/engagement")
async def get_engagement_metrics() -> dict[str, Any]:
    """
    Get attendee engagement metrics across the event.

    Returns average XP, quest completion rates, engagement
    distribution, and participation statistics. Logs structured
    metrics to Google Cloud Logging for dashboards.
    """
    return compute_engagement_metrics()


@router.get("/health")
async def get_system_health() -> dict[str, Any]:
    """
    Get system health metrics for Cloud Monitoring integration.

    Returns service availability status, cache performance,
    data volume statistics, and infrastructure health indicators.
    Designed for consumption by Google Cloud Monitoring alerts.
    """
    health = compute_system_health()

    log_event(
        "system_health_checked",
        {
            "cache_hit_rate": health["cache"].get("hit_rate", 0),
        },
    )

    return health


@router.post("/export")
async def export_interaction_data() -> dict[str, Any]:
    """
    Export all interaction data to Google Cloud Storage.

    Creates a timestamped JSON export of all recorded interactions
    and uploads it to the configured GCS bucket. Returns the GCS
    URI for downstream processing.

    Returns:
        Export status including GCS URI and record count.
    """
    interactions = db.list_interactions(limit=10000)
    interaction_dicts = [i.model_dump() for i in interactions]

    gcs_uri = export_interactions(interaction_dicts)

    log_event(
        "interactions_exported",
        {
            "record_count": len(interaction_dicts),
            "gcs_uri": gcs_uri or "local_only",
        },
    )

    return {
        "status": "exported",
        "record_count": len(interaction_dicts),
        "gcs_uri": gcs_uri,
        "message": (
            f"Exported {len(interaction_dicts)} interactions"
            + (f" to {gcs_uri}" if gcs_uri else " (Cloud Storage unavailable)")
        ),
    }
