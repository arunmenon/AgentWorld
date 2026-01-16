"""LLM response caching.

Provides both in-memory and database-backed caching per ADR-008.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Protocol


class CacheBackend(Protocol):
    """Protocol for cache backends."""

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a value in cache."""
        ...

    def clear(self) -> None:
        """Clear all cached entries."""
        ...

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        ...


class LLMCache:
    """In-memory cache for LLM responses with TTL support."""

    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """Initialize the cache.

        Args:
            ttl: Time-to-live in seconds (default: 1 hour)
            max_size: Maximum number of cached entries
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: dict[str, tuple[float, Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None

        timestamp, value = self._cache[key]
        if time.time() - timestamp > self.ttl:
            # Expired
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict oldest entries if at max size
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[key] = (time.time(), value)

    def _evict_oldest(self) -> None:
        """Evict the oldest entries to make room."""
        if not self._cache:
            return

        # Sort by timestamp and remove oldest 10%
        sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][0])
        num_to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:num_to_remove]:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0-1)."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "ttl": self.ttl,
        }


class DatabaseLLMCache:
    """Database-backed LLM cache per ADR-008.

    Stores LLM responses in SQLite for persistence across sessions.
    Also maintains an in-memory cache for performance.
    """

    def __init__(
        self,
        ttl: int = 3600,
        memory_cache_size: int = 100,
        use_memory_cache: bool = True,
    ):
        """Initialize database cache.

        Args:
            ttl: Time-to-live in seconds (default: 1 hour)
            memory_cache_size: Size of in-memory L1 cache
            use_memory_cache: Whether to use in-memory L1 cache
        """
        self.ttl = ttl
        self.use_memory_cache = use_memory_cache
        self._hits = 0
        self._misses = 0
        self._db_hits = 0
        self._memory_hits = 0

        # L1 in-memory cache for hot entries
        if use_memory_cache:
            self._memory_cache = LLMCache(ttl=ttl, max_size=memory_cache_size)
        else:
            self._memory_cache = None

        # Lazy-loaded repository
        self._repository = None

    @property
    def repository(self):
        """Get the repository, creating if needed."""
        if self._repository is None:
            from agentworld.persistence.database import init_db
            from agentworld.persistence.repository import Repository
            init_db()
            self._repository = Repository()
        return self._repository

    def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Checks in-memory cache first, then database.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        # Check L1 memory cache first
        if self._memory_cache is not None:
            value = self._memory_cache.get(key)
            if value is not None:
                self._hits += 1
                self._memory_hits += 1
                return value

        # Check database
        cached = self.repository.get_llm_cache(key)
        if cached is None:
            self._misses += 1
            return None

        self._hits += 1
        self._db_hits += 1

        # Parse the stored value
        value = {
            "content": cached["response_content"],
            "prompt_tokens": cached.get("prompt_tokens", 0),
            "completion_tokens": cached.get("completion_tokens", 0),
            "model": cached["model"],
        }

        # Populate L1 cache for next access
        if self._memory_cache is not None:
            self._memory_cache.set(key, value)

        return value

    def set(
        self,
        key: str,
        value: Any,
        model: str = "",
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> None:
        """Set a value in cache.

        Stores in both memory and database.

        Args:
            key: Cache key
            value: Value to cache (should have 'content' key or be a dict)
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        """
        # Extract content from value
        if isinstance(value, dict):
            content = value.get("content", str(value))
            model = value.get("model", model)
            prompt_tokens = value.get("prompt_tokens", prompt_tokens)
            completion_tokens = value.get("completion_tokens", completion_tokens)
        else:
            content = str(value)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl) if self.ttl > 0 else None

        # Store in database
        self.repository.save_llm_cache(
            cache_key=key,
            response_content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            expires_at=expires_at,
        )

        # Also store in L1 memory cache
        if self._memory_cache is not None:
            self._memory_cache.set(key, value)

    def clear(self) -> None:
        """Clear all cached entries."""
        self.repository.clear_all_llm_cache()
        if self._memory_cache is not None:
            self._memory_cache.clear()

    def clear_expired(self) -> int:
        """Clear expired entries from database.

        Returns:
            Number of entries cleared
        """
        return self.repository.clear_expired_llm_cache()

    @property
    def size(self) -> int:
        """Current number of cached entries (approximate, from memory cache)."""
        if self._memory_cache is not None:
            return self._memory_cache.size
        return 0

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0-1)."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "memory_hits": self._memory_hits,
            "db_hits": self._db_hits,
            "hit_rate": self.hit_rate,
            "ttl": self.ttl,
            "memory_cache_size": self._memory_cache.size if self._memory_cache else 0,
            "backend": "database",
        }


def get_cache(use_database: bool = False, **kwargs) -> LLMCache | DatabaseLLMCache:
    """Get an LLM cache instance.

    Args:
        use_database: If True, use database-backed cache (ADR-008 compliant)
        **kwargs: Additional arguments passed to cache constructor

    Returns:
        LLMCache or DatabaseLLMCache instance
    """
    if use_database:
        return DatabaseLLMCache(**kwargs)
    return LLMCache(**kwargs)
