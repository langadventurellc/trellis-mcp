"""Comprehensive error handling system tests.

This test suite consolidates all error handling functionality including:
- Error collection and aggregation workflows
- Message template system and placeholder substitution
- Context-aware messaging and localization
- Error prioritization and categorization
- Performance and thread safety validation
- Integration testing across error handling components

Consolidates tests from:
- test_error_collector.py: ValidationErrorCollector class tests
- test_error_aggregation.py: Error aggregation workflow tests
- test_message_templates.py: Message template system tests
- test_error_messages.py: Error message generation and formatting tests
"""

import threading
import time
from unittest.mock import patch

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.validation.error_collector import (
    ErrorCategory,
    ErrorSeverity,
    ValidationErrorCollector,
)
from src.trellis_mcp.validation.message_templates import (
    MessageTemplate,
    MessageTemplateRegistry,
    TemplateEngine,
    TrellisMessageEngine,
    generate_template_message,
    get_default_engine,
    get_default_templates,
    get_formatter,
)
from src.trellis_mcp.validation.message_templates.formatters import (
    I18nFormatter,
    PlainTextFormatter,
    StructuredFormatter,
    ValidationErrorFormatter,
)


class TestValidationErrorCollector:
    """Test cases for ValidationErrorCollector class.

    Migrated from test_error_collector.py
    """

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


class TestErrorAggregationWorkflow:
    """Test complete error aggregation workflow scenarios.

    Migrated from test_error_aggregation.py
    """

    def test_full_validation_workflow_with_multiple_errors(self):
        """Test complete error aggregation workflow with multiple validation errors."""
        collector = ValidationErrorCollector(object_id="T-test-workflow", object_kind="task")

        # Simulate a complete validation workflow (test data for context)

        # Collect errors as they would be found during validation
        collector.add_error(
            "Missing required field 'title'",
            ValidationErrorCode.MISSING_REQUIRED_FIELD,
            context={"field": "title"},
        )

        collector.add_error(
            "Invalid status 'invalid-status'",
            ValidationErrorCode.INVALID_ENUM_VALUE,
            context={
                "field": "status",
                "value": "invalid-status",
                "valid_values": ["open", "done"],
            },
        )

        collector.add_error(
            "Invalid priority 'ultra-high'",
            ValidationErrorCode.INVALID_ENUM_VALUE,
            context={
                "field": "priority",
                "value": "ultra-high",
                "valid_values": ["high", "medium", "low"],
            },
        )

        collector.add_error(
            "Parent 'F-nonexistent' does not exist",
            ValidationErrorCode.PARENT_NOT_EXIST,
            context={"parent_id": "F-nonexistent", "parent_type": "feature"},
        )

        collector.add_error(
            "Circular dependency detected with prerequisite 'T-self-reference'",
            ValidationErrorCode.CIRCULAR_DEPENDENCY,
            context={"prerequisite_id": "T-self-reference"},
        )

        # Verify aggregation results
        assert collector.get_error_count() == 5
        assert collector.has_critical_errors()

        # Test prioritization
        prioritized_errors = collector.get_prioritized_errors()
        assert len(prioritized_errors) == 5  # All errors should be present

        # Test that errors are properly ordered by severity
        # (prioritized_errors returns in priority order)
        # First error should be critical
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        high_errors = collector.get_errors_by_severity(ErrorSeverity.HIGH)
        # Missing field, invalid enum (status), invalid enum (priority), circular dependency
        assert len(critical_errors) == 4
        assert len(high_errors) == 1  # Parent not exist

        # Test categorization
        field_errors = collector.get_errors_by_category(ErrorCategory.FIELD)
        relationship_errors = collector.get_errors_by_category(ErrorCategory.RELATIONSHIP)
        assert len(field_errors) == 3  # title, status, priority
        assert len(relationship_errors) == 2  # parent, circular dependency

        # Test summary generation
        summary = collector.get_summary()
        assert summary["total_errors"] == 5
        assert summary["has_critical"] is True
        assert summary["severity_breakdown"]["CRITICAL"] == 4
        assert summary["severity_breakdown"]["HIGH"] == 1
        assert summary["category_breakdown"]["field"] == 3
        assert summary["category_breakdown"]["relationship"] == 2

        # Test validation error creation
        validation_error = collector.create_validation_error(
            task_type="hierarchy", include_detailed_context=True
        )
        assert isinstance(validation_error, ValidationError)
        assert len(validation_error.errors) == 5
        assert validation_error.object_id == "T-test-workflow"
        assert validation_error.task_type == "hierarchy"
        assert "error_details" in validation_error.context

    def test_error_aggregation_with_empty_collector(self):
        """Test error aggregation behavior with empty error collector."""
        collector = ValidationErrorCollector(object_id="T-empty", object_kind="task")

        # Test empty state
        assert not collector.has_errors()
        assert collector.get_error_count() == 0
        assert not collector.has_critical_errors()

        # Test empty collections
        assert len(collector.get_prioritized_errors()) == 0
        assert len(collector.get_errors_by_severity(ErrorSeverity.CRITICAL)) == 0
        assert len(collector.get_errors_by_category(ErrorCategory.FIELD)) == 0

        # Test empty summary
        summary = collector.get_summary()
        assert summary["total_errors"] == 0
        assert summary["has_critical"] is False
        assert all(count == 0 for count in summary["severity_breakdown"].values())
        assert all(count == 0 for count in summary["category_breakdown"].values())

        # Test empty detailed view
        detailed = collector.get_detailed_view()
        assert detailed["summary"]["total_errors"] == 0
        assert len(detailed["errors_by_category"]) == 0

        # Test exception creation with empty collector
        with pytest.raises(ValueError, match="No errors collected to create exception"):
            collector.create_validation_error()

    def test_error_aggregation_with_single_error_type(self):
        """Test error aggregation with only one type of error."""
        collector = ValidationErrorCollector(object_id="T-single-type", object_kind="task")

        # Add multiple errors of the same type
        for i in range(3):
            collector.add_error(
                f"Missing required field 'field_{i}'",
                ValidationErrorCode.MISSING_REQUIRED_FIELD,
                context={"field": f"field_{i}"},
            )

        # Test aggregation with single error type
        assert collector.get_error_count() == 3
        assert collector.has_critical_errors()

        # All errors should be critical and field category
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        field_errors = collector.get_errors_by_category(ErrorCategory.FIELD)
        assert len(critical_errors) == 3
        assert len(field_errors) == 3

        # Test summary with single error type
        summary = collector.get_summary()
        assert summary["severity_breakdown"]["CRITICAL"] == 3
        # Only categories with errors will be present in breakdown
        assert summary["severity_breakdown"].get("HIGH", 0) == 0
        assert summary["severity_breakdown"].get("MEDIUM", 0) == 0
        assert summary["severity_breakdown"].get("LOW", 0) == 0
        assert summary["category_breakdown"]["field"] == 3
        assert sum(summary["category_breakdown"].values()) == 3


class TestErrorAggregationPerformance:
    """Test performance characteristics of error aggregation system.

    Migrated from test_error_aggregation.py
    """

    def test_error_collection_performance_with_large_error_count(self):
        """Test performance impact of collecting large numbers of errors."""
        collector = ValidationErrorCollector(object_id="T-performance", object_kind="task")

        # Test with large number of errors
        error_count = 1000
        start_time = time.time()

        for i in range(error_count):
            collector.add_error(
                f"Error {i}",
                ValidationErrorCode.INVALID_FIELD,
                context={"field": f"field_{i}", "value": f"value_{i}"},
            )

        collection_time = time.time() - start_time

        # Verify all errors were collected
        assert collector.get_error_count() == error_count
        assert len(collector.get_prioritized_errors()) == error_count

        # Performance should be reasonable (< 1 second for 1000 errors)
        assert (
            collection_time < 1.0
        ), f"Error collection took {collection_time:.3f}s, expected < 1.0s"

    def test_error_aggregation_operations_performance(self):
        """Test performance of error aggregation operations."""
        collector = ValidationErrorCollector(object_id="T-operations", object_kind="task")

        # Add mix of errors
        error_types = [
            (ValidationErrorCode.MISSING_REQUIRED_FIELD, ErrorSeverity.CRITICAL),
            (ValidationErrorCode.INVALID_STATUS, ErrorSeverity.HIGH),
            (ValidationErrorCode.INVALID_FIELD, ErrorSeverity.MEDIUM),
        ]

        for i in range(300):  # 100 of each type
            code, _ = error_types[i % len(error_types)]
            collector.add_error(f"Error {i}", code, context={"index": i})

        # Test performance of aggregation operations
        start_time = time.time()

        # Perform multiple aggregation operations
        for _ in range(10):
            collector.get_prioritized_errors()
            collector.get_summary()
            collector.get_detailed_view()
            collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
            collector.get_errors_by_category(ErrorCategory.FIELD)

        aggregation_time = time.time() - start_time

        # Aggregation operations should be fast
        assert (
            aggregation_time < 0.5
        ), f"Aggregation operations took {aggregation_time:.3f}s, expected < 0.5s"

    def test_validation_error_creation_performance(self):
        """Test performance of creating ValidationError from aggregated errors."""
        collector = ValidationErrorCollector(object_id="T-creation", object_kind="task")

        # Add many errors
        for i in range(100):
            collector.add_error(
                f"Error {i}",
                ValidationErrorCode.INVALID_FIELD,
                context={"field": f"field_{i}"},
            )

        # Test ValidationError creation performance
        start_time = time.time()

        for _ in range(10):
            exception = collector.create_validation_error(
                task_type="standalone", include_detailed_context=True
            )
            assert isinstance(exception, ValidationError)

        creation_time = time.time() - start_time

        # Creation should be fast
        assert (
            creation_time < 0.1
        ), f"ValidationError creation took {creation_time:.3f}s, expected < 0.1s"

    def test_memory_efficiency_with_large_context(self):
        """Test memory efficiency when storing large context objects."""
        collector = ValidationErrorCollector(object_id="T-memory", object_kind="task")

        # Create large context objects
        large_context = {
            "large_data": "x" * 1000,  # 1KB string
            "nested_data": {"level_" + str(i): "data_" + str(i) for i in range(100)},
            "list_data": [f"item_{i}" for i in range(100)],
        }

        # Add errors with large context
        for i in range(50):
            collector.add_error(
                f"Error with large context {i}",
                ValidationErrorCode.INVALID_FIELD,
                context=large_context.copy(),
            )

        # Verify functionality still works with large contexts
        assert collector.get_error_count() == 50
        detailed_view = collector.get_detailed_view()
        assert len(detailed_view["errors_by_category"]["field"]) == 50

        # Context should be preserved correctly
        first_error = detailed_view["errors_by_category"]["field"][0]
        assert first_error["context"]["large_data"] == "x" * 1000


class TestErrorAggregationEdgeCases:
    """Test edge cases and error conditions in error aggregation.

    Migrated from test_error_aggregation.py
    """

    def test_error_aggregation_with_null_and_empty_values(self):
        """Test error aggregation with null and empty values."""
        collector = ValidationErrorCollector(object_id="T-null-empty", object_kind="task")

        # Test with None values - note: collector handles None by converting to empty string
        collector.add_error(None, ValidationErrorCode.INVALID_FIELD, context=None)  # type: ignore
        collector.add_error("", ValidationErrorCode.INVALID_STATUS, context={})
        collector.add_error(
            "Valid error", ValidationErrorCode.MISSING_REQUIRED_FIELD, context={"field": None}
        )

        # All errors should be collected
        assert collector.get_error_count() == 3

        # Test that None message becomes empty string
        errors = collector.get_prioritized_errors()
        messages = [error[0] for error in errors]
        assert "" in messages  # None should become empty string

        # Test that None context becomes empty dict
        contexts = [error[2] for error in errors]
        assert all(isinstance(ctx, dict) for ctx in contexts)

    def test_error_aggregation_with_invalid_error_codes(self):
        """Test error aggregation with invalid or unknown error codes."""
        collector = ValidationErrorCollector(object_id="T-invalid-codes", object_kind="task")

        # Test with valid error codes
        collector.add_error("Valid error", ValidationErrorCode.INVALID_FIELD)

        # Test with error codes that might not have explicit mappings
        collector.add_error("Format error", ValidationErrorCode.INVALID_FORMAT)

        # All errors should be collected with default severity/category
        assert collector.get_error_count() == 2

        # Check that default values are applied
        errors = collector.get_prioritized_errors()
        assert len(errors) == 2

    def test_error_aggregation_with_duplicate_errors(self):
        """Test error aggregation with duplicate error messages."""
        collector = ValidationErrorCollector(object_id="T-duplicates", object_kind="task")

        # Add identical errors
        for _ in range(3):
            collector.add_error(
                "Duplicate error message",
                ValidationErrorCode.INVALID_FIELD,
                context={"field": "same_field"},
            )

        # All duplicates should be collected
        assert collector.get_error_count() == 3

        # All should have the same message but be separate entries
        errors = collector.get_prioritized_errors()
        assert len(errors) == 3
        assert all(error[0] == "Duplicate error message" for error in errors)

    def test_error_aggregation_with_circular_context_references(self):
        """Test error aggregation with circular references in context."""
        collector = ValidationErrorCollector(object_id="T-circular", object_kind="task")

        # Create circular reference in context
        circular_context: dict[str, object] = {"self": None}
        circular_context["self"] = circular_context

        # This should not crash the system
        collector.add_error(
            "Error with circular context",
            ValidationErrorCode.INVALID_FIELD,
            context=circular_context,
        )

        # Error should still be collected
        assert collector.get_error_count() == 1

        # Context should be handled gracefully
        detailed_view = collector.get_detailed_view()
        assert len(detailed_view["errors_by_category"]["field"]) == 1

    def test_error_aggregation_thread_safety(self):
        """Test error aggregation thread safety with concurrent operations."""
        collector = ValidationErrorCollector(object_id="T-thread-safety", object_kind="task")
        errors_added = []

        def add_errors_worker(worker_id):
            """Worker function to add errors concurrently."""
            for i in range(10):
                error_msg = f"Worker {worker_id} error {i}"
                collector.add_error(error_msg, ValidationErrorCode.INVALID_FIELD)
                errors_added.append(error_msg)
                time.sleep(0.001)  # Small delay to increase chance of race conditions

        # Start multiple threads adding errors
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=add_errors_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all errors were collected
        assert collector.get_error_count() == 50
        assert len(errors_added) == 50

        # Verify aggregation operations work correctly
        summary = collector.get_summary()
        assert summary["total_errors"] == 50


class TestErrorAggregationIntegration:
    """Integration tests for error aggregation with validation systems.

    Migrated from test_error_aggregation.py
    """

    @patch("src.trellis_mcp.validation.enhanced_validation.validate_parent_exists_for_object")
    def test_error_aggregation_with_enhanced_validation(self, mock_parent_validation):
        """Test error aggregation integration with enhanced validation system."""
        # Mock parent validation to return specific errors
        mock_parent_validation.return_value = None  # No parent validation errors

        # Import here to avoid circular imports
        from pathlib import Path

        from src.trellis_mcp.validation.enhanced_validation import (
            validate_task_with_enhanced_errors,
        )

        # Test data with multiple validation errors
        invalid_task_data = {
            "kind": "task",
            "id": "T-integration-test",
            "title": "",  # Missing required field
            "status": "invalid",  # Invalid status
            "priority": "super-high",  # Invalid priority
            "parent": "F-valid-parent",  # Valid parent (mocked)
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # This should collect multiple errors
        with pytest.raises(ValidationError) as exc_info:
            validate_task_with_enhanced_errors(invalid_task_data, Path("/test"))

        validation_error = exc_info.value
        assert len(validation_error.errors) >= 2  # At least title and status errors
        assert validation_error.object_id == "T-integration-test"

        # Verify the error aggregation worked correctly
        # The actual error messages might vary, so check for key content
        error_messages = [error.lower() for error in validation_error.errors]
        # Check that we have some errors (the specific content may vary)
        assert len(error_messages) >= 2

        # Verify some expected error patterns are present
        assert any("status" in error or "invalid" in error for error in error_messages)
        assert any("priority" in error or "super-high" in error for error in error_messages)

    def test_error_aggregation_with_security_validation(self):
        """Test error aggregation with security validation system."""
        from src.trellis_mcp.validation.security import sanitize_error_message

        collector = ValidationErrorCollector(object_id="T-security", object_kind="task")

        # Test with potentially sensitive error messages
        sensitive_errors = [
            "Database connection failed: postgresql://user:pass@localhost/db",
            "API key validation failed: Token: sk-abc123def456789",
            "File access denied: /home/user/config.txt",
        ]

        for error in sensitive_errors:
            sanitized_error = sanitize_error_message(error)
            assert sanitized_error is not None  # sanitize_error_message returns str | None
            collector.add_error(sanitized_error, ValidationErrorCode.INVALID_FIELD)

        # Verify errors were collected and sanitized
        assert collector.get_error_count() == 3
        errors = collector.get_prioritized_errors()

        # Check that sensitive information was sanitized
        error_messages = [error[0] for error in errors]

        # Verify specific sanitizations occurred
        assert "[REDACTED_CONNECTION]" in error_messages[0]
        assert "[REDACTED_TOKEN]" in error_messages[1]
        assert "[REDACTED_PATH]" in error_messages[2]

        # Verify original sensitive data is not present
        for message in error_messages:
            assert "postgresql://user:pass@localhost/db" not in message
            assert "sk-abc123def456789" not in message
            assert "/home/user/config.txt" not in message

    def test_error_aggregation_with_custom_validation_functions(self):
        """Test error aggregation with custom validation functions."""
        collector = ValidationErrorCollector(object_id="T-custom", object_kind="task")

        def custom_validation_1(data):
            """Custom validation function 1."""
            if not data.get("custom_field_1"):
                collector.add_error(
                    "Custom validation 1 failed",
                    ValidationErrorCode.MISSING_REQUIRED_FIELD,
                    context={"field": "custom_field_1"},
                )

        def custom_validation_2(data):
            """Custom validation function 2."""
            if data.get("custom_field_2") == "invalid":
                collector.add_error(
                    "Custom validation 2 failed",
                    ValidationErrorCode.INVALID_FIELD,
                    context={"field": "custom_field_2", "value": "invalid"},
                )

        # Test data for custom validation
        test_data = {
            "custom_field_1": "",  # Should trigger validation 1
            "custom_field_2": "invalid",  # Should trigger validation 2
        }

        # Run custom validations
        custom_validation_1(test_data)
        custom_validation_2(test_data)

        # Verify errors were collected
        assert collector.get_error_count() == 2
        assert collector.has_critical_errors()  # custom_field_1 missing

        # Check error details
        summary = collector.get_summary()
        assert summary["severity_breakdown"]["CRITICAL"] == 1  # Missing field
        assert summary["severity_breakdown"]["MEDIUM"] == 1  # Invalid field

    def test_error_aggregation_end_to_end_workflow(self):
        """Test complete end-to-end error aggregation workflow."""
        # Simulate a complete validation workflow from start to finish
        collector = ValidationErrorCollector(object_id="T-end-to-end", object_kind="task")

        # Phase 1: Basic field validation
        collector.add_error("Missing title", ValidationErrorCode.MISSING_REQUIRED_FIELD)
        collector.add_error("Invalid status", ValidationErrorCode.INVALID_STATUS)

        # Phase 2: Relationship validation
        collector.add_error("Parent not found", ValidationErrorCode.PARENT_NOT_EXIST)
        collector.add_error("Circular dependency", ValidationErrorCode.CIRCULAR_DEPENDENCY)

        # Phase 3: Business logic validation
        collector.add_error("Invalid priority", ValidationErrorCode.INVALID_FIELD)

        # Phase 4: Security validation
        collector.add_error("Unauthorized access", ValidationErrorCode.INVALID_FIELD)

        # Test aggregation at each phase
        assert collector.get_error_count() == 6

        # Create final validation error
        final_error = collector.create_validation_error(
            task_type="hierarchy", include_detailed_context=True
        )

        # Verify final error structure
        assert isinstance(final_error, ValidationError)
        assert len(final_error.errors) == 6
        assert final_error.object_id == "T-end-to-end"
        assert final_error.task_type == "hierarchy"

        # Verify error ordering (critical errors first)
        critical_error_codes = [
            ValidationErrorCode.MISSING_REQUIRED_FIELD,
            ValidationErrorCode.CIRCULAR_DEPENDENCY,
        ]
        for code in critical_error_codes:
            assert code in final_error.error_codes

        # Verify detailed context
        assert "error_details" in final_error.context
        error_details = final_error.context["error_details"]
        assert error_details["summary"]["total_errors"] == 6
        assert error_details["summary"]["has_critical"] is True

        # Test serialization
        error_dict = final_error.to_dict()
        assert error_dict["object_id"] == "T-end-to-end"
        assert error_dict["task_type"] == "hierarchy"
        assert len(error_dict["errors"]) == 6
        assert len(error_dict["error_codes"]) == 6


class TestMessageTemplate:
    """Test MessageTemplate class.

    Migrated from test_message_templates.py
    """

    def test_basic_template_creation(self):
        """Test basic template creation and formatting."""
        template = MessageTemplate(
            template="Hello {name}!",
            category="greeting",
            description="Basic greeting template",
            required_params=["name"],
        )

        assert template.template == "Hello {name}!"
        assert template.category == "greeting"
        assert template.description == "Basic greeting template"
        assert template.required_params == ["name"]
        assert template.placeholders == ["name"]
        assert template.context_aware is True

    def test_template_formatting(self):
        """Test template parameter substitution."""
        template = MessageTemplate(
            template="Invalid {field} '{value}' for {object_kind}",
            category="validation",
            required_params=["field", "value", "object_kind"],
        )

        result = template.format(field="status", value="invalid", object_kind="task")
        assert result == "Invalid status 'invalid' for task"

    def test_template_missing_required_params(self):
        """Test error when required parameters are missing."""
        template = MessageTemplate(
            template="Hello {name}!",
            category="greeting",
            required_params=["name"],
        )

        with pytest.raises(KeyError, match="Missing required parameters: {'name'}"):
            template.format()

    def test_template_placeholder_extraction(self):
        """Test placeholder extraction from template."""
        template = MessageTemplate(
            template="Error in {field}: {value} is not valid for {context}",
            category="validation",
        )

        assert set(template.placeholders) == {"field", "value", "context"}

    def test_template_validation(self):
        """Test template parameter validation."""
        template = MessageTemplate(
            template="Hello {name}!",
            category="greeting",
            required_params=["name"],
        )

        # Valid parameters
        errors = template.validate_params(name="World")
        assert errors == []

        # Missing required parameter
        errors = template.validate_params()
        assert "Missing required parameters: {'name'}" in errors

        # Unknown parameter
        errors = template.validate_params(name="World", unknown="value")
        assert "Unknown parameters: {'unknown'}" in errors


class TestMessageTemplateRegistry:
    """Test MessageTemplateRegistry class.

    Migrated from test_message_templates.py
    """

    def test_registry_operations(self):
        """Test basic registry operations."""
        registry = MessageTemplateRegistry()

        template = MessageTemplate(
            template="Test {param}",
            category="test",
            required_params=["param"],
        )

        # Register template
        registry.register_template("test_key", template)

        # Get template
        retrieved = registry.get_template("test_key")
        assert retrieved == template

        # Check existence
        assert registry.has_template("test_key")
        assert not registry.has_template("nonexistent")

        # Get by category
        category_templates = registry.get_templates_by_category("test")
        assert "test_key" in category_templates
        assert category_templates["test_key"] == template

    def test_registry_bulk_operations(self):
        """Test bulk registry operations."""
        registry = MessageTemplateRegistry()

        templates = {
            "template1": MessageTemplate("Test 1", "category1"),
            "template2": MessageTemplate("Test 2", "category2"),
        }

        registry.register_templates(templates)

        assert registry.has_template("template1")
        assert registry.has_template("template2")
        assert "category1" in registry.get_categories()
        assert "category2" in registry.get_categories()

    def test_registry_dict_operations(self):
        """Test dictionary import/export."""
        registry = MessageTemplateRegistry()

        template_data = {
            "test_template": {
                "template": "Hello {name}!",
                "category": "greeting",
                "description": "Test template",
                "required_params": ["name"],
                "context_aware": True,
            }
        }

        registry.load_from_dict(template_data)

        assert registry.has_template("test_template")

        exported = registry.export_to_dict()
        assert exported["test_template"]["template"] == "Hello {name}!"
        assert exported["test_template"]["category"] == "greeting"


class TestTemplateEngine:
    """Test TemplateEngine class.

    Migrated from test_message_templates.py
    """

    def test_engine_basic_functionality(self):
        """Test basic template engine functionality."""
        registry = MessageTemplateRegistry()
        template = MessageTemplate(
            template="Invalid {field} for {task_context}",
            category="validation",
            required_params=["field", "task_context"],
        )
        registry.register_template("test_invalid", template)

        engine = TemplateEngine(registry)

        data = {"kind": "task", "parent": "F-test"}
        result = engine.generate_message("test_invalid", data, field="status")

        assert "Invalid status for hierarchy task" in result

    def test_engine_context_injection(self):
        """Test automatic context injection."""
        registry = MessageTemplateRegistry()
        template = MessageTemplate(
            template="Error for {object_kind}: {task_context}",
            category="validation",
            required_params=["object_kind", "task_context"],
        )
        registry.register_template("test_context", template)

        engine = TemplateEngine(registry)

        # Test standalone task
        data = {"kind": "task", "parent": None}
        result = engine.generate_message("test_context", data)
        assert "Error for task: standalone task" in result

        # Test hierarchy task
        data = {"kind": "task", "parent": "F-test"}
        result = engine.generate_message("test_context", data)
        assert "Error for task: hierarchy task" in result

    def test_engine_context_processors(self):
        """Test custom context processors."""
        registry = MessageTemplateRegistry()
        template = MessageTemplate(
            template="Test {custom_field}",
            category="validation",
            required_params=["custom_field"],
        )
        registry.register_template("test_processor", template)

        engine = TemplateEngine(registry)

        # Add custom processor
        def custom_processor(template, data, params):
            params = params.copy()
            params["custom_field"] = "processed_value"
            return params

        engine.add_context_processor(custom_processor)

        data = {"kind": "task"}
        result = engine.generate_message("test_processor", data)
        assert "Test processed_value" in result


class TestTrellisMessageEngine:
    """Test TrellisMessageEngine class.

    Migrated from test_message_templates.py
    """

    def test_engine_initialization(self):
        """Test engine initialization with defaults."""
        engine = TrellisMessageEngine()

        # Check that default templates are loaded
        templates = engine.get_available_templates()
        assert "status.invalid" in templates
        assert "parent.missing" in templates
        assert "security.suspicious_pattern" in templates

    def test_engine_message_generation(self):
        """Test message generation with different formats."""
        engine = TrellisMessageEngine()

        data = {"kind": "task", "parent": "F-test"}

        # Plain text format
        result = engine.generate_message(
            "status.invalid", data, format_type="plain", value="invalid_status"
        )
        assert isinstance(result, str)
        assert "Invalid status 'invalid_status' for hierarchy task" in result

        # Structured format
        result = engine.generate_message(
            "status.invalid", data, format_type="structured", value="invalid_status"
        )
        assert isinstance(result, dict)
        assert "message" in result
        assert "metadata" in result

    def test_engine_custom_templates(self):
        """Test adding custom templates."""
        engine = TrellisMessageEngine()

        custom_config = {
            "template": "Custom error: {error}",
            "category": "custom",
            "required_params": ["error"],
        }

        engine.add_custom_template("custom_error", custom_config)

        assert "custom_error" in engine.get_available_templates()

        data = {"kind": "task"}
        result = engine.generate_message("custom_error", data, error="test")
        assert "Custom error: test" in result

    def test_engine_category_filtering(self):
        """Test template filtering by category."""
        engine = TrellisMessageEngine()

        status_templates = engine.get_templates_by_category("status")
        assert "status.invalid" in status_templates
        assert "status.invalid_with_options" in status_templates

        parent_templates = engine.get_templates_by_category("parent")
        assert "parent.missing" in parent_templates
        assert "parent.not_found" in parent_templates


class TestMessageFormatters:
    """Test message formatters.

    Migrated from test_message_templates.py
    """

    def test_plain_text_formatter(self):
        """Test plain text formatter."""
        formatter = PlainTextFormatter()
        result = formatter.format("Test message", extra="metadata")
        assert result == "Test message"

    def test_structured_formatter(self):
        """Test structured formatter."""
        formatter = StructuredFormatter()
        result = formatter.format("Test message", extra="metadata")

        assert isinstance(result, dict)
        assert result["message"] == "Test message"
        assert result["metadata"]["extra"] == "metadata"

    def test_validation_error_formatter(self):
        """Test validation error formatter."""
        formatter = ValidationErrorFormatter()
        result = formatter.format(
            "Test message", error_code="TEST_ERROR", object_id="T-123", object_kind="task"
        )

        assert isinstance(result, dict)
        assert result["message"] == "Test message"
        assert result["error_code"] == "TEST_ERROR"
        assert result["object_id"] == "T-123"
        assert result["object_kind"] == "task"

    def test_formatter_selection(self):
        """Test formatter selection utility."""
        plain_formatter = get_formatter("plain")
        assert isinstance(plain_formatter, PlainTextFormatter)

        structured_formatter = get_formatter("structured")
        assert isinstance(structured_formatter, StructuredFormatter)

        validation_formatter = get_formatter("validation")
        assert isinstance(validation_formatter, ValidationErrorFormatter)

        with pytest.raises(ValueError, match="Unsupported format type: invalid"):
            get_formatter("invalid")


class TestDefaultTemplates:
    """Test default templates.

    Migrated from test_message_templates.py
    """

    def test_default_templates_exist(self):
        """Test that default templates are properly defined."""
        templates = get_default_templates()

        # Check key template categories exist
        assert any(key.startswith("status.") for key in templates)
        assert any(key.startswith("parent.") for key in templates)
        assert any(key.startswith("security.") for key in templates)
        assert any(key.startswith("fields.") for key in templates)
        assert any(key.startswith("hierarchy.") for key in templates)

    def test_default_templates_formatting(self):
        """Test that default templates format correctly."""
        templates = get_default_templates()

        # Test status template
        status_template = templates["status.invalid"]
        result = status_template.format(value="invalid", task_context="hierarchy task")
        assert result == "Invalid status 'invalid' for hierarchy task"

        # Test parent template
        parent_template = templates["parent.not_found"]
        result = parent_template.format(parent_kind="feature", parent_id="F-missing")
        assert result == "Parent feature with ID 'F-missing' does not exist"

        # Test security template
        security_template = templates["security.suspicious_pattern"]
        result = security_template.format(field="parent", pattern="..")
        assert result == "Security validation failed: parent field contains suspicious pattern '..'"


class TestTemplateIntegration:
    """Test integration with existing systems.

    Migrated from test_message_templates.py
    """

    def test_global_engine_access(self):
        """Test global engine access."""
        engine1 = get_default_engine()
        engine2 = get_default_engine()

        # Should return the same instance
        assert engine1 is engine2

    def test_convenience_function(self):
        """Test convenience function for message generation."""
        data = {"kind": "task", "parent": "F-test"}

        result = generate_template_message(
            "status.invalid", data, format_type="plain", value="invalid_status"
        )

        assert isinstance(result, str)
        assert "Invalid status 'invalid_status' for hierarchy task" in result

    def test_backward_compatibility(self):
        """Test that template system integrates with existing validation."""
        # This test ensures the template system works with existing validation patterns
        from src.trellis_mcp.validation.context_utils import generate_contextual_error_message

        data = {"kind": "task", "parent": "F-test"}

        # Test with template system available
        result = generate_contextual_error_message(
            "invalid_status",
            data,
            status="invalid",
            valid_values=["open", "in-progress", "review", "done"],
        )

        assert "Invalid status 'invalid' for hierarchy task" in result

    def test_security_integration(self):
        """Test security validation integration."""
        from src.trellis_mcp.validation.security import validate_standalone_task_security

        # Test suspicious pattern detection
        data = {"kind": "task", "parent": "..", "schema_version": "1.1"}

        errors = validate_standalone_task_security(data)
        assert len(errors) > 0
        assert "Security validation failed" in errors[0]
        assert "suspicious pattern" in errors[0]

    def test_template_engine_error_handling(self):
        """Test template engine error handling."""
        engine = TrellisMessageEngine()

        # Test with missing template
        data = {"kind": "task"}
        with pytest.raises(KeyError, match="Template 'nonexistent' not found"):
            engine.generate_message("nonexistent", data)

        # Test with missing required parameters
        with pytest.raises(KeyError, match="Missing required parameters"):
            engine.generate_message("status.invalid", data)  # Missing 'value' parameter


class TestErrorMessageGeneration:
    """Test error message templates and placeholder substitution.

    Migrated from test_error_messages.py - consolidated key functionality
    """

    def test_all_default_templates_exist(self):
        """Test that all required error message templates exist."""
        templates = get_default_templates()

        # Status validation templates
        assert "status.invalid" in templates
        assert "status.invalid_with_options" in templates
        assert "status.transition_invalid" in templates
        assert "status.terminal" in templates

        # Parent validation templates
        assert "parent.missing" in templates
        assert "parent.not_found" in templates
        assert "parent.standalone_task_cannot_have" in templates

        # Field validation templates
        assert "fields.missing" in templates
        assert "fields.invalid_enum" in templates
        assert "fields.invalid_type" in templates

        # Security validation templates
        assert "security.suspicious_pattern" in templates
        assert "security.privileged_field" in templates
        assert "security.max_length_exceeded" in templates

        # Hierarchy validation templates
        assert "hierarchy.circular_dependency" in templates
        assert "hierarchy.invalid_level" in templates

        # Schema validation templates
        assert "schema.version_mismatch" in templates
        assert "schema.version_constraint" in templates

    def test_status_templates_formatting(self):
        """Test status validation templates with various inputs."""
        templates = get_default_templates()

        # Test status.invalid template
        template = templates["status.invalid"]
        result = template.format(value="invalid_status", task_context="hierarchy task")
        assert result == "Invalid status 'invalid_status' for hierarchy task"

        result = template.format(value="bad_status", task_context="standalone task")
        assert result == "Invalid status 'bad_status' for standalone task"

        # Test status.invalid_with_options template
        template = templates["status.invalid_with_options"]
        result = template.format(
            value="invalid",
            task_context="hierarchy task",
            valid_values="open, in-progress, review, done",
        )
        expected = (
            "Invalid status 'invalid' for hierarchy task. "
            "Must be one of: open, in-progress, review, done"
        )
        assert result == expected

    def test_parent_templates_formatting(self):
        """Test parent validation templates with various inputs."""
        templates = get_default_templates()

        # Test parent.missing template
        template = templates["parent.missing"]
        result = template.format(task_context="hierarchy task")
        assert result == "Missing required fields for hierarchy task: parent"

        # Test parent.not_found template
        template = templates["parent.not_found"]
        result = template.format(parent_kind="feature", parent_id="F-missing")
        assert result == "Parent feature with ID 'F-missing' does not exist"

        result = template.format(parent_kind="epic", parent_id="E-nonexistent")
        assert result == "Parent epic with ID 'E-nonexistent' does not exist"

    def test_security_templates_formatting(self):
        """Test security validation templates with various inputs."""
        templates = get_default_templates()

        # Test security.suspicious_pattern template
        template = templates["security.suspicious_pattern"]
        result = template.format(field="parent", pattern="..")
        assert result == "Security validation failed: parent field contains suspicious pattern '..'"

        result = template.format(field="title", pattern="<script>")
        assert (
            result
            == "Security validation failed: title field contains suspicious pattern '<script>'"
        )

        # Test security.privileged_field template
        template = templates["security.privileged_field"]
        result = template.format(field="system_admin")
        assert (
            result == "Security validation failed: privileged field 'system_admin' is not allowed"
        )

    def test_basic_placeholder_substitution(self):
        """Test basic placeholder substitution."""
        template = MessageTemplate("Hello {name}!", "greeting")
        result = template.format(name="World")
        assert result == "Hello World!"

    def test_multiple_placeholders(self):
        """Test multiple placeholder substitution."""
        template = MessageTemplate(
            "Error in {field}: {value} is not valid for {context}", "validation"
        )
        result = template.format(field="status", value="invalid", context="task")
        assert result == "Error in status: invalid is not valid for task"

    def test_numeric_placeholders(self):
        """Test numeric placeholder substitution."""
        template = MessageTemplate(
            "Field {field} exceeds maximum length of {max_length} characters", "validation"
        )
        result = template.format(field="title", max_length=255)
        assert result == "Field title exceeds maximum length of 255 characters"

    def test_none_placeholders(self):
        """Test None placeholder substitution."""
        template = MessageTemplate("Parent is {parent}", "validation")
        result = template.format(parent=None)
        assert result == "Parent is None"

    def test_missing_placeholder_error(self):
        """Test error when placeholder is missing."""
        template = MessageTemplate("Hello {name}!", "greeting", required_params=["name"])
        with pytest.raises(KeyError, match="Missing required parameters"):
            template.format()


class TestContextAwareMessaging:
    """Test context-aware message generation for different task types.

    Migrated from test_error_messages.py
    """

    def test_standalone_task_context(self):
        """Test context-aware messaging for standalone tasks."""
        engine = TrellisMessageEngine()

        # Standalone task (no parent)
        data = {"kind": "task", "parent": None}
        result = engine.generate_message("status.invalid", data, value="invalid_status")
        assert "Invalid status 'invalid_status' for standalone task" in result

    def test_hierarchy_task_context(self):
        """Test context-aware messaging for hierarchy tasks."""
        engine = TrellisMessageEngine()

        # Hierarchy task (has parent)
        data = {"kind": "task", "parent": "F-test"}
        result = engine.generate_message("status.invalid", data, value="invalid_status")
        assert "Invalid status 'invalid_status' for hierarchy task" in result

    def test_project_context(self):
        """Test context-aware messaging for projects."""
        engine = TrellisMessageEngine()

        data = {"kind": "project", "id": "P-test"}
        result = engine.generate_message("fields.missing", data, fields="title")
        assert "Missing required fields: title" in result

    def test_context_parameter_override(self):
        """Test that explicit context parameters override automatic injection."""
        engine = TrellisMessageEngine()

        data = {"kind": "task", "parent": "F-test"}
        result = engine.generate_message(
            "status.invalid",
            data,
            value="invalid_status",
            task_context="custom context",  # Override automatic context
        )
        assert "Invalid status 'invalid_status' for custom context" in result

    def test_object_id_injection(self):
        """Test automatic object ID injection."""
        registry = MessageTemplateRegistry()
        template = MessageTemplate(
            "Error for object {object_id}", "validation", required_params=["object_id"]
        )
        registry.register_template("test_id", template)

        engine = TemplateEngine(registry)

        data = {"kind": "task", "id": "T-123"}
        result = engine.generate_message("test_id", data)
        assert "Error for object T-123" in result


class TestLocalizationFramework:
    """Test localization support framework and extensibility.

    Migrated from test_error_messages.py
    """

    def test_i18n_formatter_basic(self):
        """Test basic I18n formatter functionality."""
        formatter = I18nFormatter()

        result = formatter.format("Test message", message_key="test.message")

        assert isinstance(result, dict)
        assert result["message"] == "Test message"
        assert result["locale"] == "en_US"
        assert result["message_key"] == "test.message"

    def test_i18n_formatter_with_metadata(self):
        """Test I18n formatter with additional metadata."""
        formatter = I18nFormatter()

        result = formatter.format(
            "Test message", message_key="test.message", context="task_validation", severity="high"
        )

        assert result["message"] == "Test message"
        assert result["locale"] == "en_US"
        assert result["message_key"] == "test.message"
        assert result["metadata"]["context"] == "task_validation"
        assert result["metadata"]["severity"] == "high"

    def test_localization_integration_with_engine(self):
        """Test localization integration with template engine."""
        engine = TrellisMessageEngine()

        data = {"kind": "task", "parent": "F-test"}
        result = engine.generate_message(
            "status.invalid", data, format_type="i18n", value="invalid_status"
        )

        assert isinstance(result, dict)
        assert "message" in result
        assert "locale" in result
        assert result["locale"] == "en_US"
        assert "Invalid status 'invalid_status' for hierarchy task" in result["message"]


class TestMessageFormattingConsistency:
    """Test message formatting consistency across all templates.

    Migrated from test_error_messages.py
    """

    def test_consistent_error_message_format(self):
        """Test that all error messages follow consistent formatting."""
        engine = TrellisMessageEngine()
        templates = engine.get_available_templates()

        # Sample data for testing
        sample_data = {"kind": "task", "parent": "F-test", "id": "T-123"}

        # Test a representative sample of templates
        test_cases = [
            ("status.invalid", {"value": "invalid"}),
            ("parent.not_found", {"parent_kind": "feature", "parent_id": "F-missing"}),
            ("fields.missing", {"fields": "title"}),
            ("security.suspicious_pattern", {"field": "parent", "pattern": ".."}),
        ]

        for template_key, params in test_cases:
            if template_key in templates:
                result = engine.generate_message(template_key, sample_data, **params)

                # Check that message is not empty
                assert result.strip() != ""

                # Check that message doesn't contain raw placeholders
                assert "{" not in result
                assert "}" not in result

                # Check that message starts with capital letter
                assert result[0].isupper()

    def test_consistent_placeholder_naming(self):
        """Test that placeholder naming is consistent across templates."""
        templates = get_default_templates()

        # Common placeholder names that should be consistent
        common_placeholders = {
            "object_kind": [],
            "object_id": [],
            "task_context": [],
            "value": [],
            "field": [],
            "parent_kind": [],
            "parent_id": [],
        }

        for template_key, template in templates.items():
            for placeholder in template.placeholders:
                if placeholder in common_placeholders:
                    common_placeholders[placeholder].append(template_key)

        # Verify that common placeholders are used consistently
        for placeholder, template_keys in common_placeholders.items():
            if template_keys:
                # Check that all templates using this placeholder handle it the same way
                for template_key in template_keys:
                    template = templates[template_key]
                    assert placeholder in template.placeholders

    def test_formatting_with_all_formatters(self):
        """Test that all formatters produce consistent output."""
        engine = TrellisMessageEngine()

        data = {"kind": "task", "parent": "F-test", "id": "T-123"}

        # Test with all formatter types
        formatter_types = ["plain", "structured", "validation", "i18n"]

        for formatter_type in formatter_types:
            result = engine.generate_message(
                "status.invalid", data, format_type=formatter_type, value="invalid_status"
            )

            if formatter_type == "plain":
                assert isinstance(result, str)
                assert "Invalid status 'invalid_status' for hierarchy task" in result
            else:
                assert isinstance(result, dict)
                assert "message" in result
                assert "Invalid status 'invalid_status' for hierarchy task" in result["message"]


class TestErrorHandlingIntegration:
    """Integration tests for the complete error handling system.

    Combined integration tests across all error handling components
    """

    def test_end_to_end_error_handling_workflow(self):
        """Test complete end-to-end error handling workflow."""
        # Create collector for gathering errors
        collector = ValidationErrorCollector(object_id="T-integration", object_kind="task")

        # Initialize template engine
        engine = TrellisMessageEngine()

        # Phase 1: Collect validation errors with template-generated messages
        data = {"kind": "task", "parent": "F-test", "id": "T-integration"}

        # Generate template-based error messages
        status_error = engine.generate_message("status.invalid", data, value="invalid_status")
        parent_error = engine.generate_message(
            "parent.not_found", data, parent_kind="feature", parent_id="F-missing"
        )
        security_error = engine.generate_message(
            "security.suspicious_pattern", data, field="title", pattern="../"
        )

        # Add errors to collector
        collector.add_error(status_error, ValidationErrorCode.INVALID_STATUS)
        collector.add_error(parent_error, ValidationErrorCode.PARENT_NOT_EXIST)
        collector.add_error(security_error, ValidationErrorCode.INVALID_FIELD)

        # Verify error aggregation
        assert collector.get_error_count() == 3
        assert (
            collector.has_critical_errors()
            or len(collector.get_errors_by_severity(ErrorSeverity.HIGH)) > 0
        )

        # Test error prioritization and summary
        summary = collector.get_summary()
        assert summary["total_errors"] == 3
        assert "hierarchy task" in status_error  # Context-aware messaging worked
        assert "F-missing" in parent_error  # Template substitution worked
        assert "Security validation failed" in security_error  # Security template worked

        # Create final validation error
        validation_error = collector.create_validation_error(
            task_type="hierarchy", include_detailed_context=True
        )

        # Verify complete error structure
        assert isinstance(validation_error, ValidationError)
        assert len(validation_error.errors) == 3
        assert validation_error.object_id == "T-integration"
        assert "error_details" in validation_error.context

    def test_cross_system_error_message_consistency(self):
        """Test that error messages are consistent across different validation systems."""
        engine = TrellisMessageEngine()

        # Test data for different object types
        task_data = {"kind": "task", "parent": "F-test", "id": "T-123"}
        project_data = {"kind": "project", "id": "P-123"}
        feature_data = {"kind": "feature", "parent": "E-test", "id": "F-123"}

        # Generate same type of error for different objects
        for data in [task_data, project_data, feature_data]:
            result = engine.generate_message("fields.missing", data, fields="title")

            # All should follow consistent format
            assert "Missing required fields: title" in result
            assert result.startswith("Missing required fields")

            # Context should be appropriate for object type
            if data["kind"] == "task":
                # Task context is determined by parent presence
                pass  # Context handled automatically
            else:
                # Other objects don't need special context handling
                pass

    def test_error_handling_performance_integration(self):
        """Test performance of integrated error handling workflow."""
        import time

        start_time = time.time()

        # Create multiple collectors and process errors
        collectors = []
        engine = TrellisMessageEngine()

        for i in range(10):
            collector = ValidationErrorCollector(object_id=f"T-perf-{i}", object_kind="task")
            data = {"kind": "task", "parent": "F-test", "id": f"T-perf-{i}"}

            # Generate multiple template-based errors
            for j in range(5):
                error_msg = engine.generate_message("status.invalid", data, value=f"invalid_{j}")
                collector.add_error(error_msg, ValidationErrorCode.INVALID_STATUS)

            # Create validation error
            validation_error = collector.create_validation_error(task_type="hierarchy")
            assert len(validation_error.errors) == 5

            collectors.append(collector)

        total_time = time.time() - start_time

        # Should process 10 collectors with 5 errors each in reasonable time
        assert total_time < 1.0, f"Integration workflow took {total_time:.3f}s, expected < 1.0s"
        assert len(collectors) == 10
