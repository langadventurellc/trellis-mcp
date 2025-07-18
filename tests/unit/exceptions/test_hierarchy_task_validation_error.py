"""Tests for hierarchy task validation error classes."""

from src.trellis_mcp.exceptions.hierarchy_task_validation_error import HierarchyTaskValidationError
from src.trellis_mcp.exceptions.validation_error import ValidationErrorCode


class TestHierarchyTaskValidationError:
    """Test cases for HierarchyTaskValidationError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = HierarchyTaskValidationError("Test error", object_id="T-123")
        assert error.errors == ["Test error"]
        assert error.object_id == "T-123"
        assert error.object_kind == "task"
        assert error.task_type == "hierarchy"
        assert error.parent_id is None
        assert "hierarchy task" in str(error)

    def test_init_with_parent_id(self):
        """Test initialization with parent ID."""
        error = HierarchyTaskValidationError("Test error", object_id="T-123", parent_id="F-456")
        assert error.parent_id == "F-456"
        assert error.context["parent_id"] == "F-456"

    def test_init_with_existing_context(self):
        """Test initialization with existing context."""
        context = {"existing": "data"}
        error = HierarchyTaskValidationError(
            "Test error", object_id="T-123", parent_id="F-456", context=context
        )
        assert error.context["existing"] == "data"
        assert error.context["parent_id"] == "F-456"

    def test_missing_parent(self):
        """Test missing_parent class method."""
        error = HierarchyTaskValidationError.missing_parent("T-123", "1.0")

        assert error.object_id == "T-123"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.MISSING_PARENT]
        assert "Parent is required for hierarchy task (schema version: 1.0)" in error.errors[0]
        assert error.context["schema_version"] == "1.0"

    def test_missing_parent_without_schema_version(self):
        """Test missing_parent without schema version."""
        error = HierarchyTaskValidationError.missing_parent("T-123")

        assert error.object_id == "T-123"
        assert error.error_codes == [ValidationErrorCode.MISSING_PARENT]
        assert error.errors[0] == "Parent is required for hierarchy task"
        assert error.context["schema_version"] is None

    def test_parent_not_exist(self):
        """Test parent_not_exist class method."""
        error = HierarchyTaskValidationError.parent_not_exist("T-123", "F-456")

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.PARENT_NOT_EXIST]
        assert (
            "Parent feature with ID 'F-456' does not exist (hierarchy task validation)"
            in error.errors[0]
        )
        assert error.context["parent_type"] == "feature"

    def test_parent_not_exist_with_custom_type(self):
        """Test parent_not_exist with custom parent type."""
        error = HierarchyTaskValidationError.parent_not_exist("T-123", "E-789", "epic")

        assert error.object_id == "T-123"
        assert error.parent_id == "E-789"
        assert error.error_codes == [ValidationErrorCode.PARENT_NOT_EXIST]
        assert (
            "Parent epic with ID 'E-789' does not exist (hierarchy task validation)"
            in error.errors[0]
        )
        assert error.context["parent_type"] == "epic"

    def test_invalid_parent_type(self):
        """Test invalid_parent_type class method."""
        error = HierarchyTaskValidationError.invalid_parent_type("T-123", "E-456", "epic")

        assert error.object_id == "T-123"
        assert error.parent_id == "E-456"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.INVALID_PARENT_TYPE]
        assert (
            "Invalid parent type 'epic' for hierarchy task. Expected 'feature'" in error.errors[0]
        )
        assert error.context["parent_kind"] == "epic"
        assert error.context["expected_kind"] == "feature"

    def test_invalid_parent_type_custom_expected(self):
        """Test invalid_parent_type with custom expected kind."""
        error = HierarchyTaskValidationError.invalid_parent_type(
            "T-123", "P-456", "project", "epic"
        )

        assert error.object_id == "T-123"
        assert error.parent_id == "P-456"
        assert error.error_codes == [ValidationErrorCode.INVALID_PARENT_TYPE]
        assert (
            "Invalid parent type 'project' for hierarchy task. Expected 'epic'" in error.errors[0]
        )
        assert error.context["parent_kind"] == "project"
        assert error.context["expected_kind"] == "epic"

    def test_invalid_status(self):
        """Test invalid_status class method."""
        error = HierarchyTaskValidationError.invalid_status(
            "T-123", "F-456", "invalid", ["open", "in-progress", "done"]
        )

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS]
        assert "Invalid status 'invalid' for hierarchy task" in error.errors[0]
        assert "Valid statuses: open, in-progress, done" in error.errors[0]
        assert error.context["status"] == "invalid"
        assert error.context["valid_statuses"] == ["open", "in-progress", "done"]

    def test_invalid_status_without_valid_statuses(self):
        """Test invalid_status without valid statuses list."""
        error = HierarchyTaskValidationError.invalid_status("T-123", "F-456", "invalid")

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS]
        assert error.errors[0] == "Invalid status 'invalid' for hierarchy task"
        assert error.context["status"] == "invalid"
        assert error.context["valid_statuses"] == []

    def test_circular_dependency(self):
        """Test circular_dependency class method."""
        dependency_path = ["T-123", "T-456", "T-789", "T-123"]
        error = HierarchyTaskValidationError.circular_dependency("T-123", "F-456", dependency_path)

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.CIRCULAR_DEPENDENCY]
        assert (
            "Circular dependency detected in hierarchy task: T-123 -> T-456 -> T-789 -> T-123"
            in error.errors[0]
        )
        assert error.context["dependency_path"] == dependency_path

    def test_invalid_hierarchy_level(self):
        """Test invalid_hierarchy_level class method."""
        error = HierarchyTaskValidationError.invalid_hierarchy_level("T-123", "F-456", 2, 4)

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.INVALID_HIERARCHY_LEVEL]
        assert "Invalid hierarchy level 2 for hierarchy task. Expected level 4" in error.errors[0]
        assert error.context["current_level"] == 2
        assert error.context["expected_level"] == 4

    def test_parent_status_conflict(self):
        """Test parent_status_conflict class method."""
        error = HierarchyTaskValidationError.parent_status_conflict(
            "T-123",
            "F-456",
            "in-progress",
            "done",
            "Task cannot be in-progress when parent is done",
        )

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.STATUS_TRANSITION_NOT_ALLOWED]
        expected_msg = (
            "Status conflict: hierarchy task has status 'in-progress' but parent has status "
            "'done'. Task cannot be in-progress when parent is done"
        )
        assert error.errors[0] == expected_msg
        assert error.context["task_status"] == "in-progress"
        assert error.context["parent_status"] == "done"
        assert error.context["conflict_reason"] == "Task cannot be in-progress when parent is done"

    def test_invalid_transition(self):
        """Test invalid_transition class method."""
        allowed_transitions = {
            "open": ["in-progress", "done"],
            "in-progress": ["open", "done", "review"],
        }

        error = HierarchyTaskValidationError.invalid_transition(
            "T-123", "F-456", "done", "open", allowed_transitions
        )

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.task_type == "hierarchy"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS_TRANSITION]
        assert (
            "Invalid status transition from 'done' to 'open' for hierarchy task" in error.errors[0]
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

        error = HierarchyTaskValidationError.invalid_transition(
            "T-123", "F-456", "open", "review", allowed_transitions
        )

        assert "Valid transitions from 'open': in-progress, done" in error.errors[0]

    def test_invalid_transition_without_allowed_transitions(self):
        """Test invalid_transition without allowed transitions dict."""
        error = HierarchyTaskValidationError.invalid_transition("T-123", "F-456", "done", "open")

        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS_TRANSITION]
        assert (
            error.errors[0] == "Invalid status transition from 'done' to 'open' for hierarchy task"
        )
        assert error.context["allowed_transitions"] == {}

    def test_to_dict_inherited(self):
        """Test that to_dict works correctly for hierarchy task errors."""
        error = HierarchyTaskValidationError.invalid_status(
            "T-123", "F-456", "invalid", ["open", "done"]
        )

        result = error.to_dict()
        assert result["error_type"] == "HierarchyTaskValidationError"
        assert result["object_id"] == "T-123"
        assert result["task_type"] == "hierarchy"
        assert result["error_codes"] == ["invalid_status"]
        assert "hierarchy task" in result["message"]

    def test_multiple_errors_and_codes(self):
        """Test handling multiple errors and error codes."""
        error = HierarchyTaskValidationError(
            ["Error 1", "Error 2"],
            error_codes=[ValidationErrorCode.INVALID_STATUS, ValidationErrorCode.MISSING_PARENT],
            object_id="T-123",
            parent_id="F-456",
        )

        assert len(error.errors) == 2
        assert len(error.error_codes) == 2
        assert error.has_error_code(ValidationErrorCode.INVALID_STATUS)
        assert error.has_error_code(ValidationErrorCode.MISSING_PARENT)
        assert not error.has_error_code(ValidationErrorCode.INVALID_FIELD)
        assert error.parent_id == "F-456"

    def test_error_inheritance(self):
        """Test that hierarchy task errors inherit from ValidationError."""
        error = HierarchyTaskValidationError("Test error", object_id="T-123")

        # Should have inherited methods
        assert hasattr(error, "add_error")
        assert hasattr(error, "to_dict")
        assert hasattr(error, "has_error_code")
        assert hasattr(error, "get_errors_by_code")

        # Should be able to add errors
        error.add_error("Additional error", ValidationErrorCode.INVALID_FIELD)
        assert len(error.errors) == 2
        assert len(error.error_codes) == 1
