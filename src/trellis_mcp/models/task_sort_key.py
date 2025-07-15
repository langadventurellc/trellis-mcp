"""Task sorting key utilities for Trellis MCP.

Provides key functions for sorting tasks by priority and creation date.
"""

from datetime import datetime

from ..schema.task import TaskModel
from .priority_ranking import priority_rank


def task_sort_key(task: TaskModel) -> tuple[int, datetime]:
    """Generate sort key for TaskModel objects.

    Primary sort by priority rank (high=1, normal=2, low=3), secondary by creation date.

    Args:
        task: TaskModel object to generate sort key for

    Returns:
        Tuple of (priority_rank, created_datetime) for use with sorted()
    """
    return (priority_rank(task.priority), task.created)
