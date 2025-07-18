"""Security validation functions for standalone tasks.

This module provides security validation functions to prevent privilege
escalation and validation bypass attempts through field manipulation.
"""

import re
import time
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


def sanitize_error_message(message: str | None) -> str | None:
    """Sanitize error messages to prevent information disclosure.

    This function removes or obfuscates sensitive information from error messages
    to prevent attackers from gaining insight into system internals.

    Args:
        message: The original error message

    Returns:
        Sanitized error message safe for display
    """
    if not message:
        return message

    # Patterns that indicate sensitive information
    sensitive_patterns = [
        # Stack traces - handle these first to avoid interference with path patterns
        (r'File "[^"]+",\s*line \d+', 'File "[REDACTED]", line [REDACTED]'),
        (r"at [^(]+\([^)]+\)", "at [REDACTED]"),
        # Database connection strings
        (r"(postgresql|mysql|sqlite|mongodb)://[^\s]+", "[REDACTED_CONNECTION]"),
        # API keys and tokens (basic patterns)
        (r"[Tt]oken[:\s]+[A-Za-z0-9_-]{15,}", "Token: [REDACTED_TOKEN]"),
        (r"[Kk]ey[:\s]+[A-Za-z0-9_-]{15,}", "Key: [REDACTED_KEY]"),
        # UUIDs that might be internal IDs
        (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "[REDACTED_UUID]"),
        # Environment variables
        (r"[A-Z_]+=[^\s]+", "[REDACTED_ENV]"),
        # IP addresses
        (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_IP]"),
        # File paths (put these after stack traces to avoid conflicts)
        (r"(/[^/\s]+)+/[^/\s]+\.[^/\s]+", "[REDACTED_PATH]"),
        (r"[A-Za-z]:\\[^\\]+(?:\\[^\\]+)*", "[REDACTED_PATH]"),
    ]

    sanitized = message
    for pattern, replacement in sensitive_patterns:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized


def create_consistent_error_response(
    error_message: str, error_type: str = "validation"
) -> dict[str, Any]:
    """Create a consistent error response with timing protection.

    This function ensures all error responses have consistent timing and structure
    to prevent timing attacks and information disclosure.

    Args:
        error_message: The error message to include
        error_type: The type of error (for categorization)

    Returns:
        Dictionary with consistent error response structure
    """
    # Add a small, consistent delay to prevent timing attacks
    # This helps ensure all error responses take similar time
    time.sleep(0.001)  # 1ms delay

    sanitized_message = sanitize_error_message(error_message)

    return {
        "error": True,
        "message": sanitized_message,
        "type": error_type,
        "timestamp": time.time(),
    }


def audit_security_error(error_message: str, context: dict[str, Any] | None = None) -> None:
    """Audit security-related errors for monitoring purposes.

    This function logs security-related errors in a structured format
    for security monitoring and analysis.

    Args:
        error_message: The security error message
        context: Additional context information
    """
    import logging

    # Get or create security logger
    logger = logging.getLogger("trellis_mcp.security")

    # Sanitize context to prevent log injection
    safe_context = filter_sensitive_information(context) if context else {}

    # Log security event
    logger.warning(
        "Security validation failure: %s",
        sanitize_error_message(error_message),
        extra={"security_context": safe_context},
    )


def validate_error_message_safety(message: str | None) -> list[str]:
    """Validate that an error message is safe for display.

    This function checks error messages for potentially sensitive information
    that should not be exposed to users.

    Args:
        message: The error message to validate

    Returns:
        List of security issues found (empty if safe)
    """
    if not message:
        return []

    issues = []

    # Check for potentially sensitive information
    sensitive_checks = [
        (r"password|passwd|pwd", "Error message contains password-related information"),
        (r"secret|token|key", "Error message contains secret/token information"),
        (r"/[^/\s]+(?:/[^/\s]+){3,}", "Error message contains detailed file paths"),
        (r"[A-Za-z]:\\[^\\]+(?:\\[^\\]+){3,}", "Error message contains detailed Windows paths"),
        (r"(?i)sql.*(error|exception)", "Error message contains database error details"),
        (r"(?i)stack\s*trace", "Error message contains stack trace information"),
        (r"(?i)internal\s*error", "Error message exposes internal system details"),
        (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "Error message contains IP addresses"),
        (r":\d{4,5}\b", "Error message contains port numbers"),
    ]

    for pattern, issue in sensitive_checks:
        if re.search(pattern, message, re.IGNORECASE):
            issues.append(issue)

    return issues


def filter_sensitive_information(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Filter sensitive information from error context data.

    This function removes or obfuscates sensitive information from error
    context dictionaries to prevent information disclosure.

    Args:
        data: The error context data

    Returns:
        Filtered data with sensitive information removed
    """
    if not data:
        return data

    # Fields that should be removed entirely
    sensitive_fields = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "key",
        "api_key",
        "auth_token",
        "session_id",
        "csrf_token",
        "private_key",
        "cert",
        "certificate",
        "credential",
        "connection_string",
        "database_url",
    }

    # Fields that should be obfuscated
    obfuscate_fields = {
        "email",
        "username",
        "user_id",
        "id",
        "path",
        "file_path",
        "directory",
        "url",
        "host",
        "hostname",
        "ip",
        "address",
    }

    filtered = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Skip sensitive fields entirely
        if any(sensitive in key_lower for sensitive in sensitive_fields):
            continue

        # Obfuscate certain fields
        if any(field in key_lower for field in obfuscate_fields):
            if isinstance(value, str) and len(value) > 4:
                filtered[key] = value[:2] + "***" + value[-2:]
            else:
                filtered[key] = "***"
        else:
            # Keep non-sensitive fields
            if isinstance(value, str):
                filtered[key] = sanitize_error_message(value)
            else:
                filtered[key] = value

    return filtered


def validate_path_boundaries(path: str, allowed_root: str) -> list[str]:
    """Validate that a path stays within allowed boundaries.

    This function ensures that resolved paths remain within the designated
    project boundaries and prevents path traversal attacks.

    Args:
        path: The path to validate
        allowed_root: The root directory path that should contain the resolved path

    Returns:
        List of validation errors (empty if valid)
    """
    import os
    from pathlib import Path

    errors = []

    try:
        # Resolve both paths to absolute paths
        resolved_path = Path(path).resolve()
        resolved_root = Path(allowed_root).resolve()

        # Check if the resolved path is within the allowed root
        try:
            resolved_path.relative_to(resolved_root)
        except ValueError:
            errors.append(f"Path '{path}' resolves outside allowed boundary '{allowed_root}'")
            audit_security_error(
                f"Path boundary violation: {path} outside {allowed_root}",
                {"path": path, "allowed_root": allowed_root},
            )

        # Check for symbolic link attacks (check the original path, not resolved)
        original_path = Path(path)
        if original_path.is_symlink():
            # Get the target of the symlink
            link_target = original_path.readlink()
            if link_target.is_absolute():
                errors.append(f"Path '{path}' contains absolute symbolic link which is not allowed")
                audit_security_error(
                    f"Absolute symbolic link detected: {path} -> {link_target}",
                    {"path": path, "link_target": str(link_target)},
                )
            else:
                # Check if relative symlink stays within bounds
                final_target = (original_path.parent / link_target).resolve()
                try:
                    final_target.relative_to(resolved_root)
                except ValueError:
                    errors.append(
                        f"Path '{path}' contains symbolic link that points outside allowed boundary"
                    )
                    audit_security_error(
                        f"Symbolic link boundary violation: {path} -> {final_target}",
                        {"path": path, "final_target": str(final_target)},
                    )

        # Check for directory traversal patterns that might have been missed
        normalized_path = os.path.normpath(path)
        if ".." in normalized_path:
            errors.append(
                f"Path '{path}' contains directory traversal sequences after normalization"
            )
            audit_security_error(
                f"Directory traversal detected in normalized path: {normalized_path}",
                {"original_path": path, "normalized_path": normalized_path},
            )

    except (OSError, ValueError) as e:
        errors.append(f"Path validation failed: {sanitize_error_message(str(e))}")
        audit_security_error(
            f"Path validation error: {e}", {"path": path, "error_type": type(e).__name__}
        )

    return errors


def validate_path_construction_security(
    path_components: list[str], allow_absolute_root: bool = True
) -> list[str]:
    """Validate security of path construction operations.

    This function validates that path components are safe for filesystem
    operations and don't contain injection attempts.

    Args:
        path_components: List of path components to validate
        allow_absolute_root: Whether to allow absolute paths for the first component (default: True)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    for i, component in enumerate(path_components):
        if not component:
            continue

        # Check for path traversal attempts in individual components
        if ".." in component:
            errors.append(
                f"Path component {i} contains directory traversal sequence: '{component}'"
            )
            audit_security_error(
                f"Path traversal in component {i}: {component}",
                {"component_index": i, "component": component},
            )

        # Check for absolute path injection (but allow absolute root path)
        is_absolute = component.startswith("/") or (len(component) > 1 and component[1] == ":")
        if is_absolute and not (i == 0 and allow_absolute_root):
            errors.append(f"Path component {i} contains absolute path injection: '{component}'")
            audit_security_error(
                f"Absolute path injection in component {i}: {component}",
                {"component_index": i, "component": component},
            )

        # Check for null byte injection
        if "\x00" in component:
            errors.append(f"Path component {i} contains null byte injection: '{component}'")
            audit_security_error(
                f"Null byte injection in component {i}: {component}",
                {"component_index": i, "component": component},
            )

        # Check for control characters
        if any(ord(c) < 32 and c not in ["\t", "\n", "\r"] for c in component):
            errors.append(f"Path component {i} contains control characters: '{component}'")
            audit_security_error(
                f"Control characters in component {i}: {component}",
                {"component_index": i, "component": component},
            )

        # Check for reserved names (Windows compatibility)
        reserved_names = {
            "con",
            "prn",
            "aux",
            "nul",
            "com1",
            "com2",
            "com3",
            "com4",
            "com5",
            "com6",
            "com7",
            "com8",
            "com9",
            "lpt1",
            "lpt2",
            "lpt3",
            "lpt4",
            "lpt5",
            "lpt6",
            "lpt7",
            "lpt8",
            "lpt9",
        }
        if component.lower() in reserved_names:
            errors.append(f"Path component {i} uses reserved system name: '{component}'")
            audit_security_error(
                f"Reserved name in component {i}: {component}",
                {"component_index": i, "component": component},
            )

    return errors


def validate_standalone_task_path_security(
    task_id: str | None, project_root: str | None, resolved_path: str | None = None
) -> list[str]:
    """Enhanced security validation for standalone task paths.

    This function provides comprehensive security validation specifically
    for standalone task path operations, including boundary validation
    and path construction security.

    Args:
        task_id: The task ID being validated
        project_root: The project root directory
        resolved_path: Optional resolved path for boundary validation

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Handle None inputs gracefully
    if task_id is None:
        errors.append("Task ID cannot be None")
        return errors

    if project_root is None:
        errors.append("Project root cannot be None")
        return errors

    # Basic task ID validation
    if not task_id or not task_id.strip():
        errors.append("Task ID cannot be empty")
        return errors

    # Clean the task ID
    clean_id = task_id.strip()
    if clean_id.startswith("T-"):
        clean_id = clean_id[2:]

    # Path construction security validation
    path_components = [project_root, "tasks-open", f"T-{clean_id}.md"]
    construction_errors = validate_path_construction_security(path_components)
    errors.extend(construction_errors)

    # Path boundary validation if resolved path is provided
    if resolved_path:
        boundary_errors = validate_path_boundaries(resolved_path, project_root)
        errors.extend(boundary_errors)

    # Additional standalone task specific validations
    if clean_id.startswith("."):
        errors.append("Task ID cannot start with dot (hidden file protection)")
        audit_security_error(
            f"Task ID starts with dot: {clean_id}", {"task_id": task_id, "clean_id": clean_id}
        )

    # Check for file extension injection
    if "." in clean_id and not clean_id.endswith(".md"):
        # Allow .md extension but be suspicious of other extensions
        if any(clean_id.endswith(ext) for ext in [".exe", ".bat", ".sh", ".py", ".js"]):
            errors.append(f"Task ID contains suspicious file extension: '{clean_id}'")
            audit_security_error(
                f"Suspicious file extension in task ID: {clean_id}",
                {"task_id": task_id, "clean_id": clean_id},
            )

    # Check for URL encoding attempts
    if "%" in clean_id:
        errors.append(f"Task ID contains URL encoding sequences: '{clean_id}'")
        audit_security_error(
            f"URL encoding in task ID: {clean_id}", {"task_id": task_id, "clean_id": clean_id}
        )

    return errors
