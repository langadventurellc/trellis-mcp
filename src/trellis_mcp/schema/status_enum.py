"""Status enumeration for Trellis MCP objects.

Defines the valid status values for objects in their lifecycle.
"""

from enum import Enum


class StatusEnum(str, Enum):
    """Valid status values for objects in the Trellis MCP system.

    Different kinds of objects have different allowed transitions:
    - Task: open → in-progress → review → done, open → done, in-progress → done
    - Feature/Epic/Project: draft → in-progress → done
    """

    OPEN = "open"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    DONE = "done"
    DRAFT = "draft"
    DELETED = "deleted"
