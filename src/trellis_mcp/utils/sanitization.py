"""Centralized sanitization utilities for secure audit logging."""


def sanitize_for_audit(text: str | None, max_length: int = 50) -> str:
    """
    Sanitize text for safe audit logging by detecting and redacting suspicious patterns.

    Args:
        text: The text to sanitize (can be None)
        max_length: Maximum length before truncation (default: 50)

    Returns:
        Sanitized text safe for audit trails
    """
    if not text:
        return "[EMPTY]"

    # Patterns that could indicate malicious content
    dangerous_patterns = [
        # SQL injection attempts
        "drop",
        "select",
        "insert",
        "update",
        "delete",
        "union",
        "exec",
        # Script injection attempts
        "<script",
        "</script",
        "javascript:",
        "vbscript:",
        # Template injection attempts
        "{{",
        "}}",
        "${",
        "#{",
        # Path traversal attempts
        "../",
        "..\\",
        "/etc/",
        "c:\\",
        "passwd",
        "shadow",
        # Command injection attempts
        "|",
        "&",
        ";",
        "`",
        "$(",
        # Sensitive data patterns
        "secret",
        "password",
        "key",
        "token",
        "api",
        # Other suspicious patterns
        "null",
        "undefined",
        "function(",
        "eval(",
        "alert(",
    ]

    text_lower = text.lower()

    # Check for dangerous patterns
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return "[REDACTED]"

    # Truncate if too long
    if len(text) > max_length:
        return text[:max_length] + "[TRUNCATED]"

    return text
