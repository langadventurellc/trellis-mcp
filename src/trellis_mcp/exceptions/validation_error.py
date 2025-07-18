"""Base validation exception classes for the Trellis MCP system.

This module provides the foundation for all validation-related exceptions,
including structured error handling with error codes and context information.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationErrorCode(Enum):
    """Error codes for validation failures."""

    # General validation errors
    INVALID_FIELD = "invalid_field"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_ENUM_VALUE = "invalid_enum_value"
    INVALID_FORMAT = "invalid_format"

    # Task-specific validation errors
    INVALID_STATUS = "invalid_status"
    MISSING_PARENT = "missing_parent"
    PARENT_NOT_EXIST = "parent_not_exist"
    INVALID_PARENT_TYPE = "invalid_parent_type"

    # Hierarchy validation errors
    CIRCULAR_DEPENDENCY = "circular_dependency"
    INVALID_HIERARCHY_LEVEL = "invalid_hierarchy_level"

    # Status transition errors
    INVALID_STATUS_TRANSITION = "invalid_status_transition"
    STATUS_TRANSITION_NOT_ALLOWED = "status_transition_not_allowed"

    # Schema validation errors
    SCHEMA_VERSION_MISMATCH = "schema_version_mismatch"
    INVALID_SCHEMA_VERSION = "invalid_schema_version"

    # Cross-system validation errors
    CROSS_SYSTEM_REFERENCE_CONFLICT = "cross_system_reference_conflict"
    CROSS_SYSTEM_PREREQUISITE_INVALID = "cross_system_prerequisite_invalid"


class ValidationError(Exception):
    """Base validation exception with structured error handling.

    This exception supports:
    - Multiple error messages with individual error codes
    - Context information (task ID, object kind, etc.)
    - Structured error objects for API responses
    - Error message templates for consistency
    """

    def __init__(
        self,
        errors: List[str] | str,
        error_codes: List[ValidationErrorCode] | ValidationErrorCode | None = None,
        context: Optional[Dict[str, Any]] = None,
        object_id: Optional[str] = None,
        object_kind: Optional[str] = None,
        task_type: Optional[str] = None,
    ):
        """Initialize validation error.

        Args:
            errors: Error message(s) - can be a single string or list of strings
            error_codes: Error code(s) for programmatic handling
            context: Additional context information
            object_id: ID of the object being validated
            object_kind: Kind of object (task, feature, epic, project)
            task_type: Type of task (standalone, hierarchy)
        """
        # Normalize errors to list format
        if isinstance(errors, str):
            self.errors = [errors]
        else:
            self.errors = errors

        # Normalize error codes to list format
        if error_codes is None:
            self.error_codes = []
        elif isinstance(error_codes, ValidationErrorCode):
            self.error_codes = [error_codes]
        else:
            self.error_codes = error_codes

        # Store context information
        self.context = context or {}
        self.object_id = object_id
        self.object_kind = object_kind
        self.task_type = task_type

        # Create the main error message
        error_message = f"Validation failed: {'; '.join(self.errors)}"
        if self.object_id:
            error_message += f" (object: {self.object_id})"
        if self.task_type:
            error_message += f" ({self.task_type} task)"

        super().__init__(error_message)

    def add_error(self, error: str, error_code: Optional[ValidationErrorCode] = None):
        """Add an additional error to this exception.

        Args:
            error: Error message to add
            error_code: Error code for the new error
        """
        self.errors.append(error)
        if error_code:
            self.error_codes.append(error_code)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses.

        Returns:
            Dictionary representation of the exception
        """
        result = {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "errors": self.errors,
            "error_codes": [code.value for code in self.error_codes],
        }

        if self.object_id:
            result["object_id"] = self.object_id
        if self.object_kind:
            result["object_kind"] = self.object_kind
        if self.task_type:
            result["task_type"] = self.task_type
        if self.context:
            result["context"] = self.context

        return result

    def has_error_code(self, error_code: ValidationErrorCode) -> bool:
        """Check if this exception contains a specific error code.

        Args:
            error_code: Error code to check for

        Returns:
            True if the error code is present
        """
        return error_code in self.error_codes

    def get_errors_by_code(self, error_code: ValidationErrorCode) -> List[str]:
        """Get all error messages associated with a specific error code.

        Args:
            error_code: Error code to filter by

        Returns:
            List of error messages for the specified code
        """
        if error_code not in self.error_codes:
            return []

        # If we have the same number of errors and codes, map them 1:1
        if len(self.errors) == len(self.error_codes):
            return [
                error for error, code in zip(self.errors, self.error_codes) if code == error_code
            ]
        else:
            # If counts don't match, we can't map them directly
            return self.errors if error_code in self.error_codes else []

    @classmethod
    def create_contextual_error(
        cls,
        error_type: str,
        object_id: str,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> "ValidationError":
        """Create a contextual validation error with standard formatting.

        Args:
            error_type: Type of error (e.g., "invalid_status", "missing_parent")
            object_id: ID of the object with the error
            task_type: Type of task (standalone, hierarchy)
            context: Additional context information

        Returns:
            Formatted validation error
        """
        # Map error types to codes
        error_code_map = {
            "invalid_status": ValidationErrorCode.INVALID_STATUS,
            "missing_parent": ValidationErrorCode.MISSING_PARENT,
            "parent_not_exist": ValidationErrorCode.PARENT_NOT_EXIST,
            "invalid_parent_type": ValidationErrorCode.INVALID_PARENT_TYPE,
            "missing_fields": ValidationErrorCode.MISSING_REQUIRED_FIELD,
            "invalid_enum": ValidationErrorCode.INVALID_ENUM_VALUE,
        }

        error_code = error_code_map.get(error_type, ValidationErrorCode.INVALID_FIELD)

        # Create contextual error message
        if error_type == "invalid_status":
            status = context.get("status", "unknown") if context else "unknown"
            error_msg = f"Invalid status '{status}' for {task_type} task"
        elif error_type == "missing_parent":
            error_msg = f"Parent is required for {task_type} task"
        elif error_type == "parent_not_exist":
            parent_id = context.get("parent_id", "unknown") if context else "unknown"
            error_msg = f"Parent with ID '{parent_id}' does not exist ({task_type} task validation)"
        else:
            error_msg = f"Validation error: {error_type} ({task_type} task)"

        return cls(
            errors=[error_msg],
            error_codes=[error_code],
            context=context,
            object_id=object_id,
            task_type=task_type,
        )

    @classmethod
    def create_cross_system_error(
        cls,
        source_task_type: str,
        target_task_type: str,
        source_task_id: str,
        target_task_id: str,
        conflict_type: str = "reference",
        context: Optional[Dict[str, Any]] = None,
    ) -> "ValidationError":
        """Create a cross-system validation error with enhanced context.

        Args:
            source_task_type: Type of source task ("standalone" or "hierarchy")
            target_task_type: Type of target task ("standalone" or "hierarchy")
            source_task_id: ID of the source task
            target_task_id: ID of the target task
            conflict_type: Type of conflict ("reference" or "prerequisite")
            context: Additional context information

        Returns:
            Cross-system validation error with enhanced context
        """
        if conflict_type == "reference":
            error_code = cls._get_cross_system_error_code(source_task_type, target_task_type)
            error_msg = cls._format_cross_system_reference_error(
                source_task_type, target_task_type, source_task_id, target_task_id
            )
        elif conflict_type == "prerequisite":
            error_code = ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID
            error_msg = cls._format_cross_system_prerequisite_error(
                source_task_type, target_task_type, source_task_id, target_task_id
            )
        else:
            error_code = ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT
            error_msg = (
                f"Cross-system conflict between {source_task_type} task '{source_task_id}' "
                f"and {target_task_type} task '{target_task_id}'"
            )

        # Enhance context with cross-system information
        enhanced_context = context.copy() if context else {}
        enhanced_context.update(
            {
                "source_task_type": source_task_type,
                "target_task_type": target_task_type,
                "source_task_id": source_task_id,
                "target_task_id": target_task_id,
                "conflict_type": conflict_type,
                "cross_system_context": True,
            }
        )

        return cls(
            errors=[error_msg],
            error_codes=[error_code],
            context=enhanced_context,
            object_id=source_task_id,
            task_type=source_task_type,
        )

    @classmethod
    def _get_cross_system_error_code(
        cls, source_type: str, target_type: str
    ) -> ValidationErrorCode:
        """Get appropriate error code for cross-system validation.

        Args:
            source_type: Type of source task
            target_type: Type of target task

        Returns:
            Appropriate ValidationErrorCode for the cross-system scenario
        """
        return ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT

    @classmethod
    def _format_cross_system_reference_error(
        cls, source_type: str, target_type: str, source_id: str, target_id: str
    ) -> str:
        """Format cross-system reference error message.

        Args:
            source_type: Type of source task ("standalone" or "hierarchy")
            target_type: Type of target task ("standalone" or "hierarchy")
            source_id: ID of the source task
            target_id: ID of the target task

        Returns:
            Formatted error message for cross-system reference conflict
        """
        # Clean task IDs for display (remove prefixes for clarity)
        clean_source_id = (
            source_id.replace("T-", "").replace("F-", "").replace("E-", "").replace("P-", "")
        )
        clean_target_id = (
            target_id.replace("T-", "").replace("F-", "").replace("E-", "").replace("P-", "")
        )

        if source_type == "standalone" and target_type == "hierarchy":
            return (
                f"Cannot reference hierarchical task '{clean_target_id}' from "
                f"standalone task '{clean_source_id}'"
            )
        elif source_type == "hierarchy" and target_type == "standalone":
            return (
                f"Cannot reference standalone task '{clean_target_id}' from "
                f"hierarchical task '{clean_source_id}'"
            )
        else:
            return (
                f"Cross-system reference conflict between {source_type} task "
                f"'{clean_source_id}' and {target_type} task '{clean_target_id}'"
            )

    @classmethod
    def _format_cross_system_prerequisite_error(
        cls, source_type: str, target_type: str, source_id: str, target_id: str
    ) -> str:
        """Format cross-system prerequisite error message.

        Args:
            source_type: Type of source task
            target_type: Type of target task
            source_id: ID of the source task
            target_id: ID of the target task

        Returns:
            Formatted error message for cross-system prerequisite conflict
        """
        # Clean task IDs for display
        clean_source_id = (
            source_id.replace("T-", "").replace("F-", "").replace("E-", "").replace("P-", "")
        )
        clean_target_id = (
            target_id.replace("T-", "").replace("F-", "").replace("E-", "").replace("P-", "")
        )

        return (
            f"Prerequisite validation failed: {source_type} task '{clean_source_id}' "
            f"requires {target_type} task '{clean_target_id}' which does not exist"
        )
