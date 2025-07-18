"""Message formatters for different output formats.

This module provides formatters for converting error messages into
different output formats for various use cases.
"""

from typing import Any


class MessageFormatter:
    """Base class for message formatters."""

    def format(self, message: str, **metadata) -> Any:
        """Format message with optional metadata.

        Args:
            message: The error message to format
            **metadata: Additional metadata about the error

        Returns:
            Formatted message in target format
        """
        raise NotImplementedError("Subclasses must implement format method")


class PlainTextFormatter(MessageFormatter):
    """Plain text formatter for simple string output."""

    def format(self, message: str, **metadata) -> str:
        """Format message as plain text.

        Args:
            message: The error message to format
            **metadata: Additional metadata (ignored)

        Returns:
            Plain text message
        """
        return message


class StructuredFormatter(MessageFormatter):
    """Structured formatter for API responses and structured data."""

    def format(self, message: str, **metadata) -> dict[str, Any]:
        """Format message as structured data.

        Args:
            message: The error message to format
            **metadata: Additional metadata to include

        Returns:
            Dictionary with message and metadata
        """
        return {
            "message": message,
            "metadata": metadata,
        }


class ValidationErrorFormatter(MessageFormatter):
    """Formatter for ValidationError-compatible output."""

    def format(self, message: str, **metadata) -> dict[str, Any]:
        """Format message for ValidationError structures.

        Args:
            message: The error message to format
            **metadata: Additional metadata (error_code, object_id, etc.)

        Returns:
            Dictionary compatible with ValidationError.to_dict()
        """
        return {
            "message": message,
            "error_code": metadata.get("error_code", "VALIDATION_ERROR"),
            "object_id": metadata.get("object_id"),
            "object_kind": metadata.get("object_kind"),
            "task_type": metadata.get("task_type"),
            "context": metadata.get("context", {}),
        }


class I18nFormatter(MessageFormatter):
    """Internationalization formatter for future localization support."""

    def __init__(self, locale: str = "en_US"):
        """Initialize I18n formatter.

        Args:
            locale: Target locale for formatting
        """
        self.locale = locale

    def format(self, message: str, **metadata) -> dict[str, Any]:
        """Format message with internationalization support.

        Args:
            message: The error message to format
            **metadata: Additional metadata including i18n keys

        Returns:
            Dictionary with message and i18n metadata
        """
        return {
            "message": message,
            "locale": self.locale,
            "message_key": metadata.get("message_key"),
            "parameters": metadata.get("parameters", {}),
            "metadata": metadata,
        }


# Default formatter instances
DEFAULT_FORMATTERS = {
    "plain": PlainTextFormatter(),
    "structured": StructuredFormatter(),
    "validation": ValidationErrorFormatter(),
    "i18n": I18nFormatter(),
}


def get_formatter(format_type: str) -> MessageFormatter:
    """Get formatter by type.

    Args:
        format_type: Type of formatter ('plain', 'structured', 'validation', 'i18n')

    Returns:
        MessageFormatter instance

    Raises:
        ValueError: If format type is not supported
    """
    if format_type not in DEFAULT_FORMATTERS:
        raise ValueError(f"Unsupported format type: {format_type}")

    return DEFAULT_FORMATTERS[format_type]
