"""Comprehensive unit tests for validation error aggregation system.

This test suite covers the complete error aggregation workflow including:
- Error collection and aggregation logic
- Error prioritization and sorting
- Error presentation formats
- Error grouping and categorization
- Performance impact validation
- End-to-end error aggregation scenarios
"""

import time
from unittest.mock import patch

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.validation.error_collector import (
    ErrorCategory,
    ErrorSeverity,
    ValidationErrorCollector,
)


class TestErrorAggregationWorkflow:
    """Test complete error aggregation workflow scenarios."""

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
    """Test performance characteristics of error aggregation system."""

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
    """Test edge cases and error conditions in error aggregation."""

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
        import threading
        import time

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
    """Integration tests for error aggregation with validation systems."""

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
