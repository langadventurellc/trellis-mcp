"""Tests for InferenceCache in the Kind Inference Engine.

This module provides comprehensive tests for the LRU cache implementation
including performance validation, thread safety, file modification tracking,
and integration with the validation system.
"""

import os
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.trellis_mcp.inference.cache import (
    InferenceCache,
    InferenceResult,
    clear_inference_cache,
    get_cache_stats,
    get_inference_cache,
)
from src.trellis_mcp.inference.path_builder import PathBuilder
from src.trellis_mcp.inference.validator import ValidationResult


class TestInferenceResult:
    """Test InferenceResult dataclass."""

    def test_create_inference_result(self):
        """Test creation of inference result with current timestamp."""
        object_id = "T-test-auth"
        inferred_kind = "task"
        is_valid = True
        validation_result = ValidationResult.success()

        result = InferenceResult.create(
            object_id=object_id,
            inferred_kind=inferred_kind,
            is_valid=is_valid,
            validation_result=validation_result,
        )

        assert result.object_id == object_id
        assert result.inferred_kind == inferred_kind
        assert result.is_valid is True
        assert result.validation_result == validation_result
        assert isinstance(result.cached_at, float)
        assert result.cached_at <= time.time()

    def test_create_inference_result_without_validation(self):
        """Test creation of inference result without validation result."""
        result = InferenceResult.create(
            object_id="F-user-auth",
            inferred_kind="feature",
            is_valid=False,
        )

        assert result.object_id == "F-user-auth"
        assert result.inferred_kind == "feature"
        assert result.is_valid is False
        assert result.validation_result is None
        assert isinstance(result.cached_at, float)


class TestInferenceCache:
    """Test InferenceCache LRU implementation."""

    def test_cache_initialization(self):
        """Test cache initialization with default parameters."""
        cache = InferenceCache()

        assert cache.max_size == 1000
        assert cache.path_builder is None
        assert cache.get_stats()["size"] == 0

    def test_cache_initialization_custom_size(self):
        """Test cache initialization with custom max size."""
        cache = InferenceCache(max_size=500)

        assert cache.max_size == 500
        assert cache.get_stats()["max_size"] == 500

    def test_cache_initialization_invalid_size(self):
        """Test cache initialization with invalid max size."""
        with pytest.raises(ValueError, match="Cache max_size must be positive"):
            InferenceCache(max_size=0)

        with pytest.raises(ValueError, match="Cache max_size must be positive"):
            InferenceCache(max_size=-10)

    def test_cache_put_and_get(self):
        """Test basic cache put and get operations."""
        cache = InferenceCache()
        result = InferenceResult.create("T-auth", "task", True)

        cache.put("T-auth", result)
        cached_result = cache.get("T-auth")

        assert cached_result is not None
        assert cached_result.object_id == "T-auth"
        assert cached_result.inferred_kind == "task"
        assert cached_result.is_valid is True

    def test_cache_miss(self):
        """Test cache miss for non-existent key."""
        cache = InferenceCache()

        result = cache.get("T-nonexistent")

        assert result is None

    def test_cache_put_empty_object_id(self):
        """Test cache put with empty object ID."""
        cache = InferenceCache()
        result = InferenceResult.create("T-auth", "task", True)

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            cache.put("", result)

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            cache.put("   ", result)

    def test_cache_put_none_result(self):
        """Test cache put with None result."""
        cache = InferenceCache()

        with pytest.raises(ValueError, match="InferenceResult cannot be None"):
            cache.put("T-auth", None)  # type: ignore

    def test_cache_get_empty_object_id(self):
        """Test cache get with empty object ID."""
        cache = InferenceCache()

        assert cache.get("") is None
        assert cache.get("   ") is None

    def test_lru_eviction_behavior(self):
        """Test LRU eviction when cache exceeds max size."""
        cache = InferenceCache(max_size=3)

        # Fill cache to capacity
        result1 = InferenceResult.create("T-auth1", "task", True)
        result2 = InferenceResult.create("T-auth2", "task", True)
        result3 = InferenceResult.create("T-auth3", "task", True)

        cache.put("T-auth1", result1)
        cache.put("T-auth2", result2)
        cache.put("T-auth3", result3)

        assert cache.get_stats()["size"] == 3

        # Add fourth item - should evict least recently used (T-auth1)
        result4 = InferenceResult.create("T-auth4", "task", True)
        cache.put("T-auth4", result4)

        assert cache.get_stats()["size"] == 3
        assert cache.get("T-auth1") is None  # Evicted
        assert cache.get("T-auth2") is not None
        assert cache.get("T-auth3") is not None
        assert cache.get("T-auth4") is not None

    def test_lru_access_order_update(self):
        """Test that accessing an item updates its position in LRU order."""
        cache = InferenceCache(max_size=3)

        result1 = InferenceResult.create("T-auth1", "task", True)
        result2 = InferenceResult.create("T-auth2", "task", True)
        result3 = InferenceResult.create("T-auth3", "task", True)

        cache.put("T-auth1", result1)
        cache.put("T-auth2", result2)
        cache.put("T-auth3", result3)

        # Access T-auth1 to move it to end of LRU order
        cache.get("T-auth1")

        # Add fourth item - should evict T-auth2 (now oldest)
        result4 = InferenceResult.create("T-auth4", "task", True)
        cache.put("T-auth4", result4)

        assert cache.get("T-auth1") is not None  # Still present
        assert cache.get("T-auth2") is None  # Evicted
        assert cache.get("T-auth3") is not None
        assert cache.get("T-auth4") is not None

    def test_cache_update_existing_entry(self):
        """Test updating an existing cache entry."""
        cache = InferenceCache()
        result1 = InferenceResult.create("T-auth", "task", True)
        result2 = InferenceResult.create("T-auth", "task", False)

        cache.put("T-auth", result1)
        cached_result = cache.get("T-auth")
        assert cached_result is not None
        assert cached_result.is_valid is True

        cache.put("T-auth", result2)
        cached_result = cache.get("T-auth")
        assert cached_result is not None
        assert cached_result.is_valid is False
        assert cache.get_stats()["size"] == 1  # Size unchanged

    def test_cache_invalidate(self):
        """Test selective cache invalidation."""
        cache = InferenceCache()
        result1 = InferenceResult.create("T-auth1", "task", True)
        result2 = InferenceResult.create("T-auth2", "task", True)

        cache.put("T-auth1", result1)
        cache.put("T-auth2", result2)

        assert cache.get_stats()["size"] == 2

        cache.invalidate("T-auth1")

        assert cache.get("T-auth1") is None
        assert cache.get("T-auth2") is not None
        assert cache.get_stats()["size"] == 1

    def test_cache_invalidate_nonexistent(self):
        """Test invalidating non-existent cache entry."""
        cache = InferenceCache()

        # Should not raise exception
        cache.invalidate("T-nonexistent")
        cache.invalidate("")
        cache.invalidate("   ")

    def test_cache_clear(self):
        """Test clearing entire cache."""
        cache = InferenceCache()
        result1 = InferenceResult.create("T-auth1", "task", True)
        result2 = InferenceResult.create("T-auth2", "task", True)

        cache.put("T-auth1", result1)
        cache.put("T-auth2", result2)

        assert cache.get_stats()["size"] == 2

        cache.clear()

        assert cache.get_stats()["size"] == 0
        assert cache.get("T-auth1") is None
        assert cache.get("T-auth2") is None

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = InferenceCache(max_size=2)
        result = InferenceResult.create("T-auth", "task", True)

        # Initial stats
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.0

        # Cache miss
        cache.get("T-nonexistent")
        stats = cache.get_stats()
        assert stats["misses"] == 1

        # Cache put and hit
        cache.put("T-auth", result)
        cache.get("T-auth")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["hit_rate"] == 0.5  # 1 hit, 1 miss

        # Test eviction tracking
        result2 = InferenceResult.create("T-auth2", "task", True)
        result3 = InferenceResult.create("T-auth3", "task", True)
        cache.put("T-auth2", result2)
        cache.put("T-auth3", result3)  # Should trigger eviction

        stats = cache.get_stats()
        assert stats["evictions"] == 1


class TestInferenceCacheFileValidation:
    """Test cache validation with file modification times."""

    def test_cache_without_path_builder(self):
        """Test cache behavior without PathBuilder (time-based expiration)."""
        cache = InferenceCache()
        result = InferenceResult.create("T-auth", "task", True)

        # Mock cached_at to be recent
        result.cached_at = time.time() - 30  # 30 seconds ago

        cache.put("T-auth", result)
        cached_result = cache.get("T-auth")

        assert cached_result is not None  # Should be valid (< 60 seconds)

    def test_cache_with_expired_entry(self):
        """Test cache behavior with expired entry (no PathBuilder)."""
        cache = InferenceCache()
        result = InferenceResult.create("T-auth", "task", True)

        # Mock cached_at to be old
        result.cached_at = time.time() - 120  # 2 minutes ago

        cache.put("T-auth", result)
        cached_result = cache.get("T-auth")

        assert cached_result is None  # Should be expired

    def test_cache_with_path_builder_file_unchanged(self):
        """Test cache validation with PathBuilder when file is unchanged."""
        with TemporaryDirectory() as temp_dir:
            # Create test project structure
            project_dir = Path(temp_dir) / "planning"
            project_dir.mkdir(parents=True)

            path_builder = PathBuilder(project_dir)
            cache = InferenceCache(path_builder=path_builder)

            # Create a test task file
            task_file = project_dir / "tasks-open" / "T-auth.md"
            task_file.parent.mkdir(parents=True, exist_ok=True)
            task_file.write_text("---\nkind: task\nid: T-auth\n---\nTest task")

            result = InferenceResult.create("T-auth", "task", True)
            result.cached_at = os.path.getmtime(task_file)

            cache.put("T-auth", result)
            cached_result = cache.get("T-auth")

            assert cached_result is not None

    def test_cache_with_path_builder_file_changed(self):
        """Test cache invalidation when file is modified."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "planning"
            project_dir.mkdir(parents=True)

            path_builder = PathBuilder(project_dir)
            cache = InferenceCache(path_builder=path_builder)

            # Create test task file
            task_file = project_dir / "tasks-open" / "T-auth.md"
            task_file.parent.mkdir(parents=True, exist_ok=True)
            task_file.write_text("---\nkind: task\nid: T-auth\n---\nTest task")

            original_mtime = os.path.getmtime(task_file)

            result = InferenceResult.create("T-auth", "task", True)
            result.cached_at = original_mtime

            cache.put("T-auth", result)

            # Modify file
            time.sleep(0.01)  # Ensure timestamp difference
            task_file.write_text("---\nkind: task\nid: T-auth\n---\nModified task")

            cached_result = cache.get("T-auth")

            assert cached_result is None  # Should be invalidated

    def test_cache_with_path_builder_file_deleted(self):
        """Test cache invalidation when file is deleted."""
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "planning"
            project_dir.mkdir(parents=True)

            path_builder = PathBuilder(project_dir)
            cache = InferenceCache(path_builder=path_builder)

            # Create test task file
            task_file = project_dir / "tasks-open" / "T-auth.md"
            task_file.parent.mkdir(parents=True, exist_ok=True)
            task_file.write_text("---\nkind: task\nid: T-auth\n---\nTest task")

            result = InferenceResult.create("T-auth", "task", True)
            result.cached_at = os.path.getmtime(task_file)

            cache.put("T-auth", result)

            # Delete file
            task_file.unlink()

            cached_result = cache.get("T-auth")

            assert cached_result is None  # Should be invalidated


class TestInferenceCacheKindInference:
    """Test kind inference from object IDs."""

    def test_infer_kind_from_project_id(self):
        """Test kind inference for project IDs."""
        cache = InferenceCache()

        assert cache._infer_kind_from_id("P-ecommerce") == "project"
        assert cache._infer_kind_from_id("p-ecommerce") == "project"

    def test_infer_kind_from_epic_id(self):
        """Test kind inference for epic IDs."""
        cache = InferenceCache()

        assert cache._infer_kind_from_id("E-user-auth") == "epic"
        assert cache._infer_kind_from_id("e-user-auth") == "epic"

    def test_infer_kind_from_feature_id(self):
        """Test kind inference for feature IDs."""
        cache = InferenceCache()

        assert cache._infer_kind_from_id("F-login-form") == "feature"
        assert cache._infer_kind_from_id("f-login-form") == "feature"

    def test_infer_kind_from_task_id(self):
        """Test kind inference for task IDs."""
        cache = InferenceCache()

        assert cache._infer_kind_from_id("T-implement-auth") == "task"
        assert cache._infer_kind_from_id("t-implement-auth") == "task"

    def test_infer_kind_from_invalid_id(self):
        """Test kind inference for invalid IDs."""
        cache = InferenceCache()

        assert cache._infer_kind_from_id("invalid-id") is None
        assert cache._infer_kind_from_id("X-unknown") is None
        assert cache._infer_kind_from_id("") is None


class TestInferenceCacheThreadSafety:
    """Test thread safety of cache operations."""

    def test_concurrent_cache_access(self):
        """Test concurrent cache operations from multiple threads."""
        cache = InferenceCache(max_size=100)
        results = {}
        errors = []

        def cache_worker(thread_id: int):
            try:
                for i in range(10):
                    object_id = f"T-thread-{thread_id}-{i}"
                    result = InferenceResult.create(object_id, "task", True)

                    cache.put(object_id, result)
                    cached_result = cache.get(object_id)

                    if cached_result:
                        results[object_id] = cached_result
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors and some results cached
        assert len(errors) == 0
        assert len(results) > 0
        assert cache.get_stats()["size"] > 0

    def test_concurrent_eviction_safety(self):
        """Test thread safety during LRU eviction."""
        cache = InferenceCache(max_size=10)
        errors = []

        def eviction_worker(thread_id: int):
            try:
                for i in range(20):
                    object_id = f"T-evict-{thread_id}-{i}"
                    result = InferenceResult.create(object_id, "task", True)
                    cache.put(object_id, result)
            except Exception as e:
                errors.append(e)

        # Create threads that will trigger evictions
        threads = []
        for i in range(3):
            thread = threading.Thread(target=eviction_worker, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors and cache size is respected
        assert len(errors) == 0
        assert cache.get_stats()["size"] <= 10


class TestInferenceCachePerformance:
    """Test cache performance requirements."""

    def test_cache_hit_performance(self):
        """Test cache hit performance meets < 1ms requirement."""
        cache = InferenceCache()
        result = InferenceResult.create("T-auth", "task", True)

        cache.put("T-auth", result)

        # Measure cache hit performance
        start_time = time.perf_counter()
        for _ in range(1000):
            cache.get("T-auth")
        end_time = time.perf_counter()

        avg_time_ms = (end_time - start_time) * 1000 / 1000
        assert avg_time_ms < 1.0, f"Cache hit average: {avg_time_ms:.3f}ms"

    def test_cache_miss_performance(self):
        """Test cache miss performance meets < 5ms overhead requirement."""
        cache = InferenceCache()

        # Measure cache miss performance
        start_time = time.perf_counter()
        for i in range(100):
            cache.get(f"T-nonexistent-{i}")
        end_time = time.perf_counter()

        avg_time_ms = (end_time - start_time) * 1000 / 100
        assert avg_time_ms < 5.0, f"Cache miss average: {avg_time_ms:.3f}ms"


class TestGlobalCacheFunctions:
    """Test global cache utility functions."""

    def test_get_global_cache(self):
        """Test global cache instance creation."""
        cache1 = get_inference_cache()
        cache2 = get_inference_cache()

        assert cache1 is cache2  # Should be same instance

    def test_clear_global_cache(self):
        """Test clearing global cache."""
        cache = get_inference_cache()
        result = InferenceResult.create("T-auth", "task", True)

        cache.put("T-auth", result)
        assert cache.get("T-auth") is not None

        clear_inference_cache()
        assert cache.get("T-auth") is None

    def test_get_global_cache_stats(self):
        """Test getting global cache statistics."""
        # Clear any existing cache
        clear_inference_cache()

        stats = get_cache_stats()
        assert stats["size"] == 0

        cache = get_inference_cache()
        result = InferenceResult.create("T-auth", "task", True)
        cache.put("T-auth", result)

        stats = get_cache_stats()
        assert stats["size"] == 1

    def test_get_cache_stats_no_cache(self):
        """Test getting cache stats when no cache exists."""
        # Clear any existing cache
        clear_inference_cache()

        # Reset global cache to None
        import src.trellis_mcp.inference.cache as cache_module

        cache_module._inference_cache = None

        stats = get_cache_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
