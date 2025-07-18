"""Tests for the message template system."""

import pytest

from src.trellis_mcp.validation.message_templates import (
    MessageTemplate,
    MessageTemplateRegistry,
    TemplateEngine,
    TrellisMessageEngine,
    generate_template_message,
    get_default_engine,
    get_default_templates,
    get_formatter,
)
from src.trellis_mcp.validation.message_templates.formatters import (
    PlainTextFormatter,
    StructuredFormatter,
    ValidationErrorFormatter,
)


class TestMessageTemplate:
    """Test MessageTemplate class."""

    def test_basic_template_creation(self):
        """Test basic template creation and formatting."""
        template = MessageTemplate(
            template="Hello {name}!",
            category="greeting",
            description="Basic greeting template",
            required_params=["name"],
        )

        assert template.template == "Hello {name}!"
        assert template.category == "greeting"
        assert template.description == "Basic greeting template"
        assert template.required_params == ["name"]
        assert template.placeholders == ["name"]
        assert template.context_aware is True

    def test_template_formatting(self):
        """Test template parameter substitution."""
        template = MessageTemplate(
            template="Invalid {field} '{value}' for {object_kind}",
            category="validation",
            required_params=["field", "value", "object_kind"],
        )

        result = template.format(field="status", value="invalid", object_kind="task")
        assert result == "Invalid status 'invalid' for task"

    def test_template_missing_required_params(self):
        """Test error when required parameters are missing."""
        template = MessageTemplate(
            template="Hello {name}!",
            category="greeting",
            required_params=["name"],
        )

        with pytest.raises(KeyError, match="Missing required parameters: {'name'}"):
            template.format()

    def test_template_placeholder_extraction(self):
        """Test placeholder extraction from template."""
        template = MessageTemplate(
            template="Error in {field}: {value} is not valid for {context}",
            category="validation",
        )

        assert set(template.placeholders) == {"field", "value", "context"}

    def test_template_validation(self):
        """Test template parameter validation."""
        template = MessageTemplate(
            template="Hello {name}!",
            category="greeting",
            required_params=["name"],
        )

        # Valid parameters
        errors = template.validate_params(name="World")
        assert errors == []

        # Missing required parameter
        errors = template.validate_params()
        assert "Missing required parameters: {'name'}" in errors

        # Unknown parameter
        errors = template.validate_params(name="World", unknown="value")
        assert "Unknown parameters: {'unknown'}" in errors


class TestMessageTemplateRegistry:
    """Test MessageTemplateRegistry class."""

    def test_registry_operations(self):
        """Test basic registry operations."""
        registry = MessageTemplateRegistry()

        template = MessageTemplate(
            template="Test {param}",
            category="test",
            required_params=["param"],
        )

        # Register template
        registry.register_template("test_key", template)

        # Get template
        retrieved = registry.get_template("test_key")
        assert retrieved == template

        # Check existence
        assert registry.has_template("test_key")
        assert not registry.has_template("nonexistent")

        # Get by category
        category_templates = registry.get_templates_by_category("test")
        assert "test_key" in category_templates
        assert category_templates["test_key"] == template

    def test_registry_bulk_operations(self):
        """Test bulk registry operations."""
        registry = MessageTemplateRegistry()

        templates = {
            "template1": MessageTemplate("Test 1", "category1"),
            "template2": MessageTemplate("Test 2", "category2"),
        }

        registry.register_templates(templates)

        assert registry.has_template("template1")
        assert registry.has_template("template2")
        assert "category1" in registry.get_categories()
        assert "category2" in registry.get_categories()

    def test_registry_dict_operations(self):
        """Test dictionary import/export."""
        registry = MessageTemplateRegistry()

        template_data = {
            "test_template": {
                "template": "Hello {name}!",
                "category": "greeting",
                "description": "Test template",
                "required_params": ["name"],
                "context_aware": True,
            }
        }

        registry.load_from_dict(template_data)

        assert registry.has_template("test_template")

        exported = registry.export_to_dict()
        assert exported["test_template"]["template"] == "Hello {name}!"
        assert exported["test_template"]["category"] == "greeting"


class TestTemplateEngine:
    """Test TemplateEngine class."""

    def test_engine_basic_functionality(self):
        """Test basic template engine functionality."""
        registry = MessageTemplateRegistry()
        template = MessageTemplate(
            template="Invalid {field} for {task_context}",
            category="validation",
            required_params=["field", "task_context"],
        )
        registry.register_template("test_invalid", template)

        engine = TemplateEngine(registry)

        data = {"kind": "task", "parent": "F-test"}
        result = engine.generate_message("test_invalid", data, field="status")

        assert "Invalid status for hierarchy task" in result

    def test_engine_context_injection(self):
        """Test automatic context injection."""
        registry = MessageTemplateRegistry()
        template = MessageTemplate(
            template="Error for {object_kind}: {task_context}",
            category="validation",
            required_params=["object_kind", "task_context"],
        )
        registry.register_template("test_context", template)

        engine = TemplateEngine(registry)

        # Test standalone task
        data = {"kind": "task", "parent": None}
        result = engine.generate_message("test_context", data)
        assert "Error for task: standalone task" in result

        # Test hierarchy task
        data = {"kind": "task", "parent": "F-test"}
        result = engine.generate_message("test_context", data)
        assert "Error for task: hierarchy task" in result

    def test_engine_context_processors(self):
        """Test custom context processors."""
        registry = MessageTemplateRegistry()
        template = MessageTemplate(
            template="Test {custom_field}",
            category="validation",
            required_params=["custom_field"],
        )
        registry.register_template("test_processor", template)

        engine = TemplateEngine(registry)

        # Add custom processor
        def custom_processor(template, data, params):
            params = params.copy()
            params["custom_field"] = "processed_value"
            return params

        engine.add_context_processor(custom_processor)

        data = {"kind": "task"}
        result = engine.generate_message("test_processor", data)
        assert "Test processed_value" in result


class TestTrellisMessageEngine:
    """Test TrellisMessageEngine class."""

    def test_engine_initialization(self):
        """Test engine initialization with defaults."""
        engine = TrellisMessageEngine()

        # Check that default templates are loaded
        templates = engine.get_available_templates()
        assert "status.invalid" in templates
        assert "parent.missing" in templates
        assert "security.suspicious_pattern" in templates

    def test_engine_message_generation(self):
        """Test message generation with different formats."""
        engine = TrellisMessageEngine()

        data = {"kind": "task", "parent": "F-test"}

        # Plain text format
        result = engine.generate_message(
            "status.invalid", data, format_type="plain", value="invalid_status"
        )
        assert isinstance(result, str)
        assert "Invalid status 'invalid_status' for hierarchy task" in result

        # Structured format
        result = engine.generate_message(
            "status.invalid", data, format_type="structured", value="invalid_status"
        )
        assert isinstance(result, dict)
        assert "message" in result
        assert "metadata" in result

    def test_engine_custom_templates(self):
        """Test adding custom templates."""
        engine = TrellisMessageEngine()

        custom_config = {
            "template": "Custom error: {error}",
            "category": "custom",
            "required_params": ["error"],
        }

        engine.add_custom_template("custom_error", custom_config)

        assert "custom_error" in engine.get_available_templates()

        data = {"kind": "task"}
        result = engine.generate_message("custom_error", data, error="test")
        assert "Custom error: test" in result

    def test_engine_category_filtering(self):
        """Test template filtering by category."""
        engine = TrellisMessageEngine()

        status_templates = engine.get_templates_by_category("status")
        assert "status.invalid" in status_templates
        assert "status.invalid_with_options" in status_templates

        parent_templates = engine.get_templates_by_category("parent")
        assert "parent.missing" in parent_templates
        assert "parent.not_found" in parent_templates


class TestMessageFormatters:
    """Test message formatters."""

    def test_plain_text_formatter(self):
        """Test plain text formatter."""
        formatter = PlainTextFormatter()
        result = formatter.format("Test message", extra="metadata")
        assert result == "Test message"

    def test_structured_formatter(self):
        """Test structured formatter."""
        formatter = StructuredFormatter()
        result = formatter.format("Test message", extra="metadata")

        assert isinstance(result, dict)
        assert result["message"] == "Test message"
        assert result["metadata"]["extra"] == "metadata"

    def test_validation_error_formatter(self):
        """Test validation error formatter."""
        formatter = ValidationErrorFormatter()
        result = formatter.format(
            "Test message", error_code="TEST_ERROR", object_id="T-123", object_kind="task"
        )

        assert isinstance(result, dict)
        assert result["message"] == "Test message"
        assert result["error_code"] == "TEST_ERROR"
        assert result["object_id"] == "T-123"
        assert result["object_kind"] == "task"

    def test_formatter_selection(self):
        """Test formatter selection utility."""
        plain_formatter = get_formatter("plain")
        assert isinstance(plain_formatter, PlainTextFormatter)

        structured_formatter = get_formatter("structured")
        assert isinstance(structured_formatter, StructuredFormatter)

        validation_formatter = get_formatter("validation")
        assert isinstance(validation_formatter, ValidationErrorFormatter)

        with pytest.raises(ValueError, match="Unsupported format type: invalid"):
            get_formatter("invalid")


class TestDefaultTemplates:
    """Test default templates."""

    def test_default_templates_exist(self):
        """Test that default templates are properly defined."""
        templates = get_default_templates()

        # Check key template categories exist
        assert any(key.startswith("status.") for key in templates)
        assert any(key.startswith("parent.") for key in templates)
        assert any(key.startswith("security.") for key in templates)
        assert any(key.startswith("fields.") for key in templates)
        assert any(key.startswith("hierarchy.") for key in templates)

    def test_default_templates_formatting(self):
        """Test that default templates format correctly."""
        templates = get_default_templates()

        # Test status template
        status_template = templates["status.invalid"]
        result = status_template.format(value="invalid", task_context="hierarchy task")
        assert result == "Invalid status 'invalid' for hierarchy task"

        # Test parent template
        parent_template = templates["parent.not_found"]
        result = parent_template.format(parent_kind="feature", parent_id="F-missing")
        assert result == "Parent feature with ID 'F-missing' does not exist"

        # Test security template
        security_template = templates["security.suspicious_pattern"]
        result = security_template.format(field="parent", pattern="..")
        assert result == "Security validation failed: parent field contains suspicious pattern '..'"


class TestIntegration:
    """Test integration with existing systems."""

    def test_global_engine_access(self):
        """Test global engine access."""
        engine1 = get_default_engine()
        engine2 = get_default_engine()

        # Should return the same instance
        assert engine1 is engine2

    def test_convenience_function(self):
        """Test convenience function for message generation."""
        data = {"kind": "task", "parent": "F-test"}

        result = generate_template_message(
            "status.invalid", data, format_type="plain", value="invalid_status"
        )

        assert isinstance(result, str)
        assert "Invalid status 'invalid_status' for hierarchy task" in result

    def test_backward_compatibility(self):
        """Test that template system integrates with existing validation."""
        # This test ensures the template system works with existing validation patterns
        from src.trellis_mcp.validation.context_utils import generate_contextual_error_message

        data = {"kind": "task", "parent": "F-test"}

        # Test with template system available
        result = generate_contextual_error_message(
            "invalid_status",
            data,
            status="invalid",
            valid_values=["open", "in-progress", "review", "done"],
        )

        assert "Invalid status 'invalid' for hierarchy task" in result

    def test_security_integration(self):
        """Test security validation integration."""
        from src.trellis_mcp.validation.security import validate_standalone_task_security

        # Test suspicious pattern detection
        data = {"kind": "task", "parent": "..", "schema_version": "1.1"}

        errors = validate_standalone_task_security(data)
        assert len(errors) > 0
        assert "Security validation failed" in errors[0]
        assert "suspicious pattern" in errors[0]

    def test_template_engine_error_handling(self):
        """Test template engine error handling."""
        engine = TrellisMessageEngine()

        # Test with missing template
        data = {"kind": "task"}
        with pytest.raises(KeyError, match="Template 'nonexistent' not found"):
            engine.generate_message("nonexistent", data)

        # Test with missing required parameters
        with pytest.raises(KeyError, match="Missing required parameters"):
            engine.generate_message("status.invalid", data)  # Missing 'value' parameter
