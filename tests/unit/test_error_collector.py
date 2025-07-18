"""Tests for the ValidationErrorCollector class."""

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.validation.error_collector import (
    ErrorCategory,
    ErrorSeverity,
    ValidationErrorCollector,
)


class TestValidationErrorCollector:
    """Test cases for ValidationErrorCollector class."""

    def test_init_with_object_info(self):
        """Test collector initialization with object information."""
        collector = ValidationErrorCollector(object_id="T-123", object_kind="task")

        assert collector.object_id == "T-123"
        assert collector.object_kind == "task"
        assert not collector.has_errors()
        assert collector.get_error_count() == 0

    def test_init_without_object_info(self):
        """Test collector initialization without object information."""
        collector = ValidationErrorCollector()

        assert collector.object_id is None
        assert collector.object_kind is None
        assert not collector.has_errors()

    def test_add_error_with_auto_severity_and_category(self):
        """Test adding error with auto-determined severity and category."""
        collector = ValidationErrorCollector()

        collector.add_error("Missing required field", ValidationErrorCode.MISSING_REQUIRED_FIELD)

        assert collector.has_errors()
        assert collector.get_error_count() == 1
        assert collector.has_critical_errors()

        # Check that severity and category were auto-determined
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) == 1
        assert critical_errors[0][0] == "Missing required field"

        field_errors = collector.get_errors_by_category(ErrorCategory.FIELD)
        assert len(field_errors) == 1

    def test_add_error_with_explicit_severity_and_category(self):
        """Test adding error with explicit severity and category."""
        collector = ValidationErrorCollector()

        collector.add_error(
            "Custom error",
            ValidationErrorCode.INVALID_FIELD,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.SYSTEM,
        )

        # Should use explicit values, not auto-determined ones
        low_errors = collector.get_errors_by_severity(ErrorSeverity.LOW)
        assert len(low_errors) == 1

        system_errors = collector.get_errors_by_category(ErrorCategory.SYSTEM)
        assert len(system_errors) == 1

    def test_add_error_with_context(self):
        """Test adding error with context information."""
        collector = ValidationErrorCollector()
        context = {"field": "status", "value": "invalid"}

        collector.add_error("Invalid status", ValidationErrorCode.INVALID_STATUS, context=context)

        high_errors = collector.get_errors_by_severity(ErrorSeverity.HIGH)
        assert len(high_errors) == 1
        assert high_errors[0][2] == context

    def test_multiple_errors_different_severities(self):
        """Test collecting multiple errors with different severities."""
        collector = ValidationErrorCollector()

        # Add errors of different severities
        collector.add_error("Critical error", ValidationErrorCode.MISSING_REQUIRED_FIELD)
        collector.add_error("High error", ValidationErrorCode.INVALID_STATUS)
        collector.add_error("Medium error", ValidationErrorCode.INVALID_FIELD)

        assert collector.get_error_count() == 3
        assert collector.has_critical_errors()

        # Check counts by severity
        assert len(collector.get_errors_by_severity(ErrorSeverity.CRITICAL)) == 1
        assert len(collector.get_errors_by_severity(ErrorSeverity.HIGH)) == 1
        assert len(collector.get_errors_by_severity(ErrorSeverity.MEDIUM)) == 1

    def test_get_summary(self):
        """Test getting error summary."""
        collector = ValidationErrorCollector()

        collector.add_error("Missing field", ValidationErrorCode.MISSING_REQUIRED_FIELD)
        collector.add_error("Invalid status", ValidationErrorCode.INVALID_STATUS)
        collector.add_error("Invalid parent", ValidationErrorCode.PARENT_NOT_EXIST)

        summary = collector.get_summary()

        assert summary["total_errors"] == 3
        assert summary["has_critical"] is True
        assert summary["severity_breakdown"]["CRITICAL"] == 1
        assert summary["severity_breakdown"]["HIGH"] == 2
        assert summary["category_breakdown"]["field"] == 2
        assert summary["category_breakdown"]["relationship"] == 1

    def test_get_detailed_view(self):
        """Test getting detailed error view."""
        collector = ValidationErrorCollector(object_id="T-123", object_kind="task")

        collector.add_error(
            "Missing field", ValidationErrorCode.MISSING_REQUIRED_FIELD, context={"field": "title"}
        )
        collector.add_error(
            "Invalid parent", ValidationErrorCode.PARENT_NOT_EXIST, context={"parent_id": "F-456"}
        )

        detailed = collector.get_detailed_view()

        assert detailed["object_id"] == "T-123"
        assert detailed["object_kind"] == "task"
        assert detailed["summary"]["total_errors"] == 2

        # Check error grouping by category
        assert "field" in detailed["errors_by_category"]
        assert "relationship" in detailed["errors_by_category"]

        field_errors = detailed["errors_by_category"]["field"]
        assert len(field_errors) == 1
        assert field_errors[0]["message"] == "Missing field"
        assert field_errors[0]["error_code"] == "missing_required_field"
        assert field_errors[0]["severity"] == "CRITICAL"
        assert field_errors[0]["context"]["field"] == "title"

    def test_get_prioritized_errors(self):
        """Test getting errors in priority order."""
        collector = ValidationErrorCollector()

        # Add in non-priority order
        collector.add_error("Medium error", ValidationErrorCode.INVALID_FIELD)
        collector.add_error("Critical error", ValidationErrorCode.MISSING_REQUIRED_FIELD)
        collector.add_error("High error", ValidationErrorCode.INVALID_STATUS)

        prioritized = collector.get_prioritized_errors()

        # Should be ordered by severity (critical first)
        assert len(prioritized) == 3
        assert prioritized[0][0] == "Critical error"  # CRITICAL
        assert prioritized[1][0] == "High error"  # HIGH
        assert prioritized[2][0] == "Medium error"  # MEDIUM

    def test_create_validation_error_basic(self):
        """Test creating ValidationError from collected errors."""
        collector = ValidationErrorCollector(object_id="T-123", object_kind="task")

        collector.add_error("Error 1", ValidationErrorCode.INVALID_STATUS)
        collector.add_error("Error 2", ValidationErrorCode.MISSING_REQUIRED_FIELD)

        exception = collector.create_validation_error(task_type="standalone")

        assert isinstance(exception, ValidationError)
        assert len(exception.errors) == 2
        assert len(exception.error_codes) == 2
        assert exception.object_id == "T-123"
        assert exception.object_kind == "task"
        assert exception.task_type == "standalone"

        # Should be in priority order (critical first)
        assert exception.errors[0] == "Error 2"  # CRITICAL
        assert exception.errors[1] == "Error 1"  # HIGH

    def test_create_validation_error_with_detailed_context(self):
        """Test creating ValidationError with detailed context."""
        collector = ValidationErrorCollector(object_id="T-123")

        collector.add_error("Error 1", ValidationErrorCode.INVALID_STATUS)

        exception = collector.create_validation_error(include_detailed_context=True)

        assert "error_details" in exception.context
        assert exception.context["error_details"]["object_id"] == "T-123"
        assert exception.context["error_details"]["summary"]["total_errors"] == 1

    def test_create_validation_error_no_errors(self):
        """Test creating ValidationError with no errors raises ValueError."""
        collector = ValidationErrorCollector()

        with pytest.raises(ValueError, match="No errors collected to create exception"):
            collector.create_validation_error()

    def test_error_severity_mapping(self):
        """Test that error codes are mapped to correct severities."""
        collector = ValidationErrorCollector()

        # Test critical errors
        critical_codes = [
            ValidationErrorCode.MISSING_REQUIRED_FIELD,
            ValidationErrorCode.INVALID_ENUM_VALUE,
            ValidationErrorCode.CIRCULAR_DEPENDENCY,
            ValidationErrorCode.SCHEMA_VERSION_MISMATCH,
        ]

        for code in critical_codes:
            collector.add_error(f"Error for {code.value}", code)

        assert collector.has_critical_errors()
        assert len(collector.get_errors_by_severity(ErrorSeverity.CRITICAL)) == len(critical_codes)

        # Test high severity errors
        collector.clear()
        high_codes = [
            ValidationErrorCode.INVALID_STATUS,
            ValidationErrorCode.MISSING_PARENT,
            ValidationErrorCode.PARENT_NOT_EXIST,
            ValidationErrorCode.INVALID_STATUS_TRANSITION,
        ]

        for code in high_codes:
            collector.add_error(f"Error for {code.value}", code)

        assert not collector.has_critical_errors()
        assert len(collector.get_errors_by_severity(ErrorSeverity.HIGH)) == len(high_codes)

    def test_error_category_mapping(self):
        """Test that error codes are mapped to correct categories."""
        collector = ValidationErrorCollector()

        # Test field category
        field_codes = [
            ValidationErrorCode.MISSING_REQUIRED_FIELD,
            ValidationErrorCode.INVALID_FIELD,
            ValidationErrorCode.INVALID_ENUM_VALUE,
            ValidationErrorCode.INVALID_STATUS,
        ]

        for code in field_codes:
            collector.add_error(f"Error for {code.value}", code)

        assert len(collector.get_errors_by_category(ErrorCategory.FIELD)) == len(field_codes)

        # Test relationship category
        collector.clear()
        relationship_codes = [
            ValidationErrorCode.MISSING_PARENT,
            ValidationErrorCode.PARENT_NOT_EXIST,
            ValidationErrorCode.CIRCULAR_DEPENDENCY,
        ]

        for code in relationship_codes:
            collector.add_error(f"Error for {code.value}", code)

        assert len(collector.get_errors_by_category(ErrorCategory.RELATIONSHIP)) == len(
            relationship_codes
        )

    def test_clear_errors(self):
        """Test clearing all collected errors."""
        collector = ValidationErrorCollector()

        collector.add_error("Error 1", ValidationErrorCode.INVALID_STATUS)
        collector.add_error("Error 2", ValidationErrorCode.MISSING_REQUIRED_FIELD)

        assert collector.has_errors()
        assert collector.get_error_count() == 2

        collector.clear()

        assert not collector.has_errors()
        assert collector.get_error_count() == 0
        assert not collector.has_critical_errors()

    def test_boolean_and_length_methods(self):
        """Test __bool__ and __len__ methods."""
        collector = ValidationErrorCollector()

        # Empty collector
        assert len(collector) == 0
        assert not collector  # __bool__ returns False

        # With errors
        collector.add_error("Error", ValidationErrorCode.INVALID_STATUS)

        assert len(collector) == 1
        assert collector  # __bool__ returns True

    def test_error_code_fallback_for_unknown_codes(self):
        """Test that unknown error codes get default severity and category."""
        collector = ValidationErrorCollector()

        # Use a code that's not in the mapping (if any)
        collector.add_error("Unknown error", ValidationErrorCode.INVALID_FORMAT)

        # Should get default MEDIUM severity and FIELD category
        medium_errors = collector.get_errors_by_severity(ErrorSeverity.MEDIUM)
        assert len(medium_errors) == 1

        field_errors = collector.get_errors_by_category(ErrorCategory.FIELD)
        assert len(field_errors) == 1

    def test_context_preservation(self):
        """Test that context is preserved through all operations."""
        collector = ValidationErrorCollector()
        context = {"field": "status", "value": "invalid", "valid_values": ["open", "done"]}

        collector.add_error("Invalid status", ValidationErrorCode.INVALID_STATUS, context=context)

        # Context should be preserved in all access methods
        high_errors = collector.get_errors_by_severity(ErrorSeverity.HIGH)
        assert high_errors[0][2] == context

        field_errors = collector.get_errors_by_category(ErrorCategory.FIELD)
        assert field_errors[0][2] == context

        prioritized = collector.get_prioritized_errors()
        assert prioritized[0][2] == context

        detailed = collector.get_detailed_view()
        assert detailed["errors_by_category"]["field"][0]["context"] == context

    def test_empty_context_handling(self):
        """Test handling of None/empty context."""
        collector = ValidationErrorCollector()

        # None context should become empty dict
        collector.add_error("Error 1", ValidationErrorCode.INVALID_STATUS, context=None)

        # Empty context should remain empty
        collector.add_error("Error 2", ValidationErrorCode.INVALID_FIELD, context={})

        prioritized = collector.get_prioritized_errors()
        assert prioritized[0][2] == {}  # HIGH severity (Error 1)
        assert prioritized[1][2] == {}  # MEDIUM severity (Error 2)
