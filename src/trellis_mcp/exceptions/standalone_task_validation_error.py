"""Standalone task validation exception classes.

This module provides specialized validation exceptions for standalone tasks,
which are tasks that exist without a parent feature in the hierarchy.
"""

from typing import Any, Dict, List, Optional

from .validation_error import ValidationError, ValidationErrorCode


class StandaloneTaskValidationError(ValidationError):
    """Exception for standalone task validation failures.

    Standalone tasks are tasks that exist without a parent feature,
    introduced in schema version 1.1. They have specific validation
    rules that differ from hierarchy tasks.
    """

    def __init__(
        self,
        errors: List[str] | str,
        error_codes: List[ValidationErrorCode] | ValidationErrorCode | None = None,
        context: Optional[Dict[str, Any]] = None,
        object_id: Optional[str] = None,
        object_kind: Optional[str] = None,
    ):
        """Initialize standalone task validation error.

        Args:
            errors: Error message(s)
            error_codes: Error code(s) for programmatic handling
            context: Additional context information
            object_id: ID of the standalone task
            object_kind: Should be "task" for standalone tasks
        """
        super().__init__(
            errors=errors,
            error_codes=error_codes,
            context=context,
            object_id=object_id,
            object_kind=object_kind or "task",
            task_type="standalone",
        )

    @classmethod
    def invalid_status(
        cls, task_id: str, status: str, valid_statuses: Optional[List[str]] = None
    ) -> "StandaloneTaskValidationError":
        """Create error for invalid status in standalone task.

        Args:
            task_id: ID of the standalone task
            status: Invalid status value
            valid_statuses: List of valid status values

        Returns:
            Formatted standalone task validation error
        """
        error_msg = f"Invalid status '{status}' for standalone task"
        if valid_statuses:
            error_msg += f". Valid statuses: {', '.join(valid_statuses)}"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_STATUS],
            context={"status": status, "valid_statuses": valid_statuses or []},
            object_id=task_id,
        )

    @classmethod
    def parent_not_allowed(cls, task_id: str, parent_id: str) -> "StandaloneTaskValidationError":
        """Create error for parent specified in standalone task.

        Args:
            task_id: ID of the standalone task
            parent_id: Parent ID that was incorrectly specified

        Returns:
            Formatted standalone task validation error
        """
        error_msg = f"Standalone task cannot have a parent (parent '{parent_id}' specified)"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_PARENT_TYPE],
            context={"parent_id": parent_id},
            object_id=task_id,
        )

    @classmethod
    def schema_version_required(
        cls, task_id: str, current_version: Optional[str] = None
    ) -> "StandaloneTaskValidationError":
        """Create error for standalone task with invalid schema version.

        Args:
            task_id: ID of the standalone task
            current_version: Current schema version (if any)

        Returns:
            Formatted standalone task validation error
        """
        error_msg = "Standalone tasks require schema version 1.1 or higher"
        if current_version:
            error_msg += f" (current: {current_version})"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.SCHEMA_VERSION_MISMATCH],
            context={"current_version": current_version, "required_version": "1.1"},
            object_id=task_id,
        )

    @classmethod
    def invalid_transition(
        cls,
        task_id: str,
        from_status: str,
        to_status: str,
        allowed_transitions: Optional[Dict[str, List[str]]] = None,
    ) -> "StandaloneTaskValidationError":
        """Create error for invalid status transition in standalone task.

        Args:
            task_id: ID of the standalone task
            from_status: Current status
            to_status: Target status
            allowed_transitions: Dictionary of allowed transitions

        Returns:
            Formatted standalone task validation error
        """
        error_msg = (
            f"Invalid status transition from '{from_status}' to '{to_status}' for standalone task"
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
        )

    @classmethod
    def missing_required_field(
        cls, task_id: str, field_name: str, field_description: Optional[str] = None
    ) -> "StandaloneTaskValidationError":
        """Create error for missing required field in standalone task.

        Args:
            task_id: ID of the standalone task
            field_name: Name of the missing field
            field_description: Description of the field requirement

        Returns:
            Formatted standalone task validation error
        """
        error_msg = f"Missing required field '{field_name}' for standalone task"
        if field_description:
            error_msg += f": {field_description}"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
            context={"field_name": field_name, "field_description": field_description},
            object_id=task_id,
        )

    @classmethod
    def invalid_field_value(
        cls,
        task_id: str,
        field_name: str,
        field_value: Any,
        valid_values: Optional[List[Any]] = None,
        validation_rule: Optional[str] = None,
    ) -> "StandaloneTaskValidationError":
        """Create error for invalid field value in standalone task.

        Args:
            task_id: ID of the standalone task
            field_name: Name of the field with invalid value
            field_value: Invalid value
            valid_values: List of valid values (if applicable)
            validation_rule: Description of the validation rule

        Returns:
            Formatted standalone task validation error
        """
        error_msg = f"Invalid value '{field_value}' for field '{field_name}' in standalone task"

        if valid_values:
            error_msg += f". Valid values: {', '.join(map(str, valid_values))}"
        elif validation_rule:
            error_msg += f". Validation rule: {validation_rule}"

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_FIELD],
            context={
                "field_name": field_name,
                "field_value": field_value,
                "valid_values": valid_values or [],
                "validation_rule": validation_rule,
            },
            object_id=task_id,
        )
