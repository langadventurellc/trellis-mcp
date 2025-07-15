"""Tests for path resolution utilities module.

Tests the id_to_path function that converts object IDs to filesystem paths
within the hierarchical project structure.
"""

import pytest

from trellis_mcp.path_resolver import id_to_path, path_to_id


class TestIdToPath:
    """Test cases for the id_to_path function."""

    def test_project_path_resolution(self, temp_dir):
        """Test resolving project paths."""
        project_root = temp_dir / "planning"

        # Create a project structure
        project_dir = project_root / "projects" / "P-user-auth"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# User Auth Project")

        # Test resolving the project path
        result = id_to_path(project_root, "project", "user-auth")
        assert result == project_file
        assert result.exists()

    def test_project_path_with_prefix(self, temp_dir):
        """Test resolving project paths when ID has prefix."""
        project_root = temp_dir / "planning"

        # Create a project structure
        project_dir = project_root / "projects" / "P-user-auth"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# User Auth Project")

        # Test resolving with P- prefix (should be stripped)
        result = id_to_path(project_root, "project", "P-user-auth")
        assert result == project_file
        assert result.exists()

    def test_epic_path_resolution(self, temp_dir):
        """Test resolving epic paths."""
        project_root = temp_dir / "planning"

        # Create an epic structure
        epic_dir = project_root / "projects" / "P-user-auth" / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Authentication Epic")

        # Test resolving the epic path
        result = id_to_path(project_root, "epic", "authentication")
        assert result == epic_file
        assert result.exists()

    def test_feature_path_resolution(self, temp_dir):
        """Test resolving feature paths."""
        project_root = temp_dir / "planning"

        # Create a feature structure
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

        # Test resolving the feature path
        result = id_to_path(project_root, "feature", "login")
        assert result == feature_file
        assert result.exists()

    def test_task_path_resolution_open(self, temp_dir):
        """Test resolving task paths in tasks-open directory."""
        project_root = temp_dir / "planning"

        # Create a task structure in tasks-open
        task_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-open"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-implement-jwt.md"
        task_file.write_text("# Implement JWT Task")

        # Test resolving the task path
        result = id_to_path(project_root, "task", "implement-jwt")
        assert result == task_file
        assert result.exists()

    def test_task_path_resolution_done(self, temp_dir):
        """Test resolving task paths in tasks-done directory."""
        project_root = temp_dir / "planning"

        # Create a task structure in tasks-done
        task_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-done"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "2025-07-13T19:12:00-05:00-T-implement-jwt.md"
        task_file.write_text("# Implement JWT Task")

        # Test resolving the task path
        result = id_to_path(project_root, "task", "implement-jwt")
        assert result == task_file
        assert result.exists()

    def test_task_prefers_open_over_done(self, temp_dir):
        """Test that tasks-open is preferred over tasks-done."""
        project_root = temp_dir / "planning"

        # Create both open and done task files
        base_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
        )

        open_dir = base_dir / "tasks-open"
        open_dir.mkdir(parents=True)
        open_file = open_dir / "T-implement-jwt.md"
        open_file.write_text("# Open Task")

        done_dir = base_dir / "tasks-done"
        done_dir.mkdir(parents=True)
        done_file = done_dir / "2025-07-13T19:12:00-05:00-T-implement-jwt.md"
        done_file.write_text("# Done Task")

        # Should return the open task file
        result = id_to_path(project_root, "task", "implement-jwt")
        assert result == open_file
        assert result.exists()

    def test_invalid_kind_error(self, temp_dir):
        """Test that invalid kinds raise ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind 'invalid'"):
            id_to_path(project_root, "invalid", "some-id")

    def test_empty_kind_error(self, temp_dir):
        """Test that empty kind raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind ''"):
            id_to_path(project_root, "", "some-id")

    def test_empty_id_error(self, temp_dir):
        """Test that empty ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            id_to_path(project_root, "project", "")

    def test_whitespace_id_error(self, temp_dir):
        """Test that whitespace-only ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            id_to_path(project_root, "project", "   ")

    def test_project_not_found_error(self, temp_dir):
        """Test that non-existent project raises FileNotFoundError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Project with ID 'nonexistent' not found"):
            id_to_path(project_root, "project", "nonexistent")

    def test_epic_not_found_error(self, temp_dir):
        """Test that non-existent epic raises FileNotFoundError."""
        project_root = temp_dir / "planning"

        # Create projects directory but no epics
        projects_dir = project_root / "projects"
        projects_dir.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Epic with ID 'nonexistent' not found"):
            id_to_path(project_root, "epic", "nonexistent")

    def test_feature_not_found_error(self, temp_dir):
        """Test that non-existent feature raises FileNotFoundError."""
        project_root = temp_dir / "planning"

        # Create projects directory but no features
        projects_dir = project_root / "projects"
        projects_dir.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Feature with ID 'nonexistent' not found"):
            id_to_path(project_root, "feature", "nonexistent")

    def test_task_not_found_error(self, temp_dir):
        """Test that non-existent task raises FileNotFoundError."""
        project_root = temp_dir / "planning"

        # Create projects directory but no tasks
        projects_dir = project_root / "projects"
        projects_dir.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Task with ID 'nonexistent' not found"):
            id_to_path(project_root, "task", "nonexistent")

    def test_no_projects_directory(self, temp_dir):
        """Test behavior when projects directory doesn't exist."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Test epic without projects directory
        with pytest.raises(
            FileNotFoundError,
            match="Epic with ID 'test' not found: projects directory does not exist",
        ):
            id_to_path(project_root, "epic", "test")

    def test_multiple_projects_epic_resolution(self, temp_dir):
        """Test that epics can be found across multiple projects."""
        project_root = temp_dir / "planning"

        # Create first project without the epic
        project1_dir = project_root / "projects" / "P-project1"
        project1_dir.mkdir(parents=True)

        # Create second project with the epic
        epic_dir = project_root / "projects" / "P-project2" / "epics" / "E-shared-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Shared Epic")

        # Should find the epic in project2
        result = id_to_path(project_root, "epic", "shared-epic")
        assert result == epic_file
        assert result.exists()

    def test_multiple_levels_feature_resolution(self, temp_dir):
        """Test that features can be found across multiple projects and epics."""
        project_root = temp_dir / "planning"

        # Create complex structure with multiple levels
        feature_dir = (
            project_root
            / "projects"
            / "P-project1"
            / "epics"
            / "E-epic1"
            / "features"
            / "F-shared-feature"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Shared Feature")

        # Should find the feature
        result = id_to_path(project_root, "feature", "shared-feature")
        assert result == feature_file
        assert result.exists()

    def test_id_prefix_stripping(self, temp_dir):
        """Test that ID prefixes are properly stripped."""
        project_root = temp_dir / "planning"

        # Create project
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Test Project")

        # Test all prefixes are stripped
        test_cases = [
            ("P-test-project", "project"),
            ("E-test-project", "project"),  # Wrong prefix but should still work
            ("F-test-project", "project"),
            ("T-test-project", "project"),
            ("test-project", "project"),  # No prefix
        ]

        for test_id, kind in test_cases:
            result = id_to_path(project_root, kind, test_id)
            assert result == project_file
            assert result.exists()

    def test_complex_hierarchy_resolution(self, temp_dir):
        """Test resolving objects in a complex hierarchy."""
        project_root = temp_dir / "planning"

        # Create complex project structure
        base_path = project_root / "projects" / "P-ecommerce" / "epics" / "E-user-management"

        # Create feature and task
        feature_dir = base_path / "features" / "F-user-profile"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# User Profile Feature")

        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()
        task_file = task_dir / "T-update-avatar.md"
        task_file.write_text("# Update Avatar Task")

        # Test resolving both feature and task
        feature_result = id_to_path(project_root, "feature", "user-profile")
        task_result = id_to_path(project_root, "task", "update-avatar")

        assert feature_result == feature_file
        assert task_result == task_file
        assert feature_result.exists()
        assert task_result.exists()

    def test_edge_case_empty_directories(self, temp_dir):
        """Test behavior with empty directories in the hierarchy."""
        project_root = temp_dir / "planning"

        # Create empty directory structure
        empty_project = project_root / "projects" / "P-empty"
        empty_project.mkdir(parents=True)

        empty_epic = project_root / "projects" / "P-another" / "epics" / "E-empty"
        empty_epic.mkdir(parents=True)

        # These should not interfere with finding actual objects
        actual_project = project_root / "projects" / "P-real"
        actual_project.mkdir(parents=True)
        actual_file = actual_project / "project.md"
        actual_file.write_text("# Real Project")

        result = id_to_path(project_root, "project", "real")
        assert result == actual_file
        assert result.exists()


class TestPathToId:
    """Test cases for the path_to_id function."""

    def test_project_path_to_id(self, temp_dir):
        """Test converting project path to ID."""
        project_root = temp_dir / "planning"

        # Create a project structure
        project_dir = project_root / "projects" / "P-user-auth"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# User Auth Project")

        # Test converting path to ID
        kind, obj_id = path_to_id(project_file)
        assert kind == "project"
        assert obj_id == "user-auth"

    def test_epic_path_to_id(self, temp_dir):
        """Test converting epic path to ID."""
        project_root = temp_dir / "planning"

        # Create an epic structure
        epic_dir = project_root / "projects" / "P-user-auth" / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Authentication Epic")

        # Test converting path to ID
        kind, obj_id = path_to_id(epic_file)
        assert kind == "epic"
        assert obj_id == "authentication"

    def test_feature_path_to_id(self, temp_dir):
        """Test converting feature path to ID."""
        project_root = temp_dir / "planning"

        # Create a feature structure
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

        # Test converting path to ID
        kind, obj_id = path_to_id(feature_file)
        assert kind == "feature"
        assert obj_id == "login"

    def test_task_open_path_to_id(self, temp_dir):
        """Test converting task path (tasks-open) to ID."""
        project_root = temp_dir / "planning"

        # Create a task structure in tasks-open
        task_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-open"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-implement-jwt.md"
        task_file.write_text("# Implement JWT Task")

        # Test converting path to ID
        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "implement-jwt"

    def test_task_done_path_to_id(self, temp_dir):
        """Test converting task path (tasks-done) to ID."""
        project_root = temp_dir / "planning"

        # Create a task structure in tasks-done
        task_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-login"
            / "tasks-done"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "2025-07-13T19:12:00-05:00-T-implement-jwt.md"
        task_file.write_text("# Implement JWT Task")

        # Test converting path to ID
        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "implement-jwt"

    def test_path_to_id_non_existent_file(self, temp_dir):
        """Test that non-existent file raises FileNotFoundError."""
        project_root = temp_dir / "planning"
        non_existent_file = project_root / "nonexistent.md"

        with pytest.raises(FileNotFoundError, match="File not found"):
            path_to_id(non_existent_file)

    def test_path_to_id_directory_not_file(self, temp_dir):
        """Test that directory path raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(ValueError, match="Path is not a file"):
            path_to_id(project_root)

    def test_path_to_id_unrecognized_file_type(self, temp_dir):
        """Test that unrecognized file type raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create an unrecognized file
        unknown_file = project_root / "unknown.txt"
        unknown_file.write_text("Unknown file")

        with pytest.raises(ValueError, match="Unrecognized file type"):
            path_to_id(unknown_file)

    def test_path_to_id_invalid_project_structure(self, temp_dir):
        """Test that invalid project structure raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create a project.md file without proper P- directory
        invalid_file = project_root / "project.md"
        invalid_file.write_text("# Invalid Project")

        with pytest.raises(ValueError, match="Could not find project ID in path"):
            path_to_id(invalid_file)

    def test_path_to_id_invalid_epic_structure(self, temp_dir):
        """Test that invalid epic structure raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create an epic.md file without proper E- directory
        invalid_file = project_root / "epic.md"
        invalid_file.write_text("# Invalid Epic")

        with pytest.raises(ValueError, match="Could not find epic ID in path"):
            path_to_id(invalid_file)

    def test_path_to_id_invalid_feature_structure(self, temp_dir):
        """Test that invalid feature structure raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create a feature.md file without proper F- directory
        invalid_file = project_root / "feature.md"
        invalid_file.write_text("# Invalid Feature")

        with pytest.raises(ValueError, match="Could not find feature ID in path"):
            path_to_id(invalid_file)

    def test_path_to_id_invalid_task_done_structure(self, temp_dir):
        """Test that invalid task-done structure raises ValueError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create a task done file without proper T- prefix
        invalid_file = project_root / "2025-07-13T19:12:00-05:00-invalid-task.md"
        invalid_file.write_text("# Invalid Task")

        with pytest.raises(ValueError, match="Unrecognized file type"):
            path_to_id(invalid_file)

    def test_path_to_id_round_trip_project(self, temp_dir):
        """Test round-trip conversion for project."""
        project_root = temp_dir / "planning"

        # Create a project structure
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Test Project")

        # Round-trip test
        file_path = id_to_path(project_root, "project", "test-project")
        kind, obj_id = path_to_id(file_path)

        assert kind == "project"
        assert obj_id == "test-project"

        # Verify we can go back to the original path
        new_path = id_to_path(project_root, kind, obj_id)
        assert new_path == file_path

    def test_path_to_id_round_trip_epic(self, temp_dir):
        """Test round-trip conversion for epic."""
        project_root = temp_dir / "planning"

        # Create an epic structure
        epic_dir = project_root / "projects" / "P-test-project" / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Test Epic")

        # Round-trip test
        file_path = id_to_path(project_root, "epic", "test-epic")
        kind, obj_id = path_to_id(file_path)

        assert kind == "epic"
        assert obj_id == "test-epic"

        # Verify we can go back to the original path
        new_path = id_to_path(project_root, kind, obj_id)
        assert new_path == file_path

    def test_path_to_id_round_trip_feature(self, temp_dir):
        """Test round-trip conversion for feature."""
        project_root = temp_dir / "planning"

        # Create a feature structure
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

        # Round-trip test
        file_path = id_to_path(project_root, "feature", "test-feature")
        kind, obj_id = path_to_id(file_path)

        assert kind == "feature"
        assert obj_id == "test-feature"

        # Verify we can go back to the original path
        new_path = id_to_path(project_root, kind, obj_id)
        assert new_path == file_path

    def test_path_to_id_round_trip_task_open(self, temp_dir):
        """Test round-trip conversion for task (tasks-open)."""
        project_root = temp_dir / "planning"

        # Create a task structure in tasks-open
        task_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-open"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-test-task.md"
        task_file.write_text("# Test Task")

        # Round-trip test
        file_path = id_to_path(project_root, "task", "test-task")
        kind, obj_id = path_to_id(file_path)

        assert kind == "task"
        assert obj_id == "test-task"

        # Verify we can go back to the original path
        new_path = id_to_path(project_root, kind, obj_id)
        assert new_path == file_path

    def test_path_to_id_round_trip_task_done(self, temp_dir):
        """Test round-trip conversion for task (tasks-done)."""
        project_root = temp_dir / "planning"

        # Create a task structure in tasks-done
        task_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-done"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "2025-07-13T19:12:00-05:00-T-test-task.md"
        task_file.write_text("# Test Task")

        # Round-trip test
        file_path = id_to_path(project_root, "task", "test-task")
        kind, obj_id = path_to_id(file_path)

        assert kind == "task"
        assert obj_id == "test-task"

        # Verify we can go back to the original path
        new_path = id_to_path(project_root, kind, obj_id)
        assert new_path == file_path

    def test_path_to_id_complex_ids(self, temp_dir):
        """Test path_to_id with complex IDs containing hyphens."""
        project_root = temp_dir / "planning"

        # Create objects with complex IDs
        project_dir = project_root / "projects" / "P-user-auth-system"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# User Auth System")

        epic_dir = project_dir / "epics" / "E-jwt-token-management"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# JWT Token Management")

        feature_dir = epic_dir / "features" / "F-refresh-token-flow"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Refresh Token Flow")

        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()
        task_file = task_dir / "T-implement-token-refresh-endpoint.md"
        task_file.write_text("# Implement Token Refresh Endpoint")

        # Test all complex IDs
        kind, obj_id = path_to_id(project_file)
        assert kind == "project"
        assert obj_id == "user-auth-system"

        kind, obj_id = path_to_id(epic_file)
        assert kind == "epic"
        assert obj_id == "jwt-token-management"

        kind, obj_id = path_to_id(feature_file)
        assert kind == "feature"
        assert obj_id == "refresh-token-flow"

        kind, obj_id = path_to_id(task_file)
        assert kind == "task"
        assert obj_id == "implement-token-refresh-endpoint"


class TestRoundTripConversion:
    """Test cases specifically for round-trip conversion between IDs and paths.

    These tests ensure the invariant:
    path_to_id(id_to_path(project_root, kind, obj_id)) == (kind, obj_id)
    for all object kinds (P/E/F/T) and various edge cases.
    """

    @pytest.mark.parametrize(
        "kind,obj_id",
        [
            ("project", "simple-project"),
            ("epic", "simple-epic"),
            ("feature", "simple-feature"),
            ("task", "simple-task"),
        ],
    )
    def test_round_trip_simple_ids(self, temp_dir, kind, obj_id):
        """Test round-trip conversion for simple IDs across all object kinds."""
        project_root = temp_dir / "planning"

        # Create the necessary directory structure based on object kind
        if kind == "project":
            obj_dir = project_root / "projects" / f"P-{obj_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "project.md"
            obj_file.write_text(f"# {obj_id.title()} Project")
        elif kind == "epic":
            obj_dir = project_root / "projects" / "P-test-project" / "epics" / f"E-{obj_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "epic.md"
            obj_file.write_text(f"# {obj_id.title()} Epic")
        elif kind == "feature":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / f"F-{obj_id}"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "feature.md"
            obj_file.write_text(f"# {obj_id.title()} Feature")
        elif kind == "task":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / "F-test-feature"
                / "tasks-open"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / f"T-{obj_id}.md"
            obj_file.write_text(f"# {obj_id.title()} Task")

        # Test round-trip conversion
        file_path = id_to_path(project_root, kind, obj_id)
        result_kind, result_id = path_to_id(file_path)

        assert result_kind == kind
        assert result_id == obj_id

    @pytest.mark.parametrize(
        "kind,obj_id",
        [
            ("project", "complex-user-auth-system"),
            ("epic", "jwt-token-management-epic"),
            ("feature", "refresh-token-flow-feature"),
            ("task", "implement-token-refresh-endpoint-task"),
        ],
    )
    def test_round_trip_complex_ids(self, temp_dir, kind, obj_id):
        """Test round-trip conversion for complex IDs with hyphens."""
        project_root = temp_dir / "planning"

        # Create the necessary directory structure based on object kind
        if kind == "project":
            obj_dir = project_root / "projects" / f"P-{obj_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "project.md"
            obj_file.write_text("# Complex Project")
        elif kind == "epic":
            obj_dir = project_root / "projects" / "P-test-project" / "epics" / f"E-{obj_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "epic.md"
            obj_file.write_text("# Complex Epic")
        elif kind == "feature":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / f"F-{obj_id}"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "feature.md"
            obj_file.write_text("# Complex Feature")
        elif kind == "task":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / "F-test-feature"
                / "tasks-open"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / f"T-{obj_id}.md"
            obj_file.write_text("# Complex Task")

        # Test round-trip conversion
        file_path = id_to_path(project_root, kind, obj_id)
        result_kind, result_id = path_to_id(file_path)

        assert result_kind == kind
        assert result_id == obj_id

    @pytest.mark.parametrize(
        "kind,obj_id_with_prefix",
        [
            ("project", "P-prefixed-project"),
            ("epic", "E-prefixed-epic"),
            ("feature", "F-prefixed-feature"),
            ("task", "T-prefixed-task"),
        ],
    )
    def test_round_trip_ids_with_prefixes(self, temp_dir, kind, obj_id_with_prefix):
        """Test round-trip conversion for IDs that include prefixes."""
        project_root = temp_dir / "planning"

        # Extract the clean ID (without prefix)
        clean_id = obj_id_with_prefix[2:]  # Remove P-, E-, F-, or T-

        # Create the necessary directory structure based on object kind
        if kind == "project":
            obj_dir = project_root / "projects" / f"P-{clean_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "project.md"
            obj_file.write_text("# Prefixed Project")
        elif kind == "epic":
            obj_dir = project_root / "projects" / "P-test-project" / "epics" / f"E-{clean_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "epic.md"
            obj_file.write_text("# Prefixed Epic")
        elif kind == "feature":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / f"F-{clean_id}"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "feature.md"
            obj_file.write_text("# Prefixed Feature")
        elif kind == "task":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / "F-test-feature"
                / "tasks-open"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / f"T-{clean_id}.md"
            obj_file.write_text("# Prefixed Task")

        # Test round-trip conversion using the ID with prefix
        file_path = id_to_path(project_root, kind, obj_id_with_prefix)
        result_kind, result_id = path_to_id(file_path)

        assert result_kind == kind
        assert result_id == clean_id  # Should return clean ID without prefix

    def test_round_trip_task_in_done_directory(self, temp_dir):
        """Test round-trip conversion for tasks in tasks-done directory."""
        project_root = temp_dir / "planning"

        # Create a task in tasks-done directory
        task_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-done"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "2025-07-13T19:12:00-05:00-T-completed-task.md"
        task_file.write_text("# Completed Task")

        # Test round-trip conversion
        file_path = id_to_path(project_root, "task", "completed-task")
        result_kind, result_id = path_to_id(file_path)

        assert result_kind == "task"
        assert result_id == "completed-task"

    def test_round_trip_tasks_prefer_open_over_done(self, temp_dir):
        """Test that round-trip conversion prefers tasks-open over tasks-done."""
        project_root = temp_dir / "planning"

        # Create task in both directories
        base_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
        )

        # Create in tasks-open
        open_dir = base_dir / "tasks-open"
        open_dir.mkdir(parents=True)
        open_file = open_dir / "T-duplicate-task.md"
        open_file.write_text("# Open Task")

        # Create in tasks-done
        done_dir = base_dir / "tasks-done"
        done_dir.mkdir(parents=True)
        done_file = done_dir / "2025-07-13T19:12:00-05:00-T-duplicate-task.md"
        done_file.write_text("# Done Task")

        # Test round-trip conversion - should prefer open task
        file_path = id_to_path(project_root, "task", "duplicate-task")
        result_kind, result_id = path_to_id(file_path)

        assert result_kind == "task"
        assert result_id == "duplicate-task"
        # Verify it found the open task, not the done task
        assert file_path == open_file

    @pytest.mark.parametrize(
        "kind,obj_id",
        [
            ("project", "a"),  # Single character
            ("epic", "1"),  # Single digit
            ("feature", "x-y-z"),  # Multiple hyphens
            ("task", "very-long-task-name-with-many-hyphens"),
        ],
    )
    def test_round_trip_edge_case_ids(self, temp_dir, kind, obj_id):
        """Test round-trip conversion for edge case IDs."""
        project_root = temp_dir / "planning"

        # Create the necessary directory structure based on object kind
        if kind == "project":
            obj_dir = project_root / "projects" / f"P-{obj_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "project.md"
            obj_file.write_text("# Edge Case Project")
        elif kind == "epic":
            obj_dir = project_root / "projects" / "P-test-project" / "epics" / f"E-{obj_id}"
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "epic.md"
            obj_file.write_text("# Edge Case Epic")
        elif kind == "feature":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / f"F-{obj_id}"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / "feature.md"
            obj_file.write_text("# Edge Case Feature")
        elif kind == "task":
            obj_dir = (
                project_root
                / "projects"
                / "P-test-project"
                / "epics"
                / "E-test-epic"
                / "features"
                / "F-test-feature"
                / "tasks-open"
            )
            obj_dir.mkdir(parents=True)
            obj_file = obj_dir / f"T-{obj_id}.md"
            obj_file.write_text("# Edge Case Task")

        # Test round-trip conversion
        file_path = id_to_path(project_root, kind, obj_id)
        result_kind, result_id = path_to_id(file_path)

        assert result_kind == kind
        assert result_id == obj_id

    def test_round_trip_comprehensive_hierarchy(self, temp_dir):
        """Test round-trip conversion in a complex hierarchy with all object kinds."""
        project_root = temp_dir / "planning"

        # Create a complete hierarchy
        project_id = "ecommerce-platform"
        epic_id = "user-management"
        feature_id = "user-profile"
        task_id = "update-avatar"

        # Create project
        project_dir = project_root / "projects" / f"P-{project_id}"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# E-commerce Platform")

        # Create epic
        epic_dir = project_dir / "epics" / f"E-{epic_id}"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# User Management")

        # Create feature
        feature_dir = epic_dir / "features" / f"F-{feature_id}"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# User Profile")

        # Create task
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()
        task_file = task_dir / f"T-{task_id}.md"
        task_file.write_text("# Update Avatar")

        # Test round-trip conversion for all objects
        test_cases = [
            ("project", project_id),
            ("epic", epic_id),
            ("feature", feature_id),
            ("task", task_id),
        ]

        for kind, obj_id in test_cases:
            file_path = id_to_path(project_root, kind, obj_id)
            result_kind, result_id = path_to_id(file_path)

            assert result_kind == kind
            assert result_id == obj_id


class TestResolvePathForNewObject:
    """Test cases for the resolve_path_for_new_object function."""

    def test_project_path_resolution(self, temp_dir):
        """Test resolving project paths for new objects."""
        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("project", "user-auth", None, project_root)
        expected = project_root / "projects" / "P-user-auth" / "project.md"

        assert result == expected

    def test_project_with_prefix_id(self, temp_dir):
        """Test project path resolution when ID has prefix."""
        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("project", "P-user-auth", None, project_root)
        expected = project_root / "projects" / "P-user-auth" / "project.md"

        assert result == expected

    def test_epic_path_resolution(self, temp_dir):
        """Test resolving epic paths for new objects."""
        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("epic", "authentication", "user-auth", project_root)
        expected = (
            project_root / "projects" / "P-user-auth" / "epics" / "E-authentication" / "epic.md"
        )

        assert result == expected

    def test_epic_with_prefix_parent(self, temp_dir):
        """Test epic path resolution when parent ID has prefix."""
        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        result = resolve_path_for_new_object("epic", "authentication", "P-user-auth", project_root)
        expected = (
            project_root / "projects" / "P-user-auth" / "epics" / "E-authentication" / "epic.md"
        )

        assert result == expected

    def test_feature_path_resolution(self, temp_dir):
        """Test resolving feature paths for new objects."""
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind 'invalid'"):
            resolve_path_for_new_object("invalid", "some-id", None, project_root)

    def test_empty_kind_error(self, temp_dir):
        """Test that empty kind raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind ''"):
            resolve_path_for_new_object("", "some-id", None, project_root)

    def test_empty_id_error(self, temp_dir):
        """Test that empty ID raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            resolve_path_for_new_object("project", "", None, project_root)

    def test_whitespace_id_error(self, temp_dir):
        """Test that whitespace-only ID raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            resolve_path_for_new_object("project", "   ", None, project_root)

    def test_epic_missing_parent_error(self, temp_dir):
        """Test that epic without parent raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Parent is required for epic objects"):
            resolve_path_for_new_object("epic", "some-epic", None, project_root)

    def test_feature_missing_parent_error(self, temp_dir):
        """Test that feature without parent raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Parent is required for feature objects"):
            resolve_path_for_new_object("feature", "some-feature", None, project_root)

    def test_task_missing_parent_error(self, temp_dir):
        """Test that task without parent raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Parent is required for task objects"):
            resolve_path_for_new_object("task", "some-task", None, project_root)

    def test_feature_nonexistent_parent_error(self, temp_dir):
        """Test that feature with nonexistent parent raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(ValueError, match="Parent epic 'nonexistent' not found"):
            resolve_path_for_new_object("feature", "some-feature", "nonexistent", project_root)

    def test_task_nonexistent_parent_error(self, temp_dir):
        """Test that task with nonexistent parent raises ValueError."""
        import pytest

        from trellis_mcp.path_resolver import resolve_path_for_new_object

        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(ValueError, match="Parent feature 'nonexistent' not found"):
            resolve_path_for_new_object("task", "some-task", "nonexistent", project_root)

    def test_complex_hierarchy_path_resolution(self, temp_dir):
        """Test resolving paths in a complex hierarchy."""
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
        from trellis_mcp.path_resolver import resolve_path_for_new_object

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
