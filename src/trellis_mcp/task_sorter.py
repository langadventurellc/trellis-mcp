"""Task sorting utilities for Trellis MCP.

Provides utility functions for sorting tasks by priority and creation date.
"""

from typing import List

from .models import priority_rank
from .schema.task import TaskModel


def sort_tasks_by_priority(tasks: List[TaskModel]) -> List[TaskModel]:
    """Sort tasks by priority rank and creation date.

    Sorts tasks using a two-level sort key:
    1. Primary: Priority rank (high=1, normal=2, low=3) - lower values first
    2. Secondary: Creation date - older tasks first

    Args:
        tasks: List of TaskModel objects to sort

    Returns:
        New list of TaskModel objects sorted by priority and creation date.
        Original list is not modified.

    Examples:
        >>> from datetime import datetime
        >>> from trellis_mcp.models.common import Priority
        >>> # Assuming we have TaskModel instances with different priorities
        >>> sorted_tasks = sort_tasks_by_priority(task_list)
        >>> # High priority tasks will come first, then normal, then low
        >>> # Within same priority, older tasks come first
    """
    return sorted(tasks, key=lambda task: (priority_rank(task.priority), task.created))
