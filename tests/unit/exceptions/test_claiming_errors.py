"""Unit tests for claiming parameter validation error classes.

Tests the specific error classes for claimNextTask parameter validation,
including error message formatting, context capture, and inheritance.
"""

import pytest

from src.trellis_mcp.exceptions.claiming_errors import (
    CLAIMING_ERROR_MESSAGES,
    InvalidParameterCombinationError,
    MutualExclusivityError,
    ParameterFormatError,
    ParameterValidationError,
    _sanitize_parameter_for_error_message,
    create_claiming_parameter_error,
)
from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode


class TestParameterValidationError:
    """Test base ParameterValidationError class."""

    def test_parameter_validation_error_can_be_raised(self):
        """Test that ParameterValidationError can be raised and caught."""
        with pytest.raises(ParameterValidationError):
            raise ParameterValidationError("Test error message")

    def test_parameter_validation_error_with_message(self):
        """Test that ParameterValidationError correctly stores message."""
        error = ParameterValidationError("Error message")
        assert "Error message" in str(error)
        assert error.errors == ["Error message"]

    def test_parameter_validation_error_inherits_from_validation_error(self):
        """Test that ParameterValidationError inherits from ValidationError."""
        error = ParameterValidationError("Test error")
        assert isinstance(error, ValidationError)
        assert isinstance(error, Exception)

    def test_parameter_validation_error_with_error_codes(self):
        """Test initialization with error codes."""
        error = ParameterValidationError(
            "Test error", error_codes=ValidationErrorCode.INVALID_STATUS
        )
        assert error.errors == ["Test error"]
        assert error.error_codes == [ValidationErrorCode.INVALID_STATUS]

    def test_parameter_validation_error_with_context(self):
        """Test initialization with context information."""
        context = {"field": "scope", "value": "invalid"}
        error = ParameterValidationError(
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

    def test_parameter_validation_error_to_dict(self):
        """Test error serialization to dictionary."""
        error = ParameterValidationError(
            "Test error", error_codes=[ValidationErrorCode.INVALID_FIELD], context={"test": "value"}
        )

        result = error.to_dict()
        assert result["error_type"] == "ParameterValidationError"
        assert result["errors"] == ["Test error"]
        assert result["error_codes"] == ["invalid_field"]
        assert result["context"] == {"test": "value"}


class TestMutualExclusivityError:
    """Test MutualExclusivityError class and its methods."""

    def test_mutual_exclusivity_error_inherits_from_parameter_validation_error(self):
        """Test that MutualExclusivityError inherits from ParameterValidationError."""
        error = MutualExclusivityError("Test error")
        assert isinstance(error, ParameterValidationError)
        assert isinstance(error, ValidationError)

    def test_scope_and_task_id_conflict_class_method(self):
        """Test scope_and_task_id_conflict class method."""
        error = MutualExclusivityError.scope_and_task_id_conflict("P-test-project", "T-test-task")

        assert isinstance(error, MutualExclusivityError)
        assert error.error_codes == [ValidationErrorCode.INVALID_FIELD]
        assert "Cannot specify both scope" in error.errors[0]
        assert "P-test-project" in error.errors[0]
        assert "T-test-task" in error.errors[0]

        # Check context information
        assert error.context["scope_value"] == "P-test-project"
        assert error.context["task_id_value"] == "T-test-task"
        assert error.context["conflict_type"] == "mutual_exclusivity"
        assert "suggested_fix" in error.context

    def test_scope_and_task_id_conflict_with_context(self):
        """Test scope_and_task_id_conflict with additional context."""
        additional_context = {"operation": "claim_next_task"}
        error = MutualExclusivityError.scope_and_task_id_conflict(
            "E-epic-name", "T-task-name", additional_context
        )

        assert error.context["operation"] == "claim_next_task"
        assert error.context["scope_value"] == "E-epic-name"
        assert error.context["task_id_value"] == "T-task-name"

    def test_scope_and_task_id_conflict_sanitizes_sensitive_values(self):
        """Test that sensitive values are sanitized in error messages."""
        error = MutualExclusivityError.scope_and_task_id_conflict(
            "P-secret-project", "T-password-task"
        )

        # Values containing sensitive keywords should be redacted
        assert "[redacted-sensitive]" in error.errors[0]

    def test_scope_and_task_id_conflict_handles_empty_values(self):
        """Test handling of empty or None values."""
        error = MutualExclusivityError.scope_and_task_id_conflict("", "   ")

        assert "[empty]" in error.errors[0]


class TestInvalidParameterCombinationError:
    """Test InvalidParameterCombinationError class and its methods."""

    def test_invalid_parameter_combination_error_inherits_properly(self):
        """Test that InvalidParameterCombinationError inherits correctly."""
        error = InvalidParameterCombinationError("Test error")
        assert isinstance(error, ParameterValidationError)
        assert isinstance(error, ValidationError)

    def test_force_claim_without_task_id_class_method(self):
        """Test force_claim_without_task_id class method."""
        error = InvalidParameterCombinationError.force_claim_without_task_id(True)

        assert isinstance(error, InvalidParameterCombinationError)
        assert error.error_codes == [ValidationErrorCode.INVALID_FIELD]
        assert "force_claim parameter" in error.errors[0]
        assert "must be used with task_id" in error.errors[0]

        # Check context information
        assert error.context["force_claim_value"] is True
        assert error.context["missing_parameter"] == "task_id"
        assert error.context["parameter_combination_error"] == "force_claim_without_task_id"
        assert "suggested_fix" in error.context

    def test_force_claim_without_task_id_with_context(self):
        """Test force_claim_without_task_id with additional context."""
        additional_context = {"user": "test_user"}
        error = InvalidParameterCombinationError.force_claim_without_task_id(
            False, additional_context
        )

        assert error.context["user"] == "test_user"
        assert error.context["force_claim_value"] is False

    def test_invalid_scope_with_force_claim_class_method(self):
        """Test invalid_scope_with_force_claim class method."""
        error = InvalidParameterCombinationError.invalid_scope_with_force_claim("P-project", True)

        assert isinstance(error, InvalidParameterCombinationError)
        assert error.error_codes == [ValidationErrorCode.INVALID_FIELD]
        assert "Cannot use force_claim" in error.errors[0]
        assert "P-project" in error.errors[0]

        # Check context information
        assert error.context["scope_value"] == "P-project"
        assert error.context["force_claim_value"] is True
        assert error.context["parameter_combination_error"] == "scope_with_force_claim"

    def test_invalid_scope_with_force_claim_sanitizes_sensitive_values(self):
        """Test that sensitive scope values are sanitized."""
        error = InvalidParameterCombinationError.invalid_scope_with_force_claim(
            "P-secret-scope", True
        )

        # Values containing sensitive keywords should be redacted
        assert "[redacted-sensitive]" in error.errors[0]


class TestParameterFormatError:
    """Test ParameterFormatError class and its methods."""

    def test_parameter_format_error_inherits_properly(self):
        """Test that ParameterFormatError inherits correctly."""
        error = ParameterFormatError("Test error")
        assert isinstance(error, ParameterValidationError)
        assert isinstance(error, ValidationError)

    def test_invalid_scope_format_class_method(self):
        """Test invalid_scope_format class method."""
        error = ParameterFormatError.invalid_scope_format("invalid-scope")

        assert isinstance(error, ParameterFormatError)
        assert error.error_codes == [ValidationErrorCode.INVALID_FORMAT]
        assert "Invalid scope ID format" in error.errors[0]
        assert "invalid-scope" in error.errors[0]
        assert "P- (project), E- (epic), or F- (feature) prefix" in error.errors[0]

        # Check context information
        assert error.context["invalid_scope_value"] == "invalid-scope"
        assert error.context["format_error_type"] == "scope_format"
        assert "expected_format" in error.context
        assert "valid_examples" in error.context

    def test_invalid_scope_format_with_context(self):
        """Test invalid_scope_format with additional context."""
        additional_context = {"source": "user_input"}
        error = ParameterFormatError.invalid_scope_format("bad-format", additional_context)

        assert error.context["source"] == "user_input"
        assert error.context["invalid_scope_value"] == "bad-format"

    def test_invalid_task_id_format_class_method(self):
        """Test invalid_task_id_format class method."""
        error = ParameterFormatError.invalid_task_id_format("invalid-task")

        assert isinstance(error, ParameterFormatError)
        assert error.error_codes == [ValidationErrorCode.INVALID_FORMAT]
        assert "Invalid task ID format" in error.errors[0]
        assert "invalid-task" in error.errors[0]
        assert "T- prefix for hierarchical tasks" in error.errors[0]

        # Check context information
        assert error.context["invalid_task_id_value"] == "invalid-task"
        assert error.context["format_error_type"] == "task_id_format"
        assert "expected_format" in error.context
        assert "valid_examples" in error.context

    def test_empty_project_root_class_method(self):
        """Test empty_project_root class method."""
        error = ParameterFormatError.empty_project_root()

        assert isinstance(error, ParameterFormatError)
        assert error.error_codes == [ValidationErrorCode.MISSING_REQUIRED_FIELD]
        assert "Project root parameter cannot be empty" in error.errors[0]
        assert "absolute path" in error.errors[0]

        # Check context information
        assert error.context["format_error_type"] == "empty_project_root"
        assert "suggested_fix" in error.context
        assert "valid_examples" in error.context

    def test_empty_project_root_with_value(self):
        """Test empty_project_root with specific value."""
        error = ParameterFormatError.empty_project_root("   ")

        assert error.context["invalid_project_root_value"] == "   "

    def test_format_errors_sanitize_sensitive_values(self):
        """Test that format errors sanitize sensitive values."""
        error = ParameterFormatError.invalid_scope_format("P-secret-project")

        # Values containing sensitive keywords should be redacted
        assert "[redacted-sensitive]" in error.errors[0]


class TestSanitizationFunction:
    """Test the _sanitize_parameter_for_error_message helper function."""

    def test_sanitize_normal_values(self):
        """Test sanitization of normal parameter values."""
        assert _sanitize_parameter_for_error_message("P-project-name") == "P-project-name"
        assert _sanitize_parameter_for_error_message("T-task-123") == "T-task-123"
        assert _sanitize_parameter_for_error_message("E-epic-feature") == "E-epic-feature"

    def test_sanitize_empty_values(self):
        """Test sanitization of empty or None values."""
        assert _sanitize_parameter_for_error_message("") == "[empty]"
        assert _sanitize_parameter_for_error_message("   ") == "[empty]"
        assert _sanitize_parameter_for_error_message(None) == "[empty]"

    def test_sanitize_sensitive_patterns(self):
        """Test sanitization of values containing sensitive patterns."""
        sensitive_values = [
            "password-field",
            "secret-key",
            "api-token",
            "auth-header",
            "private-data",
            "credential-info",
            "confidential-project",
        ]

        for value in sensitive_values:
            result = _sanitize_parameter_for_error_message(value)
            assert result == "[redacted-sensitive]"

    def test_sanitize_case_insensitive(self):
        """Test that sanitization is case-insensitive."""
        assert _sanitize_parameter_for_error_message("PASSWORD-field") == "[redacted-sensitive]"
        assert _sanitize_parameter_for_error_message("Secret-Key") == "[redacted-sensitive]"
        assert _sanitize_parameter_for_error_message("API-TOKEN") == "[redacted-sensitive]"

    def test_sanitize_long_values(self):
        """Test sanitization of overly long values."""
        long_value = "a" * 150
        result = _sanitize_parameter_for_error_message(long_value)
        assert len(result) <= 103  # 100 chars + "..."
        assert result.endswith("...")

    def test_sanitize_with_custom_max_length(self):
        """Test sanitization with custom max length."""
        long_value = "abcdefghijk"
        result = _sanitize_parameter_for_error_message(long_value, max_length=5)
        assert result == "abcde..."

    def test_sanitize_whitespace_handling(self):
        """Test sanitization handles whitespace properly."""
        assert _sanitize_parameter_for_error_message("  P-project  ") == "P-project"


class TestClaimingErrorMessages:
    """Test the CLAIMING_ERROR_MESSAGES constants."""

    def test_error_messages_exist(self):
        """Test that all expected error message constants exist."""
        expected_keys = [
            "MUTUAL_EXCLUSIVITY_SCOPE_TASK_ID",
            "FORCE_CLAIM_REQUIRES_TASK_ID",
            "INVALID_SCOPE_FORMAT",
            "INVALID_TASK_ID_FORMAT",
            "EMPTY_PROJECT_ROOT",
        ]

        for key in expected_keys:
            assert key in CLAIMING_ERROR_MESSAGES
            assert isinstance(CLAIMING_ERROR_MESSAGES[key], str)
            assert len(CLAIMING_ERROR_MESSAGES[key]) > 0

    def test_error_messages_are_descriptive(self):
        """Test that error messages are descriptive and helpful."""
        for key, message in CLAIMING_ERROR_MESSAGES.items():
            # Messages should be reasonably descriptive
            assert len(message.split()) >= 5  # At least 5 words
            # Messages should not be all caps (except for abbreviations)
            assert not message.isupper()


class TestCreateClaimingParameterError:
    """Test the create_claiming_parameter_error factory function."""

    def test_create_mutual_exclusivity_error(self):
        """Test creating mutual exclusivity error via factory."""
        error = create_claiming_parameter_error(
            "mutual_exclusivity_scope_task_id", scope_value="P-project", task_id_value="T-task"
        )

        assert isinstance(error, MutualExclusivityError)
        assert "Cannot specify both scope" in error.errors[0]

    def test_create_force_claim_without_task_id_error(self):
        """Test creating force claim error via factory."""
        error = create_claiming_parameter_error(
            "force_claim_without_task_id", force_claim_value=True
        )

        assert isinstance(error, InvalidParameterCombinationError)
        assert "force_claim parameter" in error.errors[0]

    def test_create_invalid_scope_with_force_claim_error(self):
        """Test creating invalid scope with force claim error via factory."""
        error = create_claiming_parameter_error(
            "invalid_scope_with_force_claim", scope_value="P-project", force_claim_value=True
        )

        assert isinstance(error, InvalidParameterCombinationError)
        assert "Cannot use force_claim" in error.errors[0]

    def test_create_invalid_scope_format_error(self):
        """Test creating invalid scope format error via factory."""
        error = create_claiming_parameter_error("invalid_scope_format", scope_value="invalid-scope")

        assert isinstance(error, ParameterFormatError)
        assert "Invalid scope ID format" in error.errors[0]

    def test_create_invalid_task_id_format_error(self):
        """Test creating invalid task ID format error via factory."""
        error = create_claiming_parameter_error(
            "invalid_task_id_format", task_id_value="invalid-task"
        )

        assert isinstance(error, ParameterFormatError)
        assert "Invalid task ID format" in error.errors[0]

    def test_create_empty_project_root_error(self):
        """Test creating empty project root error via factory."""
        error = create_claiming_parameter_error("empty_project_root", project_root_value="")

        assert isinstance(error, ParameterFormatError)
        assert "Project root parameter cannot be empty" in error.errors[0]

    def test_create_error_with_context(self):
        """Test creating error with additional context via factory."""
        context = {"user": "test_user", "operation": "claim"}
        error = create_claiming_parameter_error(
            "empty_project_root", project_root_value=None, context=context
        )

        assert error.context["user"] == "test_user"
        assert error.context["operation"] == "claim"

    def test_factory_unknown_error_type_raises_value_error(self):
        """Test that factory raises ValueError for unknown error types."""
        with pytest.raises(ValueError) as exc_info:
            create_claiming_parameter_error("unknown_error_type")

        assert "Unknown error type: unknown_error_type" in str(exc_info.value)
        assert "Valid types:" in str(exc_info.value)

    def test_factory_lists_valid_error_types_in_exception(self):
        """Test that factory lists valid error types in exception message."""
        with pytest.raises(ValueError) as exc_info:
            create_claiming_parameter_error("invalid_type")

        error_message = str(exc_info.value)
        expected_types = [
            "mutual_exclusivity_scope_task_id",
            "force_claim_without_task_id",
            "invalid_scope_with_force_claim",
            "invalid_scope_format",
            "invalid_task_id_format",
            "empty_project_root",
        ]

        for error_type in expected_types:
            assert error_type in error_message


class TestErrorMessageQuality:
    """Test the quality and usefulness of error messages."""

    def test_error_messages_include_specific_guidance(self):
        """Test that error messages include specific guidance for fixing issues."""
        error = MutualExclusivityError.scope_and_task_id_conflict("P-proj", "T-task")
        message = error.errors[0]

        # Should explain what went wrong
        assert "Cannot specify both" in message
        # Should explain how to fix it
        assert "Use scope for" in message or "task_id for" in message

    def test_error_messages_include_parameter_context(self):
        """Test that error messages show which parameters caused the conflict."""
        error = MutualExclusivityError.scope_and_task_id_conflict("P-proj", "T-task")
        message = error.errors[0]

        # Should show both conflicting parameter values
        assert "P-proj" in message
        assert "T-task" in message

    def test_format_error_messages_include_examples(self):
        """Test that format error messages include examples of correct formats."""
        error = ParameterFormatError.invalid_scope_format("bad-format")
        message = error.errors[0]

        # Should include format explanation
        assert "P- (project), E- (epic), or F- (feature)" in message
        # Should include examples
        assert "Examples:" in message or "example" in message.lower()

    def test_context_information_is_comprehensive(self):
        """Test that context information is comprehensive and useful."""
        error = InvalidParameterCombinationError.force_claim_without_task_id(True)

        # Should have suggested fix
        assert "suggested_fix" in error.context
        assert len(error.context["suggested_fix"]) > 10  # Reasonably descriptive

        # Should have parameter information
        assert "force_claim_value" in error.context
        assert "missing_parameter" in error.context

    def test_error_messages_use_clear_language(self):
        """Test that error messages use clear, non-technical language."""
        errors = [
            MutualExclusivityError.scope_and_task_id_conflict("P-proj", "T-task"),
            InvalidParameterCombinationError.force_claim_without_task_id(True),
            ParameterFormatError.invalid_scope_format("bad"),
            ParameterFormatError.empty_project_root(),
        ]

        for error in errors:
            message = error.errors[0]
            # Should not contain overly technical jargon
            assert "mutex" not in message.lower()
            assert "validation failed" not in message.lower()
            # Should use clear action words
            clear_words = ["cannot", "must", "should", "use", "provide", "specify"]
            assert any(word in message.lower() for word in clear_words)
