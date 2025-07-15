"""Priority enumeration for Trellis MCP objects.

Defines the valid priority levels for objects in the system.
"""

from enum import Enum


class PriorityEnum(str, Enum):
    """Valid priority levels for objects in the Trellis MCP system.

    Priority determines the order in which tasks are processed.
    Default priority is NORMAL if not specified.
    """

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
