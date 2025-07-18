"""Tests for standalone task path validation functions.

This module tests the validation functions used to secure standalone task
path operations against directory traversal attacks and other security
vulnerabilities.
"""

from trellis_mcp.validation.field_validation import (
    _validate_status_parameter_security,
    _validate_task_id_security,
    validate_standalone_task_path_parameters,
)


class TestValidateStandaloneTaskPathParameters:
    """Test the main validation function for standalone task path parameters."""

    def test_validate_valid_task_id_and_status(self):
        """Test validation passes for valid task ID and status."""
        errors = validate_standalone_task_path_parameters("valid-task-id", "open")
        assert errors == []

    def test_validate_valid_task_id_without_status(self):
        """Test validation passes for valid task ID without status."""
        errors = validate_standalone_task_path_parameters("valid-task-id")
        assert errors == []

    def test_validate_task_id_with_prefix(self):
        """Test validation passes for task ID with T- prefix."""
        errors = validate_standalone_task_path_parameters("T-valid-task-id", "open")
        assert errors == []

    def test_validate_empty_task_id(self):
        """Test validation fails for empty task ID."""
        errors = validate_standalone_task_path_parameters("", "open")
        assert len(errors) == 1
        assert "Task ID cannot be empty" in errors[0]

    def test_validate_whitespace_task_id(self):
        """Test validation fails for whitespace-only task ID."""
        errors = validate_standalone_task_path_parameters("   ", "open")
        assert len(errors) == 1
        assert "Task ID cannot be empty" in errors[0]

    def test_validate_invalid_characters_in_task_id(self):
        """Test validation fails for invalid characters in task ID."""
        errors = validate_standalone_task_path_parameters("invalid@task#id", "open")
        assert len(errors) >= 1
        assert any("invalid characters" in error for error in errors)

    def test_validate_path_traversal_in_task_id(self):
        """Test validation fails for path traversal attempts in task ID."""
        errors = validate_standalone_task_path_parameters("../../../etc/passwd", "open")
        assert len(errors) >= 1
        assert any("path traversal" in error for error in errors)

    def test_validate_too_long_task_id(self):
        """Test validation fails for task ID exceeding filesystem limits."""
        long_id = "a" * 300  # Exceeds 255 character filesystem limit
        errors = validate_standalone_task_path_parameters(long_id, "open")
        assert len(errors) >= 1
        assert any("filesystem name limits" in error for error in errors)

    def test_validate_invalid_status(self):
        """Test validation fails for invalid status parameter."""
        errors = validate_standalone_task_path_parameters("valid-task-id", "invalid-status")
        assert len(errors) >= 1
        assert any("Invalid status parameter" in error for error in errors)

    def test_validate_multiple_errors(self):
        """Test validation returns multiple errors for multiple issues."""
        errors = validate_standalone_task_path_parameters("../invalid@id", "bad-status")
        assert len(errors) >= 2
        assert any("path traversal" in error for error in errors)
        assert any("Invalid status parameter" in error for error in errors)


class TestValidateTaskIdSecurity:
    """Test the task ID security validation function."""

    def test_validate_valid_task_id(self):
        """Test validation passes for valid task ID."""
        errors = _validate_task_id_security("valid-task-id")
        assert errors == []

    def test_validate_task_id_with_numbers(self):
        """Test validation passes for task ID with numbers."""
        errors = _validate_task_id_security("task-123-id")
        assert errors == []

    def test_validate_path_traversal_sequences(self):
        """Test validation fails for path traversal sequences."""
        errors = _validate_task_id_security("../parent-dir")
        assert len(errors) >= 1
        assert any("path traversal" in error for error in errors)

    def test_validate_absolute_path_attempts(self):
        """Test validation fails for absolute path attempts."""
        errors = _validate_task_id_security("/absolute/path")
        assert len(errors) >= 1
        assert any("path separators" in error for error in errors)

    def test_validate_windows_path_attempts(self):
        """Test validation fails for Windows path attempts."""
        errors = _validate_task_id_security("\\windows\\path")
        assert len(errors) >= 1
        assert any("path separators" in error for error in errors)

    def test_validate_control_characters(self):
        """Test validation fails for control characters in task ID."""
        errors = _validate_task_id_security("task\x00id")
        assert len(errors) >= 1
        assert any("control characters" in error for error in errors)

    def test_validate_reserved_names(self):
        """Test validation fails for reserved system names."""
        reserved_names = ["con", "prn", "aux", "nul", "com1", "lpt1"]
        for name in reserved_names:
            errors = _validate_task_id_security(name)
            assert len(errors) >= 1
            assert any("reserved system name" in error for error in errors)

    def test_validate_reserved_names_case_insensitive(self):
        """Test validation fails for reserved names regardless of case."""
        errors = _validate_task_id_security("CON")
        assert len(errors) >= 1
        assert any("reserved system name" in error for error in errors)

    def test_validate_filesystem_length_limits(self):
        """Test validation is handled by main function, not security function."""
        very_long_id = "a" * 300  # Exceeds 255 character filesystem limit
        errors = _validate_task_id_security(very_long_id)
        # Security function no longer checks length limits to avoid duplicates
        assert len(errors) == 0


class TestValidateStatusParameterSecurity:
    """Test the status parameter security validation function."""

    def test_validate_valid_status_values(self):
        """Test validation passes for valid status values."""
        valid_statuses = ["open", "in-progress", "review", "done"]
        for status in valid_statuses:
            errors = _validate_status_parameter_security(status)
            assert errors == []

    def test_validate_invalid_status_values(self):
        """Test validation fails for invalid status values."""
        invalid_statuses = ["invalid", "pending", "closed", "archived"]
        for status in invalid_statuses:
            errors = _validate_status_parameter_security(status)
            assert len(errors) >= 1
            assert any("Invalid status parameter" in error for error in errors)

    def test_validate_path_traversal_in_status(self):
        """Test validation fails for path traversal attempts in status."""
        errors = _validate_status_parameter_security("../directory")
        assert len(errors) >= 1
        assert any("path traversal" in error for error in errors)

    def test_validate_path_separators_in_status(self):
        """Test validation fails for path separators in status."""
        errors = _validate_status_parameter_security("invalid/status")
        assert len(errors) >= 1
        assert any("path separators" in error for error in errors)

    def test_validate_windows_path_separators_in_status(self):
        """Test validation fails for Windows path separators in status."""
        errors = _validate_status_parameter_security("invalid\\status")
        assert len(errors) >= 1
        assert any("path separators" in error for error in errors)

    def test_validate_control_characters_in_status(self):
        """Test validation fails for control characters in status."""
        errors = _validate_status_parameter_security("invalid\x00status")
        assert len(errors) >= 1
        assert any("control characters" in error for error in errors)

    def test_validate_multiple_status_errors(self):
        """Test validation returns multiple errors for multiple issues."""
        errors = _validate_status_parameter_security("invalid/../status")
        assert len(errors) >= 2
        assert any("Invalid status parameter" in error for error in errors)
        assert any("path traversal" in error for error in errors)


class TestTaskIdEdgeCases:
    """Test edge cases for task ID validation."""

    def test_validate_single_character_task_id(self):
        """Test validation for single character task ID."""
        errors = _validate_task_id_security("a")
        assert errors == []

    def test_validate_max_length_task_id(self):
        """Test validation for task ID at maximum length."""
        max_length_id = "a" * 32  # Maximum allowed length
        errors = _validate_task_id_security(max_length_id)
        assert errors == []

    def test_validate_task_id_with_hyphens(self):
        """Test validation for task ID with multiple hyphens."""
        errors = _validate_task_id_security("task-with-many-hyphens")
        assert errors == []

    def test_validate_task_id_starting_with_number(self):
        """Test validation for task ID starting with number."""
        errors = _validate_task_id_security("1-task-id")
        assert errors == []

    def test_validate_task_id_ending_with_number(self):
        """Test validation for task ID ending with number."""
        errors = _validate_task_id_security("task-id-1")
        assert errors == []

    def test_validate_numeric_only_task_id(self):
        """Test validation for numeric-only task ID."""
        errors = _validate_task_id_security("123456")
        assert errors == []


class TestIntegrationWithExistingValidation:
    """Test integration with existing validation infrastructure."""

    def test_validate_task_id_with_existing_charset_validation(self):
        """Test that new validation works with existing charset validation."""
        # This should fail the existing charset validation
        errors = validate_standalone_task_path_parameters("UPPERCASE-ID", "open")
        assert len(errors) >= 1
        assert any("invalid characters" in error for error in errors)

    def test_validate_task_id_with_existing_length_validation(self):
        """Test that new validation works with filesystem length limits."""
        # This should be acceptable (under 255 chars) but let's test the limit
        long_id = "a" * 300  # Exceeds 255 character filesystem limit
        errors = validate_standalone_task_path_parameters(long_id, "open")
        assert len(errors) >= 1
        assert any("filesystem name limits" in error for error in errors)

    def test_validate_combined_validation_errors(self):
        """Test that both existing and new validation errors are returned."""
        # This should fail both existing and new validation
        errors = validate_standalone_task_path_parameters("INVALID@../ID", "bad-status")
        assert len(errors) >= 3  # At least charset, security, and status errors
        assert any("invalid characters" in error for error in errors)
        assert any("path traversal" in error for error in errors)
        assert any("Invalid status parameter" in error for error in errors)
