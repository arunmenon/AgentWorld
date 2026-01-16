"""Tests for LLM response caching."""

import pytest
import time
from agentworld.llm.cache import LLMCache


class TestLLMCache:
    """Tests for LLMCache class."""

    @pytest.fixture
    def cache(self):
        """Create a cache instance."""
        return LLMCache(ttl=60, max_size=100)

    def test_creation(self, cache):
        """Test cache creation."""
        assert cache is not None
        assert cache.ttl == 60
        assert cache.max_size == 100
        assert cache.size == 0

    def test_set_and_get(self, cache):
        """Test setting and getting values."""
        cache.set("key1", "value1")
        result = cache.get("key1")
        assert result == "value1"

    def test_get_missing_key(self, cache):
        """Test getting a missing key."""
        result = cache.get("nonexistent")
        assert result is None

    def test_expiration(self):
        """Test that entries expire after TTL."""
        cache = LLMCache(ttl=1)  # 1 second TTL
        cache.set("key", "value")

        assert cache.get("key") == "value"
        time.sleep(1.5)  # Wait for expiration
        assert cache.get("key") is None

    def test_clear(self, cache):
        """Test clearing the cache."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()
        assert cache.size == 0
        assert cache.get("key1") is None

    def test_max_size_eviction(self):
        """Test that old entries are evicted at max size."""
        cache = LLMCache(max_size=10)

        for i in range(15):
            cache.set(f"key{i}", f"value{i}")

        assert cache.size <= 10

    def test_hit_rate(self, cache):
        """Test hit rate calculation."""
        cache.set("key", "value")

        cache.get("key")  # hit
        cache.get("key")  # hit
        cache.get("missing")  # miss

        assert cache.hit_rate > 0
        assert cache.hit_rate <= 1.0

    def test_stats(self, cache):
        """Test cache statistics."""
        cache.set("key", "value")
        cache.get("key")
        cache.get("missing")

        stats = cache.stats
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_overwrite_existing_key(self, cache):
        """Test overwriting an existing key."""
        cache.set("key", "value1")
        cache.set("key", "value2")

        assert cache.get("key") == "value2"
