"""Unit tests for cross-system validation error functionality.

Tests the enhanced ValidationError class with cross-system context information,
including error message generation, context detection, and security validation.
"""

from trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode


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
