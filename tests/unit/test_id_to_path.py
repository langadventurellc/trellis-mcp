"""Tests for id_to_path function from path resolution utilities.

Tests the id_to_path function that converts object IDs to filesystem paths
within the hierarchical project structure.
"""

import pytest

from trellis_mcp.path_resolver import id_to_path


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
