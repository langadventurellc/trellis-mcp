"""Graph operations for dependency management.

This module provides core graph manipulation functions for building and
analyzing dependency graphs from Trellis MCP objects.
"""

import logging
from pathlib import Path
from typing import Any

from .benchmark import PerformanceBenchmark
from .object_loader import get_all_objects

# Configure logger for this module
logger = logging.getLogger(__name__)


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
    from ..id_utils import clean_prerequisite_id

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
    from ..id_utils import clean_prerequisite_id

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
