"""Integration tests for path validation with path resolution functions.

This module tests how validation functions integrate with path resolver operations
to ensure security and data integrity across the entire path resolution system.
Tests the interaction between validation and actual path operations.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from trellis_mcp.path_resolver import (
    children_of,
    id_to_path,
    resolve_path_for_new_object,
)
from trellis_mcp.validation.field_validation import (
    validate_standalone_task_path_parameters,
)


class TestStandaloneTaskPathParametersValidation:
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


class TestIdToPathValidationIntegration:
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


class TestResolvePathForNewObjectValidationIntegration:
    """Test validation integration in resolve_path_for_new_object function."""

    def test_resolve_path_with_valid_task_parameters(self):
        """Test resolve_path_for_new_object works with valid parameters."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Create parent feature structure
            feature_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / "F-test-feature"
            )
            feature_dir.mkdir(parents=True)
            feature_file = feature_dir / "feature.md"
            feature_file.write_text("# Test Feature")

            # This should work without validation errors
            result = resolve_path_for_new_object(
                "task", "valid-task-id", "test-feature", project_root, "open"
            )

            expected_path = feature_dir / "tasks-open" / "T-valid-task-id.md"
            assert result == expected_path

    def test_resolve_path_rejects_invalid_task_id(self):
        """Test resolve_path_for_new_object rejects invalid task IDs."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                resolve_path_for_new_object(
                    "task", "invalid@task#id", "feature", project_root, "open"
                )

    def test_resolve_path_rejects_path_traversal(self):
        """Test resolve_path_for_new_object rejects path traversal attempts."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                resolve_path_for_new_object(
                    "task", "../../../etc/passwd", "feature", project_root, "open"
                )

    def test_resolve_path_with_standalone_task_valid_id(self):
        """Test resolve_path_for_new_object works for standalone tasks."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should work for standalone tasks
            result = resolve_path_for_new_object(
                "task", "standalone-task-id", None, project_root, "open"
            )

            expected_path = project_root / "tasks-open" / "T-standalone-task-id.md"
            assert result == expected_path

    def test_resolve_path_rejects_standalone_task_invalid_id(self):
        """Test resolve_path_for_new_object rejects invalid standalone task IDs."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError, match="Invalid task ID"):
                resolve_path_for_new_object(
                    "task", "invalid@standalone#task", None, project_root, "open"
                )


class TestChildrenOfValidationIntegration:
    """Test validation integration in children_of function."""

    def test_children_of_with_valid_parent_id(self):
        """Test children_of works with valid parent ID."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Create a test project structure
            project_dir = project_root / "projects" / "P-test-project"
            project_dir.mkdir(parents=True)
            project_file = project_dir / "project.md"
            project_file.write_text("# Test Project")

            # Create an epic
            epic_dir = project_dir / "epics" / "E-test-epic"
            epic_dir.mkdir(parents=True)
            epic_file = epic_dir / "epic.md"
            epic_file.write_text("# Test Epic")

            # This should work without validation errors
            result = children_of("project", "test-project", project_root)
            assert epic_file in result

    def test_children_of_rejects_invalid_parent_id(self):
        """Test children_of rejects invalid parent IDs."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation for task objects
            with pytest.raises(ValueError):
                children_of("task", "invalid@parent#id", project_root)

    def test_children_of_rejects_path_traversal(self):
        """Test children_of rejects path traversal attempts."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # This should fail validation
            with pytest.raises(ValueError):
                children_of("project", "../../../etc", project_root)


class TestValidationErrorMessages:
    """Test consistency and clarity of validation error messages."""

    def test_task_id_validation_error_messages(self):
        """Test that task ID validation provides clear error messages."""
        test_cases = [
            ("", "empty"),
            ("   ", "empty"),
            ("invalid@id", "invalid characters"),
            ("../traversal", "path traversal"),
            ("a" * 300, "filesystem name limits"),
        ]

        for task_id, expected_pattern in test_cases:
            errors = validate_standalone_task_path_parameters(task_id, "open")
            assert len(errors) >= 1
            assert any(
                expected_pattern in error for error in errors
            ), f"Expected '{expected_pattern}' in errors for task ID '{task_id}'"

    def test_status_validation_error_messages(self):
        """Test that status validation provides clear error messages."""
        errors = validate_standalone_task_path_parameters("valid-task", "invalid-status")
        assert len(errors) >= 1
        assert any("Invalid status parameter" in error for error in errors)

    def test_path_resolver_validation_error_messages(self):
        """Test that path resolver functions provide clear validation errors."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Test id_to_path error messages
            with pytest.raises(ValueError, match="Invalid task ID"):
                id_to_path(project_root, "task", "invalid@id")

            # Test resolve_path_for_new_object error messages
            with pytest.raises(ValueError, match="Invalid task ID"):
                resolve_path_for_new_object("task", "invalid@id", None, project_root, "open")

    def test_error_message_consistency(self):
        """Test that similar validation errors have consistent messaging."""
        # Test that path traversal is detected consistently
        path_traversal_id = "../etc/passwd"

        # Test in validation function
        validation_errors = validate_standalone_task_path_parameters(path_traversal_id, "open")
        validation_has_traversal = any("path traversal" in error for error in validation_errors)

        # Test in path resolver (should raise exception)
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            with pytest.raises(ValueError) as exc_info:
                id_to_path(project_root, "task", path_traversal_id)

            resolver_error = str(exc_info.value)

        # Both should detect the path traversal issue
        assert validation_has_traversal
        assert "Invalid task ID" in resolver_error


class TestValidationCompatibility:
    """Test validation compatibility across different scenarios."""

    def test_validation_with_prefixed_ids(self):
        """Test that validation works correctly with prefixed object IDs."""
        # Task IDs with T- prefix should be validated correctly
        errors = validate_standalone_task_path_parameters("T-valid-task-id", "open")
        assert errors == []

        # Invalid characters should still be caught even with prefix
        errors = validate_standalone_task_path_parameters("T-invalid@task#id", "open")
        assert len(errors) >= 1
        assert any("invalid characters" in error for error in errors)

    def test_validation_with_different_statuses(self):
        """Test validation compatibility with different status values."""
        valid_statuses = ["open", "done", "in-progress", "review"]
        for status in valid_statuses:
            errors = validate_standalone_task_path_parameters("valid-task-id", status)
            assert errors == []

    def test_validation_with_none_status(self):
        """Test validation compatibility when status is None."""
        errors = validate_standalone_task_path_parameters("valid-task-id", None)
        assert errors == []

    def test_validation_integration_with_existing_validation(self):
        """Test that new validation integrates with existing validation systems."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "planning"
            project_root.mkdir(parents=True)

            # Test that validation is consistently applied across all path functions
            invalid_id = "invalid@task#id"

            # All functions should reject the same invalid ID
            with pytest.raises(ValueError):
                id_to_path(project_root, "task", invalid_id)

            with pytest.raises(ValueError):
                resolve_path_for_new_object("task", invalid_id, None, project_root, "open")

            # Validation function should also catch it
            errors = validate_standalone_task_path_parameters(invalid_id, "open")
            assert len(errors) >= 1

    def test_validation_performance_with_large_inputs(self):
        """Test that validation performs adequately with large inputs."""
        # Test with maximum valid length
        max_valid_id = "a" * 255
        errors = validate_standalone_task_path_parameters(max_valid_id, "open")
        assert errors == []

        # Test with slightly over limit
        over_limit_id = "a" * 256
        errors = validate_standalone_task_path_parameters(over_limit_id, "open")
        assert len(errors) >= 1
        assert any("filesystem name limits" in error for error in errors)
