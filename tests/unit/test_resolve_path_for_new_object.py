"""Tests for resolve_path_for_new_object function from path resolution utilities.

Tests the resolve_path_for_new_object function that generates filesystem paths
for new objects in both hierarchical and standalone task structures.
"""

import time

import pytest

from trellis_mcp.path_resolver import resolve_path_for_new_object


class TestResolvePathForNewObject:
    """Test cases for the resolve_path_for_new_object function."""

    def test_project_path_resolution(self, temp_dir):
        """Test resolving project paths for new objects."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("project", "user-auth", None, project_root)
        expected = project_root / "projects" / "P-user-auth" / "project.md"

        assert result == expected

    def test_project_with_prefix_id(self, temp_dir):
        """Test project path resolution when ID has prefix."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("project", "P-user-auth", None, project_root)
        expected = project_root / "projects" / "P-user-auth" / "project.md"

        assert result == expected

    def test_epic_path_resolution(self, temp_dir):
        """Test resolving epic paths for new objects."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("epic", "authentication", "user-auth", project_root)
        expected = (
            project_root / "projects" / "P-user-auth" / "epics" / "E-authentication" / "epic.md"
        )

        assert result == expected

    def test_epic_with_prefix_parent(self, temp_dir):
        """Test epic path resolution when parent ID has prefix."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("epic", "authentication", "P-user-auth", project_root)
        expected = (
            project_root / "projects" / "P-user-auth" / "epics" / "E-authentication" / "epic.md"
        )

        assert result == expected

    def test_feature_path_resolution(self, temp_dir):
        """Test resolving feature paths for new objects."""
        project_root = temp_dir / "planning"

        # Create parent epic structure
        epic_dir = project_root / "projects" / "P-user-auth" / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Authentication Epic")

        result = resolve_path_for_new_object("feature", "login", "authentication", project_root)
        expected = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "feature.md"
        )

        assert result == expected

    def test_feature_with_prefix_parent(self, temp_dir):
        """Test feature path resolution when parent ID has prefix."""
        project_root = temp_dir / "planning"

        # Create parent epic structure
        epic_dir = project_root / "projects" / "P-user-auth" / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Authentication Epic")

        result = resolve_path_for_new_object("feature", "login", "E-authentication", project_root)
        expected = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "feature.md"
        )

        assert result == expected

    def test_task_path_resolution_open_status(self, temp_dir):
        """Test resolving task paths for new objects with open status."""
        project_root = temp_dir / "planning"

        # Create parent feature structure
        feature_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Login Feature")

        result = resolve_path_for_new_object("task", "implement-jwt", "login", project_root, "open")
        expected = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-open"
            / "T-implement-jwt.md"
        )

        assert result == expected

    def test_task_path_resolution_default_status(self, temp_dir):
        """Test resolving task paths for new objects with default status (no status specified)."""
        project_root = temp_dir / "planning"

        # Create parent feature structure
        feature_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Login Feature")

        result = resolve_path_for_new_object("task", "implement-jwt", "login", project_root)
        expected = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-open"
            / "T-implement-jwt.md"
        )

        assert result == expected

    def test_task_path_resolution_done_status(self, temp_dir):
        """Test resolving task paths for new objects with done status."""
        project_root = temp_dir / "planning"

        # Create parent feature structure
        feature_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Login Feature")

        result = resolve_path_for_new_object("task", "implement-jwt", "login", project_root, "done")

        # Should be in tasks-done directory with timestamp prefix
        assert (
            result.parent
            == project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-done"
        )
        assert result.name.endswith("-T-implement-jwt.md")
        assert len(result.name.split("-")) >= 3  # timestamp format should have hyphens

    def test_task_with_prefix_parent(self, temp_dir):
        """Test task path resolution when parent ID has prefix."""
        project_root = temp_dir / "planning"

        # Create parent feature structure
        feature_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Login Feature")

        result = resolve_path_for_new_object(
            "task", "implement-jwt", "F-login", project_root, "open"
        )
        expected = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-open"
            / "T-implement-jwt.md"
        )

        assert result == expected

    def test_invalid_kind_error(self, temp_dir):
        """Test that invalid kinds raise ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind 'invalid'"):
            resolve_path_for_new_object("invalid", "some-id", None, project_root)

    def test_empty_kind_error(self, temp_dir):
        """Test that empty kind raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind ''"):
            resolve_path_for_new_object("", "some-id", None, project_root)

    def test_empty_id_error(self, temp_dir):
        """Test that empty ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            resolve_path_for_new_object("project", "", None, project_root)

    def test_whitespace_id_error(self, temp_dir):
        """Test that whitespace-only ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            resolve_path_for_new_object("project", "   ", None, project_root)

    def test_epic_missing_parent_error(self, temp_dir):
        """Test that epic without parent raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Parent is required for epic objects"):
            resolve_path_for_new_object("epic", "some-epic", None, project_root)

    def test_feature_missing_parent_error(self, temp_dir):
        """Test that feature without parent raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Parent is required for feature objects"):
            resolve_path_for_new_object("feature", "some-feature", None, project_root)

    def test_task_missing_parent_error(self, temp_dir):
        """Test that task without parent creates standalone task path."""
        project_root = temp_dir / "planning"

        # Standalone tasks (parent=None) should now create valid paths
        result_path = resolve_path_for_new_object("task", "some-task", None, project_root)
        expected_path = project_root / "tasks-open" / "T-some-task.md"
        assert result_path == expected_path

    def test_feature_nonexistent_parent_error(self, temp_dir):
        """Test that feature with nonexistent parent raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(ValueError, match="Parent epic 'nonexistent' not found"):
            resolve_path_for_new_object("feature", "some-feature", "nonexistent", project_root)

    def test_task_nonexistent_parent_error(self, temp_dir):
        """Test that task with nonexistent parent raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(ValueError, match="Parent feature 'nonexistent' not found"):
            resolve_path_for_new_object("task", "some-task", "nonexistent", project_root)

    def test_complex_hierarchy_path_resolution(self, temp_dir):
        """Test resolving paths in a complex hierarchy."""
        project_root = temp_dir / "planning"

        # Create complex feature structure
        feature_dir = (
            project_root
            / "projects"
            / "P-ecommerce"
            / "epics"
            / "E-user-management"
            / "features"
            / "F-user-profile"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# User Profile Feature")

        # Test task creation in this hierarchy
        result = resolve_path_for_new_object("task", "update-avatar", "user-profile", project_root)
        expected = (
            project_root
            / "projects"
            / "P-ecommerce"
            / "epics"
            / "E-user-management"
            / "features"
            / "F-user-profile"
            / "tasks-open"
            / "T-update-avatar.md"
        )

        assert result == expected

    def test_multiple_hyphens_in_ids(self, temp_dir):
        """Test path resolution with complex IDs containing multiple hyphens."""
        project_root = temp_dir / "planning"

        # Test project with complex ID
        result = resolve_path_for_new_object("project", "user-auth-system", None, project_root)
        expected = project_root / "projects" / "P-user-auth-system" / "project.md"

        assert result == expected

        # Test epic with complex ID
        result = resolve_path_for_new_object(
            "epic", "jwt-token-management", "user-auth-system", project_root
        )
        expected = (
            project_root
            / "projects"
            / "P-user-auth-system"
            / "epics"
            / "E-jwt-token-management"
            / "epic.md"
        )

        assert result == expected

    def test_id_prefix_stripping(self, temp_dir):
        """Test that ID prefixes are properly stripped."""
        project_root = temp_dir / "planning"

        # Test all prefixes are stripped
        test_cases = [
            ("P-test-project", "project"),
            ("E-test-project", "project"),  # Wrong prefix but should still work
            ("F-test-project", "project"),
            ("T-test-project", "project"),
            ("test-project", "project"),  # No prefix
        ]

        for test_id, kind in test_cases:
            result = resolve_path_for_new_object(kind, test_id, None, project_root)
            expected = project_root / "projects" / "P-test-project" / "project.md"
            assert result == expected

    def test_consistency_with_createobject_patterns(self, temp_dir):
        """Test that the function produces paths consistent with createObject patterns."""
        project_root = temp_dir / "planning"

        # Create a complete hierarchy to test against
        project_dir = project_root / "projects" / "P-web-app"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Web App")

        epic_dir = project_dir / "epics" / "E-frontend"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Frontend")

        feature_dir = epic_dir / "features" / "F-ui-components"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# UI Components")

        # Test that resolve_path_for_new_object produces correct paths
        project_path = resolve_path_for_new_object("project", "web-app", None, project_root)
        epic_path = resolve_path_for_new_object("epic", "frontend", "web-app", project_root)
        feature_path = resolve_path_for_new_object(
            "feature", "ui-components", "frontend", project_root
        )
        task_open_path = resolve_path_for_new_object(
            "task", "create-button", "ui-components", project_root, "open"
        )
        task_done_path = resolve_path_for_new_object(
            "task", "create-button", "ui-components", project_root, "done"
        )

        # Verify paths match expected patterns
        assert project_path == project_file
        assert epic_path == epic_file
        assert feature_path == feature_file
        assert task_open_path == feature_dir / "tasks-open" / "T-create-button.md"
        assert task_done_path.parent == feature_dir / "tasks-done"
        assert task_done_path.name.endswith("-T-create-button.md")


class TestResolvePathForNewObjectStandaloneTasks:
    """Test cases for resolve_path_for_new_object function with standalone tasks."""

    def test_standalone_task_open_status(self, temp_dir):
        """Test resolving standalone task path for open status."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "implement-auth", None, project_root, "open")
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_standalone_task_done_status(self, temp_dir):
        """Test resolving standalone task path for done status."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "implement-auth", None, project_root, "done")

        # Should be in tasks-done directory with timestamp prefix
        assert result.parent == project_root / "tasks-done"
        assert result.name.endswith("-T-implement-auth.md")
        assert result.name.startswith("2025")  # Should start with current year

    def test_standalone_task_none_status_defaults_to_open(self, temp_dir):
        """Test resolving standalone task path when status is None (defaults to open)."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "implement-auth", None, project_root, None)
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_standalone_task_empty_parent_defaults_to_open(self, temp_dir):
        """Test resolving standalone task path when parent is empty string (defaults to open)."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "implement-auth", "", project_root)
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_standalone_task_whitespace_parent_defaults_to_open(self, temp_dir):
        """Test resolving standalone task path when parent is whitespace (defaults to open)."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "implement-auth", "   ", project_root)
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_standalone_task_with_prefix_id(self, temp_dir):
        """Test resolving standalone task path when task ID has T- prefix."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "T-implement-auth", None, project_root, "open")
        expected = project_root / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_standalone_task_project_root_contains_planning(self, temp_dir):
        """Test resolving standalone task path when project root contains planning directory."""
        project_root = temp_dir
        planning_dir = project_root / "planning"
        planning_dir.mkdir(parents=True)

        result = resolve_path_for_new_object("task", "implement-auth", None, project_root, "open")
        expected = planning_dir / "tasks-open" / "T-implement-auth.md"

        assert result == expected

    def test_standalone_task_multiple_hyphens_in_id(self, temp_dir):
        """Test resolving standalone task path with complex ID containing multiple hyphens."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object(
            "task", "implement-jwt-auth-system", None, project_root, "open"
        )
        expected = project_root / "tasks-open" / "T-implement-jwt-auth-system.md"

        assert result == expected

    def test_standalone_task_with_numbers_in_id(self, temp_dir):
        """Test resolving standalone task path with numbers in ID."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "task-123-fix", None, project_root, "open")
        expected = project_root / "tasks-open" / "T-task-123-fix.md"

        assert result == expected

    def test_standalone_task_filename_generation_open(self, temp_dir):
        """Test filename generation for open standalone tasks."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "test-task", None, project_root, "open")

        # Should use simple T-{id}.md format
        assert result.name == "T-test-task.md"

    def test_standalone_task_filename_generation_done(self, temp_dir):
        """Test filename generation for done standalone tasks."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "test-task", None, project_root, "done")

        # Should use timestamp-T-{id}.md format
        assert result.name.endswith("-T-test-task.md")
        # Extract timestamp part
        timestamp_part = result.name.split("-T-")[0]
        # Should be in format YYYYMMDD_HHMMSS
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS
        assert timestamp_part[8] == "_"  # Underscore separator
        assert timestamp_part[:8].isdigit()  # Date part should be numeric
        assert timestamp_part[9:].isdigit()  # Time part should be numeric

    def test_standalone_task_directory_structure_open(self, temp_dir):
        """Test directory structure for open standalone tasks."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "test-task", None, project_root, "open")

        # Should be in tasks-open directory
        assert result.parent == project_root / "tasks-open"
        assert result.parent.name == "tasks-open"

    def test_standalone_task_directory_structure_done(self, temp_dir):
        """Test directory structure for done standalone tasks."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "test-task", None, project_root, "done")

        # Should be in tasks-done directory
        assert result.parent == project_root / "tasks-done"
        assert result.parent.name == "tasks-done"

    @pytest.mark.parametrize("status", ["open", "done", None])
    def test_standalone_task_various_statuses(self, temp_dir, status):
        """Test resolving standalone task paths for various status values."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", "test-task", None, project_root, status)

        if status == "done":
            assert result.parent == project_root / "tasks-done"
            assert result.name.endswith("-T-test-task.md")
        else:  # "open" or None
            assert result.parent == project_root / "tasks-open"
            assert result.name == "T-test-task.md"

    @pytest.mark.parametrize(
        "task_id",
        [
            "a",  # Single character
            "1",  # Single digit
            "task-with-hyphens",  # Multiple hyphens
            "task123",  # Numbers
            "task-mixed-case",  # Lowercase with hyphens
            "very-long-task-name-with-many-components",  # Long name
        ],
    )
    def test_standalone_task_edge_case_ids(self, temp_dir, task_id):
        """Test resolving standalone task paths for edge case IDs."""
        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("task", task_id, None, project_root, "open")
        expected = project_root / "tasks-open" / f"T-{task_id}.md"

        assert result == expected

    def test_standalone_task_empty_id_error(self, temp_dir):
        """Test that empty task ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            resolve_path_for_new_object("task", "", None, project_root, "open")

    def test_standalone_task_whitespace_id_error(self, temp_dir):
        """Test that whitespace-only task ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            resolve_path_for_new_object("task", "   ", None, project_root, "open")

    def test_standalone_task_invalid_characters_error(self, temp_dir):
        """Test that invalid characters in task ID raise ValueError."""
        project_root = temp_dir / "planning"

        # Test path traversal attack
        with pytest.raises(ValueError, match="Invalid task ID"):
            resolve_path_for_new_object("task", "../../../etc/passwd", None, project_root, "open")

    def test_standalone_task_path_traversal_error(self, temp_dir):
        """Test that path traversal attempts in task ID raise ValueError."""
        project_root = temp_dir / "planning"

        malicious_ids = [
            "../parent-dir",
            "../../grandparent-dir",
            "../../../etc/passwd",
            "/absolute/path",
            "\\windows\\path",
        ]

        for malicious_id in malicious_ids:
            with pytest.raises(ValueError, match="Invalid task ID"):
                resolve_path_for_new_object("task", malicious_id, None, project_root, "open")

    def test_standalone_task_control_characters_error(self, temp_dir):
        """Test that control characters in task ID raise ValueError."""
        project_root = temp_dir / "planning"

        # Test null byte attack
        with pytest.raises(ValueError, match="Invalid task ID"):
            resolve_path_for_new_object("task", "task\x00", None, project_root, "open")

    def test_standalone_task_reserved_names_error(self, temp_dir):
        """Test that reserved system names in task ID raise ValueError."""
        project_root = temp_dir / "planning"

        reserved_names = ["con", "prn", "aux", "nul", "com1", "lpt1"]

        for reserved_name in reserved_names:
            with pytest.raises(ValueError, match="Invalid task ID"):
                resolve_path_for_new_object("task", reserved_name, None, project_root, "open")

    def test_standalone_task_security_validation_comprehensive(self, temp_dir):
        """Test comprehensive security validation for standalone tasks."""
        project_root = temp_dir / "planning"

        # Test various security threats
        security_threats = [
            "../../../etc/passwd",  # Path traversal
            "/etc/passwd",  # Absolute path
            "\\windows\\system32",  # Windows path
            "task\x00null",  # Null byte injection
            "con",  # Reserved name
            "invalid@chars",  # Invalid characters - special chars
            "Task-Mixed-Case",  # Invalid characters - uppercase
            "task_with_underscores",  # Invalid characters - underscores
        ]

        for threat in security_threats:
            with pytest.raises(ValueError, match="Invalid task ID"):
                resolve_path_for_new_object("task", threat, None, project_root, "open")

    def test_standalone_task_consistency_with_hierarchy_tasks(self, temp_dir):
        """Test that standalone tasks work alongside hierarchy-based tasks."""
        project_root = temp_dir / "planning"

        # Create hierarchy structure
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

        # Test hierarchy task path
        hierarchy_task_path = resolve_path_for_new_object(
            "task", "hierarchy-task", "test-feature", project_root, "open"
        )

        # Test standalone task path
        standalone_task_path = resolve_path_for_new_object(
            "task", "standalone-task", None, project_root, "open"
        )

        # Should be in different locations
        assert hierarchy_task_path.parent == feature_dir / "tasks-open"
        assert standalone_task_path.parent == project_root / "tasks-open"

        # Both should have proper filenames
        assert hierarchy_task_path.name == "T-hierarchy-task.md"
        assert standalone_task_path.name == "T-standalone-task.md"

    def test_standalone_task_integration_with_existing_functions(self, temp_dir):
        """Test integration between standalone task paths and existing functions."""
        from trellis_mcp.path_resolver import construct_standalone_task_path

        project_root = temp_dir / "planning"
        task_id = "integration-test"

        # Both functions should produce identical results for open tasks
        resolve_path = resolve_path_for_new_object("task", task_id, None, project_root, "open")
        construct_path = construct_standalone_task_path(task_id, "open", project_root)

        assert resolve_path == construct_path

        # Both functions should produce compatible results for done tasks
        resolve_path_done = resolve_path_for_new_object("task", task_id, None, project_root, "done")
        construct_path_done = construct_standalone_task_path(task_id, "done", project_root)

        # Directory should be the same
        assert resolve_path_done.parent == construct_path_done.parent
        # Both should end with same suffix
        assert resolve_path_done.name.endswith("-T-integration-test.md")
        assert construct_path_done.name.endswith("-T-integration-test.md")

    def test_standalone_task_timestamp_uniqueness(self, temp_dir):
        """Test that done task timestamps are unique for multiple calls."""
        project_root = temp_dir / "planning"
        task_id = "timestamp-test"

        # Create first done task
        path1 = resolve_path_for_new_object("task", task_id, None, project_root, "done")

        # Wait a full second to ensure different timestamps
        time.sleep(1.1)

        # Create second done task
        path2 = resolve_path_for_new_object("task", task_id, None, project_root, "done")

        # Should have different filenames due to timestamps
        assert path1.name != path2.name
        # But same directory and suffix
        assert path1.parent == path2.parent
        assert path1.name.endswith("-T-timestamp-test.md")
        assert path2.name.endswith("-T-timestamp-test.md")

    def test_standalone_task_path_resolution_root_handling(self, temp_dir):
        """Test that standalone tasks handle different path resolution root scenarios."""
        # Test scenario 1: project root contains planning directory
        project_root1 = temp_dir / "scenario1"
        planning_dir1 = project_root1 / "planning"
        planning_dir1.mkdir(parents=True)

        result1 = resolve_path_for_new_object("task", "test-task", None, project_root1, "open")
        expected1 = planning_dir1 / "tasks-open" / "T-test-task.md"
        assert result1 == expected1

        # Test scenario 2: project root IS the planning directory
        project_root2 = temp_dir / "scenario2"
        project_root2.mkdir(parents=True)

        result2 = resolve_path_for_new_object("task", "test-task", None, project_root2, "open")
        expected2 = project_root2 / "tasks-open" / "T-test-task.md"
        assert result2 == expected2

    def test_standalone_task_prefix_stripping_consistency(self, temp_dir):
        """Test that task ID prefix stripping works consistently."""
        project_root = temp_dir / "planning"

        # Test all possible prefixes are stripped consistently
        test_cases = [
            ("T-test-task", "T-test-task.md"),
            ("test-task", "T-test-task.md"),  # No prefix
        ]

        for input_id, expected_filename in test_cases:
            result = resolve_path_for_new_object("task", input_id, None, project_root, "open")
            assert result.name == expected_filename
            assert result.parent == project_root / "tasks-open"
