"""Hierarchy task validation exception classes.

This module provides specialized validation exceptions for hierarchy tasks,
which are traditional tasks that exist within a parent feature in the hierarchy.
"""

from typing import Any, Dict, List, Optional

from .validation_error import ValidationError, ValidationErrorCode


class HierarchyTaskValidationError(ValidationError):
    """Exception for hierarchy task validation failures.

    Hierarchy tasks are traditional tasks that exist within a parent feature
    in the project hierarchy (Projects → Epics → Features → Tasks).
    They have specific validation rules that require parent relationships.
    """

    def __init__(
        self,
        errors: List[str] | str,
        error_codes: List[ValidationErrorCode] | ValidationErrorCode | None = None,
        context: Optional[Dict[str, Any]] = None,
        object_id: Optional[str] = None,
        object_kind: Optional[str] = None,
        parent_id: Optional[str] = None,
    ):
        """Initialize hierarchy task validation error.

        Args:
            errors: Error message(s)
            error_codes: Error code(s) for programmatic handling
            context: Additional context information
            object_id: ID of the hierarchy task
            object_kind: Should be "task" for hierarchy tasks
            parent_id: ID of the parent feature
        """
        # Add parent_id to context if provided
        if context is None:
            context = {}
        if parent_id:
            context["parent_id"] = parent_id

        super().__init__(
            errors=errors,
            error_codes=error_codes,
            context=context,
            object_id=object_id,
            object_kind=object_kind or "task",
            task_type="hierarchy",
        )

        self.parent_id = parent_id

    @classmethod
    def missing_parent(
        cls, task_id: str, schema_version: Optional[str] = None
    ) -> "HierarchyTaskValidationError":
        """Create error for missing parent in hierarchy task.

        Args:
            task_id: ID of the hierarchy task
            schema_version: Schema version of the task

        Returns:
            Formatted hierarchy task validation error
        """
        error_msg = "Parent is required for hierarchy task"
        if schema_version:
            error_msg += f" (schema version: {schema_version})"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.MISSING_PARENT],
            context={"schema_version": schema_version},
            object_id=task_id,
        )

    @classmethod
    def parent_not_exist(
        cls, task_id: str, parent_id: str, parent_type: str = "feature"
    ) -> "HierarchyTaskValidationError":
        """Create error for non-existent parent in hierarchy task.

        Args:
            task_id: ID of the hierarchy task
            parent_id: ID of the non-existent parent
            parent_type: Type of parent (usually "feature")

        Returns:
            Formatted hierarchy task validation error
        """
        error_msg = (
            f"Parent {parent_type} with ID '{parent_id}' does not exist (hierarchy task validation)"
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.PARENT_NOT_EXIST],
            context={"parent_type": parent_type},
            object_id=task_id,
            parent_id=parent_id,
        )

    @classmethod
    def invalid_parent_type(
        cls, task_id: str, parent_id: str, parent_kind: str, expected_kind: str = "feature"
    ) -> "HierarchyTaskValidationError":
        """Create error for invalid parent type in hierarchy task.

        Args:
            task_id: ID of the hierarchy task
            parent_id: ID of the parent
            parent_kind: Actual kind of the parent
            expected_kind: Expected kind of the parent

        Returns:
            Formatted hierarchy task validation error
        """
        error_msg = (
            f"Invalid parent type '{parent_kind}' for hierarchy task. Expected '{expected_kind}'"
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_PARENT_TYPE],
            context={"parent_kind": parent_kind, "expected_kind": expected_kind},
            object_id=task_id,
            parent_id=parent_id,
        )

    @classmethod
    def invalid_status(
        cls, task_id: str, parent_id: str, status: str, valid_statuses: Optional[List[str]] = None
    ) -> "HierarchyTaskValidationError":
        """Create error for invalid status in hierarchy task.

        Args:
            task_id: ID of the hierarchy task
            parent_id: ID of the parent feature
            status: Invalid status value
            valid_statuses: List of valid status values

        Returns:
            Formatted hierarchy task validation error
        """
        error_msg = f"Invalid status '{status}' for hierarchy task"
        if valid_statuses:
            error_msg += f". Valid statuses: {', '.join(valid_statuses)}"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_STATUS],
            context={"status": status, "valid_statuses": valid_statuses or []},
            object_id=task_id,
            parent_id=parent_id,
        )

    @classmethod
    def circular_dependency(
        cls, task_id: str, parent_id: str, dependency_path: List[str]
    ) -> "HierarchyTaskValidationError":
        """Create error for circular dependency in hierarchy task.

        Args:
            task_id: ID of the hierarchy task
            parent_id: ID of the parent feature
            dependency_path: List of IDs forming the circular dependency

        Returns:
            Formatted hierarchy task validation error
        """
        cycle_str = " -> ".join(dependency_path)
        error_msg = f"Circular dependency detected in hierarchy task: {cycle_str}"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.CIRCULAR_DEPENDENCY],
            context={"dependency_path": dependency_path},
            object_id=task_id,
            parent_id=parent_id,
        )

    @classmethod
    def invalid_hierarchy_level(
        cls, task_id: str, parent_id: str, current_level: int, expected_level: int
    ) -> "HierarchyTaskValidationError":
        """Create error for invalid hierarchy level.

        Args:
            task_id: ID of the hierarchy task
            parent_id: ID of the parent
            current_level: Current hierarchy level
            expected_level: Expected hierarchy level

        Returns:
            Formatted hierarchy task validation error
        """
        error_msg = (
            f"Invalid hierarchy level {current_level} for hierarchy task. "
            f"Expected level {expected_level}"
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_HIERARCHY_LEVEL],
            context={"current_level": current_level, "expected_level": expected_level},
            object_id=task_id,
            parent_id=parent_id,
        )

    @classmethod
    def parent_status_conflict(
        cls,
        task_id: str,
        parent_id: str,
        task_status: str,
        parent_status: str,
        conflict_reason: str,
    ) -> "HierarchyTaskValidationError":
        """Create error for parent status conflict.

        Args:
            task_id: ID of the hierarchy task
            parent_id: ID of the parent
            task_status: Status of the task
            parent_status: Status of the parent
            conflict_reason: Reason for the conflict

        Returns:
            Formatted hierarchy task validation error
        """
        error_msg = (
            f"Status conflict: hierarchy task has status '{task_status}' but parent has status "
            f"'{parent_status}'. {conflict_reason}"
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.STATUS_TRANSITION_NOT_ALLOWED],
            context={
                "task_status": task_status,
                "parent_status": parent_status,
                "conflict_reason": conflict_reason,
            },
            object_id=task_id,
            parent_id=parent_id,
        )

    @classmethod
    def invalid_transition(
        cls,
        task_id: str,
        parent_id: str,
        from_status: str,
        to_status: str,
        allowed_transitions: Optional[Dict[str, List[str]]] = None,
    ) -> "HierarchyTaskValidationError":
        """Create error for invalid status transition in hierarchy task.

        Args:
            task_id: ID of the hierarchy task
            parent_id: ID of the parent feature
            from_status: Current status
            to_status: Target status
            allowed_transitions: Dictionary of allowed transitions

        Returns:
            Formatted hierarchy task validation error
        """
        error_msg = (
            f"Invalid status transition from '{from_status}' to '{to_status}' for hierarchy task"
        )

        if allowed_transitions and from_status in allowed_transitions:
            valid_targets = allowed_transitions[from_status]
            error_msg += f". Valid transitions from '{from_status}': {', '.join(valid_targets)}"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_STATUS_TRANSITION],
            context={
                "from_status": from_status,
                "to_status": to_status,
                "allowed_transitions": allowed_transitions or {},
            },
            object_id=task_id,
            parent_id=parent_id,
        )
