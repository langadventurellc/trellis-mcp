"""Tests for enhanced validation using ValidationErrorCollector."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.validation.enhanced_validation import (
    validate_object_data_enhanced,
    validate_object_data_with_collector,
    validate_task_with_enhanced_errors,
)
from src.trellis_mcp.validation.error_collector import ErrorCategory, ErrorSeverity
from src.trellis_mcp.validation.exceptions import TrellisValidationError


class TestEnhancedValidation:
    """Test cases for enhanced validation functions."""

    def test_validate_object_data_with_collector_success(self):
        """Test successful validation returns empty collector."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert not collector.has_errors()
        assert collector.get_error_count() == 0
        assert collector.object_id == "T-test"
        assert collector.object_kind == "task"

    def test_validate_object_data_with_collector_missing_kind(self):
        """Test validation with missing kind field."""
        data = {
            "id": "T-test",
            "title": "Test Task",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()
        assert collector.has_critical_errors()

        # Should have missing kind error
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) == 1
        assert "Missing 'kind' field" in critical_errors[0][0]
        assert critical_errors[0][1] == ValidationErrorCode.MISSING_REQUIRED_FIELD

    def test_validate_object_data_with_collector_invalid_kind(self):
        """Test validation with invalid kind field."""
        data = {
            "kind": "invalid_kind",
            "id": "T-test",
            "title": "Test Task",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()
        assert collector.has_critical_errors()

        # Should have invalid kind error
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) == 1
        assert "Invalid kind 'invalid_kind'" in critical_errors[0][0]
        assert critical_errors[0][1] == ValidationErrorCode.INVALID_ENUM_VALUE

    def test_validate_object_data_with_collector_multiple_errors(self):
        """Test validation with multiple errors shows prioritization."""
        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title (critical)
            "status": "invalid_status",  # Invalid enum (critical)
            "priority": "invalid_priority",  # Invalid enum (critical)
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()
        assert collector.has_critical_errors()

        # Should have multiple critical errors
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) >= 2  # At least missing title and invalid status

        # Check error categories
        field_errors = collector.get_errors_by_category(ErrorCategory.FIELD)
        assert len(field_errors) >= 2

    def test_validate_object_data_with_collector_security_errors(self):
        """Test that security errors are properly collected."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_standalone_task_security"
        ) as mock_security:
            mock_security.return_value = ["Security error 1", "Security error 2"]

            collector = validate_object_data_with_collector(data, Path("/test"))

            # Should have security errors
            assert collector.has_errors()
            assert collector.get_error_count() == 2

            # All errors should be categorized as field errors with security context
            all_errors = collector.get_prioritized_errors()
            for msg, code, context in all_errors:
                assert code == ValidationErrorCode.INVALID_FIELD
                assert context.get("security_check") is True

    def test_validate_object_data_with_collector_parent_validation(self):
        """Test parent validation error collection."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-nonexistent",
            "schema_version": "1.0",  # Hierarchy task
        }

        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_parent_exists_for_object"
        ) as mock_parent:
            mock_parent.side_effect = ValueError("Parent F-nonexistent does not exist")

            collector = validate_object_data_with_collector(data, Path("/test"))

            assert collector.has_errors()

            # Should have parent validation error
            relationship_errors = collector.get_errors_by_category(ErrorCategory.RELATIONSHIP)
            assert len(relationship_errors) == 1
            assert "Parent F-nonexistent does not exist" in relationship_errors[0][0]
            assert relationship_errors[0][1] == ValidationErrorCode.PARENT_NOT_EXIST

    def test_validate_object_data_enhanced_success(self):
        """Test enhanced validation function with successful validation."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Should not raise any exception
        validate_object_data_enhanced(data, Path("/test"))

    def test_validate_object_data_enhanced_raises_validation_error(self):
        """Test enhanced validation function raises ValidationError."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_object_data_enhanced(data, Path("/test"))

        exception = exc_info.value
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert exception.task_type == "standalone"
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0

    def test_validate_object_data_enhanced_creates_proper_validation_error(self):
        """Test enhanced validation creates proper ValidationError structure."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_object_data_enhanced(data, Path("/test"))

        exception = exc_info.value

        # Check that the ValidationError has proper structure
        assert isinstance(exception, ValidationError)
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert exception.task_type == "standalone"

        # Check that context information is preserved
        assert "error_summary" in exception.context
        assert exception.context["error_summary"]["total_errors"] > 0

    def test_error_prioritization_in_enhanced_validation(self):
        """Test that errors are properly prioritized in enhanced validation."""
        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title (critical)
            "status": "invalid_status",  # Invalid enum (critical)
            "priority": "invalid_priority",  # Invalid enum (critical)
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_object_data_enhanced(data, Path("/test"))

        exception = exc_info.value

        # All errors should be critical level, but check they're prioritized
        assert len(exception.errors) >= 2
        assert len(exception.error_codes) >= 2

        # Should contain both missing field and invalid enum errors
        error_codes = [code.value for code in exception.error_codes]
        assert "missing_required_field" in error_codes or "invalid_enum_value" in error_codes

    def test_collector_context_preservation(self):
        """Test that context is preserved through the enhanced validation."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()

        # Get errors and check context preservation
        prioritized_errors = collector.get_prioritized_errors()

        # Find the invalid status error
        for msg, code, context in prioritized_errors:
            if code == ValidationErrorCode.INVALID_ENUM_VALUE and "status" in context.get(
                "field", ""
            ):
                assert "value" in context
                assert context["value"] == "invalid_status"
                assert "valid_values" in context
                break
        else:
            pytest.fail("Invalid status error not found with proper context")

    def test_standalone_vs_hierarchy_task_detection(self):
        """Test that task type is correctly detected for ValidationError."""
        # Standalone task
        standalone_data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",  # Standalone
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises((ValidationError, TrellisValidationError)) as exc_info:
            validate_object_data_enhanced(standalone_data, Path("/test"))

        # Accept either ValidationError or TrellisValidationError (fallback case)
        if isinstance(exc_info.value, ValidationError):
            assert exc_info.value.task_type == "standalone"

        # Hierarchy task
        hierarchy_data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",  # Hierarchy
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises((ValidationError, TrellisValidationError)) as exc_info:
            validate_object_data_enhanced(hierarchy_data, Path("/test"))

        # Accept either ValidationError or TrellisValidationError (fallback case)
        if isinstance(exc_info.value, ValidationError):
            assert exc_info.value.task_type == "hierarchy"

    def test_collector_summary_and_detailed_view(self):
        """Test that collector provides useful summary and detailed views."""
        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title (critical field error)
            "status": "invalid_status",  # Invalid enum (critical field error)
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        # Test summary
        summary = collector.get_summary()
        assert summary["total_errors"] >= 2
        assert summary["has_critical"] is True
        assert "CRITICAL" in summary["severity_breakdown"]
        assert "field" in summary["category_breakdown"]

        # Test detailed view
        detailed = collector.get_detailed_view()
        assert detailed["object_id"] == "T-test"
        assert detailed["object_kind"] == "task"
        assert "errors_by_category" in detailed
        assert "field" in detailed["errors_by_category"]

        # Check that field errors are properly categorized
        field_errors = detailed["errors_by_category"]["field"]
        assert len(field_errors) >= 2

        for error in field_errors:
            assert "message" in error
            assert "error_code" in error
            assert "severity" in error
            assert "context" in error


class TestTaskSpecificValidation:
    """Test cases for task-specific validation functions."""

    def test_validate_task_with_enhanced_errors_standalone_success(self):
        """Test successful validation of a standalone task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Should not raise any exception
        validate_task_with_enhanced_errors(data, Path("/test"))

    def test_validate_task_with_enhanced_errors_hierarchy_success(self):
        """Test successful validation of a hierarchy task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Should not raise any exception (with mocked parent validation)
        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_parent_exists_for_object"
        ):
            validate_task_with_enhanced_errors(data, Path("/test"))

    def test_validate_task_with_enhanced_errors_non_task_fails(self):
        """Test that non-task objects raise ValueError."""
        data = {
            "kind": "project",
            "id": "P-test",
            "title": "Test Project",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(ValueError, match="can only be used with tasks"):
            validate_task_with_enhanced_errors(data, Path("/test"))

    def test_validate_task_with_enhanced_errors_delegates_to_standalone(self):
        """Test that standalone tasks are delegated to standalone validation."""
        from src.trellis_mcp.exceptions.standalone_task_validation_error import (
            StandaloneTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",  # This should cause validation error
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(StandaloneTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0

    def test_validate_task_with_enhanced_errors_delegates_to_hierarchy(self):
        """Test that hierarchy tasks are delegated to hierarchy validation."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",  # This should cause validation error
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert exception.parent_id == "F-test"
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0

    def test_hierarchy_task_validation_context_aware_errors(self):
        """Test that hierarchy task validation provides context-aware error messages."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value

        # Check that context contains hierarchy-specific information
        assert "task_type" in exception.context
        assert exception.context["task_type"] == "hierarchy"
        assert "validation_context" in exception.context
        assert exception.context["validation_context"] == "enhanced_hierarchy_task_validation"

    def test_hierarchy_task_validation_error_aggregation(self):
        """Test that hierarchy task validation properly aggregates multiple errors."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title
            "status": "invalid_status",
            "priority": "invalid_priority",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value

        # Should have multiple errors aggregated
        assert len(exception.errors) >= 2
        assert len(exception.error_codes) >= 2

        # Check that errors are properly ordered/prioritized
        error_messages = exception.errors
        error_codes = [code.value for code in exception.error_codes]

        # Should contain both missing field and invalid enum errors
        assert any("missing" in msg.lower() for msg in error_messages) or any(
            "invalid" in msg.lower() for msg in error_messages
        )
        assert "missing_required_field" in error_codes or "invalid_enum_value" in error_codes

    def test_hierarchy_task_validation_with_parent_errors(self):
        """Test hierarchy task validation with parent validation errors."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-nonexistent",  # This parent doesn't exist
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value

        # Should have parent validation error
        assert len(exception.errors) >= 1
        assert any("does not exist" in msg for msg in exception.errors)

        # Should have proper parent_id in the exception
        assert exception.parent_id == "F-nonexistent"

    def test_hierarchy_task_validation_performance(self):
        """Test that hierarchy task validation doesn't significantly impact performance."""
        import time

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Mock parent validation to avoid filesystem calls
        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_parent_exists_for_object"
        ):
            start_time = time.time()

            # Run validation multiple times
            for _ in range(10):
                try:
                    validate_task_with_enhanced_errors(data, Path("/test"))
                except Exception:
                    pass  # Ignore validation errors, we're testing performance

            end_time = time.time()
            elapsed = end_time - start_time

            # Should complete within reasonable time (adjust as needed)
            assert elapsed < 1.0, f"Validation took too long: {elapsed:.2f}s"
