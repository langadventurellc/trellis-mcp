"""Cycle detection functions for dependency validation.

This module provides high-level cycle detection functions that orchestrate
the graph operations and caching for prerequisite validation.
"""

import logging
from pathlib import Path
from typing import Any

from .benchmark import PerformanceBenchmark
from .cache import _graph_cache
from .exceptions import CircularDependencyError
from .graph_operations import (
    build_dependency_graph_in_memory,
    build_prerequisites_graph,
    detect_cycle_dfs,
)
from .object_loader import get_all_objects

# Configure logger for this module
logger = logging.getLogger(__name__)


def check_prereq_cycles_in_memory(
    project_root: str | Path,
    proposed_object_data: dict[str, Any],
    operation_type: str,
) -> bool:
    """Check if proposed object changes would introduce cycles in prerequisites.

    This function performs in-memory cycle detection by building a dependency graph
    that includes both existing objects and the proposed changes, without writing
    any files to disk.

    Args:
        project_root: The root directory of the project
        proposed_object_data: Dictionary containing the proposed object data
        operation_type: Either "create" or "update" to indicate the operation type

    Returns:
        True if there are no cycles, False if cycles are detected

    Raises:
        CircularDependencyError: If a cycle is detected (for compatibility with existing
            error handling)
    """
    try:
        # Build dependency graph including proposed changes
        graph = build_dependency_graph_in_memory(project_root, proposed_object_data, operation_type)

        # Detect cycles in the combined graph
        cycle = detect_cycle_dfs(graph)

        if cycle:
            # Get all objects for enhanced error context
            from ..utils.id_utils import clean_prerequisite_id

            # Load existing objects and add proposed object for context
            existing_objects = get_all_objects(project_root)
            if isinstance(existing_objects, tuple):
                existing_objects = existing_objects[0]

            # Create combined objects for context (same logic as graph building)
            combined_objects = existing_objects.copy()
            proposed_id = proposed_object_data.get("id")
            if proposed_id:
                clean_proposed_id = clean_prerequisite_id(proposed_id)
                if operation_type == "create":
                    combined_objects[clean_proposed_id] = proposed_object_data
                elif operation_type == "update":
                    if clean_proposed_id in combined_objects:
                        existing_data = combined_objects[clean_proposed_id].copy()
                        existing_data.update(proposed_object_data)
                        combined_objects[clean_proposed_id] = existing_data
                    else:
                        combined_objects[clean_proposed_id] = proposed_object_data

            # Raise enhanced error with object context
            raise CircularDependencyError(cycle, combined_objects)

        return True  # No cycles detected

    except CircularDependencyError:
        # Re-raise circular dependency errors for proper error handling
        raise
    except Exception:
        # For other errors, return False to be conservative
        return False


def validate_acyclic_prerequisites(
    project_root: str | Path, benchmark: PerformanceBenchmark | None = None
) -> list[str]:
    """Validate that prerequisites do not form cycles with optimized caching.

    Args:
        project_root: The root directory of the project
        benchmark: Optional performance benchmark instance

    Returns:
        List of validation errors (empty if no cycles)

    Raises:
        CircularDependencyError: If a cycle is detected
    """
    if benchmark:
        benchmark.start("validate_acyclic_prerequisites")

    try:
        project_root_path = Path(project_root)

        # Try to use cached graph first
        cached_data = _graph_cache.get_cached_graph(project_root_path)

        if cached_data is not None:
            cached_graph, cached_mtimes = cached_data

            # Check if cache is still valid
            if _graph_cache.is_cache_valid(project_root_path, cached_mtimes):
                # Use cached graph
                if benchmark:
                    benchmark.start("cached_cycle_detection")
                cycle = detect_cycle_dfs(cached_graph, benchmark)
                if benchmark:
                    benchmark.end("cached_cycle_detection")

                if cycle:
                    if benchmark:
                        benchmark.end("validate_acyclic_prerequisites")
                    # Load objects for enhanced error context
                    objects = get_all_objects(project_root)
                    if isinstance(objects, tuple):
                        objects = objects[0]
                    raise CircularDependencyError(cycle, objects)

                if benchmark:
                    benchmark.end("validate_acyclic_prerequisites")
                return []

        # Cache miss or invalid - load objects and build graph
        if benchmark:
            benchmark.start("load_objects_and_build_graph")

        result = get_all_objects(project_root, include_mtimes=True)
        if isinstance(result, tuple):
            objects, file_mtimes = result
        else:
            # Should not happen when include_mtimes=True, but handle gracefully
            objects = result
            file_mtimes = {}
        graph = build_prerequisites_graph(objects, benchmark)

        # Cache the new graph
        _graph_cache.cache_graph(project_root_path, graph, file_mtimes)

        if benchmark:
            benchmark.end("load_objects_and_build_graph")

        # Detect cycles
        cycle = detect_cycle_dfs(graph, benchmark)

        if cycle:
            if benchmark:
                benchmark.end("validate_acyclic_prerequisites")
            # Use the loaded objects for enhanced error context
            raise CircularDependencyError(cycle, objects)

        if benchmark:
            benchmark.end("validate_acyclic_prerequisites")
        return []

    except CircularDependencyError:
        # Re-raise circular dependency errors
        if benchmark:
            benchmark.end("validate_acyclic_prerequisites")
        raise
    except Exception as e:
        # Return validation error for other issues
        if benchmark:
            benchmark.end("validate_acyclic_prerequisites")
        return [f"Error validating prerequisites: {str(e)}"]


def check_prereq_cycles(
    project_root: str | Path, benchmark: PerformanceBenchmark | None = None
) -> bool:
    """Check if there are cycles in prerequisites with optimized caching.

    This is a simple boolean wrapper around validate_acyclic_prerequisites.

    Args:
        project_root: The root directory of the project
        benchmark: Optional performance benchmark instance

    Returns:
        True if there are no cycles, False if cycles are detected
    """
    try:
        errors = validate_acyclic_prerequisites(project_root, benchmark)
        return len(errors) == 0  # No cycles if no errors
    except CircularDependencyError:
        return False  # Cycles detected
    except Exception:
        return False  # Other errors (treat as validation failure)
