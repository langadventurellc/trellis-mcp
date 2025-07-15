"""Query utilities for Trellis MCP objects.

Provides functions to query and filter objects based on their properties.
"""

from pathlib import Path

from .object_parser import parse_object
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

    Scans all tasks across the project hierarchy and returns the task in 'review' status
    that has the oldest 'updated' timestamp. If multiple tasks have the same timestamp,
    priority is used as a tiebreaker (high > normal > low).

    Args:
        project_root: Root directory of the planning structure (e.g., ./planning)

    Returns:
        TaskModel instance of the oldest reviewable task, or None if no reviewable tasks exist

    Note:
        - Only scans tasks-open directories (tasks in review status should be in tasks-open)
        - Ordering: oldest updated timestamp first, then priority (high=1, normal=2, low=3)
        - Skips files that cannot be parsed (malformed YAML, invalid schema)
    """
    reviewable_tasks: list[TaskModel] = []

    # Check if projects directory exists
    projects_dir = project_root / "projects"
    if not projects_dir.exists() or not projects_dir.is_dir():
        return None

    # Scan all projects
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        # Scan epics within this project
        epics_dir = project_dir / "epics"
        if not epics_dir.exists() or not epics_dir.is_dir():
            continue

        for epic_dir in epics_dir.iterdir():
            if not epic_dir.is_dir():
                continue

            # Scan features within this epic
            features_dir = epic_dir / "features"
            if not features_dir.exists() or not features_dir.is_dir():
                continue

            for feature_dir in features_dir.iterdir():
                if not feature_dir.is_dir():
                    continue

                # Scan tasks-open directory within this feature
                tasks_open_dir = feature_dir / "tasks-open"
                if not tasks_open_dir.exists() or not tasks_open_dir.is_dir():
                    continue

                # Load all task files from tasks-open directory
                for task_file in tasks_open_dir.iterdir():
                    if not task_file.is_file() or not task_file.name.endswith(".md"):
                        continue

                    try:
                        # Parse the task file into a TaskModel
                        task_obj = parse_object(task_file)

                        # Ensure it's actually a TaskModel and is reviewable
                        if isinstance(task_obj, TaskModel) and is_reviewable(task_obj):
                            reviewable_tasks.append(task_obj)
                    except Exception:
                        # Skip files that cannot be parsed (malformed YAML, validation errors, etc.)
                        continue

    # Return None if no reviewable tasks found
    if not reviewable_tasks:
        return None

    # Sort by updated timestamp (oldest first), then by priority (higher priority first)
    # Priority: HIGH=1, NORMAL=2, LOW=3, so lower values have higher priority
    reviewable_tasks.sort(key=lambda task: (task.updated, task.priority))

    return reviewable_tasks[0]
