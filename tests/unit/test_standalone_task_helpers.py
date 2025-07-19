"""Tests for standalone task helper functions from path resolution utilities.

Tests the standalone task helper functions that manage path construction and
directory management for tasks outside the hierarchical project structure.
"""

import pytest

from trellis_mcp.path_resolver import (
    construct_standalone_task_path,
    ensure_standalone_task_directory,
    get_standalone_task_filename,
    id_to_path,
    path_to_id,
    resolve_path_for_new_object,
)


class TestStandaloneTaskHelpers:
    """Test cases for standalone task path construction helper functions."""

    def test_construct_standalone_task_path_open_status(self, temp_dir):
        """Test constructing standalone task path for open status."""
        project_root = temp_dir / "planning"

        result = construct_standalone_task_path("implement-auth", "open", project_root)
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_construct_standalone_task_path_done_status(self, temp_dir):
        """Test constructing standalone task path for done status."""
        project_root = temp_dir / "planning"

        result = construct_standalone_task_path("implement-auth", "done", project_root)

        # Should be in tasks-done directory with timestamp prefix
        assert result.parent == project_root / "tasks-done"
        assert result.name.endswith("-T-implement-auth.md")
        assert result.name.startswith("2025")  # Should start with current year

    def test_construct_standalone_task_path_none_status(self, temp_dir):
        """Test constructing standalone task path with None status (defaults to open)."""
        project_root = temp_dir / "planning"

        result = construct_standalone_task_path("implement-auth", None, project_root)
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_construct_standalone_task_path_with_prefix(self, temp_dir):
        """Test constructing standalone task path when ID has T- prefix."""
        project_root = temp_dir / "planning"

        result = construct_standalone_task_path("T-implement-auth", "open", project_root)
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_construct_standalone_task_path_project_root_contains_planning(self, temp_dir):
        """Test constructing standalone task path when project root contains planning directory."""
        project_root = temp_dir
        planning_dir = project_root / "planning"
        planning_dir.mkdir(parents=True)

        result = construct_standalone_task_path("implement-auth", "open", project_root)
        expected = planning_dir / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_construct_standalone_task_path_empty_id(self, temp_dir):
        """Test constructing standalone task path with empty ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            construct_standalone_task_path("", "open", project_root)

    def test_construct_standalone_task_path_whitespace_id(self, temp_dir):
        """Test constructing standalone task path with whitespace-only ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            construct_standalone_task_path("   ", "open", project_root)

    def test_construct_standalone_task_path_invalid_characters(self, temp_dir):
        """Test constructing standalone task path with invalid characters raises ValueError."""
        project_root = temp_dir / "planning"

        # Test path traversal attack
        with pytest.raises(ValueError, match="Invalid task ID"):
            construct_standalone_task_path("../../../etc/passwd", "open", project_root)

    def test_get_standalone_task_filename_open_status(self):
        """Test generating filename for open task."""
        result = get_standalone_task_filename("implement-auth", "open")
        assert result == "T-implement-auth.md"

    def test_get_standalone_task_filename_done_status(self):
        """Test generating filename for done task."""
        result = get_standalone_task_filename("implement-auth", "done")

        # Should have timestamp prefix
        assert result.endswith("-T-implement-auth.md")
        assert result.startswith("2025")  # Should start with current year
        assert len(result) > len("T-implement-auth.md")  # Should be longer due to timestamp

    def test_get_standalone_task_filename_none_status(self):
        """Test generating filename with None status (defaults to open)."""
        result = get_standalone_task_filename("implement-auth", None)
        assert result == "T-implement-auth.md"

    def test_get_standalone_task_filename_with_prefix(self):
        """Test generating filename when ID has T- prefix."""
        result = get_standalone_task_filename("T-implement-auth", "open")
        assert result == "T-implement-auth.md"

    def test_get_standalone_task_filename_timestamp_format(self):
        """Test that done task filename has correct timestamp format."""
        result = get_standalone_task_filename("test-task", "done")

        # Extract timestamp part
        timestamp_part = result.split("-T-")[0]

        # Should be in format YYYYMMDD_HHMMSS
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS
        assert timestamp_part[8] == "_"  # Underscore separator
        assert timestamp_part[:8].isdigit()  # Date part should be numeric
        assert timestamp_part[9:].isdigit()  # Time part should be numeric

    def test_get_standalone_task_filename_edge_cases(self):
        """Test generating filename with edge case task IDs."""
        # Test with hyphenated ID
        result = get_standalone_task_filename("multi-word-task", "open")
        assert result == "T-multi-word-task.md"

        # Test with numbers
        result = get_standalone_task_filename("task-123", "open")
        assert result == "T-task-123.md"

        # Test with mixed case
        result = get_standalone_task_filename("TestTask", "open")
        assert result == "T-TestTask.md"

    def test_ensure_standalone_task_directory_open_status(self, temp_dir):
        """Test ensuring standalone task directory for open status."""
        project_root = temp_dir / "planning"

        result = ensure_standalone_task_directory(project_root, "open")
        expected = project_root / "tasks-open"

        assert result == expected
        assert result.exists()
        assert result.is_dir()

    def test_ensure_standalone_task_directory_done_status(self, temp_dir):
        """Test ensuring standalone task directory for done status."""
        project_root = temp_dir / "planning"

        result = ensure_standalone_task_directory(project_root, "done")
        expected = project_root / "tasks-done"

        assert result == expected
        assert result.exists()
        assert result.is_dir()

    def test_ensure_standalone_task_directory_none_status(self, temp_dir):
        """Test ensuring standalone task directory with None status (defaults to open)."""
        project_root = temp_dir / "planning"

        result = ensure_standalone_task_directory(project_root, None)
        expected = project_root / "tasks-open"

        assert result == expected
        assert result.exists()
        assert result.is_dir()

    def test_ensure_standalone_task_directory_project_root_contains_planning(self, temp_dir):
        """Test ensuring standalone task directory when project root contains planning directory."""
        project_root = temp_dir
        planning_dir = project_root / "planning"
        planning_dir.mkdir(parents=True)

        result = ensure_standalone_task_directory(project_root, "open")
        expected = planning_dir / "tasks-open"

        assert result == expected
        assert result.exists()
        assert result.is_dir()

    def test_ensure_standalone_task_directory_already_exists(self, temp_dir):
        """Test ensuring standalone task directory when it already exists."""
        project_root = temp_dir / "planning"
        tasks_dir = project_root / "tasks-open"
        tasks_dir.mkdir(parents=True)

        # Should not raise error if directory already exists
        result = ensure_standalone_task_directory(project_root, "open")

        assert result == tasks_dir
        assert result.exists()
        assert result.is_dir()

    def test_ensure_standalone_task_directory_both_statuses(self, temp_dir):
        """Test ensuring both open and done task directories."""
        project_root = temp_dir / "planning"

        # Create both directories
        open_dir = ensure_standalone_task_directory(project_root, "open")
        done_dir = ensure_standalone_task_directory(project_root, "done")

        # Both should exist
        assert open_dir.exists()
        assert done_dir.exists()
        assert open_dir.is_dir()
        assert done_dir.is_dir()

        # Should be siblings
        assert open_dir.parent == done_dir.parent

    def test_standalone_task_helpers_integration(self, temp_dir):
        """Test integration of all standalone task helper functions."""
        project_root = temp_dir / "planning"

        # Test the complete workflow
        task_id = "integration-test"
        status = "open"

        # 1. Ensure directory exists
        task_dir = ensure_standalone_task_directory(project_root, status)
        assert task_dir.exists()

        # 2. Generate filename
        filename = get_standalone_task_filename(task_id, status)
        assert filename == "T-integration-test.md"

        # 3. Construct full path
        full_path = construct_standalone_task_path(task_id, status, project_root)
        expected_path = task_dir / filename

        assert full_path == expected_path

        # 4. Verify path components
        assert full_path.parent == project_root / "tasks-open"
        assert full_path.name == "T-integration-test.md"

    def test_standalone_task_helpers_with_done_status_integration(self, temp_dir):
        """Test integration of all standalone task helper functions with done status."""
        project_root = temp_dir / "planning"

        # Test the complete workflow for done tasks
        task_id = "completed-task"
        status = "done"

        # 1. Ensure directory exists
        task_dir = ensure_standalone_task_directory(project_root, status)
        assert task_dir.exists()

        # 2. Generate filename
        filename = get_standalone_task_filename(task_id, status)
        assert filename.endswith("-T-completed-task.md")
        assert filename.startswith("2025")  # Should have timestamp

        # 3. Construct full path
        full_path = construct_standalone_task_path(task_id, status, project_root)
        expected_path = task_dir / filename

        assert full_path == expected_path

        # 4. Verify path components
        assert full_path.parent == project_root / "tasks-done"
        assert full_path.name.endswith("-T-completed-task.md")

    def test_standalone_task_helpers_security_validation(self, temp_dir):
        """Test that standalone task helpers apply security validation."""
        project_root = temp_dir / "planning"

        # Test path traversal attack
        with pytest.raises(ValueError, match="Invalid task ID"):
            construct_standalone_task_path("../../../etc/passwd", "open", project_root)

        # Test absolute path attack
        with pytest.raises(ValueError, match="Invalid task ID"):
            construct_standalone_task_path("/etc/passwd", "open", project_root)

        # Test null byte attack
        with pytest.raises(ValueError, match="Invalid task ID"):
            construct_standalone_task_path("task\x00", "open", project_root)

    def test_standalone_task_helpers_consistency_with_existing_functions(self, temp_dir):
        """Test that standalone task helpers produce paths consistent with existing functions."""
        project_root = temp_dir / "planning"
        task_id = "consistency-test"

        # Test open status consistency
        helper_path = construct_standalone_task_path(task_id, "open", project_root)
        existing_path = resolve_path_for_new_object("task", task_id, None, project_root, "open")

        assert helper_path == existing_path

        # Test done status consistency (note: timestamps will differ, so just check structure)
        helper_path_done = construct_standalone_task_path(task_id, "done", project_root)
        existing_path_done = resolve_path_for_new_object(
            "task", task_id, None, project_root, "done"
        )

        # Should have same parent directory
        assert helper_path_done.parent == existing_path_done.parent

        # Both should end with same suffix
        assert helper_path_done.name.endswith("-T-consistency-test.md")
        assert existing_path_done.name.endswith("-T-consistency-test.md")


class TestStandaloneTaskPathToId:
    """Test cases for path_to_id function with standalone task paths.

    This class focuses specifically on testing the reverse path-to-ID conversion
    for standalone tasks (tasks stored in root-level tasks-open and tasks-done
    directories, not within the hierarchy).
    """

    def test_standalone_task_open_path_to_id(self, temp_dir):
        """Test converting standalone task path (tasks-open) to ID."""
        project_root = temp_dir / "planning"

        # Create standalone task structure in tasks-open
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-implement-standalone-auth.md"
        task_file.write_text("# Implement Standalone Auth Task")

        # Test converting path to ID
        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "implement-standalone-auth"

    def test_standalone_task_done_path_to_id(self, temp_dir):
        """Test converting standalone task path (tasks-done) to ID."""
        project_root = temp_dir / "planning"

        # Create standalone task structure in tasks-done
        task_dir = project_root / "tasks-done"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "20250718_143000-T-implement-standalone-auth.md"
        task_file.write_text("# Implement Standalone Auth Task")

        # Test converting path to ID
        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "implement-standalone-auth"

    def test_standalone_task_done_path_to_id_iso_format(self, temp_dir):
        """Test converting standalone task path (tasks-done) with ISO timestamp format to ID."""
        project_root = temp_dir / "planning"

        # Create standalone task structure in tasks-done with ISO format
        task_dir = project_root / "tasks-done"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "2025-07-18T19:30:00-05:00-T-implement-auth.md"
        task_file.write_text("# Implement Auth Task")

        # Test converting path to ID
        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "implement-auth"

    def test_standalone_task_complex_id_with_hyphens(self, temp_dir):
        """Test converting standalone task path with complex ID containing multiple hyphens."""
        project_root = temp_dir / "planning"

        # Create standalone task with complex ID
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-implement-user-auth-jwt-middleware.md"
        task_file.write_text("# Complex Task ID")

        # Test converting path to ID
        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "implement-user-auth-jwt-middleware"

    def test_standalone_task_id_with_numbers(self, temp_dir):
        """Test converting standalone task path with numbers in ID."""
        project_root = temp_dir / "planning"

        # Create standalone task with numbers in ID
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-task-123-v2.md"
        task_file.write_text("# Task with numbers")

        # Test converting path to ID
        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "task-123-v2"

    def test_standalone_task_round_trip_consistency_open(self, temp_dir):
        """Test round-trip consistency: path → ID → path for open standalone tasks."""
        project_root = temp_dir / "planning"

        # Create standalone task structure in tasks-open
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)
        original_file = task_dir / "T-roundtrip-test.md"
        original_file.write_text("# Roundtrip Test Task")

        # Convert path to ID
        kind, obj_id = path_to_id(original_file)
        assert kind == "task"
        assert obj_id == "roundtrip-test"

        # Convert ID back to path using id_to_path
        reconstructed_path = id_to_path(project_root, kind, obj_id)

        # Should get the same path back
        assert reconstructed_path == original_file

    def test_standalone_task_round_trip_consistency_done(self, temp_dir):
        """Test round-trip consistency: path → ID → path for done standalone tasks."""
        project_root = temp_dir / "planning"

        # Create standalone task structure in tasks-done
        task_dir = project_root / "tasks-done"
        task_dir.mkdir(parents=True)
        original_file = task_dir / "20250718_143000-T-roundtrip-test.md"
        original_file.write_text("# Roundtrip Test Task")

        # Convert path to ID
        kind, obj_id = path_to_id(original_file)
        assert kind == "task"
        assert obj_id == "roundtrip-test"

        # Convert ID back to path using id_to_path
        reconstructed_path = id_to_path(project_root, kind, obj_id)

        # Should get the same path back
        assert reconstructed_path == original_file

    def test_standalone_task_security_validation_task_id(self, temp_dir):
        """Test security validation for extracted task IDs from standalone task paths."""
        project_root = temp_dir / "planning"

        # Create tasks with potentially malicious IDs
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)

        # Test path traversal attempt in filename
        malicious_file = task_dir / "T-..%2F..%2Fetc%2Fpasswd.md"
        malicious_file.write_text("# Malicious Task")

        # Should raise ValueError due to invalid characters
        with pytest.raises(ValueError, match="Invalid task ID format"):
            path_to_id(malicious_file)

    def test_standalone_task_security_validation_path_traversal(self, temp_dir):
        """Test security validation against path traversal in task IDs."""
        project_root = temp_dir / "planning"

        # Create tasks with path traversal attempts
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)

        # Test valid cases that should work
        valid_cases = [
            "T-task-with-hyphens.md",  # Normal hyphens are OK
            "T-valid-task-id.md",  # Valid task ID
        ]

        for pattern in valid_cases:
            valid_file = task_dir / pattern
            valid_file.write_text("# Valid Task")

            # Should work normally
            kind, obj_id = path_to_id(valid_file)
            assert kind == "task"
            # Clean up
            valid_file.unlink()

        # Test invalid cases that contain dangerous characters
        invalid_cases = [
            "T-..%2F..%2Fetc%2Fpasswd.md",  # URL-encoded path traversal contains ".."
            "T-task-with-..-.md",  # Contains ".." which is blocked
        ]

        for pattern in invalid_cases:
            invalid_file = task_dir / pattern
            invalid_file.write_text("# Invalid Task")

            # Should raise ValueError due to invalid characters
            with pytest.raises(ValueError, match="Invalid task ID format"):
                path_to_id(invalid_file)

    def test_standalone_task_error_handling_invalid_filename(self, temp_dir):
        """Test error handling for invalid standalone task filenames."""
        project_root = temp_dir / "planning"

        # Create tasks with invalid filename patterns
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)

        # Test filenames that don't match expected patterns
        test_cases = [
            ("invalid-task.md", "Unrecognized file type"),  # Missing T- prefix
            ("T-.md", "Invalid task ID format"),  # Empty ID
            ("T-task.txt", "Unrecognized file type"),  # Wrong extension
            ("task-T-.md", "Invalid task ID format"),  # Wrong prefix position - matches -T- pattern
        ]

        for filename, expected_error in test_cases:
            invalid_file = task_dir / filename
            invalid_file.write_text("# Invalid Task")

            # Should raise ValueError with appropriate message
            with pytest.raises(ValueError, match=expected_error):
                path_to_id(invalid_file)

    def test_standalone_task_error_handling_malformed_done_task(self, temp_dir):
        """Test error handling for malformed done task filenames."""
        project_root = temp_dir / "planning"

        # Create tasks with malformed done task patterns
        task_dir = project_root / "tasks-done"
        task_dir.mkdir(parents=True)

        # Test malformed done task filenames
        test_cases = [
            ("invalid-T-.md", "Invalid task ID format"),  # Invalid prefix, empty ID
            ("20250718-T-.md", "Invalid task ID format"),  # Valid timestamp, empty ID
            ("T-task.md", "task"),  # Missing timestamp - treated as open task
            ("timestamp-task.md", "Unrecognized file type"),  # Missing T- prefix
        ]

        for filename, expected_result in test_cases:
            malformed_file = task_dir / filename
            malformed_file.write_text("# Malformed Task")

            if expected_result == "task":
                # This should succeed (T-task.md is valid open task pattern)
                kind, obj_id = path_to_id(malformed_file)
                assert kind == "task"
                assert obj_id == expected_result
            else:
                # Should raise ValueError for parsing issues
                with pytest.raises(ValueError, match=expected_result):
                    path_to_id(malformed_file)

    def test_standalone_task_integration_with_hierarchy_tasks(self, temp_dir):
        """Test that standalone task path parsing works alongside hierarchy-based tasks."""
        project_root = temp_dir / "planning"

        # Create both standalone and hierarchy-based tasks

        # Standalone task in root tasks-open
        standalone_dir = project_root / "tasks-open"
        standalone_dir.mkdir(parents=True)
        standalone_file = standalone_dir / "T-standalone-task.md"
        standalone_file.write_text("# Standalone Task")

        # Hierarchy-based task
        hierarchy_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-open"
        )
        hierarchy_dir.mkdir(parents=True)
        hierarchy_file = hierarchy_dir / "T-hierarchy-task.md"
        hierarchy_file.write_text("# Hierarchy Task")

        # Test parsing standalone task
        kind1, obj_id1 = path_to_id(standalone_file)
        assert kind1 == "task"
        assert obj_id1 == "standalone-task"

        # Test parsing hierarchy task
        kind2, obj_id2 = path_to_id(hierarchy_file)
        assert kind2 == "task"
        assert obj_id2 == "hierarchy-task"

    def test_standalone_task_discovery_priority_over_hierarchy(self, temp_dir):
        """Test that standalone tasks are discoverable when hierarchy tasks exist with same ID."""
        project_root = temp_dir / "planning"

        # Create standalone task
        standalone_dir = project_root / "tasks-open"
        standalone_dir.mkdir(parents=True)
        standalone_file = standalone_dir / "T-duplicate-task.md"
        standalone_file.write_text("# Standalone Task")

        # Create hierarchy task with same ID
        hierarchy_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-open"
        )
        hierarchy_dir.mkdir(parents=True)
        hierarchy_file = hierarchy_dir / "T-duplicate-task.md"
        hierarchy_file.write_text("# Hierarchy Task")

        # Test parsing each task directly
        kind1, obj_id1 = path_to_id(standalone_file)
        assert kind1 == "task"
        assert obj_id1 == "duplicate-task"

        kind2, obj_id2 = path_to_id(hierarchy_file)
        assert kind2 == "task"
        assert obj_id2 == "duplicate-task"

        # Test discovery via id_to_path - should find standalone first
        discovered_path = id_to_path(project_root, "task", "duplicate-task")
        assert discovered_path == standalone_file  # Standalone takes priority

    def test_standalone_task_edge_case_timestamps(self, temp_dir):
        """Test parsing standalone task paths with various timestamp formats."""
        project_root = temp_dir / "planning"

        # Create tasks with different timestamp formats
        task_dir = project_root / "tasks-done"
        task_dir.mkdir(parents=True)

        # Test various timestamp formats that should work
        timestamp_formats = [
            "20250718_143000-T-task.md",  # Basic format
            "2025-07-18T19:30:00-05:00-T-task.md",  # ISO format
            "1642634400-T-task.md",  # Unix timestamp
            "custom-timestamp-T-task.md",  # Custom format
        ]

        for filename in timestamp_formats:
            task_file = task_dir / filename
            task_file.write_text("# Task with timestamp")

            # Should successfully parse task ID
            kind, obj_id = path_to_id(task_file)
            assert kind == "task"
            assert obj_id == "task"

    def test_standalone_task_empty_directories(self, temp_dir):
        """Test behavior with empty standalone task directories."""
        project_root = temp_dir / "planning"

        # Create empty directories
        open_dir = project_root / "tasks-open"
        open_dir.mkdir(parents=True)

        done_dir = project_root / "tasks-done"
        done_dir.mkdir(parents=True)

        # Directories exist but are empty - should not affect path_to_id
        # Create a test file to verify normal operation
        test_file = open_dir / "T-test-task.md"
        test_file.write_text("# Test Task")

        # Should work normally
        kind, obj_id = path_to_id(test_file)
        assert kind == "task"
        assert obj_id == "test-task"

    def test_standalone_task_various_file_extensions(self, temp_dir):
        """Test that only .md files are recognized as standalone tasks."""
        project_root = temp_dir / "planning"

        # Create task directory
        task_dir = project_root / "tasks-open"
        task_dir.mkdir(parents=True)

        # Test .md file (should work)
        md_file = task_dir / "T-valid-task.md"
        md_file.write_text("# Valid Task")

        kind, obj_id = path_to_id(md_file)
        assert kind == "task"
        assert obj_id == "valid-task"

        # Test non-.md files (should fail)
        invalid_extensions = [
            "T-task.txt",
            "T-task.html",
            "T-task.rst",
            "T-task",  # No extension
        ]

        for filename in invalid_extensions:
            invalid_file = task_dir / filename
            invalid_file.write_text("# Invalid Task")

            with pytest.raises(ValueError, match="Unrecognized file type"):
                path_to_id(invalid_file)
