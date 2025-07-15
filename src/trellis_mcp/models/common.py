"""Common data models for Trellis MCP.

Contains shared enums and data structures used across the Trellis MCP system.
"""

from enum import IntEnum


class Priority(IntEnum):
    """Priority levels for task sorting and selection.

    Lower integer values indicate higher priority.
    Used for sorting tasks when claiming next available task.
    """

    HIGH = 1
    NORMAL = 2
    LOW = 3
