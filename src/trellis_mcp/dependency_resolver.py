"""Task dependency resolution logic for Trellis MCP.

This module provides functionality to determine if a task is unblocked
by checking the completion status of all its prerequisites.
"""

from pathlib import Path
from typing import Any, cast

from .id_utils import clean_prerequisite_id
from .schema.task import TaskModel
from .validation import get_all_objects


def is_unblocked(task: TaskModel, project_root: str | Path = ".") -> bool:
    """Check if a task is unblocked by verifying all prerequisites are completed.

    A task is considered unblocked if all of its prerequisites have a status of "done".
    If any prerequisite is missing or has a status other than "done", the task is blocked.

    Args:
        task: The TaskModel to check for prerequisite completion
        project_root: The root directory of the project (default: current directory)

    Returns:
        bool: True if all prerequisites are done (or no prerequisites exist),
              False if any prerequisite is incomplete or missing

    Raises:
        Exception: If there's an error loading objects from the filesystem
    """
    if not task.prerequisites:
        # No prerequisites means task is unblocked
        return True

    # Load all objects to check prerequisite status
    all_objects = cast(dict[str, dict[str, Any]], get_all_objects(project_root))

    # Check each prerequisite
    for prereq_id in task.prerequisites:
        # Clean prerequisite ID to match how objects are stored in all_objects
        clean_prereq_id = clean_prerequisite_id(prereq_id)

        # Check if prerequisite exists
        if clean_prereq_id not in all_objects:
            # Missing prerequisite means task is blocked
            return False

        # Check prerequisite status
        prereq_status = all_objects[clean_prereq_id].get("status", "")
        if prereq_status != "done":
            # Incomplete prerequisite means task is blocked
            return False

    # All prerequisites are completed
    return True
