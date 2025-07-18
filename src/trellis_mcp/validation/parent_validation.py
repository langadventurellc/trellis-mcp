"""Parent validation functions for object relationships.

This module provides functions to validate parent-child relationships
in the Trellis MCP object hierarchy.

With schema v1.1, tasks can have optional parent relationships, supporting both:
- Traditional hierarchy-based tasks with required parent feature IDs
- Standalone tasks that exist independently (parent=None)
"""

import os
from pathlib import Path

from ..id_utils import clean_prerequisite_id
from ..path_resolver import id_to_path
from ..schema.kind_enum import KindEnum
from .task_utils import is_standalone_task


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
