"""Type utilities for Trellis MCP.

This module provides type guard functions using typing.TypeGuard for proper
type narrowing and runtime type checking of Trellis MCP objects.
It also provides generic type definitions for enhanced type safety with
optional parent relationships and task type discrimination.
"""

from typing import Any, Callable, Literal, TypeGuard, TypeVar

from .schema.kind_enum import KindEnum

# Generic type variables for task types
T = TypeVar("T", bound=dict[str, Any])
StandaloneTaskType = TypeVar("StandaloneTaskType", bound=dict[str, Any])
HierarchyTaskType = TypeVar("HierarchyTaskType", bound=dict[str, Any])

# Type discrimination using Literal types
TaskKind = Literal["task"]
ProjectKind = Literal["project"]
EpicKind = Literal["epic"]
FeatureKind = Literal["feature"]
ObjectKind = Literal["task", "project", "epic", "feature"]

# Generic type for parent relationships
ParentType = TypeVar("ParentType", bound=str | None)

# Generic type for objects with optional parent relationships
OptionalParentObject = TypeVar("OptionalParentObject", bound=dict[str, Any])

# Generic type for task objects with specific parent constraints
TaskWithParent = TypeVar("TaskWithParent", bound=dict[str, Any])
TaskWithoutParent = TypeVar("TaskWithoutParent", bound=dict[str, Any])


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


# Generic type discrimination functions
def is_object_with_kind(obj: Any, kind: ObjectKind) -> TypeGuard[dict[str, Any]]:
    """Generic type guard to check if an object has a specific kind.

    Args:
        obj: The object to check
        kind: The kind to check for

    Returns:
        True if obj has the specified kind, False otherwise

    Usage:
        if is_object_with_kind(data, "task"):
            # data is now narrowed to dict[str, Any] and guaranteed to have kind="task"
            process_object_with_kind(data)
    """
    if not isinstance(obj, dict):
        return False

    return obj.get("kind") == kind


def is_task_with_parent_type(obj: Any, parent_required: bool) -> TypeGuard[dict[str, Any]]:
    """Generic type guard to check if a task object has the required parent type.

    Args:
        obj: The object to check
        parent_required: True if parent is required, False if parent should be None/empty

    Returns:
        True if obj is a task with the correct parent type, False otherwise

    Usage:
        if is_task_with_parent_type(data, True):
            # data is guaranteed to be a hierarchy task
            process_hierarchy_task(data)
        if is_task_with_parent_type(data, False):
            # data is guaranteed to be a standalone task
            process_standalone_task(data)
    """
    if not isinstance(obj, dict):
        return False

    # Check if this is a task object
    if obj.get("kind") != "task":
        return False

    # Check parent field based on requirement
    parent = obj.get("parent")
    if parent_required:
        return parent is not None and parent != ""
    else:
        return parent is None or parent == ""


# Generic factory functions for task objects
def create_task_object_generic(
    task_id: str, title: str, parent: str | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Generic factory function for creating task objects with optional parent.

    Args:
        task_id: Unique identifier for the task
        title: Human-readable title
        parent: Optional parent ID (None for standalone tasks)
        **kwargs: Additional task fields

    Returns:
        Task object dictionary with proper type structure

    Usage:
        standalone_task = create_task_object_generic("T-1", "Task 1")
        hierarchy_task = create_task_object_generic("T-2", "Task 2", "F-feature")
    """
    task_data = {"kind": "task", "id": task_id, "title": title, "parent": parent, **kwargs}
    return task_data


def process_task_generic(task_obj: T, processor_func: Callable[[T], T]) -> T:
    """Generic function for processing task objects while preserving type.

    Args:
        task_obj: Task object to process
        processor_func: Function to apply to the task object

    Returns:
        Processed task object with same type as input

    Usage:
        def add_timestamp(task):
            task["processed_at"] = datetime.now()
            return task

        processed_task = process_task_generic(task_data, add_timestamp)
    """
    if not isinstance(task_obj, dict):
        raise ValueError("task_obj must be a dictionary")

    # Check if this is a task object (without type narrowing)
    if task_obj.get("kind") != "task":
        raise ValueError("task_obj must be a task object")

    return processor_func(task_obj)


# Generic template functions for task type discrimination
def handle_task_by_type(
    task_obj: T, standalone_handler: Callable[[T], T], hierarchy_handler: Callable[[T], T]
) -> T:
    """Generic template function to handle tasks based on their parent type.

    Args:
        task_obj: Task object to handle
        standalone_handler: Function to handle standalone tasks
        hierarchy_handler: Function to handle hierarchy tasks

    Returns:
        Processed task object with same type as input

    Usage:
        def process_standalone(task):
            task["type"] = "standalone"
            return task

        def process_hierarchy(task):
            task["type"] = "hierarchy"
            return task

        result = handle_task_by_type(task_data, process_standalone, process_hierarchy)
    """
    if not isinstance(task_obj, dict):
        raise ValueError("task_obj must be a dictionary")

    # Check if this is a task object (without type narrowing)
    if task_obj.get("kind") != "task":
        raise ValueError("task_obj must be a task object")

    # Check parent field to determine task type
    parent = task_obj.get("parent")
    if parent is None or parent == "":
        return standalone_handler(task_obj)
    else:
        return hierarchy_handler(task_obj)


def validate_task_parent_constraint(
    task_obj: dict[str, Any], expected_parent_type: type[str | None]
) -> bool:
    """Generic function to validate task parent constraints.

    Args:
        task_obj: Task object to validate
        expected_parent_type: Expected type for parent field

    Returns:
        True if parent constraint is satisfied, False otherwise

    Usage:
        # Validate standalone task (parent should be None)
        is_valid = validate_task_parent_constraint(task_data, type(None))

        # Validate hierarchy task (parent should be str)
        is_valid = validate_task_parent_constraint(task_data, str)
    """
    if not isinstance(task_obj, dict):
        return False

    if not is_task_object(task_obj):
        return False

    parent = task_obj.get("parent")

    # Check if parent type matches expected type
    if expected_parent_type is type(None):
        return parent is None or parent == ""
    elif expected_parent_type is str:
        return parent is not None and parent != ""
    else:
        return False


def create_typed_task_factory(parent_constraint: bool):
    """Factory function that creates task creation functions with parent constraints.

    Args:
        parent_constraint: True if parent is required, False if parent should be None

    Returns:
        Factory function for creating tasks with the specified parent constraint

    Usage:
        create_standalone_task = create_typed_task_factory(False)
        create_hierarchy_task = create_typed_task_factory(True)

        standalone = create_standalone_task("T-1", "Task 1")
        hierarchy = create_hierarchy_task("T-2", "Task 2", "F-feature")
    """

    def task_factory(
        task_id: str, title: str, parent: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Factory function for creating tasks with parent constraints."""
        if parent_constraint and (parent is None or parent == ""):
            raise ValueError("Parent is required for this task type")
        if not parent_constraint and parent is not None and parent != "":
            raise ValueError("Parent must be None or empty for this task type")

        return create_task_object_generic(task_id, title, parent, **kwargs)

    return task_factory
