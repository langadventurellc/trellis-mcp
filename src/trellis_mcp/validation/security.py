"""Security validation functions for standalone tasks.

This module provides security validation functions to prevent privilege
escalation and validation bypass attempts through field manipulation.
"""

from typing import Any


def validate_standalone_task_security(data: dict[str, Any]) -> list[str]:
    """Validate security constraints for standalone tasks.

    This function implements security validation to ensure standalone tasks don't
    introduce privilege escalation opportunities or allow validation bypass through
    parent field manipulation.

    Note: Security validation is only performed for schema version 1.1 as schema 1.0
    does not support standalone tasks.

    Args:
        data: The object data dictionary

    Returns:
        List of security validation errors (empty if valid)
    """
    errors = []

    # Only validate if this is a task object
    if data.get("kind") != "task":
        return errors

    # Skip security validation for schema 1.0 - standalone tasks not supported
    schema_version = data.get("schema_version", "1.1")
    if schema_version == "1.0":
        return errors

    # Get parent field value
    parent = data.get("parent")

    # Security check: Ensure parent field consistency
    # If parent is None or empty string, this should be a standalone task
    if parent is None or parent == "":
        # Valid standalone task - no additional security checks needed
        return errors

    # Security check: Prevent privilege escalation through parent field manipulation
    # If parent is present, ensure it's not attempting to bypass validation
    if isinstance(parent, str):
        # Check for suspicious parent values that might indicate bypass attempts
        suspicious_patterns = [
            "..",  # Path traversal attempts
            "/",  # Absolute path attempts (only at start)
            "\\",  # Windows path attempts
            "null",  # String representation of null
            "none",  # String representation of none
            "undefined",  # JavaScript-style undefined
            "{}",  # Empty object representation
            "[]",  # Empty array representation
            "false",  # Boolean false as string
            "true",  # Boolean true as string
        ]

        # Check for suspicious patterns (case-insensitive)
        parent_lower = parent.lower().strip()
        for pattern in suspicious_patterns:
            if pattern == "/" and parent_lower.startswith("/"):
                # Only flag absolute paths (starting with /)
                errors.append(
                    f"Security validation failed: parent field contains "
                    f"suspicious pattern '{pattern}'"
                )
                break
            elif pattern in ["..", "\\"]:
                # Check for path traversal and backslash patterns as substrings
                if pattern in parent_lower:
                    errors.append(
                        f"Security validation failed: parent field contains "
                        f"suspicious pattern '{pattern}'"
                    )
                    break
            elif pattern != "/" and pattern == parent_lower:
                # Only flag exact matches for other patterns to avoid false positives
                errors.append(
                    f"Security validation failed: parent field contains "
                    f"suspicious pattern '{pattern}'"
                )
                break

        # Check for specific whitespace characters that might indicate bypass attempts
        if parent in [" ", "\t", "\n", "\r"]:
            errors.append(
                f"Security validation failed: parent field contains "
                f"suspicious pattern '{repr(parent)}'"
            )
        elif parent.strip() == "":
            errors.append("Security validation failed: parent field contains only whitespace")

        # Check for numeric-only parent values that might indicate bypass attempts
        if parent.strip() in ["0", "1"]:
            errors.append(
                f"Security validation failed: parent field contains "
                f"suspicious pattern '{parent.strip()}'"
            )

        # Check for excessively long parent values (potential buffer overflow attempt)
        if len(parent) > 255:
            errors.append(
                "Security validation failed: parent field exceeds maximum length "
                "(255 characters)"
            )

        # Check for control characters that might indicate injection attempts
        if any(ord(c) < 32 for c in parent if c not in ["\t", "\n", "\r"]):
            errors.append("Security validation failed: parent field contains control characters")

    # Security check: Ensure no privilege escalation through field manipulation
    # Tasks should not have certain privileged fields that could indicate bypass attempts
    privileged_fields = [
        "system_admin",
        "root_access",
        "privileged",
        "admin",
        "superuser",
        "elevated",
        "bypass_validation",
        "skip_checks",
        "ignore_constraints",
    ]

    for field in privileged_fields:
        if field in data:
            errors.append(f"Security validation failed: privileged field '{field}' is not allowed")

    return errors
