"""
Google Cloud Secret Manager integration for the NPC Actor System.

Provides secure credential retrieval from Google Cloud Secret Manager,
replacing static environment variable-based secrets in production.

Security Model:
    - Production: Secrets are fetched from Secret Manager using IAM-based
      authentication (no keys stored in code or environment).
    - Development: Falls back to environment variables / .env file.

Managed Secrets:
    - GEMINI_API_KEY: Google Gemini API key for AI dialogue generation
    - ADMIN_API_KEY: API key for admin endpoint authentication

Usage:
    from backend.secret_manager import get_secret

    api_key = get_secret("GEMINI_API_KEY")
"""

from __future__ import annotations

import logging
from functools import lru_cache

from backend.config import settings
from backend.exceptions import SecretManagerError

logger = logging.getLogger("npc-system.secret-manager")

# Module-level client (lazy-initialized)
_sm_client = None


def _get_client():  # pragma: no cover
    """Lazy-initialize the Secret Manager client."""
    global _sm_client
    if _sm_client is None:
        try:
            from google.cloud import secretmanager

            _sm_client = secretmanager.SecretManagerServiceClient()
            logger.info("Google Cloud Secret Manager client initialized")
        except Exception as e:
            logger.warning(f"Secret Manager initialization failed: {e}")
            raise SecretManagerError(f"Failed to initialize client: {e}") from e
    return _sm_client


@lru_cache(maxsize=16)
def get_secret(
    secret_id: str,
    *,
    version: str = "latest",
    fallback: str | None = None,
) -> str:
    """
    Retrieve a secret value from Google Cloud Secret Manager.

    In production with a configured GCP project, secrets are fetched from
    Secret Manager. In development mode, falls back to environment variables.

    Args:
        secret_id: The secret identifier in Secret Manager.
        version: The secret version to access (default: "latest").
        fallback: Fallback value if the secret cannot be retrieved.

    Returns:
        The secret value as a string.

    Raises:
        SecretManagerError: If the secret cannot be retrieved and no fallback
            is provided.
    """
    # In non-production or without a project, use env-var fallback
    if not settings.is_production or not settings.google_cloud_project:
        env_value = _get_env_fallback(secret_id)
        if env_value:
            logger.debug(f"Secret '{secret_id}' loaded from environment")
            return env_value
        if fallback is not None:
            return fallback
        logger.warning(f"Secret '{secret_id}' not found in environment")
        return ""

    # Production: fetch from Secret Manager
    try:  # pragma: no cover
        client = _get_client()
        name = (
            f"projects/{settings.google_cloud_project}" f"/secrets/{secret_id}/versions/{version}"
        )
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        logger.info(f"Secret '{secret_id}' retrieved from Secret Manager")
        return secret_value

    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to retrieve secret '{secret_id}': {e}")
        if fallback is not None:
            logger.warning(f"Using fallback value for '{secret_id}'")
            return fallback
        raise SecretManagerError(f"Cannot retrieve secret '{secret_id}': {e}") from e


def _get_env_fallback(secret_id: str) -> str:
    """
    Retrieve a secret value from environment variables or settings.

    Maps Secret Manager secret IDs to their corresponding settings fields.

    Args:
        secret_id: The secret identifier to look up.

    Returns:
        The secret value from environment, or empty string if not found.
    """
    secret_map = {
        "GEMINI_API_KEY": settings.gemini_api_key,
        "ADMIN_API_KEY": settings.admin_api_key,
    }
    return secret_map.get(secret_id, "")


def list_available_secrets() -> list[str]:
    """
    List all secret IDs that are available for retrieval.

    In development, returns the list of known secret mappings.
    In production, queries Secret Manager for available secrets.

    Returns:
        List of available secret identifiers.
    """
    if not settings.is_production or not settings.google_cloud_project:
        return [
            k
            for k, v in {
                "GEMINI_API_KEY": settings.gemini_api_key,
                "ADMIN_API_KEY": settings.admin_api_key,
            }.items()
            if v
        ]

    try:  # pragma: no cover
        client = _get_client()
        parent = f"projects/{settings.google_cloud_project}"
        secrets = client.list_secrets(request={"parent": parent})
        return [s.name.split("/")[-1] for s in secrets]
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to list secrets: {e}")
        return []
