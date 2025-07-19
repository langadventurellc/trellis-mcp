"""Tests for validation error classes.

This module consolidates validation-related exception tests:
- ValidationError base class and ValidationErrorCode enum
- Cross-system validation functionality
- Hierarchy-specific task validation errors
- Standalone-specific task validation errors
- Integration tests between validation error types
"""

import pytest

from src.trellis_mcp.exceptions.hierarchy_task_validation_error import HierarchyTaskValidationError
from src.trellis_mcp.exceptions.standalone_task_validation_error import (
    StandaloneTaskValidationError,
)
from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode


class TestValidationError:
    """Test cases for ValidationError class."""

    def test_init_with_single_error(self):
        """Test initialization with single error string."""
        error = ValidationError("Test error")
        assert error.errors == ["Test error"]
        assert error.error_codes == []
        assert error.context == {}
        assert error.object_id is None
        assert error.object_kind is None
        assert error.task_type is None
        assert str(error) == "Validation failed: Test error"

    def test_init_with_multiple_errors(self):
        """Test initialization with multiple error strings."""
        errors = ["Error 1", "Error 2", "Error 3"]
        error = ValidationError(errors)
        assert error.errors == errors
        assert str(error) == "Validation failed: Error 1; Error 2; Error 3"

    def test_init_with_error_codes(self):
        """Test initialization with error codes."""
        error = ValidationError("Test error", error_codes=ValidationErrorCode.INVALID_STATUS)
        assert error.errors == ["Test error"]
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS]

    def test_init_with_multiple_error_codes(self):
        """Test initialization with multiple error codes."""
        error_codes = [ValidationErrorCode.INVALID_STATUS, ValidationErrorCode.MISSING_PARENT]
        error = ValidationError(["Error 1", "Error 2"], error_codes=error_codes)
        assert error.error_codes == error_codes

    def test_init_with_context(self):
        """Test initialization with context information."""
        context = {"field": "status", "value": "invalid"}
        error = ValidationError(
            "Test error",
            context=context,
            object_id="T-123",
            object_kind="task",
            task_type="standalone",
        )
        assert error.context == context
        assert error.object_id == "T-123"
        assert error.object_kind == "task"
        assert error.task_type == "standalone"
        assert str(error) == "Validation failed: Test error (object: T-123) (standalone task)"

    def test_add_error(self):
        """Test adding errors to existing exception."""
        error = ValidationError("Initial error")
        error.add_error("Additional error", ValidationErrorCode.INVALID_FIELD)

        assert len(error.errors) == 2
        assert error.errors[1] == "Additional error"
        assert len(error.error_codes) == 1
        assert error.error_codes[0] == ValidationErrorCode.INVALID_FIELD

    def test_to_dict(self):
        """Test conversion to dictionary."""
        error = ValidationError(
            ["Error 1", "Error 2"],
            error_codes=[ValidationErrorCode.INVALID_STATUS, ValidationErrorCode.MISSING_PARENT],
            context={"field": "status"},
            object_id="T-123",
            object_kind="task",
            task_type="standalone",
        )

        result = error.to_dict()
        expected = {
            "error_type": "ValidationError",
            "message": "Validation failed: Error 1; Error 2 (object: T-123) (standalone task)",
            "errors": ["Error 1", "Error 2"],
            "error_codes": ["invalid_status", "missing_parent"],
            "object_id": "T-123",
            "object_kind": "task",
            "task_type": "standalone",
            "context": {"field": "status"},
        }

        assert result == expected

    def test_to_dict_minimal(self):
        """Test conversion to dictionary with minimal information."""
        error = ValidationError("Test error")
        result = error.to_dict()
        expected = {
            "error_type": "ValidationError",
            "message": "Validation failed: Test error",
            "errors": ["Test error"],
            "error_codes": [],
        }

        assert result == expected

    def test_has_error_code(self):
        """Test checking for specific error codes."""
        error = ValidationError(
            "Test error",
            error_codes=[ValidationErrorCode.INVALID_STATUS, ValidationErrorCode.MISSING_PARENT],
        )

        assert error.has_error_code(ValidationErrorCode.INVALID_STATUS)
        assert error.has_error_code(ValidationErrorCode.MISSING_PARENT)
        assert not error.has_error_code(ValidationErrorCode.INVALID_FIELD)

    def test_get_errors_by_code(self):
        """Test getting errors by specific error code."""
        error = ValidationError(
            ["Status error", "Parent error"],
            error_codes=[ValidationErrorCode.INVALID_STATUS, ValidationErrorCode.MISSING_PARENT],
        )

        status_errors = error.get_errors_by_code(ValidationErrorCode.INVALID_STATUS)
        assert status_errors == ["Status error"]

        parent_errors = error.get_errors_by_code(ValidationErrorCode.MISSING_PARENT)
        assert parent_errors == ["Parent error"]

        field_errors = error.get_errors_by_code(ValidationErrorCode.INVALID_FIELD)
        assert field_errors == []

    def test_get_errors_by_code_mismatched_counts(self):
        """Test getting errors by code when error and code counts don't match."""
        error = ValidationError(
            ["Error 1", "Error 2", "Error 3"], error_codes=[ValidationErrorCode.INVALID_STATUS]
        )

        # When counts don't match, should return all errors if code is present
        status_errors = error.get_errors_by_code(ValidationErrorCode.INVALID_STATUS)
        assert status_errors == ["Error 1", "Error 2", "Error 3"]

        # Should return empty list if code is not present
        field_errors = error.get_errors_by_code(ValidationErrorCode.INVALID_FIELD)
        assert field_errors == []

    def test_create_contextual_error_invalid_status(self):
        """Test creating contextual error for invalid status."""
        error = ValidationError.create_contextual_error(
            "invalid_status", "T-123", "standalone", {"status": "invalid"}
        )

        assert error.errors == ["Invalid status 'invalid' for standalone task"]
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS]
        assert error.object_id == "T-123"
        assert error.task_type == "standalone"

    def test_create_contextual_error_missing_parent(self):
        """Test creating contextual error for missing parent."""
        error = ValidationError.create_contextual_error("missing_parent", "T-123", "hierarchy")

        assert error.errors == ["Parent is required for hierarchy task"]
        assert error.error_codes == [ValidationErrorCode.MISSING_PARENT]
        assert error.object_id == "T-123"
        assert error.task_type == "hierarchy"

    def test_create_contextual_error_parent_not_exist(self):
        """Test creating contextual error for non-existent parent."""
        error = ValidationError.create_contextual_error(
            "parent_not_exist", "T-123", "hierarchy", {"parent_id": "F-456"}
        )

        assert error.errors == ["Parent with ID 'F-456' does not exist (hierarchy task validation)"]
        assert error.error_codes == [ValidationErrorCode.PARENT_NOT_EXIST]
        assert error.object_id == "T-123"
        assert error.task_type == "hierarchy"

    def test_create_contextual_error_unknown_type(self):
        """Test creating contextual error for unknown error type."""
        error = ValidationError.create_contextual_error("unknown_error", "T-123", "standalone")

        assert error.errors == ["Validation error: unknown_error (standalone task)"]
        assert error.error_codes == [ValidationErrorCode.INVALID_FIELD]
        assert error.object_id == "T-123"
        assert error.task_type == "standalone"


class TestValidationErrorCode:
    """Test cases for ValidationErrorCode enum."""

    def test_error_code_values(self):
        """Test that error codes have expected string values."""
        assert ValidationErrorCode.INVALID_FIELD.value == "invalid_field"
        assert ValidationErrorCode.MISSING_REQUIRED_FIELD.value == "missing_required_field"
        assert ValidationErrorCode.INVALID_ENUM_VALUE.value == "invalid_enum_value"
        assert ValidationErrorCode.INVALID_STATUS.value == "invalid_status"
        assert ValidationErrorCode.MISSING_PARENT.value == "missing_parent"
        assert ValidationErrorCode.PARENT_NOT_EXIST.value == "parent_not_exist"
        assert ValidationErrorCode.CIRCULAR_DEPENDENCY.value == "circular_dependency"
        assert ValidationErrorCode.INVALID_STATUS_TRANSITION.value == "invalid_status_transition"

    def test_error_code_uniqueness(self):
        """Test that all error codes are unique."""
        codes = [code.value for code in ValidationErrorCode]
        assert len(codes) == len(set(codes))

    def test_error_code_enum_membership(self):
        """Test error code enum membership."""
        assert ValidationErrorCode.INVALID_FIELD in ValidationErrorCode
        assert ValidationErrorCode.MISSING_PARENT in ValidationErrorCode
        assert ValidationErrorCode.CIRCULAR_DEPENDENCY in ValidationErrorCode


class TestCrossSystemValidationError:
    """Test class for cross-system validation error functionality."""

    def test_cross_system_error_code_constants(self):
        """Test that cross-system error codes are properly defined."""
        assert (
            ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT.value
            == "cross_system_reference_conflict"
        )
        assert (
            ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID.value
            == "cross_system_prerequisite_invalid"
        )

    def test_create_cross_system_reference_error(self):
        """Test creating cross-system reference error with enhanced context."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth-setup",
            target_task_id="T-user-model",
            conflict_type="reference",
        )

        assert len(error.errors) == 1
        assert "Cannot reference hierarchical task 'user-model'" in error.errors[0]
        assert "from standalone task 'auth-setup'" in error.errors[0]
        assert error.error_codes[0] == ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT
        assert error.object_id == "T-auth-setup"
        assert error.task_type == "standalone"

    def test_create_cross_system_prerequisite_error(self):
        """Test creating cross-system prerequisite error with enhanced context."""
        error = ValidationError.create_cross_system_error(
            source_task_type="hierarchy",
            target_task_type="standalone",
            source_task_id="T-user-registration",
            target_task_id="T-auth-setup",
            conflict_type="prerequisite",
        )

        assert len(error.errors) == 1
        assert "Prerequisite validation failed" in error.errors[0]
        assert "hierarchy task 'user-registration'" in error.errors[0]
        assert "requires standalone task 'auth-setup'" in error.errors[0]
        assert "which does not exist" in error.errors[0]
        assert error.error_codes[0] == ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID

    def test_cross_system_error_context_enhancement(self):
        """Test that cross-system errors include enhanced context information."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth",
            target_task_id="F-user-login",
            conflict_type="reference",
            context={"additional_info": "test context"},
        )

        assert error.context["source_task_type"] == "standalone"
        assert error.context["target_task_type"] == "hierarchy"
        assert error.context["source_task_id"] == "T-auth"
        assert error.context["target_task_id"] == "F-user-login"
        assert error.context["conflict_type"] == "reference"
        assert error.context["cross_system_context"] is True
        assert error.context["additional_info"] == "test context"

    def test_cross_system_reference_error_standalone_to_hierarchy(self):
        """Test reference error from standalone to hierarchy task."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth-setup",
            target_task_id="T-user-model",
        )

        expected_msg = (
            "Cannot reference hierarchical task 'user-model' from standalone task 'auth-setup'"
        )
        assert error.errors[0] == expected_msg

    def test_cross_system_reference_error_hierarchy_to_standalone(self):
        """Test reference error from hierarchy to standalone task."""
        error = ValidationError.create_cross_system_error(
            source_task_type="hierarchy",
            target_task_type="standalone",
            source_task_id="T-user-model",
            target_task_id="T-auth-setup",
        )

        expected_msg = (
            "Cannot reference standalone task 'auth-setup' from hierarchical task 'user-model'"
        )
        assert error.errors[0] == expected_msg

    def test_clean_task_id_display(self):
        """Test that task IDs are cleaned for display (prefixes removed)."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth-setup",
            target_task_id="F-user-login",
        )

        # Should show clean IDs without prefixes
        assert "'auth-setup'" in error.errors[0]
        assert "'user-login'" in error.errors[0]
        # Should not show the prefixes
        assert "'T-auth-setup'" not in error.errors[0]
        assert "'F-user-login'" not in error.errors[0]

    def test_to_dict_includes_cross_system_context(self):
        """Test that to_dict() includes cross-system context information."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth",
            target_task_id="T-user",
        )

        error_dict = error.to_dict()

        assert error_dict["error_type"] == "ValidationError"
        assert error_dict["object_id"] == "T-auth"
        assert error_dict["task_type"] == "standalone"
        assert error_dict["context"]["cross_system_context"] is True
        assert error_dict["context"]["source_task_type"] == "standalone"
        assert error_dict["context"]["target_task_type"] == "hierarchy"

    def test_has_error_code_for_cross_system_errors(self):
        """Test error code checking for cross-system errors."""
        reference_error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth",
            target_task_id="T-user",
            conflict_type="reference",
        )

        prerequisite_error = ValidationError.create_cross_system_error(
            source_task_type="hierarchy",
            target_task_type="standalone",
            source_task_id="T-user",
            target_task_id="T-auth",
            conflict_type="prerequisite",
        )

        assert reference_error.has_error_code(ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT)
        assert not reference_error.has_error_code(
            ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID
        )

        assert prerequisite_error.has_error_code(
            ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID
        )
        assert not prerequisite_error.has_error_code(
            ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT
        )

    def test_unknown_conflict_type_fallback(self):
        """Test fallback behavior for unknown conflict types."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth",
            target_task_id="T-user",
            conflict_type="unknown",
        )

        assert "Cross-system conflict between" in error.errors[0]
        assert error.error_codes[0] == ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT

    def test_error_message_security_no_file_paths(self):
        """Test that error messages don't expose internal file paths."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth",
            target_task_id="T-user",
        )

        # Error message should not contain file paths or sensitive info
        error_msg = error.errors[0]
        assert "/" not in error_msg  # No file paths
        assert "\\" not in error_msg  # No Windows paths
        assert ".md" not in error_msg  # No file extensions
        assert "planning" not in error_msg  # No internal directory names

    def test_performance_requirement_fast_execution(self):
        """Test that cross-system error creation is fast (<1ms requirement)."""
        import time

        start_time = time.perf_counter()

        # Create multiple errors to test performance
        for i in range(100):
            ValidationError.create_cross_system_error(
                source_task_type="standalone",
                target_task_type="hierarchy",
                source_task_id=f"T-auth-{i}",
                target_task_id=f"T-user-{i}",
            )

        end_time = time.perf_counter()
        avg_time_per_error = (end_time - start_time) / 100

        # Should be much faster than 1ms per error
        assert (
            avg_time_per_error < 0.001
        ), f"Error creation took {avg_time_per_error:.4f}s per error"

    def test_backward_compatibility_existing_methods(self):
        """Test that existing ValidationError methods still work."""
        # Test original constructor
        error = ValidationError(
            errors=["Test error"],
            error_codes=[ValidationErrorCode.INVALID_FIELD],
            object_id="test-object",
            task_type="hierarchy",
        )

        assert len(error.errors) == 1
        assert error.errors[0] == "Test error"
        assert error.object_id == "test-object"
        assert error.task_type == "hierarchy"

        # Test create_contextual_error still works
        contextual_error = ValidationError.create_contextual_error(
            error_type="invalid_status",
            object_id="test-task",
            task_type="standalone",
            context={"status": "invalid"},
        )

        assert "Invalid status 'invalid' for standalone task" in str(contextual_error)


class TestCrossSystemErrorScenarios:
    """Test class for specific cross-system error scenarios."""

    def test_scenario_standalone_references_hierarchy_feature(self):
        """Test scenario: standalone task tries to reference hierarchy feature."""
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-auth-setup",
            target_task_id="F-user-management",
            conflict_type="reference",
        )

        assert "Cannot reference hierarchical task 'user-management'" in error.errors[0]
        assert "from standalone task 'auth-setup'" in error.errors[0]

    def test_scenario_hierarchy_prerequisite_missing_standalone(self):
        """Test scenario: hierarchy task has prerequisite on missing standalone task."""
        error = ValidationError.create_cross_system_error(
            source_task_type="hierarchy",
            target_task_type="standalone",
            source_task_id="T-user-registration",
            target_task_id="T-auth-service",
            conflict_type="prerequisite",
        )

        assert "Prerequisite validation failed" in error.errors[0]
        assert "hierarchy task 'user-registration'" in error.errors[0]
        assert "requires standalone task 'auth-service'" in error.errors[0]
        assert "which does not exist" in error.errors[0]

    def test_scenario_mixed_project_epic_task_references(self):
        """Test scenario: mixed references between different object types."""
        # Standalone task trying to reference project
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchy",
            source_task_id="T-deployment",
            target_task_id="P-ecommerce-platform",
            conflict_type="reference",
        )

        assert "hierarchical task 'ecommerce-platform'" in error.errors[0]
        assert "standalone task 'deployment'" in error.errors[0]


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


class TestValidationErrorIntegration:
    """Integration tests for validation error classes."""

    def test_exception_hierarchy(self):
        """Test that custom exceptions inherit from ValidationError."""
        standalone_error = StandaloneTaskValidationError("Test error")
        hierarchy_error = HierarchyTaskValidationError("Test error")

        assert isinstance(standalone_error, ValidationError)
        assert isinstance(hierarchy_error, ValidationError)
        assert isinstance(standalone_error, Exception)
        assert isinstance(hierarchy_error, Exception)

    def test_error_code_consistency(self):
        """Test that error codes are consistent across different exception types."""
        # Test that the same error code is used across different exception types
        standalone_error = StandaloneTaskValidationError.invalid_status("T-123", "invalid")
        hierarchy_error = HierarchyTaskValidationError.invalid_status("T-123", "F-456", "invalid")

        assert standalone_error.error_codes == hierarchy_error.error_codes
        assert standalone_error.has_error_code(ValidationErrorCode.INVALID_STATUS)
        assert hierarchy_error.has_error_code(ValidationErrorCode.INVALID_STATUS)

    def test_serialization_consistency(self):
        """Test that serialization works consistently across exception types."""
        standalone_error = StandaloneTaskValidationError.invalid_status("T-123", "invalid")
        hierarchy_error = HierarchyTaskValidationError.invalid_status("T-123", "F-456", "invalid")

        standalone_dict = standalone_error.to_dict()
        hierarchy_dict = hierarchy_error.to_dict()

        # Both should have the same basic structure
        assert "error_type" in standalone_dict
        assert "error_type" in hierarchy_dict
        assert "message" in standalone_dict
        assert "message" in hierarchy_dict
        assert "errors" in standalone_dict
        assert "errors" in hierarchy_dict
        assert "error_codes" in standalone_dict
        assert "error_codes" in hierarchy_dict

        # Error codes should be the same
        assert standalone_dict["error_codes"] == hierarchy_dict["error_codes"]

        # Task types should be different
        assert standalone_dict["task_type"] == "standalone"
        assert hierarchy_dict["task_type"] == "hierarchy"

    def test_contextual_error_creation(self):
        """Test creating contextual errors that match existing patterns."""
        # Create errors that match the existing validation system patterns
        standalone_error = ValidationError.create_contextual_error(
            "invalid_status", "T-123", "standalone", {"status": "draft"}
        )

        hierarchy_error = ValidationError.create_contextual_error(
            "parent_not_exist", "T-456", "hierarchy", {"parent_id": "F-789"}
        )

        # Should have appropriate error messages
        assert "Invalid status 'draft' for standalone task" in standalone_error.errors[0]
        assert (
            "Parent with ID 'F-789' does not exist (hierarchy task validation)"
            in hierarchy_error.errors[0]
        )

        # Should have appropriate error codes
        assert standalone_error.has_error_code(ValidationErrorCode.INVALID_STATUS)
        assert hierarchy_error.has_error_code(ValidationErrorCode.PARENT_NOT_EXIST)

    def test_error_accumulation_pattern(self):
        """Test that errors can be accumulated similar to existing TrellisValidationError."""
        # Simulate the pattern used in existing validation code
        errors = []

        # Collect validation errors
        if True:  # Simulate a validation condition
            errors.append("Invalid status 'draft' for standalone task")

        if True:  # Simulate another validation condition
            errors.append("Missing required field 'title' for standalone task")

        # Create validation error with accumulated errors
        validation_error = None
        if errors:
            validation_error = StandaloneTaskValidationError(
                errors,
                error_codes=[
                    ValidationErrorCode.INVALID_STATUS,
                    ValidationErrorCode.MISSING_REQUIRED_FIELD,
                ],
                object_id="T-123",
            )

        assert validation_error is not None
        assert len(validation_error.errors) == 2
        assert len(validation_error.error_codes) == 2
        assert validation_error.has_error_code(ValidationErrorCode.INVALID_STATUS)
        assert validation_error.has_error_code(ValidationErrorCode.MISSING_REQUIRED_FIELD)

    def test_exception_chaining_support(self):
        """Test that exception chaining works properly."""
        try:
            # Simulate original exception
            raise ValueError("Original error")
        except ValueError as original_error:
            # Create custom validation error and chain it
            validation_error = StandaloneTaskValidationError(
                "Validation failed due to original error", object_id="T-123"
            )

            # Chain the exceptions
            try:
                raise validation_error from original_error
            except StandaloneTaskValidationError as e:
                # Should have proper exception chaining
                assert e.__cause__ is original_error
                assert isinstance(e.__cause__, ValueError)
                assert str(e.__cause__) == "Original error"

    def test_error_filtering_by_code(self):
        """Test filtering errors by error code for programmatic handling."""
        # Create a validation error with multiple error codes
        validation_error = ValidationError(
            ["Status error", "Parent error", "Field error"],
            error_codes=[
                ValidationErrorCode.INVALID_STATUS,
                ValidationErrorCode.MISSING_PARENT,
                ValidationErrorCode.INVALID_FIELD,
            ],
            object_id="T-123",
        )

        # Should be able to filter by specific error codes
        status_errors = validation_error.get_errors_by_code(ValidationErrorCode.INVALID_STATUS)
        parent_errors = validation_error.get_errors_by_code(ValidationErrorCode.MISSING_PARENT)
        field_errors = validation_error.get_errors_by_code(ValidationErrorCode.INVALID_FIELD)

        assert status_errors == ["Status error"]
        assert parent_errors == ["Parent error"]
        assert field_errors == ["Field error"]

    def test_api_response_format(self):
        """Test that exceptions format properly for API responses."""
        error = StandaloneTaskValidationError.invalid_status(
            "T-123", "invalid", ["open", "in-progress", "done"]
        )

        response_dict = error.to_dict()

        # Should have all required fields for API response
        required_fields = ["error_type", "message", "errors", "error_codes"]
        for field in required_fields:
            assert field in response_dict

        # Should have proper types
        assert isinstance(response_dict["error_type"], str)
        assert isinstance(response_dict["message"], str)
        assert isinstance(response_dict["errors"], list)
        assert isinstance(response_dict["error_codes"], list)

        # Error codes should be serialized as strings
        assert all(isinstance(code, str) for code in response_dict["error_codes"])

    def test_compatibility_with_existing_exceptions(self):
        """Test that new exceptions are compatible with existing exception handling."""
        # Test that new exceptions can be caught with generic Exception
        with pytest.raises(Exception):
            raise StandaloneTaskValidationError("Test error")

        # Test that new exceptions can be caught with ValidationError
        with pytest.raises(ValidationError):
            raise HierarchyTaskValidationError("Test error")

        # Test that new exceptions have proper string representation
        error = StandaloneTaskValidationError("Test error", object_id="T-123")
        error_str = str(error)
        assert "Validation failed" in error_str
        assert "Test error" in error_str
        assert "T-123" in error_str
        assert "standalone task" in error_str

    def test_error_message_formatting_consistency(self):
        """Test that error messages are formatted consistently."""
        # Test different error types to ensure consistent formatting
        standalone_status_error = StandaloneTaskValidationError.invalid_status("T-123", "invalid")
        hierarchy_status_error = HierarchyTaskValidationError.invalid_status(
            "T-123", "F-456", "invalid"
        )

        # Both should mention the task type
        assert "standalone task" in standalone_status_error.errors[0]
        assert "hierarchy task" in hierarchy_status_error.errors[0]

        # Both should have similar structure
        assert "Invalid status 'invalid'" in standalone_status_error.errors[0]
        assert "Invalid status 'invalid'" in hierarchy_status_error.errors[0]

    def test_context_information_preservation(self):
        """Test that context information is preserved properly."""
        error = HierarchyTaskValidationError.parent_not_exist("T-123", "F-456")

        # Should preserve context information
        assert error.object_id == "T-123"
        assert error.parent_id == "F-456"
        assert error.task_type == "hierarchy"
        assert error.context["parent_id"] == "F-456"
        assert error.context["parent_type"] == "feature"

        # Should be available in serialized form
        result_dict = error.to_dict()
        assert result_dict["object_id"] == "T-123"
        assert result_dict["task_type"] == "hierarchy"
        assert result_dict["context"]["parent_id"] == "F-456"
