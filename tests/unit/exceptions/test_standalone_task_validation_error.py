"""Tests for standalone task validation error classes."""

from src.trellis_mcp.exceptions.standalone_task_validation_error import (
    StandaloneTaskValidationError,
)
from src.trellis_mcp.exceptions.validation_error import ValidationErrorCode


class TestStandaloneTaskValidationError:
    """Test cases for StandaloneTaskValidationError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = StandaloneTaskValidationError("Test error", object_id="T-123")
        assert error.errors == ["Test error"]
        assert error.object_id == "T-123"
        assert error.object_kind == "task"
        assert error.task_type == "standalone"
        assert "standalone task" in str(error)

    def test_init_with_custom_object_kind(self):
        """Test initialization with custom object kind."""
        error = StandaloneTaskValidationError(
            "Test error", object_id="T-123", object_kind="custom_task"
        )
        assert error.object_kind == "custom_task"
        assert error.task_type == "standalone"

    def test_invalid_status(self):
        """Test invalid_status class method."""
        error = StandaloneTaskValidationError.invalid_status(
            "T-123", "invalid", ["open", "in-progress", "done"]
        )

        assert error.object_id == "T-123"
        assert error.task_type == "standalone"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS]
        assert "Invalid status 'invalid' for standalone task" in error.errors[0]
        assert "Valid statuses: open, in-progress, done" in error.errors[0]
        assert error.context["status"] == "invalid"
        assert error.context["valid_statuses"] == ["open", "in-progress", "done"]

    def test_invalid_status_without_valid_statuses(self):
        """Test invalid_status without valid statuses list."""
        error = StandaloneTaskValidationError.invalid_status("T-123", "invalid")

        assert error.object_id == "T-123"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS]
        assert error.errors[0] == "Invalid status 'invalid' for standalone task"
        assert error.context["status"] == "invalid"
        assert error.context["valid_statuses"] == []

    def test_parent_not_allowed(self):
        """Test parent_not_allowed class method."""
        error = StandaloneTaskValidationError.parent_not_allowed("T-123", "F-456")

        assert error.object_id == "T-123"
        assert error.task_type == "standalone"
        assert error.error_codes == [ValidationErrorCode.INVALID_PARENT_TYPE]
        assert error.errors[0] == "Standalone task cannot have a parent (parent 'F-456' specified)"
        assert error.context["parent_id"] == "F-456"

    def test_schema_version_required(self):
        """Test schema_version_required class method."""
        error = StandaloneTaskValidationError.schema_version_required("T-123", "1.0")

        assert error.object_id == "T-123"
        assert error.task_type == "standalone"
        assert error.error_codes == [ValidationErrorCode.SCHEMA_VERSION_MISMATCH]
        assert (
            "Standalone tasks require schema version 1.1 or higher (current: 1.0)"
            in error.errors[0]
        )
        assert error.context["current_version"] == "1.0"
        assert error.context["required_version"] == "1.1"

    def test_schema_version_required_without_current(self):
        """Test schema_version_required without current version."""
        error = StandaloneTaskValidationError.schema_version_required("T-123")

        assert error.object_id == "T-123"
        assert error.error_codes == [ValidationErrorCode.SCHEMA_VERSION_MISMATCH]
        assert error.errors[0] == "Standalone tasks require schema version 1.1 or higher"
        assert error.context["current_version"] is None
        assert error.context["required_version"] == "1.1"

    def test_invalid_transition(self):
        """Test invalid_transition class method."""
        allowed_transitions = {
            "open": ["in-progress", "done"],
            "in-progress": ["open", "done", "review"],
        }

        error = StandaloneTaskValidationError.invalid_transition(
            "T-123", "done", "open", allowed_transitions
        )

        assert error.object_id == "T-123"
        assert error.task_type == "standalone"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS_TRANSITION]
        assert (
            "Invalid status transition from 'done' to 'open' for standalone task" in error.errors[0]
        )
        assert error.context["from_status"] == "done"
        assert error.context["to_status"] == "open"
        assert error.context["allowed_transitions"] == allowed_transitions

    def test_invalid_transition_with_suggestions(self):
        """Test invalid_transition with transition suggestions."""
        allowed_transitions = {
            "open": ["in-progress", "done"],
            "in-progress": ["open", "done", "review"],
        }

        error = StandaloneTaskValidationError.invalid_transition(
            "T-123", "open", "review", allowed_transitions
        )

        assert "Valid transitions from 'open': in-progress, done" in error.errors[0]

    def test_invalid_transition_without_allowed_transitions(self):
        """Test invalid_transition without allowed transitions dict."""
        error = StandaloneTaskValidationError.invalid_transition("T-123", "done", "open")

        assert error.object_id == "T-123"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS_TRANSITION]
        assert (
            error.errors[0] == "Invalid status transition from 'done' to 'open' for standalone task"
        )
        assert error.context["allowed_transitions"] == {}

    def test_missing_required_field(self):
        """Test missing_required_field class method."""
        error = StandaloneTaskValidationError.missing_required_field(
            "T-123", "title", "Task title is required for all tasks"
        )

        assert error.object_id == "T-123"
        assert error.task_type == "standalone"
        assert error.error_codes == [ValidationErrorCode.MISSING_REQUIRED_FIELD]
        expected_msg = (
            "Missing required field 'title' for standalone task: "
            "Task title is required for all tasks"
        )
        assert expected_msg in error.errors[0]
        assert error.context["field_name"] == "title"
        assert error.context["field_description"] == "Task title is required for all tasks"

    def test_missing_required_field_without_description(self):
        """Test missing_required_field without description."""
        error = StandaloneTaskValidationError.missing_required_field("T-123", "title")

        assert error.object_id == "T-123"
        assert error.error_codes == [ValidationErrorCode.MISSING_REQUIRED_FIELD]
        assert error.errors[0] == "Missing required field 'title' for standalone task"
        assert error.context["field_name"] == "title"
        assert error.context["field_description"] is None

    def test_invalid_field_value(self):
        """Test invalid_field_value class method."""
        error = StandaloneTaskValidationError.invalid_field_value(
            "T-123", "priority", "urgent", ["high", "normal", "low"]
        )

        assert error.object_id == "T-123"
        assert error.task_type == "standalone"
        assert error.error_codes == [ValidationErrorCode.INVALID_FIELD]
        assert "Invalid value 'urgent' for field 'priority' in standalone task" in error.errors[0]
        assert "Valid values: high, normal, low" in error.errors[0]
        assert error.context["field_name"] == "priority"
        assert error.context["field_value"] == "urgent"
        assert error.context["valid_values"] == ["high", "normal", "low"]

    def test_invalid_field_value_with_validation_rule(self):
        """Test invalid_field_value with validation rule."""
        error = StandaloneTaskValidationError.invalid_field_value(
            "T-123", "title", "", validation_rule="Title must be non-empty string"
        )

        assert error.object_id == "T-123"
        assert error.error_codes == [ValidationErrorCode.INVALID_FIELD]
        assert "Invalid value '' for field 'title' in standalone task" in error.errors[0]
        assert "Validation rule: Title must be non-empty string" in error.errors[0]
        assert error.context["field_name"] == "title"
        assert error.context["field_value"] == ""
        assert error.context["validation_rule"] == "Title must be non-empty string"

    def test_invalid_field_value_without_constraints(self):
        """Test invalid_field_value without constraints."""
        error = StandaloneTaskValidationError.invalid_field_value("T-123", "description", 123)

        assert error.object_id == "T-123"
        assert error.error_codes == [ValidationErrorCode.INVALID_FIELD]
        assert error.errors[0] == "Invalid value '123' for field 'description' in standalone task"
        assert error.context["field_name"] == "description"
        assert error.context["field_value"] == 123
        assert error.context["valid_values"] == []
        assert error.context["validation_rule"] is None

    def test_to_dict_inherited(self):
        """Test that to_dict works correctly for standalone task errors."""
        error = StandaloneTaskValidationError.invalid_status("T-123", "invalid", ["open", "done"])

        result = error.to_dict()
        assert result["error_type"] == "StandaloneTaskValidationError"
        assert result["object_id"] == "T-123"
        assert result["task_type"] == "standalone"
        assert result["error_codes"] == ["invalid_status"]
        assert "standalone task" in result["message"]

    def test_multiple_errors_and_codes(self):
        """Test handling multiple errors and error codes."""
        error = StandaloneTaskValidationError(
            ["Error 1", "Error 2"],
            error_codes=[ValidationErrorCode.INVALID_STATUS, ValidationErrorCode.INVALID_FIELD],
            object_id="T-123",
        )

        assert len(error.errors) == 2
        assert len(error.error_codes) == 2
        assert error.has_error_code(ValidationErrorCode.INVALID_STATUS)
        assert error.has_error_code(ValidationErrorCode.INVALID_FIELD)
        assert not error.has_error_code(ValidationErrorCode.MISSING_PARENT)
