"""Unit tests for ChildrenCache functionality.

Tests cache operations, LRU eviction, modification time tracking,
thread safety, and error handling for the children discovery cache.
"""

import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from trellis_mcp.children.cache import (
    ChildrenCache,
    ChildrenCacheEntry,
    clear_children_cache,
    get_cache_stats,
    get_children_cache,
)


class TestChildrenCacheEntry:
    """Test ChildrenCacheEntry data structure."""

    def test_create_entry(self):
        """Test creating a cache entry with current timestamp."""
        children = [{"id": "child-1", "title": "Child 1", "status": "open", "kind": "epic"}]
        parent_mtime = 1234567890.0
        children_mtimes = {"/path/child.md": 1234567891.0}

        entry = ChildrenCacheEntry.create(children, parent_mtime, children_mtimes)

        assert entry.children == children
        assert entry.parent_mtime == parent_mtime
        assert entry.children_mtimes == children_mtimes
        assert isinstance(entry.cached_at, float)
        assert entry.cached_at > 0


class TestChildrenCache:
    """Test ChildrenCache functionality."""

    def test_init_valid_max_entries(self):
        """Test cache initialization with valid max_entries."""
        cache = ChildrenCache(max_entries=500)
        assert cache.max_entries == 500

    def test_init_invalid_max_entries(self):
        """Test cache initialization with invalid max_entries."""
        with pytest.raises(ValueError, match="Cache max_entries must be positive"):
            ChildrenCache(max_entries=0)

        with pytest.raises(ValueError, match="Cache max_entries must be positive"):
            ChildrenCache(max_entries=-1)

    def test_get_children_cache_miss(self):
        """Test cache miss when key doesn't exist."""
        cache = ChildrenCache()
        parent_path = Path("/nonexistent/parent.md")

        result = cache.get_children(parent_path)

        assert result is None
        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_get_children_none_path(self):
        """Test get_children with None path."""
        cache = ChildrenCache()

        result = cache.get_children(None)

        assert result is None

    def test_set_and_get_children_basic(self):
        """Test basic cache set and get operations."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [
            {
                "id": "child-1",
                "title": "Child 1",
                "status": "open",
                "kind": "epic",
                "file_path": "/test/child1.md",
            },
            {
                "id": "child-2",
                "title": "Child 2",
                "status": "done",
                "kind": "epic",
                "file_path": "/test/child2.md",
            },
        ]

        # Mock file modification times
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = [
                1234567890.0,
                1234567891.0,
                1234567892.0,
            ]  # parent, child1, child2

            cache.set_children(parent_path, children)

        # Test cache hit
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = [1234567890.0, 1234567891.0, 1234567892.0]  # same mtimes

            result = cache.get_children(parent_path)

        assert result == children
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_set_children_validation(self):
        """Test set_children input validation."""
        cache = ChildrenCache()
        children = [{"id": "child-1", "title": "Child 1"}]

        with pytest.raises(ValueError, match="Parent path cannot be None"):
            cache.set_children(None, children)

        with pytest.raises(ValueError, match="Children list cannot be None"):
            cache.set_children(Path("/test/parent.md"), None)

    def test_cache_invalidation_parent_changed(self):
        """Test cache invalidation when parent file is modified."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1", "file_path": "/test/child1.md"}]

        # Set cache with initial mtime
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = [1234567890.0, 1234567891.0]  # parent, child
            cache.set_children(parent_path, children)

        # Get with changed parent mtime (should invalidate)
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = [1234567999.0, 1234567891.0]  # changed parent, same child
            result = cache.get_children(parent_path)

        assert result is None
        stats = cache.get_stats()
        assert stats["misses"] == 1

    def test_cache_invalidation_child_changed(self):
        """Test cache invalidation when child file is modified."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1", "file_path": "/test/child1.md"}]

        # Set cache with initial mtime
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = [1234567890.0, 1234567891.0]  # parent, child
            cache.set_children(parent_path, children)

        # Get with changed child mtime (should invalidate)
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = [1234567890.0, 1234567999.0]  # same parent, changed child
            result = cache.get_children(parent_path)

        assert result is None
        stats = cache.get_stats()
        assert stats["misses"] == 1

    def test_cache_invalidation_file_deleted(self):
        """Test cache invalidation when files are deleted."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1", "file_path": "/test/child1.md"}]

        # Set cache
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = [1234567890.0, 1234567891.0]
            cache.set_children(parent_path, children)

        # Get with deleted parent file
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = lambda: False  # parent doesn't exist
            result = cache.get_children(parent_path)

        assert result is None

    def test_lru_eviction(self):
        """Test LRU eviction when cache exceeds max_entries."""
        cache = ChildrenCache(max_entries=2)

        # Add three entries (should evict first one)
        for i in range(3):
            parent_path = Path(f"/test/parent{i}.md")
            children = [{"id": f"child-{i}", "title": f"Child {i}"}]

            with (
                patch("os.path.getmtime") as mock_getmtime,
                patch.object(Path, "exists", return_value=True),
            ):
                mock_getmtime.return_value = 1234567890.0 + i
                cache.set_children(parent_path, children)

        # First entry should be evicted
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            result = cache.get_children(Path("/test/parent0.md"))

        assert result is None  # Evicted
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["evictions"] == 1

    def test_lru_access_order_update(self):
        """Test that cache access updates LRU order."""
        cache = ChildrenCache(max_entries=2)

        # Add two entries
        parent1 = Path("/test/parent1.md")
        parent2 = Path("/test/parent2.md")
        children1 = [{"id": "child-1", "title": "Child 1"}]
        children2 = [{"id": "child-2", "title": "Child 2"}]

        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.set_children(parent1, children1)
            cache.set_children(parent2, children2)

        # Access first entry to update its position
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.get_children(parent1)

        # Add third entry (should evict parent2, not parent1)
        parent3 = Path("/test/parent3.md")
        children3 = [{"id": "child-3", "title": "Child 3"}]

        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.set_children(parent3, children3)

        # parent1 should still be cached, parent2 should be evicted
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            assert cache.get_children(parent1) == children1  # Still cached
            assert cache.get_children(parent2) is None  # Evicted

    def test_invalidate_specific_entry(self):
        """Test invalidating a specific cache entry."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1"}]

        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.set_children(parent_path, children)

        cache.invalidate(parent_path)

        result = cache.get_children(parent_path)
        assert result is None

    def test_invalidate_none_path(self):
        """Test invalidate with None path (should not crash)."""
        cache = ChildrenCache()
        cache.invalidate(None)  # Should not raise exception

    def test_clear_cache(self):
        """Test clearing entire cache."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1"}]

        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.set_children(parent_path, children)

        cache.clear()

        result = cache.get_children(parent_path)
        assert result is None
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 1  # From the get_children call above

    def test_cache_stats(self):
        """Test cache statistics reporting."""
        cache = ChildrenCache(max_entries=100)
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1"}]

        # Initial stats
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["max_size"] == 100
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.0

        # Add entry and get stats
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.set_children(parent_path, children)

        stats = cache.get_stats()
        assert stats["size"] == 1

        # Test hit/miss rates
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.get_children(parent_path)  # Hit
            cache.get_children(Path("/nonexistent.md"))  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_thread_safety_concurrent_access(self):
        """Test thread safety with concurrent cache operations."""
        cache = ChildrenCache()
        errors = []

        def cache_operations(thread_id):
            try:
                parent_path = Path(f"/test/parent{thread_id}.md")
                children = [{"id": f"child-{thread_id}", "title": f"Child {thread_id}"}]

                with (
                    patch("os.path.getmtime") as mock_getmtime,
                    patch.object(Path, "exists", return_value=True),
                ):
                    mock_getmtime.return_value = 1234567890.0 + thread_id

                    # Perform multiple operations
                    for _ in range(10):
                        cache.set_children(parent_path, children)
                        result = cache.get_children(parent_path)
                        assert result == children
                        cache.invalidate(parent_path)
            except Exception as e:
                errors.append(e)

        # Run concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_operations, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert not errors, f"Thread safety errors: {errors}"

    def test_cache_validation_error_handling(self):
        """Test cache validation with file system errors."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1", "file_path": "/test/child1.md"}]

        # Set cache successfully
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.set_children(parent_path, children)

        # Get with mtime error (should invalidate cache gracefully)
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = OSError("Permission denied")
            result = cache.get_children(parent_path)

        assert result is None  # Cache should be invalidated due to error

    def test_cache_set_error_handling(self):
        """Test cache set operations with file system errors."""
        cache = ChildrenCache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1", "file_path": "/test/child1.md"}]

        # Set cache with mtime error (should not crash)
        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.side_effect = OSError("Permission denied")

            # Should not raise exception
            cache.set_children(parent_path, children)

        # Cache should be empty due to error
        result = cache.get_children(parent_path)
        assert result is None


class TestGlobalCacheFunctions:
    """Test global cache singleton functions."""

    def setup_method(self):
        """Clear global cache before each test."""
        clear_children_cache()

    def test_get_children_cache_singleton(self):
        """Test global cache singleton pattern."""
        cache1 = get_children_cache()
        cache2 = get_children_cache()

        assert cache1 is cache2  # Same instance
        assert cache1.max_entries == 1000  # Default value

    def test_get_children_cache_custom_size(self):
        """Test global cache with custom max_entries."""
        # First call should use the provided max_entries
        cache = get_children_cache(max_entries=500)
        assert cache.max_entries == 500

        # Subsequent calls should return same instance, ignoring new max_entries
        cache2 = get_children_cache(max_entries=100)
        assert cache2 is cache
        assert cache2.max_entries == 500  # Still uses original value

        # After clearing, new instance with new max_entries
        clear_children_cache()
        cache3 = get_children_cache(max_entries=300)
        assert cache3.max_entries == 300

    def test_clear_children_cache(self):
        """Test clearing global cache."""
        cache = get_children_cache()
        parent_path = Path("/test/parent.md")
        children = [{"id": "child-1", "title": "Child 1"}]

        with (
            patch("os.path.getmtime") as mock_getmtime,
            patch.object(Path, "exists", return_value=True),
        ):
            mock_getmtime.return_value = 1234567890.0
            cache.set_children(parent_path, children)

        clear_children_cache()

        result = cache.get_children(parent_path)
        assert result is None

    def test_get_cache_stats_global(self):
        """Test getting stats from global cache."""
        # No cache initialized
        stats = get_cache_stats()
        assert stats["size"] == 0
        assert stats["max_size"] == 0

        # Initialize cache
        get_children_cache()
        stats = get_cache_stats()
        assert stats["max_size"] == 1000  # Default size
