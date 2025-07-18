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
                    _generate_security_error(
                        "suspicious_pattern", data, field="parent", pattern=pattern
                    )
                )
                break
            elif pattern in ["..", "\\"]:
                # Check for path traversal and backslash patterns as substrings
                if pattern in parent_lower:
                    errors.append(
                        _generate_security_error(
                            "suspicious_pattern", data, field="parent", pattern=pattern
                        )
                    )
                    break
            elif pattern != "/" and pattern == parent_lower:
                # Only flag exact matches for other patterns to avoid false positives
                errors.append(
                    _generate_security_error(
                        "suspicious_pattern", data, field="parent", pattern=pattern
                    )
                )
                break

        # Check for specific whitespace characters that might indicate bypass attempts
        if parent in [" ", "\t", "\n", "\r"]:
            errors.append(
                _generate_security_error(
                    "suspicious_pattern", data, field="parent", pattern=repr(parent)
                )
            )
        elif parent.strip() == "":
            errors.append(_generate_security_error("whitespace_only", data, field="parent"))

        # Check for numeric-only parent values that might indicate bypass attempts
        if parent.strip() in ["0", "1"]:
            errors.append(
                _generate_security_error(
                    "suspicious_pattern", data, field="parent", pattern=parent.strip()
                )
            )

        # Check for excessively long parent values (potential buffer overflow attempt)
        if len(parent) > 255:
            errors.append(
                _generate_security_error(
                    "max_length_exceeded", data, field="parent", max_length="255"
                )
            )

        # Check for control characters that might indicate injection attempts
        if any(ord(c) < 32 for c in parent if c not in ["\t", "\n", "\r"]):
            errors.append(_generate_security_error("control_characters", data, field="parent"))

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
            errors.append(_generate_security_error("privileged_field", data, field=field))

    return errors


def _generate_security_error(error_type: str, data: dict[str, Any], **kwargs) -> str:
    """Generate security error message using template system with fallback.

    Args:
        error_type: Type of security error
        data: Object data for context
        **kwargs: Additional parameters for message generation

    Returns:
        Formatted error message string
    """
    try:
        from .message_templates import generate_template_message

        # Map error types to template keys
        template_mapping = {
            "suspicious_pattern": "security.suspicious_pattern",
            "privileged_field": "security.privileged_field",
            "whitespace_only": "security.whitespace_only",
            "control_characters": "security.control_characters",
            "max_length_exceeded": "security.max_length_exceeded",
        }

        template_key = template_mapping.get(error_type)
        if template_key:
            return generate_template_message(template_key, data, **kwargs)

    except (ImportError, KeyError):
        # Fall back to hardcoded messages if template system fails
        pass

    # Fallback messages for backward compatibility
    if error_type == "suspicious_pattern":
        field = kwargs.get("field", "field")
        pattern = kwargs.get("pattern", "unknown")
        return f"Security validation failed: {field} field contains suspicious pattern '{pattern}'"
    elif error_type == "privileged_field":
        field = kwargs.get("field", "field")
        return f"Security validation failed: privileged field '{field}' is not allowed"
    elif error_type == "whitespace_only":
        field = kwargs.get("field", "field")
        return f"Security validation failed: {field} field contains only whitespace"
    elif error_type == "control_characters":
        field = kwargs.get("field", "field")
        return f"Security validation failed: {field} field contains control characters"
    elif error_type == "max_length_exceeded":
        field = kwargs.get("field", "field")
        max_length = kwargs.get("max_length", "unknown")
        return (
            f"Security validation failed: {field} field exceeds maximum length "
            f"({max_length} characters)"
        )

    # Default fallback
    return f"Security validation failed: {error_type}"
