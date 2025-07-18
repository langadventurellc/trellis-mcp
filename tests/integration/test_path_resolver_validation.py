"""Integration tests for path resolver validation.

This module tests the integration of validation functions with the path
resolver to ensure security and data integrity for standalone task operations.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from trellis_mcp.path_resolver import (
    children_of,
    id_to_path,
    resolve_path_for_new_object,
)


class TestIdToPathValidation:
    """Test validation integration in id_to_path function."""

    def test_id_to_path_with_valid_task_id(self):
        """Test id_to_path works with valid task ID."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Create a test task file
            tasks_dir = project_root / "tasks-open"
            tasks_dir.mkdir(parents=True)
            task_file = tasks_dir / "T-valid-task.md"
            task_file.write_text("# Valid Task")

            # This should work without validation errors
            result = id_to_path(project_root, "task", "valid-task")
            assert result == task_file

    def test_id_to_path_rejects_invalid_task_id_characters(self):
        """Test id_to_path rejects task IDs with invalid characters."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                id_to_path(project_root, "task", "invalid@task#id")

    def test_id_to_path_rejects_path_traversal_attacks(self):
        """Test id_to_path rejects path traversal attempts."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                id_to_path(project_root, "task", "../../../etc/passwd")

    def test_id_to_path_rejects_empty_task_id(self):
        """Test id_to_path rejects empty task ID."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Object ID cannot be empty"):
                id_to_path(project_root, "task", "")

    def test_id_to_path_rejects_too_long_task_id(self):
        """Test id_to_path rejects task IDs exceeding filesystem limits."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            long_id = "a" * 300  # Exceeds 255 character filesystem limit

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                id_to_path(project_root, "task", long_id)

    def test_id_to_path_allows_valid_non_task_objects(self):
        """Test id_to_path allows non-task objects without task validation."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Create a test project file
            projects_dir = project_root / "projects" / "P-test-project"
            projects_dir.mkdir(parents=True)
            project_file = projects_dir / "project.md"
            project_file.write_text("# Test Project")

            # This should work without task validation
            result = id_to_path(project_root, "project", "test-project")
            assert result == project_file


class TestResolvePathForNewObjectValidation:
    """Test validation integration in resolve_path_for_new_object function."""

    def test_resolve_path_with_valid_task_parameters(self):
        """Test resolve_path_for_new_object works with valid task parameters."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should work without validation errors
            result = resolve_path_for_new_object("task", "valid-task", None, project_root, "open")
            expected = project_root / "tasks-open" / "T-valid-task.md"
            assert result == expected

    def test_resolve_path_rejects_invalid_task_id(self):
        """Test resolve_path_for_new_object rejects invalid task IDs."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task parameters"):
                resolve_path_for_new_object("task", "invalid@task", None, project_root, "open")

    def test_resolve_path_rejects_invalid_status(self):
        """Test resolve_path_for_new_object rejects invalid status parameters."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task parameters"):
                resolve_path_for_new_object(
                    "task", "valid-task", None, project_root, "invalid-status"
                )

    def test_resolve_path_rejects_path_traversal_in_status(self):
        """Test resolve_path_for_new_object rejects path traversal in status."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task parameters"):
                resolve_path_for_new_object(
                    "task", "valid-task", None, project_root, "../bad-status"
                )

    def test_resolve_path_allows_valid_non_task_objects(self):
        """Test resolve_path_for_new_object allows non-task objects without validation."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should work without task validation
            result = resolve_path_for_new_object("project", "test-project", None, project_root)
            expected = project_root / "projects" / "P-test-project" / "project.md"
            assert result == expected


class TestChildrenOfValidation:
    """Test validation integration in children_of function."""

    def test_children_of_with_valid_task_id(self):
        """Test children_of works with valid task ID."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Tasks have no children, so this should return empty list
            result = children_of("task", "valid-task", project_root)
            assert result == []

    def test_children_of_rejects_invalid_task_id(self):
        """Test children_of rejects invalid task IDs."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                children_of("task", "invalid@task", project_root)

    def test_children_of_rejects_path_traversal_in_task_id(self):
        """Test children_of rejects path traversal attempts in task ID."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                children_of("task", "../../../etc/passwd", project_root)


class TestValidationErrorMessages:
    """Test that validation error messages are clear and useful."""

    def test_validation_error_includes_specific_issue(self):
        """Test that validation errors include specific issue details."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Test path traversal error message
            with pytest.raises(ValueError) as exc_info:
                id_to_path(project_root, "task", "../bad-path")

            error_msg = str(exc_info.value)
            assert "Invalid task ID" in error_msg
            # The path traversal error might be caught by invalid characters validation first
            assert (
                "path traversal" in error_msg.lower() or "invalid characters" in error_msg.lower()
            )

    def test_validation_error_for_invalid_characters(self):
        """Test validation error for invalid characters is clear."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Test invalid characters error message
            with pytest.raises(ValueError) as exc_info:
                id_to_path(project_root, "task", "invalid@task")

            error_msg = str(exc_info.value)
            assert "Invalid task ID" in error_msg
            assert "invalid characters" in error_msg.lower()

    def test_validation_error_for_invalid_status(self):
        """Test validation error for invalid status is clear."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Test invalid status error message
            with pytest.raises(ValueError) as exc_info:
                resolve_path_for_new_object("task", "valid-task", None, project_root, "bad-status")

            error_msg = str(exc_info.value)
            assert "Invalid task parameters" in error_msg
            assert "Invalid status parameter" in error_msg


class TestValidationCompatibility:
    """Test that new validation is compatible with existing validation."""

    def test_validation_preserves_existing_behavior(self):
        """Test that new validation doesn't break existing valid operations."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Create valid task structure
            tasks_dir = project_root / "tasks-open"
            tasks_dir.mkdir(parents=True)
            task_file = tasks_dir / "T-valid-task-name.md"
            task_file.write_text("# Valid Task")

            # These operations should continue to work
            result = id_to_path(project_root, "task", "valid-task-name")
            assert result == task_file

            result = resolve_path_for_new_object(
                "task", "another-valid-task", None, project_root, "open"
            )
            expected = project_root / "tasks-open" / "T-another-valid-task.md"
            assert result == expected

    def test_validation_works_with_task_prefixes(self):
        """Test that validation works correctly with T- prefixes."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Create valid task structure
            tasks_dir = project_root / "tasks-open"
            tasks_dir.mkdir(parents=True)
            task_file = tasks_dir / "T-prefixed-task.md"
            task_file.write_text("# Prefixed Task")

            # Both with and without prefix should work
            result1 = id_to_path(project_root, "task", "prefixed-task")
            result2 = id_to_path(project_root, "task", "T-prefixed-task")
            assert result1 == task_file
            assert result2 == task_file

    def test_validation_maintains_error_precedence(self):
        """Test that validation errors are reported in logical order."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Empty task ID should be caught first
            with pytest.raises(ValueError, match="Object ID cannot be empty"):
                id_to_path(project_root, "task", "")

            # Invalid kind should be caught before task validation
            with pytest.raises(ValueError, match="Invalid kind"):
                id_to_path(project_root, "invalid-kind", "valid-task")
