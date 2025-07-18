"""Core validation functions for Trellis MCP objects.

This module provides the main validation orchestration functions that
coordinate all aspects of object validation.
"""

from pathlib import Path
from typing import Any

from .task_utils import is_standalone_task


def validate_object_data(data: dict[str, Any], project_root: str | Path) -> None:
    """Comprehensive validation of object data with enhanced error handling.

    This function now uses ValidationErrorCollector for better error aggregation
    and prioritization, especially for standalone tasks. It maintains backward
    compatibility by converting ValidationError to TrellisValidationError.

    Args:
        data: The object data dictionary
        project_root: The root directory of the project

    Raises:
        TrellisValidationError: If validation fails (legacy compatibility maintained)
    """
    from ..exceptions.validation_error import ValidationError
    from .enhanced_validation import validate_object_data_enhanced
    from .exceptions import TrellisValidationError

    try:
        # Use enhanced validation for better error handling
        validate_object_data_enhanced(data, project_root)
    except ValidationError as e:
        # Convert ValidationError to TrellisValidationError for backward compatibility
        raise TrellisValidationError(e.errors)


def validate_standalone_task_data(data: dict[str, Any], project_root: str | Path) -> None:
    """Enhanced validation specifically for standalone tasks.

    This function provides specialized validation for standalone tasks with
    context-aware error messages and prioritization. It uses ValidationErrorCollector
    to aggregate and prioritize errors specific to standalone task validation.

    Args:
        data: The standalone task data dictionary
        project_root: The root directory of the project

    Raises:
        StandaloneTaskValidationError: If validation fails with standalone task context
    """
    from ..exceptions.standalone_task_validation_error import StandaloneTaskValidationError
    from .enhanced_validation import validate_object_data_with_collector

    # Validate that this is actually a standalone task
    if not is_standalone_task(data):
        raise ValueError("validate_standalone_task_data can only be used with standalone tasks")

    # Use enhanced validation with collector
    collector = validate_object_data_with_collector(data, project_root)

    if collector.has_errors():
        # Get prioritized errors for standalone task context
        prioritized_errors = collector.get_prioritized_errors()

        # Extract messages and codes
        messages = [msg for msg, _, _ in prioritized_errors]
        error_codes = [code for _, code, _ in prioritized_errors]

        # Get additional context for standalone task errors
        context = collector.get_summary()
        context["task_type"] = "standalone"

        # Create standalone task-specific error
        raise StandaloneTaskValidationError(
            errors=messages,
            error_codes=error_codes,
            context=context,
            object_id=data.get("id"),
            object_kind="task",
        )
