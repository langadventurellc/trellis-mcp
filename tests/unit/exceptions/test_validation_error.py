"""Tests for validation error classes."""

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
