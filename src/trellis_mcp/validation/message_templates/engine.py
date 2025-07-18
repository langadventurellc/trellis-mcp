"""High-level message template engine with default configuration.

This module provides a pre-configured message template engine with
default templates and context processors for easy integration.
"""

from typing import Any

from .core import TemplateEngine
from .formatters import get_formatter
from .registry import MessageTemplateRegistry
from .templates import get_default_templates


class TrellisMessageEngine:
    """High-level message template engine for Trellis MCP.

    Provides a pre-configured template engine with default templates,
    formatters, and context processors for validation error messages.
    """

    def __init__(self):
        """Initialize Trellis message engine with defaults."""
        # Create registry and load default templates
        self.registry = MessageTemplateRegistry()
        self.registry.register_templates(get_default_templates())

        # Create template engine
        self.engine = TemplateEngine(self.registry)

        # Add default context processors
        self._add_default_context_processors()

    def _add_default_context_processors(self):
        """Add default context processors for common patterns."""

        def format_list_processor(template, data, params):
            """Process list parameters for consistent formatting."""
            updated_params = params.copy()

            # Format lists as comma-separated strings
            for key, value in params.items():
                if isinstance(value, list):
                    if key in ["fields", "valid_transitions"]:
                        updated_params[key] = ", ".join(str(v) for v in value)
                    elif key == "valid_values":
                        # Keep original list format for backward compatibility
                        updated_params[key] = str(value)
                    elif key == "cycle_path":
                        updated_params[key] = " -> ".join(str(v) for v in value)

            return updated_params

        def status_processor(template, data, params):
            """Process status-related parameters."""
            updated_params = params.copy()

            # Convert status enums to strings
            for key in ["value", "old_status", "new_status"]:
                if key in params and hasattr(params[key], "value"):
                    updated_params[key] = params[key].value

            return updated_params

        self.engine.add_context_processor(format_list_processor)
        self.engine.add_context_processor(status_processor)

    def generate_message(
        self, template_key: str, data: dict[str, Any], format_type: str = "plain", **params
    ) -> Any:
        """Generate formatted error message.

        Args:
            template_key: Template identifier
            data: Object data for context
            format_type: Output format ('plain', 'structured', 'validation', 'i18n')
            **params: Template parameters

        Returns:
            Formatted message in requested format
        """
        # Generate message using template engine
        message = self.engine.generate_message(template_key, data, **params)

        # Format message
        formatter = get_formatter(format_type)

        # Prepare metadata for formatter
        metadata = {
            "template_key": template_key,
            "object_id": data.get("id"),
            "object_kind": data.get("kind"),
            "task_type": self._get_task_type(data),
            "context": data,
        }

        return formatter.format(message, **metadata)

    def _get_task_type(self, data: dict[str, Any]) -> str | None:
        """Get task type from data.

        Args:
            data: Object data

        Returns:
            Task type string or None
        """
        from ..context_utils import get_task_type_context

        task_context = get_task_type_context(data)
        if task_context:
            return task_context.replace(" ", "_")  # Convert to snake_case
        return None

    def add_custom_template(self, key: str, template_config: dict[str, Any]):
        """Add custom template to registry.

        Args:
            key: Template identifier
            template_config: Template configuration dictionary
        """
        from .core import MessageTemplate

        template = MessageTemplate(
            template=template_config["template"],
            category=template_config["category"],
            description=template_config.get("description", ""),
            required_params=template_config.get("required_params"),
            context_aware=template_config.get("context_aware", True),
        )

        self.registry.register_template(key, template)

    def get_available_templates(self) -> list[str]:
        """Get list of available template keys.

        Returns:
            List of template identifiers
        """
        return list(self.registry.get_all_templates().keys())

    def get_templates_by_category(self, category: str) -> list[str]:
        """Get template keys by category.

        Args:
            category: Category name

        Returns:
            List of template identifiers in category
        """
        templates = self.registry.get_templates_by_category(category)
        return list(templates.keys())


# Global instance for easy access
_default_engine = None


def get_default_engine() -> TrellisMessageEngine:
    """Get the default message engine instance.

    Returns:
        Shared TrellisMessageEngine instance
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = TrellisMessageEngine()
    return _default_engine


def generate_template_message(
    template_key: str, data: dict[str, Any], format_type: str = "plain", **params
) -> Any:
    """Generate message using default engine.

    Convenience function for generating messages with the default engine.

    Args:
        template_key: Template identifier
        data: Object data for context
        format_type: Output format
        **params: Template parameters

    Returns:
        Formatted message
    """
    engine = get_default_engine()
    return engine.generate_message(template_key, data, format_type, **params)
