"""Exceptions package for Trellis MCP.

Contains custom exception classes used throughout the system.
"""

from .cascade_error import CascadeError
from .claiming_errors import (
    InvalidParameterCombinationError,
    MutualExclusivityError,
    ParameterFormatError,
    ParameterValidationError,
)
from .hierarchy_task_validation_error import HierarchyTaskValidationError
from .invalid_status_for_completion import InvalidStatusForCompletion
from .no_available_task import NoAvailableTask
from .prerequisites_not_complete import PrerequisitesNotComplete
from .protected_object_error import ProtectedObjectError
from .standalone_task_validation_error import StandaloneTaskValidationError
from .validation_error import ValidationError, ValidationErrorCode

__all__ = [
    "CascadeError",
    "HierarchyTaskValidationError",
    "InvalidParameterCombinationError",
    "InvalidStatusForCompletion",
    "MutualExclusivityError",
    "NoAvailableTask",
    "ParameterFormatError",
    "ParameterValidationError",
    "PrerequisitesNotComplete",
    "ProtectedObjectError",
    "StandaloneTaskValidationError",
    "ValidationError",
    "ValidationErrorCode",
]
