"""ID pattern matching system for Trellis MCP object type inference.

This module provides efficient regex-based pattern matching to automatically
detect object types from ID prefixes, supporting both hierarchical and
standalone task systems.
"""

import re
from typing import Final

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..schema.kind_enum import KindEnum


class PatternMatcher:
    """High-performance ID pattern matcher for object kind inference.

    Pre-compiles regex patterns at initialization for optimal pattern matching
    performance (<1ms). Supports both hierarchical objects and standalone tasks
    with comprehensive error handling.

    Pattern Mapping:
        P-xxx -> PROJECT
        E-xxx -> EPIC
        F-xxx -> FEATURE
        T-xxx -> TASK (both hierarchical and standalone)

    Example:
        >>> matcher = PatternMatcher()
        >>> matcher.infer_kind("P-user-auth-system")
        'project'
        >>> matcher.infer_kind("T-implement-login")
        'task'
        >>> matcher.validate_id_format("F-user-registration")
        True
    """

    # Pre-compiled regex patterns for maximum performance
    # Patterns ensure valid prefix, no consecutive hyphens, and valid suffix
    _PATTERNS: Final[dict[KindEnum, re.Pattern[str]]] = {
        KindEnum.PROJECT: re.compile(r"^P-[a-z0-9]+(?:-[a-z0-9]+)*$"),
        KindEnum.EPIC: re.compile(r"^E-[a-z0-9]+(?:-[a-z0-9]+)*$"),
        KindEnum.FEATURE: re.compile(r"^F-[a-z0-9]+(?:-[a-z0-9]+)*$"),
        KindEnum.TASK: re.compile(r"^T-[a-z0-9]+(?:-[a-z0-9]+)*$"),
    }

    def __init__(self):
        """Initialize pattern matcher with pre-compiled regex patterns.

        Patterns are compiled once at initialization for optimal performance
        in subsequent matching operations.
        """
        # Patterns are already compiled as class constants for thread safety
        # and memory efficiency
        pass

    def infer_kind(self, object_id: str) -> str:
        """Infer object kind from ID prefix pattern.

        Analyzes the object ID to determine its type based on prefix patterns.
        Returns the corresponding KindEnum value for valid patterns.

        Args:
            object_id: The object ID to analyze (e.g., "P-auth-system")

        Returns:
            The KindEnum value ("project", "epic", "feature", or "task")

        Raises:
            ValidationError: If object_id is empty, None, or doesn't match
                any valid pattern

        Example:
            >>> matcher.infer_kind("P-user-management")
            'project'
            >>> matcher.infer_kind("T-create-login-form")
            'task'
        """
        # Validate input
        if not isinstance(object_id, str):
            if object_id is None:
                raise ValidationError(
                    errors=["Object ID cannot be empty"],
                    error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                    context={"object_id": object_id},
                )
            else:
                raise ValidationError(
                    errors=["Object ID must be a string"],
                    error_codes=[ValidationErrorCode.INVALID_FIELD],
                    context={"object_id": object_id, "type": type(object_id).__name__},
                )

        if not object_id:
            raise ValidationError(
                errors=["Object ID cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"object_id": object_id},
            )

        # Check each pattern for a match
        for kind, pattern in self._PATTERNS.items():
            if pattern.match(object_id):
                return kind.value

        # No pattern matched - provide helpful error message
        prefix = self._extract_prefix(object_id)
        error_msg = self._format_pattern_error(object_id, prefix)

        raise ValidationError(
            errors=[error_msg],
            error_codes=[ValidationErrorCode.INVALID_FORMAT],
            context={
                "object_id": object_id,
                "extracted_prefix": prefix,
                "valid_prefixes": ["P-", "E-", "F-", "T-"],
            },
        )

    def validate_id_format(self, object_id: str) -> bool:
        """Validate that an ID follows expected pattern format.

        Checks if the object ID matches any of the supported pattern formats
        without raising exceptions. Useful for non-critical validation checks.

        Args:
            object_id: The object ID to validate

        Returns:
            True if ID matches any valid pattern, False otherwise

        Example:
            >>> matcher.validate_id_format("P-auth-system")
            True
            >>> matcher.validate_id_format("invalid-id")
            False
            >>> matcher.validate_id_format("")
            False
        """
        if not object_id or not isinstance(object_id, str):
            return False

        # Check if any pattern matches
        return any(pattern.match(object_id) for pattern in self._PATTERNS.values())

    def _extract_prefix(self, object_id: str) -> str | None:
        """Extract prefix from object ID for error reporting.

        Args:
            object_id: The object ID to extract prefix from

        Returns:
            The prefix (e.g., "P-", "X-") or None if no hyphen found
        """
        if not object_id:
            return None

        hyphen_index = object_id.find("-")
        if hyphen_index > 0:
            return object_id[: hyphen_index + 1]
        return None

    def _format_pattern_error(self, object_id: str, prefix: str | None) -> str:
        """Format descriptive error message for pattern matching failures.

        Args:
            object_id: The invalid object ID
            prefix: The extracted prefix (if any)

        Returns:
            Formatted error message with suggestions
        """
        if not prefix:
            return (
                f"Invalid object ID format '{object_id}'. "
                f"Expected format: [PREFIX]-[name] where PREFIX is one of: P, E, F, T"
            )

        # Handle common prefix issues
        clean_prefix = prefix.rstrip("-")
        if clean_prefix.upper() in ["P", "E", "F", "T"]:
            if clean_prefix.islower():
                return (
                    f"Invalid prefix '{prefix}' in object ID '{object_id}'. "
                    f"Prefix must be uppercase. Did you mean '{clean_prefix.upper()}-'?"
                )
            elif clean_prefix.isupper():
                # Check if the issue is with the suffix format
                suffix = object_id[len(prefix) :]
                if not re.match(r"^[a-z0-9-]+$", suffix):
                    return (
                        f"Invalid suffix '{suffix}' in object ID '{object_id}'. "
                        f"Suffix must contain only lowercase letters, numbers, and hyphens"
                    )

        return (
            f"Unrecognized prefix '{prefix}' in object ID '{object_id}'. "
            f"Valid prefixes are: P- (project), E- (epic), F- (feature), T- (task)"
        )
