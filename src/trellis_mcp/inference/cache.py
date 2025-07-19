"""LRU cache for inference results with intelligent invalidation.

This module provides high-performance caching for inference results to optimize
repeated kind inference operations. Follows existing cache patterns from the
validation system and integrates with file system validation.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import TypedDict

from .path_builder import PathBuilder
from .validator import ValidationResult

# Configure logger for this module
logger = logging.getLogger(__name__)


class InferenceCacheStats(TypedDict):
    """Type definition for inference cache statistics."""

    size: int
    max_size: int
    hits: int
    misses: int
    evictions: int
    hit_rate: float
    memory_usage: int


@dataclass
class InferenceResult:
    """Cacheable inference result structure.

    Provides detailed information about inference operations including
    the inferred object type, validation status, and cache metadata
    for intelligent invalidation.
    """

    object_id: str
    inferred_kind: str
    is_valid: bool
    cached_at: float
    validation_result: ValidationResult | None = None
    file_mtime: float | None = None

    @classmethod
    def create(
        cls,
        object_id: str,
        inferred_kind: str,
        is_valid: bool,
        validation_result: ValidationResult | None = None,
        file_mtime: float | None = None,
    ) -> "InferenceResult":
        """Create a new inference result with current timestamp."""
        return cls(
            object_id=object_id,
            inferred_kind=inferred_kind,
            is_valid=is_valid,
            cached_at=time.time(),
            validation_result=validation_result,
            file_mtime=file_mtime,
        )


class InferenceCache:
    """High-performance LRU cache for inference results with invalidation.

    Implements a thread-safe LRU cache that tracks file modification times
    for intelligent cache invalidation. Follows existing patterns from
    DependencyGraphCache while providing optimized performance for
    inference operations.

    Performance targets:
    - Cache hits: < 1ms
    - Cache misses: < 5ms overhead
    - Thread-safe concurrent access
    - Memory efficiency with bounded size

    Example:
        >>> cache = InferenceCache(max_size=1000)
        >>> result = InferenceResult.create("T-auth", "task", True)
        >>> cache.put("T-auth", result)
        >>> cached = cache.get("T-auth")
        >>> if cached:
        ...     print(f"Cache hit: {cached.inferred_kind}")
    """

    def __init__(self, max_size: int = 1000, path_builder: PathBuilder | None = None):
        """Initialize InferenceCache with configurable parameters.

        Args:
            max_size: Maximum number of cache entries (default: 1000)
            path_builder: PathBuilder instance for file validation (optional)

        Raises:
            ValueError: If max_size is not positive
        """
        if max_size <= 0:
            raise ValueError("Cache max_size must be positive")

        self.max_size = max_size
        self.path_builder = path_builder

        # Thread-safe cache storage
        self._cache: dict[str, InferenceResult] = {}
        self._access_order: list[str] = []
        self._lock = threading.RLock()

        # Cache statistics for monitoring
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, object_id: str) -> InferenceResult | None:
        """Retrieve cached inference result if valid.

        Checks cache for the object_id and validates the entry is still
        current by checking file modification times. Updates LRU order
        on cache hit.

        Args:
            object_id: Object ID to retrieve from cache

        Returns:
            InferenceResult if found and valid, None otherwise
        """
        if not object_id or not object_id.strip():
            return None

        with self._lock:
            clean_id = object_id.strip()

            if clean_id not in self._cache:
                self._misses += 1
                return None

            result = self._cache[clean_id]

            # Validate cache entry is still current
            if self._is_cache_valid(clean_id, result):
                # Update LRU order
                self._access_order.remove(clean_id)
                self._access_order.append(clean_id)
                self._hits += 1
                return result
            else:
                # Remove stale entry
                self._invalidate_unsafe(clean_id)
                self._misses += 1
                return None

    def put(self, object_id: str, result: InferenceResult) -> None:
        """Cache inference result with LRU eviction if needed.

        Stores the inference result in cache and evicts least recently
        used entries if cache exceeds max_size.

        Args:
            object_id: Object ID to use as cache key
            result: InferenceResult to cache

        Raises:
            ValueError: If object_id is empty or result is None
        """
        if not object_id or not object_id.strip():
            raise ValueError("Object ID cannot be empty")
        if result is None:
            raise ValueError("InferenceResult cannot be None")

        with self._lock:
            clean_id = object_id.strip()

            # Remove existing entry if present
            if clean_id in self._cache:
                self._access_order.remove(clean_id)

            # Evict LRU entries if needed
            while len(self._cache) >= self.max_size and self._access_order:
                self._evict_lru_unsafe()

            # Add new entry
            self._cache[clean_id] = result
            self._access_order.append(clean_id)

    def invalidate(self, object_id: str) -> None:
        """Remove specific entry from cache.

        Args:
            object_id: Object ID to remove from cache
        """
        if not object_id or not object_id.strip():
            return

        with self._lock:
            self._invalidate_unsafe(object_id.strip())

    def clear(self) -> None:
        """Clear entire cache and reset statistics."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def get_stats(self) -> InferenceCacheStats:
        """Get cache statistics for monitoring.

        Returns:
            Dictionary containing cache performance metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "memory_usage": len(self._cache) * 100,  # Rough estimate in bytes
            }

    def _is_cache_valid(self, object_id: str, result: InferenceResult) -> bool:
        """Check if cache entry is still valid by comparing file modification times.

        Uses tolerance-based comparison (1ms) following existing patterns from
        DependencyGraphCache to avoid floating point precision issues and
        filesystem timestamp resolution differences.

        Args:
            object_id: Object ID to validate
            result: Cached inference result with stored file modification time

        Returns:
            True if cache entry is valid, False if file has changed
        """
        if not self.path_builder:
            # Without path validation, use simple time-based expiration (1 minute)
            return time.time() - result.cached_at < 60.0

        # If no file modification time was stored, use time-based expiration
        if result.file_mtime is None:
            return time.time() - result.cached_at < 60.0

        try:
            # Infer kind from object ID prefix for path construction
            kind = self._infer_kind_from_id(object_id)
            if not kind:
                return False

            # Build path using PathBuilder
            builder = self.path_builder.for_object(kind, object_id)
            path = builder.build_path()

            if not path.exists():
                return False

            current_mtime = os.path.getmtime(path)
            # Compare current file modification time with stored modification time
            # Use 1ms tolerance following existing patterns
            return abs(current_mtime - result.file_mtime) <= 0.001

        except Exception as e:
            # If anything goes wrong, consider cache invalid
            logger.debug(f"Cache validation failed for {object_id}: {e}")
            return False

    def _infer_kind_from_id(self, object_id: str) -> str | None:
        """Infer object kind from ID prefix.

        Args:
            object_id: Object ID with potential prefix

        Returns:
            Object kind or None if not recognized
        """
        clean_id = object_id.strip().upper()

        if clean_id.startswith("P-"):
            return "project"
        elif clean_id.startswith("E-"):
            return "epic"
        elif clean_id.startswith("F-"):
            return "feature"
        elif clean_id.startswith("T-"):
            return "task"
        else:
            return None

    def _evict_lru_unsafe(self) -> None:
        """Evict least recently used entry. Must be called with lock held."""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._evictions += 1

    def _invalidate_unsafe(self, object_id: str) -> None:
        """Remove entry without locking. Must be called with lock held."""
        if object_id in self._cache:
            del self._cache[object_id]
        if object_id in self._access_order:
            self._access_order.remove(object_id)


# Global cache instance for singleton pattern
_inference_cache: InferenceCache | None = None


def get_inference_cache(
    max_size: int = 1000, path_builder: PathBuilder | None = None
) -> InferenceCache:
    """Get global inference cache instance.

    Args:
        max_size: Maximum cache size (only used on first call)
        path_builder: PathBuilder instance (only used on first call)

    Returns:
        Global InferenceCache instance
    """
    global _inference_cache
    if _inference_cache is None:
        _inference_cache = InferenceCache(max_size=max_size, path_builder=path_builder)
    return _inference_cache


def clear_inference_cache() -> None:
    """Clear the global inference cache."""
    if _inference_cache:
        _inference_cache.clear()


def get_cache_stats() -> InferenceCacheStats:
    """Get statistics about the global inference cache.

    Returns:
        Dictionary containing cache statistics
    """
    if _inference_cache:
        return _inference_cache.get_stats()
    else:
        return {
            "size": 0,
            "max_size": 0,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "hit_rate": 0.0,
            "memory_usage": 0,
        }
