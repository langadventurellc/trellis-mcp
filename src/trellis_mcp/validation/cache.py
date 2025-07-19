"""Dependency graph cache for improved performance in validation operations.

This module provides caching functionality for dependency graphs to avoid
redundant file I/O operations when validating prerequisites.
"""

import logging
import os
from pathlib import Path
from typing import TypedDict

# Configure logger for this module
logger = logging.getLogger(__name__)


class CacheStats(TypedDict):
    """Type definition for cache statistics."""

    cached_projects: int
    cache_keys: list[str]


class DependencyGraphCache:
    """Simple cache for dependency graphs with file modification time validation.

    This cache improves performance by avoiding redundant file I/O when
    no objects have changed since the last graph build.
    """

    def __init__(self):
        self._cache: dict[str, tuple[dict[str, list[str]], dict[str, float]]] = {}

    def get_cached_graph(
        self, project_root: Path
    ) -> tuple[dict[str, list[str]], dict[str, float]] | None:
        """Get cached graph if it exists for the project root.

        Args:
            project_root: The project root path

        Returns:
            Tuple of (graph, file_mtimes) if cached, None otherwise
        """
        cache_key = str(project_root)
        return self._cache.get(cache_key)

    def cache_graph(
        self, project_root: Path, graph: dict[str, list[str]], file_mtimes: dict[str, float]
    ) -> None:
        """Cache a dependency graph with its file modification times.

        Args:
            project_root: The project root path
            graph: The dependency graph (adjacency list)
            file_mtimes: Dictionary mapping file paths to modification times
        """
        cache_key = str(project_root)
        self._cache[cache_key] = (graph, file_mtimes)

    def is_cache_valid(self, project_root: Path, cached_mtimes: dict[str, float]) -> bool:
        """Check if cached graph is still valid by comparing file modification times.

        Uses tolerance-based comparison (1ms) to avoid floating point precision
        issues and filesystem timestamp resolution differences across platforms.

        Args:
            project_root: The project root path
            cached_mtimes: Cached file modification times

        Returns:
            True if cache is valid, False if any files have changed
        """
        try:
            # Check if any cached files have been modified
            for file_path, cached_mtime in cached_mtimes.items():
                if not os.path.exists(file_path):
                    # File was deleted
                    return False
                current_mtime = os.path.getmtime(file_path)
                if abs(current_mtime - cached_mtime) > 0.001:
                    # File was modified (using tolerance to avoid float precision issues)
                    return False

            # Check for new files that might have been added
            # This is a simplified check - we'll let the cache miss handle new files
            patterns = [
                "projects/P-*/project.md",
                "projects/P-*/epics/E-*/epic.md",
                "projects/P-*/epics/E-*/features/F-*/feature.md",
                "projects/P-*/epics/E-*/features/F-*/tasks-open/T-*.md",
                "projects/P-*/epics/E-*/features/F-*/tasks-done/*-T-*.md",
            ]

            current_files = set()
            for pattern in patterns:
                for file_path in project_root.glob(pattern):
                    current_files.add(str(file_path))

            cached_files = set(cached_mtimes.keys())

            # If new files were added, cache is invalid
            if current_files != cached_files:
                return False

            return True
        except Exception as e:
            # If anything goes wrong, consider cache invalid
            logger.debug(f"Cache validation failed: {e}")
            return False

    def clear_cache(self, project_root: Path | None = None) -> None:
        """Clear cache for a specific project or all projects.

        Args:
            project_root: Project to clear cache for, or None to clear all
        """
        if project_root:
            cache_key = str(project_root)
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()


# Global cache instance
_graph_cache = DependencyGraphCache()


def get_cache_stats() -> CacheStats:
    """Get statistics about the dependency graph cache.

    Returns:
        Dictionary containing cache statistics
    """
    return {
        "cached_projects": len(_graph_cache._cache),
        "cache_keys": list(_graph_cache._cache.keys()) if _graph_cache._cache else [],
    }


def clear_dependency_cache(project_root: str | Path | None = None) -> None:
    """Clear the dependency graph cache.

    Args:
        project_root: Specific project to clear, or None to clear all
    """
    if project_root:
        _graph_cache.clear_cache(Path(project_root))
    else:
        _graph_cache.clear_cache()
