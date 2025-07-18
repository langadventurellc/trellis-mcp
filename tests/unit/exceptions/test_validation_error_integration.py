"""Integration tests for validation error classes with existing validation system."""

import pytest

from src.trellis_mcp.exceptions.hierarchy_task_validation_error import HierarchyTaskValidationError
from src.trellis_mcp.exceptions.standalone_task_validation_error import (
    StandaloneTaskValidationError,
)
from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode


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
