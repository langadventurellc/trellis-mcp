"""Validation utilities for Trellis MCP objects.

This module provides validation functions for checking object relationships
and constraints beyond basic field validation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .path_resolver import id_to_path
from .id_utils import clean_prerequisite_id
from .schema.kind_enum import KindEnum
from .schema.status_enum import StatusEnum
from .schema.priority_enum import PriorityEnum

# Configure logger for this module
logger = logging.getLogger(__name__)


class CircularDependencyError(ValueError):
    """Exception raised when a circular dependency is detected in prerequisites."""

    def __init__(self, cycle_path: List[str]):
        """Initialize circular dependency error.

        Args:
            cycle_path: List of object IDs that form the cycle
        """
        self.cycle_path = cycle_path
        cycle_str = " -> ".join(cycle_path)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class TrellisValidationError(Exception):
    """Custom validation error that can hold multiple error messages."""

    def __init__(self, errors: List[str]):
        """Initialize validation error.

        Args:
            errors: List of validation error messages
        """
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


def get_all_objects(project_root: str | Path) -> Dict[str, Dict[str, Any]]:
    """Load all objects from the filesystem using glob patterns for resilient discovery.

    Args:
        project_root: The root directory of the project

    Returns:
        Dictionary mapping object IDs to their parsed data

    Raises:
        FileNotFoundError: If the project root doesn't exist
        ValueError: If object parsing fails
    """
    from .object_parser import parse_object

    project_root_path = Path(project_root)
    if not project_root_path.exists():
        raise FileNotFoundError(f"Project root not found: {project_root}")

    objects = {}

    # Use glob patterns to find all object files more efficiently
    patterns = [
        "projects/P-*/project.md",  # Projects
        "projects/P-*/epics/E-*/epic.md",  # Epics
        "projects/P-*/epics/E-*/features/F-*/feature.md",  # Features
        "projects/P-*/epics/E-*/features/F-*/tasks-open/T-*.md",  # Open tasks
        "projects/P-*/epics/E-*/features/F-*/tasks-done/*-T-*.md",  # Done tasks
    ]

    for pattern in patterns:
        for file_path in project_root_path.glob(pattern):
            try:
                obj = parse_object(file_path)
                objects[obj.id] = obj.model_dump()
            except Exception as e:
                logger.warning(f"Skipping invalid file {file_path}: {e}")
                continue

    return objects


def build_prerequisites_graph(objects: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build an adjacency list representation of the prerequisites graph.

    Args:
        objects: Dictionary mapping object IDs to their data

    Returns:
        Dictionary mapping object IDs to lists of their prerequisites
    """
    graph = {}

    for obj_id, obj_data in objects.items():
        prerequisites = obj_data.get("prerequisites", [])
        # Clean prerequisite IDs using robust prefix removal
        clean_prereqs = [clean_prerequisite_id(prereq) for prereq in prerequisites]

        # Clean our own ID too
        clean_obj_id = clean_prerequisite_id(obj_id)

        graph[clean_obj_id] = clean_prereqs

    return graph


def detect_cycle_dfs(graph: Dict[str, List[str]]) -> Optional[List[str]]:
    """Detect cycles in the prerequisites graph using DFS.

    Args:
        graph: Adjacency list representation of the graph

    Returns:
        List of node IDs forming a cycle, or None if no cycle exists
    """
    visited = set()
    recursion_stack = set()

    def dfs(node: str, path: List[str]) -> Optional[List[str]]:
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
                return cycle

    return None


def validate_acyclic_prerequisites(project_root: str | Path) -> List[str]:
    """Validate that prerequisites do not form cycles.

    Args:
        project_root: The root directory of the project

    Returns:
        List of validation errors (empty if no cycles)

    Raises:
        CircularDependencyError: If a cycle is detected
    """
    try:
        # Get all objects
        objects = get_all_objects(project_root)

        # Build prerequisites graph
        graph = build_prerequisites_graph(objects)

        # Detect cycles
        cycle = detect_cycle_dfs(graph)

        if cycle:
            raise CircularDependencyError(cycle)

        return []

    except CircularDependencyError:
        # Re-raise circular dependency errors
        raise
    except Exception as e:
        # Return validation error for other issues
        return [f"Error validating prerequisites: {str(e)}"]


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
    parent_id: Optional[str], object_kind: KindEnum, project_root: str | Path
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
    # Projects should not have parents
    if object_kind == KindEnum.PROJECT:
        if parent_id is not None:
            raise ValueError("Projects cannot have parent objects")
        return True

    # All other objects must have parents
    if parent_id is None:
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


def validate_required_fields_per_kind(data: Dict[str, Any], object_kind: KindEnum) -> List[str]:
    """Validate that all required fields are present for a specific object kind.

    Args:
        data: The object data dictionary
        object_kind: The kind of object being validated

    Returns:
        List of missing required fields (empty if all fields are present)
    """
    # Common required fields for all objects
    common_required = {"kind", "id", "status", "title", "created", "updated", "schema_version"}

    # Kind-specific required fields
    kind_specific_required = {
        KindEnum.PROJECT: set(),  # Projects have no additional required fields
        KindEnum.EPIC: {"parent"},  # Epics require parent
        KindEnum.FEATURE: {"parent"},  # Features require parent
        KindEnum.TASK: {"parent"},  # Tasks require parent
    }

    # Get all required fields for this kind
    required_fields = common_required | kind_specific_required.get(object_kind, set())

    # Check for missing fields
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    return missing_fields


def validate_enum_membership(data: Dict[str, Any]) -> List[str]:
    """Validate that enum fields have valid values.

    Args:
        data: The object data dictionary

    Returns:
        List of validation errors (empty if all enums are valid)
    """
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
            PriorityEnum(data["priority"])
        except ValueError:
            valid_priorities = [p.value for p in PriorityEnum]
            errors.append(
                f"Invalid priority '{data['priority']}'. Must be one of: {valid_priorities}"
            )

    return errors


def validate_status_for_kind(status: StatusEnum, object_kind: KindEnum) -> bool:
    """Validate that the status is allowed for the specific object kind.

    Args:
        status: The status to validate
        object_kind: The kind of object

    Returns:
        True if status is valid for the kind, False otherwise

    Raises:
        ValueError: If status is invalid for the kind
    """
    # Define allowed statuses per kind
    allowed_statuses = {
        KindEnum.PROJECT: {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE},
        KindEnum.EPIC: {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE},
        KindEnum.FEATURE: {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE},
        KindEnum.TASK: {
            StatusEnum.OPEN,
            StatusEnum.IN_PROGRESS,
            StatusEnum.REVIEW,
            StatusEnum.DONE,
        },
    }

    valid_statuses = allowed_statuses.get(object_kind, set())

    if status not in valid_statuses:
        valid_values = ", ".join(s.value for s in valid_statuses)
        raise ValueError(
            f"Invalid status '{status.value}' for {object_kind.value.lower()}. "
            f"Must be one of: {valid_values}"
        )

    return True


def validate_object_data(data: Dict[str, Any], project_root: str | Path) -> None:
    """Comprehensive validation of object data.

    Validates required fields, enum membership, and parent existence.

    Args:
        data: The object data dictionary
        project_root: The root directory of the project

    Raises:
        TrellisValidationError: If validation fails
    """
    errors = []

    # Get object kind
    kind_value = data.get("kind")
    if not kind_value:
        errors.append("Missing 'kind' field")
        raise TrellisValidationError(errors)

    try:
        object_kind = KindEnum(kind_value)
    except ValueError:
        errors.append(f"Invalid kind '{kind_value}'")
        raise TrellisValidationError(errors)

    # Validate required fields
    missing_fields = validate_required_fields_per_kind(data, object_kind)
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(missing_fields)}")

    # Validate enum membership
    enum_errors = validate_enum_membership(data)
    errors.extend(enum_errors)

    # Validate parent existence (if we have all required data)
    if "parent" in data:
        try:
            validate_parent_exists_for_object(data["parent"], object_kind, project_root)
        except ValueError as e:
            errors.append(str(e))

    # Validate status for kind
    if "status" in data:
        try:
            status = StatusEnum(data["status"])
            validate_status_for_kind(status, object_kind)
        except ValueError as e:
            errors.append(str(e))

    # Raise exception if any errors were found
    if errors:
        raise TrellisValidationError(errors)
