"""Core message template system.

This module implements the core MessageTemplate and TemplateEngine classes
that provide parameterized error message generation with context awareness.
"""

import re
from typing import Any


class MessageTemplate:
    """A message template with placeholder substitution support.

    Supports parameter substitution using {placeholder} syntax and provides
    metadata for template categorization and context requirements.
    """

    def __init__(
        self,
        template: str,
        category: str,
        description: str = "",
        required_params: list[str] | None = None,
        context_aware: bool = True,
    ):
        """Initialize message template.

        Args:
            template: Template string with {placeholder} syntax
            category: Template category (e.g., 'status', 'parent', 'security')
            description: Human-readable description of template purpose
            required_params: List of required parameter names
            context_aware: Whether template uses context injection
        """
        self.template = template
        self.category = category
        self.description = description
        self.required_params = required_params or []
        self.context_aware = context_aware

        # Extract placeholders from template
        self.placeholders = self._extract_placeholders(template)

        # Validate required params match placeholders
        missing_params = set(self.required_params) - set(self.placeholders)
        if missing_params:
            raise ValueError(
                f"Required parameters {missing_params} not found in template placeholders"
            )

    def _extract_placeholders(self, template: str) -> list[str]:
        """Extract placeholder names from template string.

        Args:
            template: Template string with {placeholder} syntax

        Returns:
            List of placeholder names found in template
        """
        return re.findall(r"\{([^}]+)\}", template)

    def format(self, **kwargs) -> str:
        """Format template with provided parameters.

        Args:
            **kwargs: Parameters to substitute in template

        Returns:
            Formatted message string

        Raises:
            KeyError: If required parameters are missing
        """
        # Check for required parameters
        missing_required = set(self.required_params) - set(kwargs.keys())
        if missing_required:
            raise KeyError(f"Missing required parameters: {missing_required}")

        # Perform substitution
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing parameter for template placeholder: {e}")

    def validate_params(self, **kwargs) -> list[str]:
        """Validate that provided parameters are sufficient for template.

        Args:
            **kwargs: Parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required parameters
        missing_required = set(self.required_params) - set(kwargs.keys())
        if missing_required:
            errors.append(f"Missing required parameters: {missing_required}")

        # Check for unknown parameters (optional - helps catch typos)
        unknown_params = set(kwargs.keys()) - set(self.placeholders)
        if unknown_params:
            errors.append(f"Unknown parameters: {unknown_params}")

        return errors


class TemplateEngine:
    """Template engine with context awareness and parameter injection.

    Provides high-level interface for generating error messages with
    automatic context injection and parameter preprocessing.
    """

    def __init__(self, template_registry=None):
        """Initialize template engine.

        Args:
            template_registry: MessageTemplateRegistry instance
        """
        self.template_registry = template_registry
        self._context_processors = []

    def add_context_processor(self, processor):
        """Add context processor function.

        Context processors are called with (template, data, params) and
        should return updated params dictionary.

        Args:
            processor: Function that processes context
        """
        self._context_processors.append(processor)

    def generate_message(self, template_key: str, data: dict[str, Any], **params) -> str:
        """Generate error message using template and context.

        Args:
            template_key: Template identifier in registry
            data: Object data for context awareness
            **params: Additional parameters for template

        Returns:
            Formatted error message

        Raises:
            KeyError: If template not found
            ValueError: If template validation fails
        """
        if not self.template_registry:
            raise ValueError("No template registry configured")

        # Get template from registry
        template = self.template_registry.get_template(template_key)

        # Process context if template is context-aware
        if template.context_aware:
            params = self._inject_context(template, data, params)

        # Apply context processors
        for processor in self._context_processors:
            params = processor(template, data, params)

        # Format message
        return template.format(**params)

    def _inject_context(
        self, template: MessageTemplate, data: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        """Inject context information into parameters.

        Args:
            template: Message template
            data: Object data for context
            params: Current parameters

        Returns:
            Updated parameters with context injection
        """
        # Import here to avoid circular imports
        from ..context_utils import get_task_type_context

        # Create new params dict to avoid modifying original
        updated_params = params.copy()

        # Inject object kind
        if "object_kind" not in updated_params:
            updated_params["object_kind"] = data.get("kind", "object")

        # Inject task context
        if "task_context" not in updated_params:
            task_context = get_task_type_context(data)
            if task_context:
                updated_params["task_context"] = task_context
            else:
                updated_params["task_context"] = updated_params.get("object_kind", "object")

        # Inject object ID for context
        if "object_id" not in updated_params:
            updated_params["object_id"] = data.get("id", "unknown")

        return updated_params
