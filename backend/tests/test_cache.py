"""
Tests for the caching layer.

Tests LRU eviction, TTL expiration, hit/miss tracking, and edge cases.
"""

from __future__ import annotations

import time

import pytest

from backend.cache import CacheEntry, CacheKey, LRUCache


class TestCacheKey:
    """Tests for the CacheKey dataclass."""

    def test_hash_deterministic(self) -> None:
        """Same inputs should produce the same hash."""
        k1 = CacheKey("chr-1", "att-1", "greeting")
        k2 = CacheKey("chr-1", "att-1", "greeting")
        assert k1.to_hash() == k2.to_hash()

    def test_hash_unique_for_different_inputs(self) -> None:
        k1 = CacheKey("chr-1", "att-1", "greeting")
        k2 = CacheKey("chr-1", "att-1", "quest")
        assert k1.to_hash() != k2.to_hash()

    def test_frozen(self) -> None:
        """CacheKey should be immutable."""
        key = CacheKey("chr-1", "att-1", "greeting")
        with pytest.raises(AttributeError):
            key.character_id = "changed"


class TestCacheEntry:
    """Tests for the CacheEntry dataclass."""

    def test_not_expired_immediately(self) -> None:
        entry = CacheEntry(value="test")
        assert not entry.is_expired(300.0)

    def test_expired_with_zero_ttl(self) -> None:
        entry = CacheEntry(value="test", created_at=time.monotonic() - 1)
        assert entry.is_expired(0.0)


class TestLRUCache:
    """Tests for the LRU cache implementation."""

    def test_put_and_get(self) -> None:
        cache = LRUCache(max_size=10, ttl_seconds=300.0)
        key = CacheKey("chr-1", "att-1", "greeting")
        cache.put(key, "hello")
        assert cache.get(key) == "hello"

    def test_cache_miss(self) -> None:
        cache = LRUCache(max_size=10, ttl_seconds=300.0)
        key = CacheKey("chr-1", "att-1", "greeting")
        assert cache.get(key) is None

    def test_ttl_expiration(self) -> None:
        """Expired entries should not be returned."""
        cache = LRUCache(max_size=10, ttl_seconds=0.01)
        key = CacheKey("chr-1", "att-1", "greeting")
        cache.put(key, "hello")
        time.sleep(0.02)
        assert cache.get(key) is None

    def test_lru_eviction(self) -> None:
        """Oldest entry should be evicted when at capacity."""
        cache = LRUCache(max_size=2, ttl_seconds=300.0)
        k1 = CacheKey("chr-1", "att-1", "greeting")
        k2 = CacheKey("chr-2", "att-2", "quest")
        k3 = CacheKey("chr-3", "att-3", "advice")

        cache.put(k1, "first")
        cache.put(k2, "second")
        cache.put(k3, "third")  # Should evict k1

        assert cache.get(k1) is None  # Evicted
        assert cache.get(k2) == "second"
        assert cache.get(k3) == "third"

    def test_access_refreshes_lru_order(self) -> None:
        """Accessing an entry should make it most-recently-used."""
        cache = LRUCache(max_size=2, ttl_seconds=300.0)
        k1 = CacheKey("chr-1", "att-1", "greeting")
        k2 = CacheKey("chr-2", "att-2", "quest")
        k3 = CacheKey("chr-3", "att-3", "advice")

        cache.put(k1, "first")
        cache.put(k2, "second")
        cache.get(k1)  # Access k1 → now most recent
        cache.put(k3, "third")  # Should evict k2 (not k1)

        assert cache.get(k1) == "first"
        assert cache.get(k2) is None  # Evicted
        assert cache.get(k3) == "third"

    def test_invalidate(self) -> None:
        cache = LRUCache(max_size=10, ttl_seconds=300.0)
        key = CacheKey("chr-1", "att-1", "greeting")
        cache.put(key, "hello")
        assert cache.invalidate(key) is True
        assert cache.get(key) is None

    def test_invalidate_nonexistent(self) -> None:
        cache = LRUCache(max_size=10, ttl_seconds=300.0)
        key = CacheKey("chr-1", "att-1", "greeting")
        assert cache.invalidate(key) is False

    def test_clear(self) -> None:
        cache = LRUCache(max_size=10, ttl_seconds=300.0)
        k1 = CacheKey("chr-1", "att-1", "greeting")
        k2 = CacheKey("chr-2", "att-2", "quest")
        cache.put(k1, "a")
        cache.put(k2, "b")
        cache.clear()
        assert cache.get(k1) is None
        assert cache.get(k2) is None
        assert cache.stats["size"] == 0

    def test_stats_tracking(self) -> None:
        cache = LRUCache(max_size=10, ttl_seconds=300.0)
        key = CacheKey("chr-1", "att-1", "greeting")

        cache.get(key)  # miss
        cache.put(key, "hello")
        cache.get(key)  # hit
        cache.get(key)  # hit

        stats = cache.stats
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate_percent"] == pytest.approx(66.67, abs=0.01)

    def test_update_existing_key(self) -> None:
        cache = LRUCache(max_size=10, ttl_seconds=300.0)
        key = CacheKey("chr-1", "att-1", "greeting")
        cache.put(key, "first")
        cache.put(key, "second")
        assert cache.get(key) == "second"
        assert cache.stats["size"] == 1
