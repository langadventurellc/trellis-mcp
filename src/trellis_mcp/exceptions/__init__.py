"""Exceptions package for Trellis MCP.

Contains custom exception classes used throughout the system.
"""

from .invalid_status_for_completion import InvalidStatusForCompletion
from .no_available_task import NoAvailableTask
from .prerequisites_not_complete import PrerequisitesNotComplete

__all__ = [
    "InvalidStatusForCompletion",
    "NoAvailableTask",
    "PrerequisitesNotComplete",
]
