"""Exceptions package for Trellis MCP.

Contains custom exception classes used throughout the system.
"""

from .cascade_error import CascadeError
from .invalid_status_for_completion import InvalidStatusForCompletion
from .no_available_task import NoAvailableTask
from .prerequisites_not_complete import PrerequisitesNotComplete
from .protected_object_error import ProtectedObjectError

__all__ = [
    "CascadeError",
    "InvalidStatusForCompletion",
    "NoAvailableTask",
    "PrerequisitesNotComplete",
    "ProtectedObjectError",
]
