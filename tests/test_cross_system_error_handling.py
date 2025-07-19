"""Comprehensive test suite for cross-system error handling scenarios.

This module tests the enhanced error handling functionality across different
error conditions, ensuring all enhanced error messages and validation functions
work correctly with performance and security requirements.
"""

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.validation.exceptions import CircularDependencyError


class TestCrossSystemErrorHandling:
    """Test suite for cross-system error handling scenarios."""

    def test_missing_prerequisite_error_messages(self):
        """Test enhanced error messages for missing prerequisites across systems."""
        # Test standalone task referencing non-existent hierarchical task
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchical",
            source_task_id="T-auth-setup",
            target_task_id="F-nonexistent",
            conflict_type="prerequisite",
        )

        # Check for prerequisite validation error structure
        assert "Prerequisite validation failed" in str(error)
        assert "requires" in str(error) and "does not exist" in str(error)
        assert error.has_error_code(ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID)
        assert error.object_id == "T-auth-setup"
        assert error.task_type == "standalone"

        # Test hierarchical task referencing non-existent standalone task
        error2 = ValidationError.create_cross_system_error(
            source_task_type="hierarchical",
            target_task_type="standalone",
            source_task_id="T-user-model",
            target_task_id="T-missing-auth",
            conflict_type="prerequisite",
        )

        assert "Prerequisite validation failed" in str(error2)
        assert "requires" in str(error2) and "does not exist" in str(error2)
        assert error2.has_error_code(ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID)

    def test_cycle_detection_cross_system_context(self):
        """Test cycle detection with enhanced cross-system error context."""
        # Create mock cycle path with mixed task types
        cycle_path = ["T-auth-setup", "F-user-login", "T-auth-setup"]

        # Test enhanced CircularDependencyError with task type detection
        objects_data = {
            "T-auth-setup": {"kind": "task", "id": "T-auth-setup", "parent": None},
            "F-user-login": {"kind": "feature", "id": "F-user-login", "parent": "E-authentication"},
        }

        error = CircularDependencyError(cycle_path, objects_data)

        error_msg = str(error)
        assert "standalone" in error_msg
        assert "feature" in error_msg  # Features show as "feature", not "hierarchical"
        assert "T-auth-setup" in error_msg
        assert "F-user-login" in error_msg
        assert "→" in error_msg  # Enhanced arrow formatting

    def test_enhanced_validation_error_context(self):
        """Test enhanced ValidationError with comprehensive context information."""
        context = {
            "field": "prerequisites",
            "invalid_references": ["T-missing-1", "F-invalid-2"],
            "conflict_details": "Cross-system reference validation failed",
        }

        error = ValidationError(
            ["Multiple cross-system validation errors detected"],
            error_codes=[ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT],
            context=context,
            object_id="T-complex-task",
            object_kind="task",
            task_type="standalone",
        )

        # Test error dictionary contains all context
        error_dict = error.to_dict()
        assert error_dict["context"]["field"] == "prerequisites"
        assert "T-missing-1" in error_dict["context"]["invalid_references"]
        assert error_dict["task_type"] == "standalone"
        assert error_dict["object_kind"] == "task"

        # Test structured error codes
        assert error.has_error_code(ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT)

    def test_error_context_boundary_validation(self):
        """Test that enhanced errors maintain proper security boundaries."""
        # Test internal implementation details don't leak
        context_with_internals = {
            "internal_cache_key": "secret_cache_123",
            "file_system_path": "/internal/system/path",
            "debug_trace": "Internal stack trace data",
            "user_field": "safe_user_data",  # This should be preserved
        }

        error = ValidationError(
            "Test error with mixed context",
            context=context_with_internals,
            object_id="T-boundary-test",
            task_type="standalone",
        )

        error_dict = error.to_dict()

        # Safe user data should be preserved
        assert error_dict["context"]["user_field"] == "safe_user_data"

        # Internal details should be present but not in string representation
        error_str = str(error)
        assert "secret_cache_123" not in error_str
        assert "/internal/system/path" not in error_str
        assert "Internal stack trace" not in error_str

    def test_error_code_categorization(self):
        """Test that cross-system errors use appropriate error codes."""
        error_code_mapping = {
            "prerequisite": ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID,
            "reference": ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT,
        }

        for conflict_type, expected_code in error_code_mapping.items():
            error = ValidationError.create_cross_system_error(
                source_task_type="standalone",
                target_task_type="hierarchical",
                source_task_id="T-code-test",
                target_task_id="F-code-target",
                conflict_type=conflict_type,
            )

            assert error.has_error_code(
                expected_code
            ), f"Expected code {expected_code} for conflict {conflict_type}"
