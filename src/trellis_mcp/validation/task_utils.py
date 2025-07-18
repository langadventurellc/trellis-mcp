"""Task-specific utility functions for validation.

This module provides utility functions for working with task objects,
including standalone and hierarchy task detection.
"""

from typing import Any, TypeGuard

from ..schema.kind_enum import KindEnum


def is_standalone_task(
    object_kind_or_task_data: KindEnum | dict[str, Any] | None, parent_id: str | None = None
) -> bool:
    """Check if an object is a standalone task (task with no parent).

    This function supports two call patterns:
    1. is_standalone_task(object_kind, parent_id) - Original signature
    2. is_standalone_task(task_data) - New signature for task data structures

    Note: Standalone tasks are only supported in schema version 1.1.
    Schema version 1.0 tasks must have a parent (hierarchy tasks only).

    Args:
        object_kind_or_task_data: Either a KindEnum or a task data dictionary
        parent_id: The parent ID (None for standalone) - only used with KindEnum

    Returns:
        True if this is a standalone task, False otherwise
    """
    # Handle None case
    if object_kind_or_task_data is None:
        return False

    # Handle the new signature: is_standalone_task(task_data)
    if isinstance(object_kind_or_task_data, dict):
        task_data = object_kind_or_task_data

        if not task_data:
            return False

        # Check if this is a task object
        if task_data.get("kind") != "task":
            return False

        # Check schema version - standalone tasks only supported in 1.1
        schema_version = task_data.get("schema_version", "1.1")
        if schema_version == "1.0":
            return False

        # Check if parent field is None or missing (both indicate standalone)
        parent = task_data.get("parent")
        return parent is None or parent == ""

    # Handle the original signature: is_standalone_task(object_kind, parent_id)
    else:
        object_kind = object_kind_or_task_data
        return object_kind == KindEnum.TASK and parent_id is None


def is_hierarchy_task(task_data: dict[str, Any] | None) -> bool:
    """Check if task data represents a hierarchy task (has parent field).

    Args:
        task_data: Dictionary containing task data structure

    Returns:
        True if the task data represents a hierarchy task, False otherwise

    Note:
        This function examines the task data structure to determine if it's
        a hierarchy task. A hierarchy task has a non-empty parent field.
        Handles edge cases like None/empty data gracefully.
    """
    if not task_data:
        return False

    # Check if this is a task object
    if task_data.get("kind") != "task":
        return False

    # Check if parent field exists and is not None/empty
    parent = task_data.get("parent")
    return parent is not None and parent != ""


def is_standalone_task_guard(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is a standalone task.

    A standalone task is a task object with no parent (parent is None or empty).
    This function provides proper type narrowing for static type checkers.

    Note: Standalone tasks are only supported in schema version 1.1.

    Args:
        obj: The object to check

    Returns:
        True if obj is a standalone task, False otherwise

    Usage:
        if is_standalone_task_guard(task_data):
            # task_data is now narrowed to dict[str, Any] and guaranteed to be a standalone task
            process_standalone_task(task_data)
    """
    if not isinstance(obj, dict):
        return False

    # Check if this is a task object
    if obj.get("kind") != "task":
        return False

    # Check schema version - standalone tasks only supported in 1.1
    schema_version = obj.get("schema_version", "1.1")
    if schema_version == "1.0":
        return False

    # Check if parent field is None or empty (both indicate standalone)
    parent = obj.get("parent")
    return parent is None or parent == ""


def is_hierarchy_task_guard(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is a hierarchy task.

    A hierarchy task is a task object with a parent (parent is not None/empty).
    This function provides proper type narrowing for static type checkers.

    Args:
        obj: The object to check

    Returns:
        True if obj is a hierarchy task, False otherwise

    Usage:
        if is_hierarchy_task_guard(task_data):
            # task_data is now narrowed to dict[str, Any] and guaranteed to be a hierarchy task
            process_hierarchy_task(task_data)
    """
    if not isinstance(obj, dict):
        return False

    # Check if this is a task object
    if obj.get("kind") != "task":
        return False

    # Check if parent field exists and is not None/empty
    parent = obj.get("parent")
    return parent is not None and parent != ""


def validate_standalone_task_with_enhanced_errors(
    task_data: dict[str, Any], project_root: str | Any
) -> None:
    """Enhanced validation for standalone tasks with improved error handling.

    This function provides enhanced validation specifically for standalone tasks,
    using ValidationErrorCollector for better error aggregation and prioritization.
    It integrates with the existing validation system while providing specialized
    error handling for standalone task scenarios.

    Args:
        task_data: The standalone task data dictionary
        project_root: The root directory of the project

    Raises:
        ValueError: If the task_data is not a standalone task
        StandaloneTaskValidationError: If validation fails with context-aware errors
    """
    from pathlib import Path

    from ..exceptions.standalone_task_validation_error import StandaloneTaskValidationError
    from .enhanced_validation import validate_object_data_with_collector

    # Validate that this is actually a standalone task
    if not is_standalone_task_guard(task_data):
        raise ValueError(
            "validate_standalone_task_with_enhanced_errors can only be used with standalone tasks"
        )

    # Convert project_root to Path if it's a string
    if isinstance(project_root, str):
        project_root = Path(project_root)

    # Use enhanced validation with collector
    collector = validate_object_data_with_collector(task_data, project_root)

    if collector.has_errors():
        # Get prioritized errors for standalone task context
        prioritized_errors = collector.get_prioritized_errors()

        # Extract messages and codes
        messages = [msg for msg, _, _ in prioritized_errors]
        error_codes = [code for _, code, _ in prioritized_errors]

        # Get additional context for standalone task errors
        context = collector.get_summary()
        context["task_type"] = "standalone"
        context["validation_context"] = "enhanced_standalone_task_validation"

        # Create standalone task-specific error
        raise StandaloneTaskValidationError(
            errors=messages,
            error_codes=error_codes,
            context=context,
            object_id=task_data.get("id"),
            object_kind="task",
        )


def validate_hierarchy_task_with_enhanced_errors(
    task_data: dict[str, Any], project_root: str | Any
) -> None:
    """Enhanced validation for hierarchy tasks with improved error handling.

    This function provides enhanced validation specifically for hierarchy tasks,
    using ValidationErrorCollector for better error aggregation and prioritization.
    It integrates with the existing validation system while providing specialized
    error handling for hierarchy task scenarios.

    Args:
        task_data: The hierarchy task data dictionary
        project_root: The root directory of the project

    Raises:
        ValueError: If the task_data is not a hierarchy task
        HierarchyTaskValidationError: If validation fails with context-aware errors
    """
    from pathlib import Path

    from ..exceptions.hierarchy_task_validation_error import HierarchyTaskValidationError
    from .enhanced_validation import validate_object_data_with_collector

    # Validate that this is actually a hierarchy task
    if not is_hierarchy_task_guard(task_data):
        raise ValueError(
            "validate_hierarchy_task_with_enhanced_errors can only be used with hierarchy tasks"
        )

    # Convert project_root to Path if it's a string
    if isinstance(project_root, str):
        project_root = Path(project_root)

    # Use enhanced validation with collector
    collector = validate_object_data_with_collector(task_data, project_root)

    if collector.has_errors():
        # Get prioritized errors for hierarchy task context
        prioritized_errors = collector.get_prioritized_errors()

        # Extract messages and codes
        messages = [msg for msg, _, _ in prioritized_errors]
        error_codes = [code for _, code, _ in prioritized_errors]

        # Get additional context for hierarchy task errors
        context = collector.get_summary()
        context["task_type"] = "hierarchy"
        context["validation_context"] = "enhanced_hierarchy_task_validation"

        # Create hierarchy task-specific error
        raise HierarchyTaskValidationError(
            errors=messages,
            error_codes=error_codes,
            context=context,
            object_id=task_data.get("id"),
            object_kind="task",
            parent_id=task_data.get("parent"),
        )
