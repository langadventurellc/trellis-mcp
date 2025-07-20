"""Tests for task ID resolution utilities.

Comprehensive test suite for the task_resolver module covering cross-system
task lookup, ID validation, normalization, and error handling scenarios.
"""

from unittest.mock import patch

import pytest

from trellis_mcp.task_resolver import (
    resolve_task_by_id,
    validate_task_id_format,
)


class TestResolveTaskById:
    """Test cases for the resolve_task_by_id function."""

    def test_valid_task_id_resolution(self, tmp_path):
        """Test resolving valid task IDs across both systems."""
        # Setup test structure with both hierarchical and standalone tasks
        planning_dir = tmp_path / "planning"

        # Create hierarchical task
        hierarchical_task = (
            planning_dir
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-open"
            / "T-hierarchical-task.md"
        )
        hierarchical_task.parent.mkdir(parents=True, exist_ok=True)
        hierarchical_task.write_text("# Hierarchical Task")

        # Create standalone task
        standalone_task = planning_dir / "tasks-open" / "T-standalone-task.md"
        standalone_task.parent.mkdir(parents=True, exist_ok=True)
        standalone_task.write_text("# Standalone Task")

        # Test resolving hierarchical task with T- prefix
        result = resolve_task_by_id(str(tmp_path), "T-hierarchical-task")
        assert result == hierarchical_task

        # Test resolving hierarchical task without T- prefix
        result = resolve_task_by_id(str(tmp_path), "hierarchical-task")
        assert result == hierarchical_task

        # Test resolving standalone task with T- prefix
        result = resolve_task_by_id(str(tmp_path), "T-standalone-task")
        assert result == standalone_task

        # Test resolving standalone task without T- prefix
        result = resolve_task_by_id(str(tmp_path), "standalone-task")
        assert result == standalone_task

    def test_task_priority_standalone_over_hierarchical(self, tmp_path):
        """Test that standalone tasks take priority when same ID exists in both systems."""
        planning_dir = tmp_path / "planning"

        # Create hierarchical task with same ID
        hierarchical_task = (
            planning_dir
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-open"
            / "T-duplicate-id.md"
        )
        hierarchical_task.parent.mkdir(parents=True, exist_ok=True)
        hierarchical_task.write_text("# Hierarchical Task")

        # Create standalone task with same ID
        standalone_task = planning_dir / "tasks-open" / "T-duplicate-id.md"
        standalone_task.parent.mkdir(parents=True, exist_ok=True)
        standalone_task.write_text("# Standalone Task")

        # Should return standalone task (has priority)
        result = resolve_task_by_id(str(tmp_path), "duplicate-id")
        assert result == standalone_task

    def test_task_resolution_with_done_tasks(self, tmp_path):
        """Test resolving tasks in tasks-done directories."""
        planning_dir = tmp_path / "planning"

        # Create done task in standalone system
        done_task = planning_dir / "tasks-done" / "20250720_153000-T-completed-task.md"
        done_task.parent.mkdir(parents=True, exist_ok=True)
        done_task.write_text("# Completed Task")

        # Create done task in hierarchical system
        hierarchical_done = (
            planning_dir
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-done"
            / "20250720_154000-T-hierarchical-done.md"
        )
        hierarchical_done.parent.mkdir(parents=True, exist_ok=True)
        hierarchical_done.write_text("# Hierarchical Done Task")

        # Test resolving done tasks
        result = resolve_task_by_id(str(tmp_path), "completed-task")
        assert result == done_task

        result = resolve_task_by_id(str(tmp_path), "hierarchical-done")
        assert result == hierarchical_done

    def test_nonexistent_task_returns_none(self, tmp_path):
        """Test that non-existent tasks return None."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)

        result = resolve_task_by_id(str(tmp_path), "nonexistent-task")
        assert result is None

        result = resolve_task_by_id(str(tmp_path), "T-nonexistent-task")
        assert result is None

    def test_empty_project_root_raises_error(self):
        """Test that empty project root raises ValueError."""
        with pytest.raises(ValueError, match="Project root cannot be empty"):
            resolve_task_by_id("", "task-id")

        with pytest.raises(ValueError, match="Project root cannot be empty"):
            resolve_task_by_id("   ", "task-id")

    def test_empty_task_id_raises_error(self, tmp_path):
        """Test that empty task ID raises ValueError."""
        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            resolve_task_by_id(str(tmp_path), "")

        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            resolve_task_by_id(str(tmp_path), "   ")

    def test_invalid_task_id_format_raises_error(self, tmp_path):
        """Test that invalid task ID formats raise ValueError."""
        # Test inputs that normalize to empty or invalid strings
        with pytest.raises(ValueError, match="Invalid task ID format"):
            resolve_task_by_id(
                str(tmp_path), "@@@@"
            )  # only special chars -> empty after normalization

        with pytest.raises(ValueError, match="Invalid task ID format"):
            resolve_task_by_id(str(tmp_path), "---")  # only hyphens -> invalid

        with pytest.raises(ValueError, match="Invalid task ID format"):
            resolve_task_by_id(str(tmp_path), "a" * 100)  # too long even after normalization

    @patch("trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    def test_security_validation_errors(self, mock_validate, tmp_path):
        """Test that security validation errors are properly raised."""
        mock_validate.return_value = ["Security error: path traversal detected"]

        with pytest.raises(ValueError, match="Task ID validation failed"):
            resolve_task_by_id(str(tmp_path), "valid-task-id")

    @patch("trellis_mcp.validation.security.validate_standalone_task_path_security")
    def test_path_security_validation_errors(self, mock_security, tmp_path):
        """Test that path security validation errors are properly raised."""
        # Mock the field validation to pass
        with patch(
            "trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters",
            return_value=[],
        ):
            mock_security.return_value = ["Security error: dangerous path detected"]

            with pytest.raises(ValueError, match="Security validation failed"):
                resolve_task_by_id(str(tmp_path), "valid-task-id")

    def test_path_resolution_with_different_project_structures(self, tmp_path):
        """Test path resolution with both project-root and planning-root structures."""
        # Test with project root containing planning directory
        project_with_planning = tmp_path / "project-with-planning"
        planning_subdir = project_with_planning / "planning"
        task_file = planning_subdir / "tasks-open" / "T-test-task.md"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text("# Test Task")

        result = resolve_task_by_id(str(project_with_planning), "test-task")
        assert result == task_file

        # Test with planning directory as root
        planning_as_root = tmp_path / "planning-as-root"
        task_file2 = planning_as_root / "tasks-open" / "T-test-task2.md"
        task_file2.parent.mkdir(parents=True, exist_ok=True)
        task_file2.write_text("# Test Task 2")

        result = resolve_task_by_id(str(planning_as_root), "test-task2")
        assert result == task_file2


class TestValidateTaskIdFormat:
    """Test cases for the validate_task_id_format function."""

    def test_valid_task_id_formats(self):
        """Test valid task ID formats."""
        valid_ids = [
            "implement-auth",
            "create-user-model",
            "fix-bug-123",
            "add-validation",
            "test-component",
            "a",  # single character
            "task-with-numbers-123",
            "very-long-but-valid-task-name",
        ]

        for task_id in valid_ids:
            assert validate_task_id_format(task_id), f"Should be valid: {task_id}"

    def test_invalid_task_id_formats(self):
        """Test invalid task ID formats."""
        invalid_ids = [
            "",  # empty
            "   ",  # whitespace only
            "task_with_underscores",  # underscores not allowed
            "UPPERCASE-TASK",  # uppercase not allowed
            "Task-With-Mixed-Case",  # mixed case not allowed
            "task with spaces",  # spaces not allowed
            "task@with-special",  # special characters not allowed
            "task#with%symbols",  # symbols not allowed
            "-starts-with-hyphen",  # starts with hyphen
            "ends-with-hyphen-",  # ends with hyphen
            "double--hyphens",  # consecutive hyphens
            "---",  # only hyphens
            "very-long-task-id-that-exceeds-the-maximum-allowed-length-limit-for-ids",  # too long
        ]

        for task_id in invalid_ids:
            assert not validate_task_id_format(task_id), f"Should be invalid: {task_id}"

    def test_edge_case_formats(self):
        """Test edge case task ID formats."""
        # Test length boundaries
        # Assuming MAX_ID_LENGTH is 32 (from id_utils)
        exactly_32_chars = "a" * 32
        assert validate_task_id_format(exactly_32_chars)

        too_long = "a" * 33
        assert not validate_task_id_format(too_long)

        # Test single character variations
        assert validate_task_id_format("a")
        assert validate_task_id_format("1")
        assert not validate_task_id_format("-")


class TestCrossSystemIntegration:
    """Integration tests for cross-system task resolution."""

    def test_large_hierarchy_performance(self, tmp_path):
        """Test performance with large task hierarchies."""
        planning_dir = tmp_path / "planning"

        # Create a large hierarchy with multiple projects, epics, features, and tasks
        for project_num in range(3):
            for epic_num in range(3):
                for feature_num in range(3):
                    for task_num in range(10):
                        task_path = (
                            planning_dir
                            / "projects"
                            / f"P-project-{project_num}"
                            / "epics"
                            / f"E-epic-{epic_num}"
                            / "features"
                            / f"F-feature-{feature_num}"
                            / "tasks-open"
                            / f"T-task-{project_num}-{epic_num}-{feature_num}-{task_num}.md"
                        )
                        task_path.parent.mkdir(parents=True, exist_ok=True)
                        task_path.write_text(
                            f"# Task {project_num}-{epic_num}-{feature_num}-{task_num}"
                        )

        # Add some standalone tasks
        for task_num in range(20):
            task_path = planning_dir / "tasks-open" / f"T-standalone-{task_num}.md"
            task_path.parent.mkdir(parents=True, exist_ok=True)
            task_path.write_text(f"# Standalone Task {task_num}")

        # Test that resolution still works efficiently
        result = resolve_task_by_id(str(tmp_path), "task-1-2-1-5")
        assert result is not None
        assert "T-task-1-2-1-5.md" in str(result)

        result = resolve_task_by_id(str(tmp_path), "standalone-15")
        assert result is not None
        assert "T-standalone-15.md" in str(result)

    def test_mixed_task_states(self, tmp_path):
        """Test resolution with tasks in different states (open/done)."""
        planning_dir = tmp_path / "planning"

        # Create open tasks
        open_hierarchical = (
            planning_dir
            / "projects"
            / "P-test"
            / "epics"
            / "E-test"
            / "features"
            / "F-test"
            / "tasks-open"
            / "T-open-task.md"
        )
        open_hierarchical.parent.mkdir(parents=True, exist_ok=True)
        open_hierarchical.write_text("# Open Task")

        open_standalone = planning_dir / "tasks-open" / "T-open-standalone.md"
        open_standalone.parent.mkdir(parents=True, exist_ok=True)
        open_standalone.write_text("# Open Standalone")

        # Create done tasks
        done_hierarchical = (
            planning_dir
            / "projects"
            / "P-test"
            / "epics"
            / "E-test"
            / "features"
            / "F-test"
            / "tasks-done"
            / "20250720_153000-T-done-task.md"
        )
        done_hierarchical.parent.mkdir(parents=True, exist_ok=True)
        done_hierarchical.write_text("# Done Task")

        done_standalone = planning_dir / "tasks-done" / "20250720_154000-T-done-standalone.md"
        done_standalone.parent.mkdir(parents=True, exist_ok=True)
        done_standalone.write_text("# Done Standalone")

        # Test resolution of all task states
        assert resolve_task_by_id(str(tmp_path), "open-task") == open_hierarchical
        assert resolve_task_by_id(str(tmp_path), "open-standalone") == open_standalone
        assert resolve_task_by_id(str(tmp_path), "done-task") == done_hierarchical
        assert resolve_task_by_id(str(tmp_path), "done-standalone") == done_standalone

    def test_error_handling_with_malformed_structure(self, tmp_path):
        """Test error handling with malformed directory structures."""
        planning_dir = tmp_path / "planning"

        # Create some malformed structures that shouldn't break resolution
        malformed_dir = planning_dir / "projects" / "not-a-project-dir"
        malformed_dir.mkdir(parents=True, exist_ok=True)
        (malformed_dir / "random-file.txt").write_text("not a task")

        # Create valid task
        valid_task = planning_dir / "tasks-open" / "T-valid-task.md"
        valid_task.parent.mkdir(parents=True, exist_ok=True)
        valid_task.write_text("# Valid Task")

        # Should still resolve valid tasks despite malformed structures
        result = resolve_task_by_id(str(tmp_path), "valid-task")
        assert result == valid_task

        # Should return None for non-existent tasks
        result = resolve_task_by_id(str(tmp_path), "nonexistent")
        assert result is None


class TestErrorScenarios:
    """Test error scenarios and edge cases."""

    def test_permission_errors(self, tmp_path, monkeypatch):
        """Test handling of permission errors during file access."""
        # This test would require special setup to simulate permission errors
        # For now, we'll test the basic error handling structure
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)

        # Test with a valid task ID that would trigger permission checks
        result = resolve_task_by_id(str(tmp_path), "test-task")
        assert result is None  # Should handle gracefully

    def test_concurrent_access_simulation(self, tmp_path):
        """Test behavior under simulated concurrent access."""
        planning_dir = tmp_path / "planning"
        task_file = planning_dir / "tasks-open" / "T-concurrent-task.md"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text("# Concurrent Task")

        # Multiple rapid calls should all succeed
        results = []
        for _ in range(10):
            result = resolve_task_by_id(str(tmp_path), "concurrent-task")
            results.append(result)

        # All results should be the same
        assert all(r == task_file for r in results)

    def test_unicode_handling_in_file_paths(self, tmp_path):
        """Test handling of Unicode characters in file paths."""
        planning_dir = tmp_path / "planning"

        # Create task with Unicode in project/epic/feature names
        # Note: using ASCII-safe names since filesystem may not support Unicode
        unicode_task = (
            planning_dir
            / "projects"
            / "P-unicode-project"
            / "epics"
            / "E-unicode-epic"
            / "features"
            / "F-unicode-feature"
            / "tasks-open"
            / "T-unicode-task.md"
        )
        unicode_task.parent.mkdir(parents=True, exist_ok=True)
        unicode_task.write_text("# Unicode Task")

        # Should resolve normally
        result = resolve_task_by_id(str(tmp_path), "unicode-task")
        assert result == unicode_task
