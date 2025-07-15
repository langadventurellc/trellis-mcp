"""Task sorting key utilities for Trellis MCP.

Provides key functions for sorting tasks by priority and creation date.
"""

from datetime import datetime

from ..schema.task import TaskModel
from .priority_ranking import priority_rank


def task_sort_key(task: TaskModel) -> tuple[int, datetime]:
    """Generate sort key for TaskModel objects.

    Generates a tuple sort key with:
    - Primary: Priority rank (high=1, normal=2, low=3) - lower values first
    - Secondary: Creation date - older tasks first

    Args:
        task: TaskModel object to generate sort key for

    Returns:
        Tuple of (priority_rank, created_datetime) for use with sorted()

    Example:
        >>> tasks = [task1, task2, task3]
        >>> sorted_tasks = sorted(tasks, key=task_sort_key)
        >>> # High priority tasks first, then older tasks within same priority
    """
    return (priority_rank(task.priority), task.created)
