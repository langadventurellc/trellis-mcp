"""Parameter validation error classes for claiming operations.

This module provides specific error classes for claimNextTask parameter validation
to provide clear, actionable error messages for different validation failure scenarios.
"""

from typing import Any, Dict, List, Optional

from .validation_error import ValidationError, ValidationErrorCode


class ParameterValidationError(ValidationError):
    """Specific error for parameter validation failures in claiming operations.

    Base class for all claiming parameter validation errors. Provides standardized
    error handling with clear error messages and actionable guidance for users.
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
        """Initialize parameter validation error.

        Args:
            errors: Error message(s) - can be a single string or list of strings
            error_codes: Error code(s) for programmatic handling
            context: Additional context information
            object_id: ID of the object being validated
            object_kind: Kind of object (task, feature, epic, project)
            task_type: Type of task (standalone, hierarchy)
        """
        super().__init__(
            errors=errors,
            error_codes=error_codes,
            context=context,
            object_id=object_id,
            object_kind=object_kind,
            task_type=task_type,
        )


class MutualExclusivityError(ParameterValidationError):
    """Error when mutually exclusive parameters are both specified.

    Raised when both scope and task_id parameters are provided to claimNextTask,
    which are mutually exclusive operations.
    """

    @classmethod
    def scope_and_task_id_conflict(
        cls,
        scope_value: str,
        task_id_value: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> "MutualExclusivityError":
        """Create error for scope and task_id mutual exclusivity violation.

        Args:
            scope_value: The scope parameter value that was provided
            task_id_value: The task_id parameter value that was provided
            context: Additional context information

        Returns:
            MutualExclusivityError with appropriate message and context
        """
        # Sanitize parameter values for error message
        clean_scope = _sanitize_parameter_for_error_message(scope_value)
        clean_task_id = _sanitize_parameter_for_error_message(task_id_value)

        error_msg = (
            f"Cannot specify both scope '{clean_scope}' and task_id '{clean_task_id}' parameters. "
            "Use scope for filtering tasks within project boundaries, "
            "or task_id for direct claiming."
        )

        enhanced_context = context.copy() if context else {}
        enhanced_context.update(
            {
                "scope_value": clean_scope,
                "task_id_value": clean_task_id,
                "conflict_type": "mutual_exclusivity",
                "suggested_fix": (
                    "Choose either scope-based claiming or direct task claiming, not both"
                ),
            }
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_FIELD],
            context=enhanced_context,
        )


class InvalidParameterCombinationError(ParameterValidationError):
    """Error for invalid parameter combinations.

    Raised when parameter combinations violate business rules, such as
    force_claim being used without task_id.
    """

    @classmethod
    def force_claim_without_task_id(
        cls,
        force_claim_value: bool,
        context: Optional[Dict[str, Any]] = None,
    ) -> "InvalidParameterCombinationError":
        """Create error for force_claim used without task_id.

        Args:
            force_claim_value: The force_claim parameter value
            context: Additional context information

        Returns:
            InvalidParameterCombinationError with appropriate message and context
        """
        error_msg = (
            f"force_claim parameter (set to {force_claim_value}) must be used with task_id. "
            "Force claiming only applies to direct task claiming operations."
        )

        enhanced_context = context.copy() if context else {}
        enhanced_context.update(
            {
                "force_claim_value": force_claim_value,
                "missing_parameter": "task_id",
                "parameter_combination_error": "force_claim_without_task_id",
                "suggested_fix": "Provide a task_id when using force_claim=True",
            }
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_FIELD],
            context=enhanced_context,
        )

    @classmethod
    def invalid_scope_with_force_claim(
        cls,
        scope_value: str,
        force_claim_value: bool,
        context: Optional[Dict[str, Any]] = None,
    ) -> "InvalidParameterCombinationError":
        """Create error for using scope with force_claim.

        Args:
            scope_value: The scope parameter value
            force_claim_value: The force_claim parameter value
            context: Additional context information

        Returns:
            InvalidParameterCombinationError with appropriate message and context
        """
        clean_scope = _sanitize_parameter_for_error_message(scope_value)

        error_msg = (
            f"Cannot use force_claim ({force_claim_value}) with scope parameter '{clean_scope}'. "
            "Force claiming is only supported for direct task claiming by task_id."
        )

        enhanced_context = context.copy() if context else {}
        enhanced_context.update(
            {
                "scope_value": clean_scope,
                "force_claim_value": force_claim_value,
                "parameter_combination_error": "scope_with_force_claim",
                "suggested_fix": "Use either scope-based claiming OR force claim with task_id",
            }
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_FIELD],
            context=enhanced_context,
        )


class ParameterFormatError(ParameterValidationError):
    """Error for invalid parameter format or value.

    Raised when parameter values don't match expected formats or contain
    invalid characters or patterns.
    """

    @classmethod
    def invalid_scope_format(
        cls,
        scope_value: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> "ParameterFormatError":
        """Create error for invalid scope ID format.

        Args:
            scope_value: The invalid scope parameter value
            context: Additional context information

        Returns:
            ParameterFormatError with appropriate message and context
        """
        clean_scope = _sanitize_parameter_for_error_message(scope_value)

        error_msg = (
            f"Invalid scope ID format: '{clean_scope}'. "
            "Scope must use P- (project), E- (epic), or F- (feature) prefix "
            "followed by alphanumeric characters, hyphens, or underscores. "
            "Examples: 'P-ecommerce-platform', 'E-user-auth', 'F-login-form'."
        )

        enhanced_context = context.copy() if context else {}
        enhanced_context.update(
            {
                "invalid_scope_value": clean_scope,
                "expected_format": (
                    "P-|E-|F- followed by alphanumeric, hyphen, or underscore characters"
                ),
                "format_error_type": "scope_format",
                "valid_examples": ["P-project-name", "E-epic-name", "F-feature-name"],
            }
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_FORMAT],
            context=enhanced_context,
        )

    @classmethod
    def invalid_task_id_format(
        cls,
        task_id_value: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> "ParameterFormatError":
        """Create error for invalid task_id format.

        Args:
            task_id_value: The invalid task_id parameter value
            context: Additional context information

        Returns:
            ParameterFormatError with appropriate message and context
        """
        clean_task_id = _sanitize_parameter_for_error_message(task_id_value)

        error_msg = (
            f"Invalid task ID format: '{clean_task_id}'. "
            "Task ID must use T- prefix for hierarchical tasks "
            "or be a valid standalone task identifier. "
            "Examples: 'T-implement-auth', 'task-database-setup'."
        )

        enhanced_context = context.copy() if context else {}
        enhanced_context.update(
            {
                "invalid_task_id_value": clean_task_id,
                "expected_format": ("T- prefix for hierarchical tasks or valid standalone format"),
                "format_error_type": "task_id_format",
                "valid_examples": ["T-task-name", "task-standalone-name"],
            }
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_FORMAT],
            context=enhanced_context,
        )

    @classmethod
    def empty_project_root(
        cls,
        project_root_value: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "ParameterFormatError":
        """Create error for empty or None project_root parameter.

        Args:
            project_root_value: The invalid project_root parameter value
            context: Additional context information

        Returns:
            ParameterFormatError with appropriate message and context
        """
        error_msg = (
            "Project root parameter cannot be empty or None. "
            "Provide the absolute path to your Trellis planning directory. "
            "Example: '/path/to/my-project/planning' or './planning'."
        )

        enhanced_context = context.copy() if context else {}
        enhanced_context.update(
            {
                "invalid_project_root_value": project_root_value,
                "format_error_type": "empty_project_root",
                "suggested_fix": "Provide a valid path to your planning directory",
                "valid_examples": ["/path/to/planning", "./planning", "../planning"],
            }
        )

        return cls(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
            context=enhanced_context,
        )


def _sanitize_parameter_for_error_message(value: str | None, max_length: int = 100) -> str:
    """Sanitize parameter values for safe inclusion in error messages.

    Removes or redacts potentially sensitive information while preserving
    readability for legitimate parameter values.

    Args:
        value: Parameter value to sanitize
        max_length: Maximum length before truncation

    Returns:
        Sanitized parameter value safe for error messages
    """
    if not value:
        return "[empty]"

    # Convert to string and strip whitespace
    clean_value = str(value).strip()

    # Check if empty after stripping
    if not clean_value:
        return "[empty]"

    # Check for potentially sensitive patterns (case-insensitive)
    sensitive_patterns = [
        "password",
        "secret",
        "key",
        "token",
        "api",
        "auth",
        "credential",
        "private",
        "confidential",
    ]

    value_lower = clean_value.lower()
    for pattern in sensitive_patterns:
        if pattern in value_lower:
            return "[redacted-sensitive]"

    # Truncate if too long
    if len(clean_value) > max_length:
        return clean_value[:max_length] + "..."

    return clean_value


# Error message constants for standardized messaging
CLAIMING_ERROR_MESSAGES = {
    "MUTUAL_EXCLUSIVITY_SCOPE_TASK_ID": (
        "Cannot specify both scope and task_id parameters. "
        "Use scope for filtering tasks within boundaries, or task_id for direct claiming."
    ),
    "FORCE_CLAIM_REQUIRES_TASK_ID": (
        "force_claim parameter requires task_id to be specified. "
        "Force claiming only applies to direct task claiming operations."
    ),
    "INVALID_SCOPE_FORMAT": (
        "Invalid scope ID format. Must use P-, E-, or F- prefix followed by "
        "alphanumeric characters, hyphens, or underscores."
    ),
    "INVALID_TASK_ID_FORMAT": (
        "Invalid task ID format. Must use T- prefix for hierarchical tasks "
        "or be a valid standalone task identifier."
    ),
    "EMPTY_PROJECT_ROOT": (
        "Project root parameter cannot be empty. "
        "Provide the path to your Trellis planning directory."
    ),
}


def create_claiming_parameter_error(
    error_type: str,
    **kwargs: Any,
) -> ParameterValidationError:
    """Factory function to create claiming parameter validation errors.

    Args:
        error_type: Type of error to create
        **kwargs: Additional arguments specific to each error type

    Returns:
        Appropriate ParameterValidationError subclass instance

    Raises:
        ValueError: If error_type is not recognized
    """
    error_creators = {
        "mutual_exclusivity_scope_task_id": lambda: (
            MutualExclusivityError.scope_and_task_id_conflict(
                kwargs["scope_value"], kwargs["task_id_value"], kwargs.get("context")
            )
        ),
        "force_claim_without_task_id": lambda: (
            InvalidParameterCombinationError.force_claim_without_task_id(
                kwargs["force_claim_value"], kwargs.get("context")
            )
        ),
        "invalid_scope_with_force_claim": lambda: (
            InvalidParameterCombinationError.invalid_scope_with_force_claim(
                kwargs["scope_value"], kwargs["force_claim_value"], kwargs.get("context")
            )
        ),
        "invalid_scope_format": lambda: ParameterFormatError.invalid_scope_format(
            kwargs["scope_value"], kwargs.get("context")
        ),
        "invalid_task_id_format": lambda: ParameterFormatError.invalid_task_id_format(
            kwargs["task_id_value"], kwargs.get("context")
        ),
        "empty_project_root": lambda: ParameterFormatError.empty_project_root(
            kwargs.get("project_root_value"), kwargs.get("context")
        ),
    }

    if error_type not in error_creators:
        valid_types = list(error_creators.keys())
        raise ValueError(f"Unknown error type: {error_type}. Valid types: {valid_types}")

    return error_creators[error_type]()
