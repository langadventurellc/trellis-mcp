"""Type utilities for Trellis MCP.

This module provides type guard functions using typing.TypeGuard for proper
type narrowing and runtime type checking of Trellis MCP objects.
"""

from typing import Any, TypeGuard

from .schema.kind_enum import KindEnum


def is_standalone_task(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is a standalone task.

    A standalone task is a task object with no parent (parent is None or empty).

    Args:
        obj: The object to check

    Returns:
        True if obj is a standalone task, False otherwise

    Usage:
        if is_standalone_task(task_data):
            # task_data is now narrowed to dict[str, Any] and guaranteed to be a standalone task
            process_standalone_task(task_data)
    """
    if not isinstance(obj, dict):
        return False

    # Check if this is a task object
    if obj.get("kind") != "task":
        return False

    # Check if parent field is None or empty (both indicate standalone)
    parent = obj.get("parent")
    return parent is None or parent == ""


def is_hierarchy_task(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is a hierarchy task.

    A hierarchy task is a task object with a parent (parent is not None/empty).

    Args:
        obj: The object to check

    Returns:
        True if obj is a hierarchy task, False otherwise

    Usage:
        if is_hierarchy_task(task_data):
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


def is_project_object(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is a project object.

    Args:
        obj: The object to check

    Returns:
        True if obj is a project object, False otherwise

    Usage:
        if is_project_object(data):
            # data is now narrowed to dict[str, Any] and guaranteed to be a project
            process_project(data)
    """
    if not isinstance(obj, dict):
        return False

    return obj.get("kind") == KindEnum.PROJECT.value


def is_epic_object(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is an epic object.

    Args:
        obj: The object to check

    Returns:
        True if obj is an epic object, False otherwise

    Usage:
        if is_epic_object(data):
            # data is now narrowed to dict[str, Any] and guaranteed to be an epic
            process_epic(data)
    """
    if not isinstance(obj, dict):
        return False

    return obj.get("kind") == KindEnum.EPIC.value


def is_feature_object(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is a feature object.

    Args:
        obj: The object to check

    Returns:
        True if obj is a feature object, False otherwise

    Usage:
        if is_feature_object(data):
            # data is now narrowed to dict[str, Any] and guaranteed to be a feature
            process_feature(data)
    """
    if not isinstance(obj, dict):
        return False

    return obj.get("kind") == KindEnum.FEATURE.value


def is_task_object(obj: Any) -> TypeGuard[dict[str, Any]]:
    """Type guard to check if an object is a task object.

    Args:
        obj: The object to check

    Returns:
        True if obj is a task object, False otherwise

    Usage:
        if is_task_object(data):
            # data is now narrowed to dict[str, Any] and guaranteed to be a task
            process_task(data)
    """
    if not isinstance(obj, dict):
        return False

    return obj.get("kind") == KindEnum.TASK.value
