"""File modification time-based cache for children discovery.

This module provides high-performance caching for children discovery operations
to optimize repeated children lookup operations. Follows existing cache patterns
from the validation and inference systems and integrates with file system validation.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

# Configure logger for this module
logger = logging.getLogger(__name__)


class ChildrenCacheStats(TypedDict):
    """Type definition for children cache statistics."""

    size: int
    max_size: int
    hits: int
    misses: int
    evictions: int
    hit_rate: float
    memory_usage: int


@dataclass
class ChildrenCacheEntry:
    """Cacheable children discovery result structure.

    Provides detailed information about discovered children including
    their metadata and file modification times for intelligent invalidation.
    """

    children: list[dict[str, str]]
    parent_mtime: float
    children_mtimes: dict[str, float]
    cached_at: float

    @classmethod
    def create(
        cls,
        children: list[dict[str, str]],
        parent_mtime: float,
        children_mtimes: dict[str, float],
    ) -> "ChildrenCacheEntry":
        """Create a new cache entry with current timestamp."""
        return cls(
            children=children,
            parent_mtime=parent_mtime,
            children_mtimes=children_mtimes,
            cached_at=time.time(),
        )


class ChildrenCache:
    """File modification time-based cache for children discovery.

    Provides efficient caching of children metadata with automatic invalidation
    when parent or child objects are modified, following patterns from the
    validation and inference cache systems.

    Performance targets:
    - Cache hits: < 1ms
    - Cache misses: < 100ms (includes file system scan + cache update)
    - Thread-safe concurrent access
    - Memory efficiency with bounded size

    Example:
        >>> cache = ChildrenCache(max_entries=1000)
        >>> children = [{"id": "child-1", "title": "Child", "status": "open", "kind": "epic"}]
        >>> cache.set_children(Path("/path/to/parent.md"), children)
        >>> cached = cache.get_children(Path("/path/to/parent.md"))
        >>> if cached:
        ...     print(f"Cache hit: {len(cached)} children")
    """

    def __init__(self, max_entries: int = 1000):
        """Initialize cache with LRU eviction.

        Args:
            max_entries: Maximum number of cache entries (default: 1000)

        Raises:
            ValueError: If max_entries is not positive
        """
        if max_entries <= 0:
            raise ValueError("Cache max_entries must be positive")

        self.max_entries = max_entries

        # Thread-safe cache storage
        self._cache: dict[str, ChildrenCacheEntry] = {}
        self._access_order: list[str] = []
        self._lock = threading.RLock()

        # Cache statistics for monitoring
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get_children(self, parent_path: Path | None) -> list[dict[str, str]] | None:
        """Retrieve cached children metadata if still valid.

        Checks cache for the parent_path and validates the entry is still
        current by checking file modification times. Updates LRU order
        on cache hit.

        Args:
            parent_path: Path to parent object file

        Returns:
            List of children metadata dictionaries if found and valid, None otherwise
        """
        if not parent_path:
            return None

        with self._lock:
            cache_key = str(parent_path)

            if cache_key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[cache_key]

            # Validate cache entry is still current
            if self._is_cache_valid(parent_path, entry):
                # Update LRU order
                self._access_order.remove(cache_key)
                self._access_order.append(cache_key)
                self._hits += 1
                return entry.children
            else:
                # Remove stale entry
                self._invalidate_unsafe(cache_key)
                self._misses += 1
                return None

    def set_children(self, parent_path: Path | None, children: list[dict[str, str]] | None) -> None:
        """Cache children metadata with current modification times.

        Stores the children metadata in cache with current file modification
        times for validation and evicts least recently used entries if needed.

        Args:
            parent_path: Path to parent object file
            children: List of children metadata dictionaries

        Raises:
            ValueError: If parent_path is None or children is None
        """
        if not parent_path:
            raise ValueError("Parent path cannot be None")
        if children is None:
            raise ValueError("Children list cannot be None")

        with self._lock:
            cache_key = str(parent_path)

            try:
                # Get current modification times
                parent_mtime = os.path.getmtime(parent_path) if parent_path.exists() else 0.0
                children_mtimes = {}

                for child in children:
                    child_path_str = child.get("file_path")
                    if child_path_str:
                        child_path = Path(child_path_str)
                        if child_path.exists():
                            children_mtimes[child_path_str] = os.path.getmtime(child_path)

                # Create cache entry
                entry = ChildrenCacheEntry.create(children, parent_mtime, children_mtimes)

                # Remove existing entry if present
                if cache_key in self._cache:
                    self._access_order.remove(cache_key)

                # Evict LRU entries if needed
                while len(self._cache) >= self.max_entries and self._access_order:
                    self._evict_lru_unsafe()

                # Add new entry
                self._cache[cache_key] = entry
                self._access_order.append(cache_key)

            except Exception as e:
                # If anything goes wrong, log and continue without caching
                logger.debug(f"Failed to cache children for {parent_path}: {e}")

    def invalidate(self, parent_path: Path | None) -> None:
        """Remove cached entry for specific parent.

        Args:
            parent_path: Path to parent object file to remove from cache
        """
        if not parent_path:
            return

        with self._lock:
            self._invalidate_unsafe(str(parent_path))

    def clear(self) -> None:
        """Clear all cached entries and reset statistics."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def get_stats(self) -> ChildrenCacheStats:
        """Get cache statistics for monitoring.

        Returns:
            Dictionary containing cache performance metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_entries,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
                "memory_usage": len(self._cache) * 200,  # Rough estimate in bytes
            }

    def _is_cache_valid(self, parent_path: Path, entry: ChildrenCacheEntry) -> bool:
        """Check if cache entry is still valid by comparing file modification times.

        Uses tolerance-based comparison (1ms) following existing patterns from
        DependencyGraphCache to avoid floating point precision issues and
        filesystem timestamp resolution differences.

        Args:
            parent_path: Path to parent object file
            entry: Cached children entry with stored modification times

        Returns:
            True if cache entry is valid, False if any files have changed
        """
        try:
            # Check parent file modification time
            if parent_path.exists():
                current_parent_mtime = os.path.getmtime(parent_path)
                if abs(current_parent_mtime - entry.parent_mtime) > 0.001:
                    return False
            elif entry.parent_mtime != 0.0:
                # Parent file was deleted
                return False

            # Check all children file modification times
            for child_path_str, cached_mtime in entry.children_mtimes.items():
                child_path = Path(child_path_str)
                if child_path.exists():
                    current_mtime = os.path.getmtime(child_path)
                    if abs(current_mtime - cached_mtime) > 0.001:
                        return False
                else:
                    # Child file was deleted
                    return False

            return True

        except Exception as e:
            # If anything goes wrong, consider cache invalid
            logger.debug(f"Cache validation failed for {parent_path}: {e}")
            return False

    def _evict_lru_unsafe(self) -> None:
        """Evict least recently used entry. Must be called with lock held."""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._evictions += 1

    def _invalidate_unsafe(self, cache_key: str) -> None:
        """Remove entry without locking. Must be called with lock held."""
        if cache_key in self._cache:
            del self._cache[cache_key]
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)


# Global cache instance for singleton pattern
_children_cache: ChildrenCache | None = None


def get_children_cache(max_entries: int = 1000) -> ChildrenCache:
    """Get global children cache instance.

    Args:
        max_entries: Maximum cache size (only used on first call)

    Returns:
        Global ChildrenCache instance
    """
    global _children_cache
    if _children_cache is None:
        _children_cache = ChildrenCache(max_entries=max_entries)
    return _children_cache


def clear_children_cache() -> None:
    """Clear the global children cache."""
    global _children_cache
    if _children_cache:
        _children_cache.clear()
    _children_cache = None


def get_cache_stats() -> ChildrenCacheStats:
    """Get statistics about the global children cache.

    Returns:
        Dictionary containing cache statistics
    """
    if _children_cache:
        return _children_cache.get_stats()
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
