"""Query utilities for Trellis MCP objects.

Provides functions to query and filter objects based on their properties.
"""

from pathlib import Path

from .scanner import scan_tasks
from .schema.base_schema import BaseSchemaModel
from .schema.status_enum import StatusEnum
from .schema.task import TaskModel


def is_reviewable(obj: BaseSchemaModel) -> bool:
    """Check if an object is in reviewable state.

    Args:
        obj: The object to check (any Trellis MCP object model)

    Returns:
        True if the object has status 'review', False otherwise

    Note:
        Only tasks can have 'review' status according to the Trellis MCP schema.
        For other object types (projects, epics, features), this will always return False.
    """
    return obj.status == StatusEnum.REVIEW


def get_oldest_review(project_root: Path) -> TaskModel | None:
    """Get the oldest reviewable task by updated timestamp with priority tiebreaker.

    Scans all tasks across both hierarchical and standalone task structures and returns
    the task in 'review' status that has the oldest 'updated' timestamp. If multiple
    tasks have the same timestamp, priority is used as a tiebreaker (high > normal > low).

    Args:
        project_root: Root directory of the planning structure (e.g., ./planning)

    Returns:
        TaskModel instance of the oldest reviewable task, or None if no reviewable tasks exist

    Note:
        - Scans both hierarchical tasks (planning/projects/.../tasks-open) and standalone tasks
          (planning/tasks-open)
        - Ordering: oldest updated timestamp first, then priority (high=1, normal=2, low=3)
        - Skips files that cannot be parsed (malformed YAML, invalid schema)
    """
    reviewable_tasks: list[TaskModel] = []

    # scan_tasks expects the project root that contains the planning directory,
    # but this function receives the planning directory itself
    # So we need to get the parent directory
    actual_project_root = project_root.parent

    # Use the existing scan_tasks function to get all tasks (both hierarchical and standalone)
    for task in scan_tasks(actual_project_root):
        if is_reviewable(task):
            reviewable_tasks.append(task)

    # Return None if no reviewable tasks found
    if not reviewable_tasks:
        return None

    # Sort by updated timestamp (oldest first), then by priority (higher priority first)
    # Priority: HIGH=1, NORMAL=2, LOW=3, so lower values have higher priority
    reviewable_tasks.sort(key=lambda task: (task.updated, task.priority))

    return reviewable_tasks[0]
