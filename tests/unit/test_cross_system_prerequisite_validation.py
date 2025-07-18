"""Unit tests for cross-system prerequisite existence validation.

Tests the validate_prerequisite_existence function for both hierarchical and
standalone task systems, including security validation and error handling.
"""

from unittest.mock import patch

import pytest

from trellis_mcp.exceptions.validation_error import ValidationErrorCode
from trellis_mcp.validation.error_collector import ValidationErrorCollector
from trellis_mcp.validation.field_validation import (
    _validate_prerequisite_id_security,
    validate_prerequisite_existence,
)


class TestValidatePrerequisiteExistence:
    """Test class for prerequisite existence validation."""

    def test_empty_prerequisites_list(self):
        """Test that empty prerequisites list does not trigger validation."""
        collector = ValidationErrorCollector()
        validate_prerequisite_existence([], "/fake/project", collector)

        assert not collector.has_errors()

    def test_none_prerequisites_list(self):
        """Test that None prerequisites list does not trigger validation."""
        collector = ValidationErrorCollector()
        # Pass empty list instead of None to match function signature
        validate_prerequisite_existence([], "/fake/project", collector)

        assert not collector.has_errors()

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_valid_prerequisites_exist(self, mock_get_objects):
        """Test that valid prerequisites that exist pass validation."""
        # Mock objects that exist in the project
        mock_get_objects.return_value = {
            "task-1": {"id": "task-1", "kind": "task"},
            "task-2": {"id": "task-2", "kind": "task"},
            "feature-1": {"id": "feature-1", "kind": "feature"},
        }

        collector = ValidationErrorCollector()
        prerequisites = ["task-1", "T-task-2", "F-feature-1"]
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)

        assert not collector.has_errors()
        mock_get_objects.assert_called_once_with("/fake/project")

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_nonexistent_prerequisites(self, mock_get_objects):
        """Test that nonexistent prerequisites trigger validation errors."""
        # Mock objects that exist in the project
        mock_get_objects.return_value = {
            "task-1": {"id": "task-1", "kind": "task"},
        }

        collector = ValidationErrorCollector()
        prerequisites = ["task-1", "nonexistent-task", "T-missing-task"]
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)

        assert collector.has_errors()
        assert collector.get_error_count() == 2  # Two missing prerequisites

        errors = collector.get_prioritized_errors()
        assert any("nonexistent-task" in msg for msg, _, _ in errors)
        assert any("T-missing-task" in msg for msg, _, _ in errors)
        assert any("does not exist in project" in msg for msg, _, _ in errors)
        assert any(
            "cross-system" in msg.lower() or "hierarchical and standalone" in msg.lower()
            for msg, _, _ in errors
        )

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_empty_prerequisite_id(self, mock_get_objects):
        """Test that empty prerequisite IDs trigger validation errors."""
        mock_get_objects.return_value = {}

        collector = ValidationErrorCollector()
        prerequisites = ["", "  ", "valid-task"]
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)

        assert collector.has_errors()

        errors = collector.get_prioritized_errors()
        empty_errors = [msg for msg, code, _ in errors if "Empty prerequisite ID" in msg]
        assert len(empty_errors) == 2  # Two empty prerequisite IDs

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_get_all_objects_failure(self, mock_get_objects):
        """Test handling of get_all_objects failure."""
        mock_get_objects.side_effect = Exception("Failed to load objects")

        collector = ValidationErrorCollector()
        prerequisites = ["task-1"]
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)

        assert collector.has_errors()
        errors = collector.get_prioritized_errors()
        assert any("Failed to load project objects" in msg for msg, _, _ in errors)

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    @patch("trellis_mcp.validation.field_validation._validate_prerequisite_id_security")
    def test_security_validation_failure(self, mock_security, mock_get_objects):
        """Test that security validation failures prevent existence checks."""
        mock_get_objects.return_value = {"task-1": {"id": "task-1"}}
        mock_security.return_value = ["contains path traversal sequences"]

        collector = ValidationErrorCollector()
        prerequisites = ["../malicious-task"]
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)

        assert collector.has_errors()
        errors = collector.get_prioritized_errors()
        assert any("security validation failed" in msg.lower() for msg, _, _ in errors)

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_cross_system_validation(self, mock_get_objects):
        """Test that both hierarchical and standalone tasks are checked."""
        # Mock both hierarchical and standalone tasks
        mock_get_objects.return_value = {
            "hierarchy-task": {"id": "hierarchy-task", "kind": "task", "parent": "feature-1"},
            "standalone-task": {"id": "standalone-task", "kind": "task"},
        }

        collector = ValidationErrorCollector()
        prerequisites = ["hierarchy-task", "standalone-task"]
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)

        assert not collector.has_errors()  # Both should be found

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_prerequisite_id_cleaning(self, mock_get_objects):
        """Test that prerequisite IDs are properly cleaned before lookup."""
        # Mock objects stored with clean IDs
        mock_get_objects.return_value = {
            "task-name": {"id": "task-name", "kind": "task"},
            "feature-name": {"id": "feature-name", "kind": "feature"},
        }

        collector = ValidationErrorCollector()
        # Test with prefixed IDs
        prerequisites = ["T-task-name", "F-feature-name"]
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)

        assert not collector.has_errors()  # Should find the cleaned IDs

    def test_error_codes_and_context(self):
        """Test that proper error codes and context are used."""
        with patch("trellis_mcp.validation.object_loader.get_all_objects") as mock_get_objects:
            mock_get_objects.return_value = {}

            collector = ValidationErrorCollector()
            prerequisites = ["missing-task"]
            validate_prerequisite_existence(prerequisites, "/fake/project", collector)

            assert collector.has_errors()
            errors = collector.get_prioritized_errors()

            # Check that the correct error code is used
            for msg, code, context in errors:
                assert code == ValidationErrorCode.PARENT_NOT_EXIST
                assert "validation_type" in context
                assert context["validation_type"] == "prerequisite_existence"
                assert "cross_system_check" in context
                assert context["cross_system_check"] is True


class TestValidatePrerequisiteIdSecurity:
    """Test class for prerequisite ID security validation."""

    def test_valid_prerequisite_ids(self):
        """Test that valid prerequisite IDs pass security validation."""
        valid_ids = [
            "task-name",
            "feature-123",
            "project-name",
            "epic-with-dashes",
            "id123abc",
        ]

        for prereq_id in valid_ids:
            errors = _validate_prerequisite_id_security(prereq_id)
            assert not errors, f"Valid ID '{prereq_id}' should not have security errors"

    def test_path_traversal_detection(self):
        """Test detection of path traversal attempts."""
        malicious_ids = [
            "../etc/passwd",
            "task/../../../etc",
            "good-task/../bad-path",
        ]

        for prereq_id in malicious_ids:
            errors = _validate_prerequisite_id_security(prereq_id)
            assert any(
                "path traversal" in error for error in errors
            ), f"Should detect path traversal in '{prereq_id}'"

    def test_absolute_path_detection(self):
        """Test detection of absolute path attempts."""
        malicious_ids = [
            "/etc/passwd",
            "\\Windows\\System32",
            "/usr/bin/malicious",
        ]

        for prereq_id in malicious_ids:
            errors = _validate_prerequisite_id_security(prereq_id)
            assert any(
                "path separators" in error for error in errors
            ), f"Should detect absolute path in '{prereq_id}'"

    def test_control_character_detection(self):
        """Test detection of control characters."""
        malicious_ids = [
            "task\x00name",  # Null byte
            "task\x01name",  # Control character
            "task\x1fname",  # Unit separator
        ]

        for prereq_id in malicious_ids:
            errors = _validate_prerequisite_id_security(prereq_id)
            assert any(
                "control characters" in error for error in errors
            ), f"Should detect control characters in '{prereq_id}'"

    def test_length_validation(self):
        """Test validation of prerequisite ID length."""
        # Test extremely long ID (over filesystem limit)
        long_id = "a" * 300
        errors = _validate_prerequisite_id_security(long_id)
        assert any("filesystem name limits" in error for error in errors)

    @patch("trellis_mcp.id_utils.validate_id_charset")
    def test_invalid_charset_detection(self, mock_validate_charset):
        """Test detection of invalid character sets."""
        mock_validate_charset.return_value = False

        errors = _validate_prerequisite_id_security("invalid-chars")
        assert any("invalid characters" in error for error in errors)
        mock_validate_charset.assert_called_once_with("invalid-chars")

    def test_empty_id_handling(self):
        """Test handling of empty prerequisite IDs."""
        # Empty IDs should be caught by the main validation function,
        # but security validation should handle them gracefully
        with patch("trellis_mcp.id_utils.validate_id_charset") as mock_validate:
            mock_validate.return_value = True  # Assume charset validation passes for empty
            errors = _validate_prerequisite_id_security("")
            # Should not crash, may or may not have errors depending on charset validation
            assert isinstance(errors, list)


class TestPerformanceRequirements:
    """Test performance requirements for prerequisite validation."""

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_performance_with_typical_prerequisite_list(self, mock_get_objects):
        """Test that validation meets <10ms requirement for 1-10 prerequisites."""
        import time

        # Mock a typical project with moderate number of objects
        mock_objects = {f"task-{i}": {"id": f"task-{i}"} for i in range(100)}
        mock_get_objects.return_value = mock_objects

        collector = ValidationErrorCollector()
        # Typical prerequisite list (5 items)
        prerequisites = ["task-1", "task-2", "task-3", "task-4", "task-5"]

        start_time = time.perf_counter()
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)
        end_time = time.perf_counter()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Should complete in under 10ms for typical case
        assert execution_time < 10, f"Validation took {execution_time:.2f}ms, should be <10ms"
        assert not collector.has_errors()  # All prerequisites should exist

    @patch("trellis_mcp.validation.object_loader.get_all_objects")
    def test_performance_with_large_project(self, mock_get_objects):
        """Test performance with a large project (many objects)."""
        import time

        # Mock a large project with many objects
        mock_objects = {f"object-{i}": {"id": f"object-{i}"} for i in range(1000)}
        mock_get_objects.return_value = mock_objects

        collector = ValidationErrorCollector()
        prerequisites = ["object-1", "object-2", "object-3"]

        start_time = time.perf_counter()
        validate_prerequisite_existence(prerequisites, "/fake/project", collector)
        end_time = time.perf_counter()

        execution_time = (end_time - start_time) * 1000

        # Should still be reasonable even with large project
        assert execution_time < 50, f"Validation took {execution_time:.2f}ms, should be <50ms"
        assert not collector.has_errors()


if __name__ == "__main__":
    pytest.main([__file__])
