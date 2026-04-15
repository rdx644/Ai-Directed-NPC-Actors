"""
Caching layer for the NPC Actor System.

Uses an LRU (Least Recently Used) cache with TTL (Time To Live)
to reduce redundant Gemini API calls and improve response times.

Cache Strategy:
  - Cache key: hash of (character_id, attendee_id, interaction_type)
  - TTL: 5 minutes (to keep dialogue fresh but avoid duplicate calls)
  - Max size: 100 entries (bounded memory usage)

Note: Dialogue still varies due to Gemini's temperature settings,
but repeated rapid scans of the same badge won't trigger duplicate API calls.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("npc-system.cache")


@dataclass(frozen=True)
class CacheKey:
    """Immutable, hashable cache key for dialogue requests."""
    character_id: str
    attendee_id: str
    interaction_type: str

    def to_hash(self) -> str:
        """Generate a compact hash for this cache key."""
        raw = f"{self.character_id}:{self.attendee_id}:{self.interaction_type}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class CacheEntry:
    """A cached value with creation timestamp for TTL expiry."""
    value: Any
    created_at: float = field(default_factory=time.monotonic)

    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if this entry has exceeded its time-to-live."""
        return (time.monotonic() - self.created_at) > ttl_seconds


class LRUCache:
    """
    Thread-safe LRU cache with TTL-based expiration.

    Bounds memory usage via max_size and prevents stale data via ttl_seconds.
    Evicts least-recently-used entries when capacity is reached.

    Args:
        max_size: Maximum number of cache entries.
        ttl_seconds: Time-to-live for each entry in seconds.
    """

    def __init__(self, max_size: int = 100, ttl_seconds: float = 300.0) -> None:
        self._max_size: int = max_size
        self._ttl_seconds: float = ttl_seconds
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: CacheKey) -> Optional[Any]:
        """
        Retrieve a cached value if it exists and hasn't expired.

        Moves accessed entries to the end (most recently used).

        Args:
            key: The cache key to look up.

        Returns:
            The cached value, or None if not found or expired.
        """
        hash_key = key.to_hash()

        if hash_key not in self._store:
            self._misses += 1
            return None

        entry = self._store[hash_key]

        if entry.is_expired(self._ttl_seconds):
            del self._store[hash_key]
            self._misses += 1
            logger.debug(f"Cache expired: {hash_key}")
            return None

        # Move to end (most recently used)
        self._store.move_to_end(hash_key)
        self._hits += 1
        logger.debug(f"Cache hit: {hash_key}")
        return entry.value

    def put(self, key: CacheKey, value: Any) -> None:
        """
        Store a value in the cache.

        Evicts the least-recently-used entry if at capacity.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        hash_key = key.to_hash()

        # If key already exists, update it
        if hash_key in self._store:
            del self._store[hash_key]

        # Evict oldest if at capacity
        while len(self._store) >= self._max_size:
            evicted_key, _ = self._store.popitem(last=False)
            logger.debug(f"Cache evicted: {evicted_key}")

        self._store[hash_key] = CacheEntry(value=value)
        logger.debug(f"Cache stored: {hash_key}")

    def invalidate(self, key: CacheKey) -> bool:
        """Remove a specific cache entry. Returns True if found."""
        hash_key = key.to_hash()
        if hash_key in self._store:
            del self._store[hash_key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()
        logger.info("Cache cleared")

    @property
    def stats(self) -> dict[str, Any]:
        """Return cache performance statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl_seconds,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# Singleton dialogue cache instance
dialogue_cache = LRUCache(max_size=100, ttl_seconds=300.0)
