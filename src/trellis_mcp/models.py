"""Priority ranking utilities for Trellis MCP.

Provides utility functions for converting priority enums to sortable integer ranks.
"""

from typing import Union
from .models.common import Priority


def priority_rank(priority: Union[Priority, str, None]) -> int:
    """Convert priority value to integer rank for sorting.

    Args:
        priority: Priority enum, string value, or None

    Returns:
        Integer rank where lower values indicate higher priority:
        - high: 1
        - normal: 2
        - low: 3
        - None defaults to normal (2)

    Raises:
        ValueError: If priority string is invalid

    Examples:
        >>> priority_rank(Priority.HIGH)
        1
        >>> priority_rank("high")
        1
        >>> priority_rank(None)
        2
    """
    if priority is None:
        return Priority.NORMAL.value

    if isinstance(priority, Priority):
        return priority.value

    if isinstance(priority, str):
        # Use the Priority enum's _missing_ method to handle string conversion
        priority_enum = Priority(priority)
        if priority_enum is None:
            raise ValueError(
                f"Invalid priority string: '{priority}'. " "Must be one of: high, normal, low"
            )
        return priority_enum.value
