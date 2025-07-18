"""Message template registry for centralized template management.

This module provides the MessageTemplateRegistry class that manages
template storage, loading, and retrieval with support for categories
and runtime template registration.
"""

from typing import Any

from .core import MessageTemplate


class MessageTemplateRegistry:
    """Registry for managing message templates with categorization and lookup.

    Provides centralized storage and management of message templates with
    support for categories, runtime registration, and template overrides.
    """

    def __init__(self):
        """Initialize empty template registry."""
        self._templates: dict[str, MessageTemplate] = {}
        self._categories: dict[str, set[str]] = {}

    def register_template(self, key: str, template: MessageTemplate) -> None:
        """Register a message template.

        Args:
            key: Unique identifier for template
            template: MessageTemplate instance

        Raises:
            ValueError: If template is invalid
        """
        if not isinstance(template, MessageTemplate):
            raise ValueError("Template must be MessageTemplate instance")

        # Register template
        self._templates[key] = template

        # Update category index
        if template.category not in self._categories:
            self._categories[template.category] = set()
        self._categories[template.category].add(key)

    def register_templates(self, templates: dict[str, MessageTemplate]) -> None:
        """Register multiple templates at once.

        Args:
            templates: Dictionary of template key to MessageTemplate
        """
        for key, template in templates.items():
            self.register_template(key, template)

    def get_template(self, key: str) -> MessageTemplate:
        """Get template by key.

        Args:
            key: Template identifier

        Returns:
            MessageTemplate instance

        Raises:
            KeyError: If template not found
        """
        if key not in self._templates:
            raise KeyError(f"Template '{key}' not found in registry")

        return self._templates[key]

    def has_template(self, key: str) -> bool:
        """Check if template exists in registry.

        Args:
            key: Template identifier

        Returns:
            True if template exists
        """
        return key in self._templates

    def get_templates_by_category(self, category: str) -> dict[str, MessageTemplate]:
        """Get all templates in a category.

        Args:
            category: Category name

        Returns:
            Dictionary of template keys to MessageTemplate instances
        """
        if category not in self._categories:
            return {}

        return {key: self._templates[key] for key in self._categories[category]}

    def get_all_templates(self) -> dict[str, MessageTemplate]:
        """Get all registered templates.

        Returns:
            Dictionary of all templates keyed by identifier
        """
        return self._templates.copy()

    def get_categories(self) -> list[str]:
        """Get list of all categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def remove_template(self, key: str) -> None:
        """Remove template from registry.

        Args:
            key: Template identifier

        Raises:
            KeyError: If template not found
        """
        if key not in self._templates:
            raise KeyError(f"Template '{key}' not found in registry")

        template = self._templates[key]

        # Remove from templates
        del self._templates[key]

        # Remove from category index
        if template.category in self._categories:
            self._categories[template.category].discard(key)

            # Remove empty category
            if not self._categories[template.category]:
                del self._categories[template.category]

    def clear(self) -> None:
        """Clear all templates from registry."""
        self._templates.clear()
        self._categories.clear()

    def load_from_dict(self, template_data: dict[str, dict[str, Any]]) -> None:
        """Load templates from dictionary configuration.

        Args:
            template_data: Dictionary with template configurations
                Each key is template identifier, value is dict with:
                - template: Template string
                - category: Category name
                - description: Optional description
                - required_params: Optional list of required parameters
                - context_aware: Optional boolean (default True)
        """
        for key, config in template_data.items():
            template = MessageTemplate(
                template=config["template"],
                category=config["category"],
                description=config.get("description", ""),
                required_params=config.get("required_params"),
                context_aware=config.get("context_aware", True),
            )
            self.register_template(key, template)

    def export_to_dict(self) -> dict[str, dict[str, Any]]:
        """Export templates to dictionary format.

        Returns:
            Dictionary suitable for serialization or loading
        """
        return {
            key: {
                "template": template.template,
                "category": template.category,
                "description": template.description,
                "required_params": template.required_params,
                "context_aware": template.context_aware,
            }
            for key, template in self._templates.items()
        }
