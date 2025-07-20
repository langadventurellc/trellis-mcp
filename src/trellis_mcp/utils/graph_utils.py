"""Dependency graph utilities for Trellis MCP.

This module provides a clean API for building and analyzing dependency graphs
from Trellis MCP object hierarchies. It supports cycle detection to ensure
acyclic prerequisites as required by the Trellis MCP specification.
"""

from pathlib import Path
from typing import Any

from ..validation import (
    build_prerequisites_graph,
    get_all_objects,
)


class DependencyGraph:
    """A dependency graph for Trellis MCP objects.

    This class provides a clean API for building dependency graphs from
    Trellis MCP objects and detecting cycles in prerequisites.
    """

    def __init__(self) -> None:
        """Initialize an empty dependency graph."""
        self._graph: dict[str, list[str]] = {}
        self._objects: dict[str, dict[str, Any]] = {}

    def build(self, project_root: str | Path) -> None:
        """Build the dependency graph by scanning all objects in the project.

        Scans all *.md files in the project, extracts object IDs and prerequisites,
        and builds an adjacency list representation of the dependency graph.

        Args:
            project_root: The root directory of the project

        Raises:
            FileNotFoundError: If the project root doesn't exist
            ValueError: If object parsing fails
        """
        # Load all objects from the filesystem
        objects_result = get_all_objects(project_root)

        # Handle both tuple and dict return types from get_all_objects
        if isinstance(objects_result, tuple):
            self._objects = objects_result[0]
        else:
            self._objects = objects_result

        # Build prerequisites graph from loaded objects
        self._graph = build_prerequisites_graph(self._objects)

    def has_cycle(self) -> bool:
        """Check if the dependency graph contains any cycles.

        Uses Kahn's algorithm (topological sort) to detect cycles in the prerequisite graph.
        If we cannot process all vertices using topological sort, a cycle exists.

        Returns:
            True if a cycle is detected, False otherwise
        """
        if not self._graph:
            return False

        # Calculate in-degree for each vertex
        in_degree = {}

        # Initialize all vertices with in-degree 0
        for vertex in self._graph:
            in_degree[vertex] = 0

        # Calculate actual in-degrees
        for vertex in self._graph:
            for neighbor in self._graph[vertex]:
                # Ensure neighbor exists in in_degree dict
                if neighbor not in in_degree:
                    in_degree[neighbor] = 0
                in_degree[neighbor] += 1

        # Find all vertices with in-degree 0
        queue = [vertex for vertex, degree in in_degree.items() if degree == 0]
        processed_count = 0

        # Process vertices with in-degree 0
        while queue:
            vertex = queue.pop(0)
            processed_count += 1

            # Reduce in-degree for all neighbors
            for neighbor in self._graph.get(vertex, []):
                in_degree[neighbor] -= 1

                # If neighbor's in-degree becomes 0, add to queue
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If we processed all vertices, no cycle exists
        # If we couldn't process all vertices, a cycle exists
        total_vertices = len(in_degree)
        return processed_count < total_vertices

    @property
    def graph(self) -> dict[str, list[str]]:
        """Get the adjacency list representation of the graph.

        Returns:
            Dictionary mapping object IDs to lists of their prerequisites
        """
        return {k: v.copy() for k, v in self._graph.items()}

    @property
    def objects(self) -> dict[str, dict[str, Any]]:
        """Get the objects that were loaded to build the graph.

        Returns:
            Dictionary mapping object IDs to their parsed data
        """
        return {k: v.copy() for k, v in self._objects.items()}
