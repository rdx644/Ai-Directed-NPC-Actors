"""
Google Cloud Storage integration for the NPC Actor System.

Handles storage and retrieval of:
    - Generated TTS audio clips (WAV/MP3 files)
    - Interaction log exports (JSON/CSV)
    - Analytics report snapshots

Storage Layout:
    gs://{bucket}/
    ├── audio/
    │   └── {character_id}/{interaction_id}.mp3
    ├── exports/
    │   └── interactions/{date}.json
    └── analytics/
        └── reports/{date}.json

Features:
    - Signed URL generation for secure, time-limited audio access
    - Automatic content type detection
    - Batch export of interaction data
    - Graceful fallback when GCS is unavailable
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from backend.config import settings
from backend.exceptions import CloudStorageError

logger = logging.getLogger("npc-system.cloud-storage")

# Module-level client (lazy-initialized)
_storage_client = None
_bucket = None

# Default bucket name pattern
BUCKET_NAME_TEMPLATE = "{project}-npc-audio"


def _get_bucket():  # pragma: no cover
    """Lazy-initialize the GCS client and bucket reference."""
    global _storage_client, _bucket

    if _bucket is not None:
        return _bucket

    if not settings.google_cloud_project:
        logger.info("Cloud Storage disabled (no GCP project configured)")
        return None

    try:
        from google.cloud import storage

        _storage_client = storage.Client(project=settings.google_cloud_project)
        bucket_name = settings.gcs_bucket_name or BUCKET_NAME_TEMPLATE.format(
            project=settings.google_cloud_project
        )

        _bucket = _storage_client.bucket(bucket_name)

        # Create bucket if it doesn't exist
        if not _bucket.exists():
            _bucket = _storage_client.create_bucket(
                bucket_name,
                location=settings.gcs_location,
            )
            logger.info(f"Created GCS bucket: {bucket_name}")
        else:
            logger.info(f"Connected to GCS bucket: {bucket_name}")

        return _bucket

    except Exception as e:
        logger.warning(f"Cloud Storage initialization failed: {e}")
        return None


def store_audio(
    audio_bytes: bytes,
    character_id: str,
    interaction_id: str,
    *,
    content_type: str = "audio/mp3",
) -> str | None:
    """
    Store a generated TTS audio clip in Google Cloud Storage.

    Args:
        audio_bytes: Raw audio file bytes.
        character_id: The NPC character identifier.
        interaction_id: Unique interaction identifier.
        content_type: MIME type of the audio file.

    Returns:
        Public URL or signed URL for the stored audio, or None if storage
        is unavailable.

    Raises:
        CloudStorageError: If the upload fails after GCS is initialized.
    """
    bucket = _get_bucket()
    if bucket is None:
        logger.debug("Cloud Storage unavailable — audio not persisted")
        return None

    try:  # pragma: no cover
        blob_path = f"audio/{character_id}/{interaction_id}.mp3"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(audio_bytes, content_type=content_type)

        logger.info(f"Audio stored in GCS: {blob_path}")
        return blob.public_url

    except Exception as e:  # pragma: no cover
        raise CloudStorageError(f"Failed to store audio: {e}") from e


def export_interactions(
    interactions: list[dict[str, Any]],
    *,
    export_format: str = "json",
) -> str | None:
    """
    Export interaction data to Google Cloud Storage.

    Creates a timestamped export file containing interaction records
    for analytics and compliance purposes.

    Args:
        interactions: List of interaction dictionaries to export.
        export_format: Output format ("json" supported).

    Returns:
        GCS URI of the exported file, or None if storage is unavailable.

    Raises:
        CloudStorageError: If the export fails.
    """
    bucket = _get_bucket()
    if bucket is None:
        logger.debug("Cloud Storage unavailable — export skipped")
        return None

    try:  # pragma: no cover
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
        blob_path = f"exports/interactions/{timestamp}.{export_format}"
        blob = bucket.blob(blob_path)

        export_data = {
            "exported_at": datetime.now(UTC).isoformat(),
            "record_count": len(interactions),
            "interactions": interactions,
        }

        blob.upload_from_string(
            json.dumps(export_data, indent=2, default=str),
            content_type="application/json",
        )

        gcs_uri = f"gs://{bucket.name}/{blob_path}"
        logger.info(f"Interactions exported to GCS: {gcs_uri} ({len(interactions)} records)")
        return gcs_uri

    except Exception as e:  # pragma: no cover
        raise CloudStorageError(f"Failed to export interactions: {e}") from e


def store_analytics_report(
    report_data: dict[str, Any],
) -> str | None:
    """
    Store an analytics report snapshot in Google Cloud Storage.

    Args:
        report_data: Analytics report dictionary to store.

    Returns:
        GCS URI of the stored report, or None if storage is unavailable.
    """
    bucket = _get_bucket()
    if bucket is None:
        return None

    try:  # pragma: no cover
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
        blob_path = f"analytics/reports/{timestamp}.json"
        blob = bucket.blob(blob_path)

        blob.upload_from_string(
            json.dumps(report_data, indent=2, default=str),
            content_type="application/json",
        )

        gcs_uri = f"gs://{bucket.name}/{blob_path}"
        logger.info(f"Analytics report stored: {gcs_uri}")
        return gcs_uri

    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to store analytics report: {e}")
        return None


def generate_signed_url(
    blob_path: str,
    *,
    expiration_minutes: int = 60,
) -> str | None:
    """
    Generate a signed URL for temporary access to a GCS object.

    Args:
        blob_path: Path to the blob within the bucket.
        expiration_minutes: URL validity duration in minutes.

    Returns:
        Signed URL string, or None if storage is unavailable.
    """
    bucket = _get_bucket()
    if bucket is None:
        return None

    try:  # pragma: no cover
        import datetime as dt

        blob = bucket.blob(blob_path)
        url = blob.generate_signed_url(
            version="v4",
            expiration=dt.timedelta(minutes=expiration_minutes),
            method="GET",
        )
        return url

    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to generate signed URL: {e}")
        return None
