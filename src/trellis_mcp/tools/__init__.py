"""Tools package for Trellis MCP.

Contains individual FastMCP tool functions extracted from the monolithic server module.
Each tool is implemented in its own module following the one-export-per-file principle.

Import pattern for future tool modules:
    from .tool_name import tool_function

Tools will be added to this package as they are extracted from server.py.
"""

from .claim_next_task import create_claim_next_task_tool
from .complete_task import create_complete_task_tool
from .create_object import create_create_object_tool
from .get_next_reviewable_task import create_get_next_reviewable_task_tool
from .get_object import create_get_object_tool
from .health_check import create_health_check_tool
from .list_backlog import create_list_backlog_tool
from .update_object import create_update_object_tool

# from .claim_next_task import claimNextTask
# from .complete_task import completeTask
# from .get_next_reviewable_task import getNextReviewableTask

__all__ = [
    # Tool exports will be added here as tools are extracted
    "create_health_check_tool",
    "create_create_object_tool",
    "create_get_object_tool",
    "create_list_backlog_tool",
    "create_update_object_tool",
    "create_claim_next_task_tool",
    "create_complete_task_tool",
    "create_get_next_reviewable_task_tool",
    # "completeTask",
    # "getNextReviewableTask",
]
