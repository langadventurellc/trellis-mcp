"""Validation error aggregation and prioritization system.

This module provides the ValidationErrorCollector class that aggregates multiple
validation errors, prioritizes them, and presents them in organized formats.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from .security import (
    audit_security_error,
    filter_sensitive_information,
    sanitize_error_message,
    validate_error_message_safety,
)


class ErrorSeverity(Enum):
    """Severity levels for validation errors."""

    CRITICAL = 1  # Errors that prevent object creation/update
    HIGH = 2  # Errors that cause functional problems
    MEDIUM = 3  # Errors that may cause issues
    LOW = 4  # Warnings or minor issues


class ErrorCategory(Enum):
    """Categories for grouping related validation errors."""

    SCHEMA = "schema"  # Schema validation errors
    FIELD = "field"  # Field-level validation errors
    RELATIONSHIP = "relationship"  # Parent/child relationship errors
    SECURITY = "security"  # Security-related errors
    BUSINESS = "business"  # Business logic errors
    SYSTEM = "system"  # System-level errors


class ValidationErrorCollector:
    """Collects and organizes multiple validation errors with prioritization.

    This class provides a structured way to collect validation errors during
    object validation, then present them in organized formats with proper
    prioritization and grouping.
    """

    def __init__(self, object_id: Optional[str] = None, object_kind: Optional[str] = None):
        """Initialize the error collector.

        Args:
            object_id: ID of the object being validated
            object_kind: Kind of object (task, feature, epic, project)
        """
        self.object_id = object_id
        self.object_kind = object_kind
        self._errors: List[
            Tuple[str, ValidationErrorCode, ErrorSeverity, ErrorCategory, Dict[str, Any]]
        ] = []

        # Error code to severity mapping
        self._severity_map = {
            # Critical errors - prevent object creation/update
            ValidationErrorCode.MISSING_REQUIRED_FIELD: ErrorSeverity.CRITICAL,
            ValidationErrorCode.INVALID_ENUM_VALUE: ErrorSeverity.CRITICAL,
            ValidationErrorCode.CIRCULAR_DEPENDENCY: ErrorSeverity.CRITICAL,
            ValidationErrorCode.SCHEMA_VERSION_MISMATCH: ErrorSeverity.CRITICAL,
            ValidationErrorCode.INVALID_SCHEMA_VERSION: ErrorSeverity.CRITICAL,
            # High severity - functional problems
            ValidationErrorCode.INVALID_STATUS: ErrorSeverity.HIGH,
            ValidationErrorCode.MISSING_PARENT: ErrorSeverity.HIGH,
            ValidationErrorCode.PARENT_NOT_EXIST: ErrorSeverity.HIGH,
            ValidationErrorCode.INVALID_PARENT_TYPE: ErrorSeverity.HIGH,
            ValidationErrorCode.INVALID_STATUS_TRANSITION: ErrorSeverity.HIGH,
            ValidationErrorCode.STATUS_TRANSITION_NOT_ALLOWED: ErrorSeverity.HIGH,
            ValidationErrorCode.INVALID_HIERARCHY_LEVEL: ErrorSeverity.HIGH,
            # Medium severity - may cause issues
            ValidationErrorCode.INVALID_FIELD: ErrorSeverity.MEDIUM,
            ValidationErrorCode.INVALID_FORMAT: ErrorSeverity.MEDIUM,
        }

        # Error code to category mapping
        self._category_map = {
            # Schema-related errors
            ValidationErrorCode.SCHEMA_VERSION_MISMATCH: ErrorCategory.SCHEMA,
            ValidationErrorCode.INVALID_SCHEMA_VERSION: ErrorCategory.SCHEMA,
            # Field-level errors
            ValidationErrorCode.MISSING_REQUIRED_FIELD: ErrorCategory.FIELD,
            ValidationErrorCode.INVALID_FIELD: ErrorCategory.FIELD,
            ValidationErrorCode.INVALID_ENUM_VALUE: ErrorCategory.FIELD,
            ValidationErrorCode.INVALID_FORMAT: ErrorCategory.FIELD,
            ValidationErrorCode.INVALID_STATUS: ErrorCategory.FIELD,
            # Relationship errors
            ValidationErrorCode.MISSING_PARENT: ErrorCategory.RELATIONSHIP,
            ValidationErrorCode.PARENT_NOT_EXIST: ErrorCategory.RELATIONSHIP,
            ValidationErrorCode.INVALID_PARENT_TYPE: ErrorCategory.RELATIONSHIP,
            ValidationErrorCode.CIRCULAR_DEPENDENCY: ErrorCategory.RELATIONSHIP,
            ValidationErrorCode.INVALID_HIERARCHY_LEVEL: ErrorCategory.RELATIONSHIP,
            # Business logic errors
            ValidationErrorCode.INVALID_STATUS_TRANSITION: ErrorCategory.BUSINESS,
            ValidationErrorCode.STATUS_TRANSITION_NOT_ALLOWED: ErrorCategory.BUSINESS,
        }

    def add_error(
        self,
        message: str,
        error_code: ValidationErrorCode,
        context: Optional[Dict[str, Any]] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        perform_security_validation: bool = False,
    ) -> None:
        """Add a validation error to the collection.

        Args:
            message: Error message
            error_code: Error code for programmatic handling
            context: Additional context information
            severity: Error severity (auto-determined from code if not provided)
            category: Error category (auto-determined from code if not provided)
            perform_security_validation: Whether to perform security validation on the error
        """
        # Auto-determine severity and category if not provided
        if severity is None:
            severity = self._severity_map.get(error_code, ErrorSeverity.MEDIUM)

        if category is None:
            category = self._category_map.get(error_code, ErrorCategory.FIELD)

        # Perform security validation if requested
        if perform_security_validation:
            # Sanitize the error message
            sanitized_message = sanitize_error_message(message)

            # Validate message safety
            safety_issues = validate_error_message_safety(sanitized_message)
            if safety_issues:
                # Log security concern but don't prevent adding the error
                audit_security_error(
                    f"Unsafe error message detected: {'; '.join(safety_issues)}",
                    {"original_message": message[:100]},  # Truncate for safety
                )
                # Use a generic message instead
                sanitized_message = "Validation error occurred"

            # Filter sensitive information from context
            safe_context = filter_sensitive_information(context or {})

            # Audit security-related errors
            if category == ErrorCategory.SECURITY:
                audit_security_error(sanitized_message or "", safe_context)
        else:
            sanitized_message = message
            safe_context = context or {}

        # Store the error with metadata
        self._errors.append(
            (sanitized_message or "", error_code, severity, category, safe_context or {})
        )

    def add_security_error(
        self,
        message: str,
        error_code: ValidationErrorCode,
        context: Optional[Dict[str, Any]] = None,
        severity: Optional[ErrorSeverity] = None,
    ) -> None:
        """Add a security-related error to the collection.

        This method specifically handles security errors with enhanced security
        validation and auditing.

        Args:
            message: Security error message
            error_code: Error code for programmatic handling
            context: Additional context information
            severity: Error severity (defaults to HIGH for security errors)
        """
        # Security errors default to HIGH severity
        if severity is None:
            severity = ErrorSeverity.HIGH

        # Add the error with security category and validation enabled
        self.add_error(
            message=message,
            error_code=error_code,
            context=context,
            severity=severity,
            category=ErrorCategory.SECURITY,
            perform_security_validation=True,
        )

    def has_errors(self) -> bool:
        """Check if any errors have been collected.

        Returns:
            True if there are errors in the collection
        """
        return len(self._errors) > 0

    def get_error_count(self) -> int:
        """Get the total number of errors collected.

        Returns:
            Number of errors in the collection
        """
        return len(self._errors)

    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors.

        Returns:
            True if there are critical severity errors
        """
        return any(severity == ErrorSeverity.CRITICAL for _, _, severity, _, _ in self._errors)

    def get_errors_by_severity(
        self, severity: ErrorSeverity
    ) -> List[Tuple[str, ValidationErrorCode, Dict[str, Any]]]:
        """Get all errors of a specific severity level.

        Args:
            severity: Severity level to filter by

        Returns:
            List of (message, error_code, context) tuples for the specified severity
        """
        return [(msg, code, ctx) for msg, code, sev, _, ctx in self._errors if sev == severity]

    def get_errors_by_category(
        self, category: ErrorCategory
    ) -> List[Tuple[str, ValidationErrorCode, Dict[str, Any]]]:
        """Get all errors of a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of (message, error_code, context) tuples for the specified category
        """
        return [(msg, code, ctx) for msg, code, _, cat, ctx in self._errors if cat == category]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected errors.

        Returns:
            Dictionary with error counts by severity and category
        """
        severity_counts = {}
        category_counts = {}

        for _, _, severity, category, _ in self._errors:
            severity_counts[severity.name] = severity_counts.get(severity.name, 0) + 1
            category_counts[category.value] = category_counts.get(category.value, 0) + 1

        return {
            "total_errors": len(self._errors),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "has_critical": self.has_critical_errors(),
        }

    def get_detailed_view(self) -> Dict[str, Any]:
        """Get a detailed view of all errors, grouped by category.

        Returns:
            Dictionary with errors organized by category
        """
        grouped_errors = {}

        for message, error_code, severity, category, context in self._errors:
            cat_name = category.value
            if cat_name not in grouped_errors:
                grouped_errors[cat_name] = []

            grouped_errors[cat_name].append(
                {
                    "message": message,
                    "error_code": error_code.value,
                    "severity": severity.name,
                    "context": context,
                }
            )

        return {
            "object_id": self.object_id,
            "object_kind": self.object_kind,
            "summary": self.get_summary(),
            "errors_by_category": grouped_errors,
        }

    def get_prioritized_errors(self) -> List[Tuple[str, ValidationErrorCode, Dict[str, Any]]]:
        """Get all errors sorted by priority (critical first).

        Returns:
            List of (message, error_code, context) tuples sorted by severity
        """
        # Sort by severity (critical first), then by order added
        sorted_errors = sorted(
            enumerate(self._errors),
            key=lambda x: (x[1][2].value, x[0]),  # (severity, original_order)
        )

        return [(msg, code, ctx) for _, (msg, code, _, _, ctx) in sorted_errors]

    def create_validation_error(
        self,
        task_type: Optional[str] = None,
        include_detailed_context: bool = False,
    ) -> ValidationError:
        """Create a ValidationError exception from collected errors.

        Args:
            task_type: Type of task (standalone, hierarchy)
            include_detailed_context: Whether to include detailed error breakdown in context

        Returns:
            ValidationError exception with all collected errors
        """
        if not self.has_errors():
            raise ValueError("No errors collected to create exception")

        # Get prioritized errors
        prioritized = self.get_prioritized_errors()

        # Extract messages and codes
        messages = [msg for msg, _, _ in prioritized]
        error_codes = [code for _, code, _ in prioritized]

        # Build context
        context = {}
        if include_detailed_context:
            context["error_details"] = self.get_detailed_view()
        else:
            context["error_summary"] = self.get_summary()

        return ValidationError(
            errors=messages,
            error_codes=error_codes,
            context=context,
            object_id=self.object_id,
            object_kind=self.object_kind,
            task_type=task_type,
        )

    def clear(self) -> None:
        """Clear all collected errors."""
        self._errors.clear()

    def __len__(self) -> int:
        """Return the number of collected errors."""
        return len(self._errors)

    def __bool__(self) -> bool:
        """Return True if there are errors collected."""
        return self.has_errors()
