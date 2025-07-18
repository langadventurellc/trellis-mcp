"""Validation utilities for Trellis MCP objects.

This module provides validation functions for checking object relationships
and constraints beyond basic field validation.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .id_utils import clean_prerequisite_id
from .models.common import Priority
from .path_resolver import id_to_path
from .schema.kind_enum import KindEnum
from .schema.status_enum import StatusEnum

# Configure logger for this module
logger = logging.getLogger(__name__)


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


class PerformanceBenchmark:
    """Utility class for benchmarking cycle detection performance."""

    def __init__(self):
        self.start_time: float | None = None
        self.timings: dict[str, float] = {}

    def start(self, operation: str) -> None:
        """Start timing an operation.

        Args:
            operation: Name of the operation being timed
        """
        self.start_time = time.perf_counter()
        logger.debug(f"Starting benchmark: {operation}")

    def end(self, operation: str) -> float:
        """End timing an operation and record the duration.

        Args:
            operation: Name of the operation being timed

        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            logger.warning(f"No start time recorded for operation: {operation}")
            return 0.0

        duration = time.perf_counter() - self.start_time
        self.timings[operation] = duration
        logger.debug(f"Completed benchmark: {operation} in {duration:.4f}s")
        self.start_time = None
        return duration

    def get_timings(self) -> dict[str, float]:
        """Get all recorded timings.

        Returns:
            Dictionary mapping operation names to durations in seconds
        """
        return self.timings.copy()

    def log_summary(self) -> None:
        """Log a summary of all benchmarked operations."""
        if not self.timings:
            logger.info("No benchmark timings recorded")
            return

        total_time = sum(self.timings.values())
        logger.info(f"Performance Summary (Total: {total_time:.4f}s):")
        for operation, duration in sorted(self.timings.items()):
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            logger.info(f"  {operation}: {duration:.4f}s ({percentage:.1f}%)")


# Global cache instance
_graph_cache = DependencyGraphCache()


class CircularDependencyError(ValueError):
    """Exception raised when a circular dependency is detected in prerequisites."""

    def __init__(self, cycle_path: list[str]):
        """Initialize circular dependency error.

        Args:
            cycle_path: List of object IDs that form the cycle
        """
        self.cycle_path = cycle_path
        cycle_str = " -> ".join(cycle_path)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class TrellisValidationError(Exception):
    """Custom validation error that can hold multiple error messages."""

    def __init__(self, errors: list[str]):
        """Initialize validation error.

        Args:
            errors: List of validation error messages
        """
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


def get_all_objects(project_root: str | Path, include_mtimes: bool = False):
    """Load all objects from the filesystem using glob patterns for resilient discovery.

    Args:
        project_root: The root directory of the project
        include_mtimes: If True, also return file modification times for caching

    Returns:
        Dictionary mapping object IDs to their parsed data, optionally with file mtimes

    Raises:
        FileNotFoundError: If the project root doesn't exist
        ValueError: If object parsing fails
    """
    from .object_parser import parse_object

    project_root_path = Path(project_root)
    if not project_root_path.exists():
        raise FileNotFoundError(f"Project root not found: {project_root}")

    objects: dict[str, dict[str, Any]] = {}
    file_mtimes: dict[str, float] = {}

    # Use glob patterns to find all object files more efficiently
    patterns = [
        "projects/P-*/project.md",  # Projects
        "projects/P-*/epics/E-*/epic.md",  # Epics
        "projects/P-*/epics/E-*/features/F-*/feature.md",  # Features
        "projects/P-*/epics/E-*/features/F-*/tasks-open/T-*.md",  # Open tasks
        "projects/P-*/epics/E-*/features/F-*/tasks-done/*-T-*.md",  # Done tasks
        "tasks-open/T-*.md",  # Standalone open tasks
        "tasks-done/*-T-*.md",  # Standalone done tasks
    ]

    for pattern in patterns:
        for file_path in project_root_path.glob(pattern):
            try:
                obj = parse_object(file_path)
                # Store objects using clean IDs (without prefixes) for consistent lookup
                from .id_utils import clean_prerequisite_id

                clean_id = clean_prerequisite_id(obj.id)
                objects[clean_id] = obj.model_dump()

                # Record file modification time for caching
                if include_mtimes and file_mtimes is not None:
                    file_mtimes[str(file_path)] = os.path.getmtime(file_path)

            except Exception as e:
                logger.warning(f"Skipping invalid file {file_path}: {e}")
                continue

    if include_mtimes:
        return objects, file_mtimes
    return objects


def build_prerequisites_graph(
    objects: dict[str, dict[str, Any]], benchmark: PerformanceBenchmark | None = None
) -> dict[str, list[str]]:
    """Build an adjacency list representation of the prerequisites graph.

    Args:
        objects: Dictionary mapping object IDs to their data
        benchmark: Optional performance benchmark instance

    Returns:
        Dictionary mapping object IDs to lists of their prerequisites
    """
    if benchmark:
        benchmark.start("build_prerequisites_graph")

    graph = {}

    for obj_id, obj_data in objects.items():
        prerequisites = obj_data.get("prerequisites", [])
        # Clean prerequisite IDs using robust prefix removal
        clean_prereqs = [clean_prerequisite_id(prereq) for prereq in prerequisites]

        # Clean our own ID too
        clean_obj_id = clean_prerequisite_id(obj_id)

        graph[clean_obj_id] = clean_prereqs

    if benchmark:
        benchmark.end("build_prerequisites_graph")

    return graph


def detect_cycle_dfs(
    graph: dict[str, list[str]], benchmark: PerformanceBenchmark | None = None
) -> list[str] | None:
    """Detect cycles in the prerequisites graph using DFS.

    Args:
        graph: Adjacency list representation of the graph
        benchmark: Optional performance benchmark instance

    Returns:
        List of node IDs forming a cycle, or None if no cycle exists
    """
    if benchmark:
        benchmark.start("detect_cycle_dfs")

    visited = set()
    recursion_stack = set()

    def dfs(node: str, path: list[str]) -> list[str] | None:
        """Depth-first search to detect cycles.

        Args:
            node: Current node being visited
            path: Current path from root to this node

        Returns:
            List of nodes forming a cycle, or None if no cycle
        """
        if node in recursion_stack:
            # Found back edge - cycle detected
            cycle_start = path.index(node)
            return path[cycle_start:] + [node]

        if node in visited:
            # Already processed, no cycle through this node
            return None

        visited.add(node)
        recursion_stack.add(node)

        # Visit all prerequisites
        for prereq in graph.get(node, []):
            cycle = dfs(prereq, path + [node])
            if cycle:
                return cycle

        recursion_stack.remove(node)
        return None

    # Check all nodes as potential starting points
    for node in graph:
        if node not in visited:
            cycle = dfs(node, [])
            if cycle:
                if benchmark:
                    benchmark.end("detect_cycle_dfs")
                return cycle

    if benchmark:
        benchmark.end("detect_cycle_dfs")
    return None


def build_dependency_graph_in_memory(
    project_root: str | Path,
    proposed_object_data: dict[str, Any],
    operation_type: str,
    benchmark: PerformanceBenchmark | None = None,
) -> dict[str, list[str]]:
    """Build dependency graph in memory including proposed changes without file writes.

    This function simulates the effect of creating or updating an object by building
    a dependency graph that includes both existing objects from the filesystem and
    the proposed object data, allowing cycle detection before any file operations.

    Args:
        project_root: The root directory of the project
        proposed_object_data: Dictionary containing the proposed object data
        operation_type: Either "create" or "update" to indicate the operation type
        benchmark: Optional performance benchmark instance

    Returns:
        Dictionary mapping object IDs to lists of their prerequisites (adjacency list)

    Raises:
        FileNotFoundError: If the project root doesn't exist
        ValueError: If object parsing fails or invalid operation type
    """
    if benchmark:
        benchmark.start("build_dependency_graph_in_memory")

    # Validate operation type
    if operation_type not in ["create", "update"]:
        raise ValueError(f"Invalid operation_type '{operation_type}'. Must be 'create' or 'update'")

    # Get all existing objects from filesystem (no caching for in-memory operations)
    existing_objects = get_all_objects(project_root)

    # Ensure we have objects dictionary (not tuple)
    if isinstance(existing_objects, tuple):
        existing_objects = existing_objects[0]

    # Create a copy to avoid modifying the original
    combined_objects = existing_objects.copy()

    # Get the proposed object ID (cleaned)
    proposed_id = proposed_object_data.get("id")
    if not proposed_id:
        raise ValueError("Proposed object data must include 'id' field")

    # Clean the proposed object ID consistently
    clean_proposed_id = clean_prerequisite_id(proposed_id)

    # Add or update the proposed object in the combined objects
    if operation_type == "create":
        # For create operations, add the new object
        combined_objects[clean_proposed_id] = proposed_object_data
    elif operation_type == "update":
        # For update operations, merge with existing object if it exists
        if clean_proposed_id in combined_objects:
            # Merge the update into the existing object data
            existing_data = combined_objects[clean_proposed_id].copy()
            existing_data.update(proposed_object_data)
            combined_objects[clean_proposed_id] = existing_data
        else:
            # Object doesn't exist yet, treat as create
            combined_objects[clean_proposed_id] = proposed_object_data

    # Build prerequisites graph from combined objects
    graph = build_prerequisites_graph(combined_objects, benchmark)

    if benchmark:
        benchmark.end("build_dependency_graph_in_memory")

    return graph


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
            # Raise the same error type as existing code for compatibility
            raise CircularDependencyError(cycle)

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
                    raise CircularDependencyError(cycle)

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
            raise CircularDependencyError(cycle)

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


def is_standalone_task(
    object_kind_or_task_data: KindEnum | dict[str, Any] | None, parent_id: str | None = None
) -> bool:
    """Check if an object is a standalone task (task with no parent).

    This function supports two call patterns:
    1. is_standalone_task(object_kind, parent_id) - Original signature
    2. is_standalone_task(task_data) - New signature for task data structures

    Args:
        object_kind_or_task_data: Either a KindEnum or a task data dictionary
        parent_id: The parent ID (None for standalone) - only used with KindEnum

    Returns:
        True if this is a standalone task, False otherwise
    """
    # Handle None case
    if object_kind_or_task_data is None:
        return False

    # Handle the new signature: is_standalone_task(task_data)
    if isinstance(object_kind_or_task_data, dict):
        task_data = object_kind_or_task_data

        if not task_data:
            return False

        # Check if this is a task object
        if task_data.get("kind") != "task":
            return False

        # Check if parent field is None or missing (both indicate standalone)
        parent = task_data.get("parent")
        return parent is None or parent == ""

    # Handle the original signature: is_standalone_task(object_kind, parent_id)
    else:
        object_kind = object_kind_or_task_data
        return object_kind == KindEnum.TASK and parent_id is None


def is_hierarchy_task(task_data: dict[str, Any] | None) -> bool:
    """Check if task data represents a hierarchy task (has parent field).

    Args:
        task_data: Dictionary containing task data structure

    Returns:
        True if the task data represents a hierarchy task, False otherwise

    Note:
        This function examines the task data structure to determine if it's
        a hierarchy task. A hierarchy task has a non-empty parent field.
        Handles edge cases like None/empty data gracefully.
    """
    if not task_data:
        return False

    # Check if this is a task object
    if task_data.get("kind") != "task":
        return False

    # Check if parent field exists and is not None/empty
    parent = task_data.get("parent")
    return parent is not None and parent != ""


def validate_parent_exists(parent_id: str, parent_kind: KindEnum, project_root: str | Path) -> bool:
    """Validate that a parent object exists on the filesystem.

    Args:
        parent_id: The ID of the parent object to check (without prefix)
        parent_kind: The kind of parent object (PROJECT, EPIC, or FEATURE)
        project_root: The root directory of the project

    Returns:
        True if the parent object exists, False otherwise

    Raises:
        ValueError: If parent_kind is TASK (tasks cannot be parents)
    """
    if parent_kind == KindEnum.TASK:
        raise ValueError("Tasks cannot be parents of other objects")

    # Use path_resolver to get the expected path for the parent
    try:
        project_root_path = Path(project_root)
        parent_path = id_to_path(project_root_path, parent_kind.value, parent_id)
        return os.path.exists(parent_path)
    except Exception:
        # If path resolution fails, parent doesn't exist
        return False


def validate_parent_exists_for_object(
    parent_id: str | None, object_kind: KindEnum, project_root: str | Path
) -> bool:
    """Validate parent existence for a specific object type.

    Args:
        parent_id: The parent ID to validate (None for projects)
        object_kind: The kind of object being validated
        project_root: The root directory of the project

    Returns:
        True if validation passes, False otherwise

    Raises:
        ValueError: If validation requirements are not met
    """
    # Convert empty string to None for consistency
    if parent_id == "":
        parent_id = None

    # Projects should not have parents
    if object_kind == KindEnum.PROJECT:
        if parent_id is not None:
            raise ValueError("Projects cannot have parent objects")
        return True

    # All other objects must have parents except standalone tasks
    if parent_id is None:
        # Allow standalone tasks (tasks with no parent)
        if is_standalone_task(object_kind, parent_id):
            return True  # Standalone task validation passes
        else:
            raise ValueError(f"{object_kind.value} objects must have a parent")

    # Clean parent ID using robust prefix removal
    clean_parent_id = clean_prerequisite_id(parent_id)

    # Determine expected parent kind
    if object_kind == KindEnum.EPIC:
        parent_kind = KindEnum.PROJECT
    elif object_kind == KindEnum.FEATURE:
        parent_kind = KindEnum.EPIC
    elif object_kind == KindEnum.TASK:
        parent_kind = KindEnum.FEATURE
    else:
        raise ValueError(f"Unknown object kind: {object_kind}")

    # Validate parent exists
    if not validate_parent_exists(clean_parent_id, parent_kind, project_root):
        raise ValueError(f"Parent {parent_kind.value.lower()} with ID '{parent_id}' does not exist")

    return True


def validate_required_fields_per_kind(data: dict[str, Any], object_kind: KindEnum) -> list[str]:
    """Validate that all required fields are present for a specific object kind.

    This function now uses Pydantic schema model validation to detect missing fields
    instead of manual validation logic.

    Args:
        data: The object data dictionary
        object_kind: The kind of object being validated

    Returns:
        List of missing required fields (empty if all fields are present)
    """
    from .schema import get_model_class_for_kind

    try:
        # Get the appropriate Pydantic model class for this kind
        model_class = get_model_class_for_kind(object_kind)

        # Filter data to only include fields that are defined in the model
        model_fields = set(model_class.model_fields.keys())
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Attempt validation to detect missing fields
        model_class.model_validate(filtered_data)

        # If validation succeeds, check for fields that have defaults but should be
        # considered missing (for backward compatibility)
        missing_fields = []
        required_fields_with_defaults = {"schema_version"}
        for field in required_fields_with_defaults:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        return missing_fields

    except ValidationError as e:
        # Extract missing field names from Pydantic validation errors
        missing_fields = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")

            # Check for missing field errors
            if error_type == "missing":
                missing_fields.append(str(field))
            elif (
                error_type == "value_error"
                and "parent" in str(field)
                and "must have a parent" in error.get("msg", "")
            ):
                # Handle parent validation errors as missing fields (for backward compatibility)
                missing_fields.append("parent")
            elif error_type == "enum" and input_value is None and str(field) in ["status"]:
                # Handle None values for required enum fields as missing fields
                missing_fields.append(str(field))

        # Also check for fields that have defaults in Pydantic but were considered
        # required in original logic (for backward compatibility)
        required_fields_with_defaults = {"schema_version"}
        for field in required_fields_with_defaults:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        return missing_fields

    except ValueError:
        # Handle invalid kind from get_model_class_for_kind
        # In this case, we can't validate so return empty list
        # (kind validation is handled elsewhere)
        return []


def validate_enum_membership(data: dict[str, Any]) -> list[str]:
    """Validate that enum fields have valid values.

    This function now uses Pydantic schema model validation to detect invalid enum values
    instead of manual validation logic. Note that this function requires a 'kind' field
    to determine which model to use for validation.

    Args:
        data: The object data dictionary

    Returns:
        List of validation errors (empty if all enums are valid)
    """
    from .schema import get_model_class_for_kind

    # If no kind field, we can't determine which model to use, so fall back to manual validation
    if "kind" not in data:
        return _validate_enum_membership_manual(data)

    try:
        # Get the appropriate Pydantic model class for this kind
        kind_value = data["kind"]
        model_class = get_model_class_for_kind(kind_value)

        # Filter data to only include fields that are defined in the model
        model_fields = set(model_class.model_fields.keys())
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Attempt validation to detect enum errors
        model_class.model_validate(filtered_data)

        # If validation succeeds, no enum errors
        return []

    except ValidationError as e:
        # Extract enum validation errors from Pydantic validation errors
        errors = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")

            # Check for enum validation errors (but skip missing field errors)
            if error_type == "enum" and input_value is not None:
                if "kind" in str(field):
                    valid_kinds = [k.value for k in KindEnum]
                    errors.append(f"Invalid kind '{input_value}'. Must be one of: {valid_kinds}")
                elif "status" in str(field):
                    valid_statuses = [s.value for s in StatusEnum]
                    errors.append(
                        f"Invalid status '{input_value}'. Must be one of: {valid_statuses}"
                    )
                elif "priority" in str(field):
                    valid_priorities = [str(p) for p in Priority]
                    errors.append(
                        f"Invalid priority '{input_value}'. Must be one of: {valid_priorities}"
                    )

        return errors

    except ValueError:
        # Handle invalid kind - fall back to manual validation
        return _validate_enum_membership_manual(data)


def _validate_enum_membership_manual(data: dict[str, Any]) -> list[str]:
    """Manual enum validation fallback when Pydantic validation cannot be used."""
    errors = []

    # Validate kind enum
    if "kind" in data:
        try:
            KindEnum(data["kind"])
        except ValueError:
            valid_kinds = [k.value for k in KindEnum]
            errors.append(f"Invalid kind '{data['kind']}'. Must be one of: {valid_kinds}")

    # Validate status enum
    if "status" in data:
        try:
            StatusEnum(data["status"])
        except ValueError:
            valid_statuses = [s.value for s in StatusEnum]
            errors.append(f"Invalid status '{data['status']}'. Must be one of: {valid_statuses}")

    # Validate priority enum
    if "priority" in data:
        try:
            Priority(data["priority"])
        except ValueError:
            valid_priorities = [str(p) for p in Priority]
            errors.append(
                f"Invalid priority '{data['priority']}'. Must be one of: {valid_priorities}"
            )

    return errors


def validate_priority_field(data: dict[str, Any]) -> list[str]:
    """Validate priority field and set default value if missing.

    This function explicitly validates the priority field in YAML data and
    ensures that the default value 'normal' is set if the field is missing.

    Args:
        data: The object data dictionary (will be modified in-place)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Set default priority if missing
    if "priority" not in data or data["priority"] is None:
        data["priority"] = str(Priority.NORMAL)

    # Validate priority field value
    priority_value = data["priority"]
    try:
        Priority(priority_value)
    except ValueError:
        valid_priorities = [str(p) for p in Priority]
        errors.append(f"Invalid priority '{priority_value}'. Must be one of: {valid_priorities}")

    return errors


def validate_status_for_kind(status: StatusEnum, object_kind: KindEnum) -> bool:
    """Validate that the status is allowed for the specific object kind.

    This function now uses Pydantic schema model validation to check status validity
    instead of hardcoded status sets.

    Args:
        status: The status to validate
        object_kind: The kind of object

    Returns:
        True if status is valid for the kind, False otherwise

    Raises:
        ValueError: If status is invalid for the kind
    """
    from datetime import datetime

    from .schema import get_model_class_for_kind

    try:
        # Get the appropriate Pydantic model class for this kind
        model_class = get_model_class_for_kind(object_kind)

        # Create minimal validation data with all required fields
        validation_data = {
            "kind": object_kind.value,
            "status": status.value,
            "id": "temp-id",
            "title": "temp-title",
            "created": datetime.now(),
            "updated": datetime.now(),
            "schema_version": "1.1",
        }

        # Add parent field for kinds that require it
        if object_kind in [KindEnum.EPIC, KindEnum.FEATURE, KindEnum.TASK]:
            validation_data["parent"] = "temp-parent"

        # Attempt validation - if successful, status is valid
        model_class.model_validate(validation_data)
        return True

    except ValidationError as e:
        # Check if any error is specifically about status validation
        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            msg = error.get("msg", "")

            # If we find a status validation error, re-raise it with proper formatting
            if str(field) == "status" and "Invalid status" in msg:
                # Clean up the error message to match original format
                clean_msg = msg
                if "Value error, " in clean_msg:
                    clean_msg = clean_msg.replace("Value error, ", "")
                # Replace StatusEnum.VALUE with 'value' to match original format
                clean_msg = clean_msg.replace("'StatusEnum.DRAFT'", "'draft'")
                clean_msg = clean_msg.replace("'StatusEnum.OPEN'", "'open'")
                clean_msg = clean_msg.replace("'StatusEnum.IN_PROGRESS'", "'in-progress'")
                clean_msg = clean_msg.replace("'StatusEnum.REVIEW'", "'review'")
                clean_msg = clean_msg.replace("'StatusEnum.DONE'", "'done'")
                raise ValueError(clean_msg)

        # If no status validation errors, the status is valid (other errors are about other fields)
        return True

    except ValueError as e:
        # Handle invalid kind from get_model_class_for_kind or re-raised status validation errors
        raise e


def validate_object_data(data: dict[str, Any], project_root: str | Path) -> None:
    """Comprehensive validation of object data.

    This function now uses Pydantic schema model validation for field validation,
    enum validation, and status validation, while maintaining filesystem-based
    parent existence validation.

    Args:
        data: The object data dictionary
        project_root: The root directory of the project

    Raises:
        TrellisValidationError: If validation fails
    """
    from .schema import get_model_class_for_kind

    errors = []

    # Get object kind (still need to check manually for error handling)
    kind_value = data.get("kind")
    if not kind_value:
        errors.append("Missing 'kind' field")
        raise TrellisValidationError(errors)

    try:
        object_kind = KindEnum(kind_value)
    except ValueError:
        errors.append(f"Invalid kind '{kind_value}'")
        raise TrellisValidationError(errors)

    # Use Pydantic model validation for required fields, enum validation, and status validation
    try:
        model_class = get_model_class_for_kind(object_kind)

        # Filter data to only include fields that are defined in the model
        model_fields = set(model_class.model_fields.keys())
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Attempt validation using Pydantic model
        model_class.model_validate(filtered_data)

    except ValidationError as e:
        # Parse Pydantic validation errors to maintain backward compatibility
        missing_fields = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")
            msg = error.get("msg", "")

            # Handle missing field errors
            if error_type == "missing":
                missing_fields.append(str(field))
            elif (
                error_type == "value_error"
                and "parent" in str(field)
                and "must have a parent" in msg
            ):
                # Handle parent validation errors as missing fields (for backward compatibility)
                missing_fields.append("parent")
            elif error_type == "enum" and input_value is None and str(field) in ["status"]:
                # Handle None values for required enum fields as missing fields
                missing_fields.append(str(field))
            elif error_type == "enum" and input_value is not None:
                # Handle enum validation errors
                if "kind" in str(field):
                    valid_kinds = [k.value for k in KindEnum]
                    errors.append(f"Invalid kind '{input_value}'. Must be one of: {valid_kinds}")
                elif "status" in str(field):
                    valid_statuses = [s.value for s in StatusEnum]
                    errors.append(
                        f"Invalid status '{input_value}'. Must be one of: {valid_statuses}"
                    )
                elif "priority" in str(field):
                    valid_priorities = [str(p) for p in Priority]
                    errors.append(
                        f"Invalid priority '{input_value}'. Must be one of: {valid_priorities}"
                    )
            elif error_type == "value_error":
                # Handle custom validator errors (like status-for-kind validation)
                clean_msg = msg
                if "StatusEnum." in clean_msg:
                    # Clean up the error message format to match original
                    clean_msg = clean_msg.replace("StatusEnum.OPEN", "open")
                    clean_msg = clean_msg.replace("StatusEnum.IN_PROGRESS", "in-progress")
                    clean_msg = clean_msg.replace("StatusEnum.REVIEW", "review")
                    clean_msg = clean_msg.replace("StatusEnum.DONE", "done")
                    clean_msg = clean_msg.replace("StatusEnum.DRAFT", "draft")
                    # Remove "Value error, " prefix
                    if clean_msg.startswith("Value error, "):
                        clean_msg = clean_msg[13:]
                errors.append(clean_msg)
            else:
                # Handle other validation errors
                if field:
                    errors.append(f"Invalid {field}: {msg}")
                else:
                    errors.append(msg)

        # Add missing fields error if any fields are missing
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")

    except ValueError as e:
        # Handle invalid kind from get_model_class_for_kind
        # (shouldn't happen since we validated kind above)
        errors.append(str(e))

    # Validate parent existence (still requires filesystem access)
    # Skip parent validation for standalone tasks - they don't need parent references
    if "parent" in data:
        # Early return: skip parent validation for standalone tasks
        if object_kind == KindEnum.TASK and is_standalone_task(data):
            pass  # Standalone tasks don't require parent validation
        else:
            try:
                validate_parent_exists_for_object(data["parent"], object_kind, project_root)
            except ValueError as e:
                errors.append(str(e))

    # Raise exception if any errors were found
    if errors:
        raise TrellisValidationError(errors)


def enforce_status_transition(
    old: str | StatusEnum, new: str | StatusEnum, kind: str | KindEnum
) -> bool:
    """Enforce status transition rules per lifecycle table.

    Validates that the transition from old status to new status is allowed
    for the given object kind according to the lifecycle specifications.

    This function now delegates to the Pydantic schema model validation
    to maintain centralized transition logic in the schema models.

    Args:
        old: The current status (string or StatusEnum)
        new: The new status to transition to (string or StatusEnum)
        kind: The object kind (string or KindEnum)

    Returns:
        True if the transition is valid

    Raises:
        ValueError: If the transition is invalid for the given kind
    """
    # Import here to avoid circular imports
    from .schema import get_model_class_for_kind

    # Convert string parameters to enums
    if isinstance(old, str):
        try:
            old_status = StatusEnum(old)
        except ValueError:
            raise ValueError(f"Invalid old status '{old}'. Must be a valid StatusEnum value.")
    else:
        old_status = old

    if isinstance(new, str):
        try:
            new_status = StatusEnum(new)
        except ValueError:
            raise ValueError(f"Invalid new status '{new}'. Must be a valid StatusEnum value.")
    else:
        new_status = new

    if isinstance(kind, str):
        try:
            kind_enum = KindEnum(kind)
        except ValueError:
            raise ValueError(f"Invalid kind '{kind}'. Must be a valid KindEnum value.")
    else:
        kind_enum = kind

    # Get the appropriate schema model class for this kind
    try:
        model_class = get_model_class_for_kind(kind_enum)
    except ValueError as e:
        raise ValueError(f"Could not get model class for kind '{kind_enum}': {e}")

    # Delegate to the schema model's transition validation
    return model_class.validate_status_transition(old_status, new_status)


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


def validate_front_matter(yaml_dict: dict[str, Any], kind: str | KindEnum) -> list[str]:
    """Validate front matter for required fields and enum values.

    This function validates YAML front matter using Pydantic schema models.
    It focuses on field presence and enum validation, not parent existence.

    Args:
        yaml_dict: Dictionary containing the parsed YAML front matter
        kind: The object kind (string or KindEnum)

    Returns:
        List of validation error messages (empty if valid)
    """
    from .schema import get_model_class_for_kind

    # Validate priority field and set default value if missing
    priority_errors = validate_priority_field(yaml_dict)

    try:
        # Get the appropriate model class for this kind
        model_class = get_model_class_for_kind(kind)

        # Attempt to validate using Pydantic (filtering to only model fields)
        # Get the model's field names
        model_fields = set(model_class.model_fields.keys())

        # Filter yaml_dict to only include fields that are defined in the model
        filtered_dict = {k: v for k, v in yaml_dict.items() if k in model_fields}
        model_class.model_validate(filtered_dict)

        # If validation succeeds, return only priority errors (if any)
        return priority_errors

    except ValidationError as e:
        # Convert Pydantic validation errors to string list
        errors = []
        missing_fields = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")
            msg = error.get("msg", "")

            # Format error messages to match existing format
            if error_type == "missing":
                # Collect missing fields to group them
                missing_fields.append(str(field))
            elif error_type == "enum":
                # Handle enum validation errors
                # Special case: None values for required enums should be treated as missing fields
                if input_value is None and str(field) in ["status"]:
                    missing_fields.append(str(field))
                elif "kind" in str(field):
                    valid_kinds = [k.value for k in KindEnum]
                    errors.append(f"Invalid kind '{input_value}'. Must be one of: {valid_kinds}")
                elif "status" in str(field):
                    valid_statuses = [s.value for s in StatusEnum]
                    errors.append(
                        f"Invalid status '{input_value}'. Must be one of: {valid_statuses}"
                    )
                elif "priority" in str(field):
                    # Skip priority errors if they were already handled by explicit validation
                    if not priority_errors:
                        valid_priorities = [str(p) for p in Priority]
                        errors.append(
                            f"Invalid priority '{input_value}'. Must be one of: {valid_priorities}"
                        )
                else:
                    errors.append(msg)
            elif error_type == "value_error":
                # Handle custom validator errors
                if "parent" in str(field) and ("must have a parent" in msg):
                    # Treat parent validation errors as missing required fields
                    # to match original behavior
                    missing_fields.append("parent")
                else:
                    # Other value errors (like status-for-kind validation)
                    # Clean up the error message format to match original
                    clean_msg = msg
                    if "StatusEnum." in clean_msg:
                        # Replace StatusEnum.VALUE with just VALUE
                        # (without quotes since they're already in the message)
                        clean_msg = clean_msg.replace("StatusEnum.OPEN", "open")
                        clean_msg = clean_msg.replace("StatusEnum.IN_PROGRESS", "in-progress")
                        clean_msg = clean_msg.replace("StatusEnum.REVIEW", "review")
                        clean_msg = clean_msg.replace("StatusEnum.DONE", "done")
                        clean_msg = clean_msg.replace("StatusEnum.DRAFT", "draft")
                        # Remove "Value error, " prefix
                        if clean_msg.startswith("Value error, "):
                            clean_msg = clean_msg[13:]
                    errors.append(clean_msg)
            else:
                # Handle other validation errors
                if field:
                    errors.append(f"Invalid {field}: {msg}")
                else:
                    errors.append(msg)

        # Add missing fields error if any fields are missing
        if missing_fields:
            errors.insert(0, f"Missing required fields: {', '.join(missing_fields)}")

        # Combine priority validation errors with Pydantic validation errors
        all_errors = priority_errors + errors
        return all_errors

    except ValueError as e:
        # Handle invalid kind from get_model_class_for_kind
        return [str(e)]


def benchmark_cycle_detection(project_root: str | Path, operations: int = 10) -> dict[str, float]:
    """Benchmark cycle detection performance.

    This function runs multiple cycle detection operations to measure performance
    characteristics and identify bottlenecks.

    Args:
        project_root: The root directory of the project
        operations: Number of operations to run for averaging

    Returns:
        Dictionary containing benchmark results with operation timings
    """
    benchmark = PerformanceBenchmark()
    project_root_path = Path(project_root)

    # Clear cache to get true cold performance
    _graph_cache.clear_cache(project_root_path)

    logger.info(f"Starting cycle detection benchmark with {operations} operations")

    # Run cold (no cache) operation
    benchmark.start("cold_cycle_check")
    try:
        check_prereq_cycles(project_root, benchmark)
    except Exception as e:
        logger.warning(f"Cold cycle check failed: {e}")
    benchmark.end("cold_cycle_check")

    # Run warm (cached) operations
    warm_times = []
    for i in range(operations - 1):  # -1 because we already did cold operation
        warm_benchmark = PerformanceBenchmark()
        warm_benchmark.start(f"warm_cycle_check_{i}")
        try:
            check_prereq_cycles(project_root, warm_benchmark)
        except Exception as e:
            logger.warning(f"Warm cycle check {i} failed: {e}")
        warm_time = warm_benchmark.end(f"warm_cycle_check_{i}")
        warm_times.append(warm_time)

    # Calculate statistics
    results = benchmark.get_timings()
    if warm_times:
        results["avg_warm_time"] = sum(warm_times) / len(warm_times)
        results["min_warm_time"] = min(warm_times)
        results["max_warm_time"] = max(warm_times)

        # Calculate cache effectiveness
        cold_time = results.get("cold_cycle_check", 0)
        avg_warm_time = results["avg_warm_time"]
        if cold_time > 0:
            speedup = cold_time / avg_warm_time if avg_warm_time > 0 else 1
            results["cache_speedup_factor"] = speedup
            results["cache_improvement_percent"] = ((cold_time - avg_warm_time) / cold_time) * 100

    # Log summary
    benchmark.log_summary()
    logger.info(f"Cache performance: {results.get('cache_speedup_factor', 1):.1f}x speedup")

    return results


def get_cache_stats() -> dict[str, Any]:
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
