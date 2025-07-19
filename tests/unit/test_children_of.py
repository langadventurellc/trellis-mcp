"""Tests for children_of function from path resolution utilities.

Tests the children_of function that finds all descendant objects within
the hierarchical project structure.
"""

import pytest

from trellis_mcp.path_resolver import children_of


class TestChildrenOf:
    """Test cases for the children_of function."""

    def test_project_children_complete_hierarchy(self, temp_dir):
        """Test finding all children of a project with complete hierarchy."""
        project_root = temp_dir / "planning"

        # Create complete hierarchy
        project_dir = project_root / "projects" / "P-user-auth"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# User Auth Project")

        # Create epic
        epic_dir = project_dir / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Authentication Epic")

        # Create feature
        feature_dir = epic_dir / "features" / "F-login"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Login Feature")

        # Create tasks
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_open_dir.mkdir()
        task_open_file = tasks_open_dir / "T-implement-jwt.md"
        task_open_file.write_text("# Implement JWT Task")

        tasks_done_dir = feature_dir / "tasks-done"
        tasks_done_dir.mkdir()
        task_done_file = tasks_done_dir / "2025-07-13T19:12:00-05:00-T-setup-auth.md"
        task_done_file.write_text("# Setup Auth Task")

        # Test finding all children of project
        result = children_of("project", "user-auth", project_root)

        # Should return all descendant paths
        expected_paths = [epic_file, feature_file, task_open_file, task_done_file]
        assert len(result) == len(expected_paths)
        for path in expected_paths:
            assert path in result

    def test_project_children_multiple_epics(self, temp_dir):
        """Test finding children of a project with multiple epics."""
        project_root = temp_dir / "planning"

        # Create project with two epics
        project_dir = project_root / "projects" / "P-ecommerce"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Ecommerce Project")

        # Epic 1
        epic1_dir = project_dir / "epics" / "E-user-management"
        epic1_dir.mkdir(parents=True)
        epic1_file = epic1_dir / "epic.md"
        epic1_file.write_text("# User Management Epic")

        # Epic 2
        epic2_dir = project_dir / "epics" / "E-payment"
        epic2_dir.mkdir(parents=True)
        epic2_file = epic2_dir / "epic.md"
        epic2_file.write_text("# Payment Epic")

        # Test finding all children
        result = children_of("project", "ecommerce", project_root)

        # Should return both epics
        assert len(result) == 2
        assert epic1_file in result
        assert epic2_file in result

    def test_epic_children_complete_hierarchy(self, temp_dir):
        """Test finding all children of an epic with complete hierarchy."""
        project_root = temp_dir / "planning"

        # Create epic structure
        epic_dir = project_root / "projects" / "P-user-auth" / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Authentication Epic")

        # Create two features
        feature1_dir = epic_dir / "features" / "F-login"
        feature1_dir.mkdir(parents=True)
        feature1_file = feature1_dir / "feature.md"
        feature1_file.write_text("# Login Feature")

        feature2_dir = epic_dir / "features" / "F-registration"
        feature2_dir.mkdir(parents=True)
        feature2_file = feature2_dir / "feature.md"
        feature2_file.write_text("# Registration Feature")

        # Create tasks under first feature
        tasks_open_dir = feature1_dir / "tasks-open"
        tasks_open_dir.mkdir()
        task_file = tasks_open_dir / "T-implement-jwt.md"
        task_file.write_text("# Implement JWT Task")

        # Test finding all children of epic
        result = children_of("epic", "authentication", project_root)

        # Should return features and tasks
        expected_paths = [feature1_file, feature2_file, task_file]
        assert len(result) == len(expected_paths)
        for path in expected_paths:
            assert path in result

    def test_feature_children_tasks_only(self, temp_dir):
        """Test finding children of a feature (only tasks)."""
        project_root = temp_dir / "planning"

        # Create feature structure
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

        # Create tasks
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_open_dir.mkdir()
        task_open_file = tasks_open_dir / "T-implement-jwt.md"
        task_open_file.write_text("# Implement JWT Task")

        tasks_done_dir = feature_dir / "tasks-done"
        tasks_done_dir.mkdir()
        task_done_file = tasks_done_dir / "2025-07-13T19:12:00-05:00-T-setup-auth.md"
        task_done_file.write_text("# Setup Auth Task")

        # Test finding children of feature
        result = children_of("feature", "login", project_root)

        # Should return only tasks
        assert len(result) == 2
        assert task_open_file in result
        assert task_done_file in result

    def test_task_children_empty(self, temp_dir):
        """Test that tasks have no children."""
        project_root = temp_dir / "planning"

        # Create task structure
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

        # Test finding children of task
        result = children_of("task", "implement-jwt", project_root)

        # Should return empty list
        assert result == []

    def test_project_children_empty_project(self, temp_dir):
        """Test finding children of an empty project."""
        project_root = temp_dir / "planning"

        # Create empty project
        project_dir = project_root / "projects" / "P-empty"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Empty Project")

        # Test finding children
        result = children_of("project", "empty", project_root)

        # Should return empty list
        assert result == []

    def test_epic_children_empty_epic(self, temp_dir):
        """Test finding children of an empty epic."""
        project_root = temp_dir / "planning"

        # Create empty epic
        epic_dir = project_root / "projects" / "P-user-auth" / "epics" / "E-empty"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Empty Epic")

        # Test finding children
        result = children_of("epic", "empty", project_root)

        # Should return empty list
        assert result == []

    def test_feature_children_empty_feature(self, temp_dir):
        """Test finding children of an empty feature."""
        project_root = temp_dir / "planning"

        # Create empty feature
        feature_dir = (
            project_root
            / "projects"
            / "P-user-auth"
            / "epics"
            / "E-authentication"
            / "features"
            / "F-empty"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("# Empty Feature")

        # Test finding children
        result = children_of("feature", "empty", project_root)

        # Should return empty list
        assert result == []

    def test_children_of_with_id_prefix(self, temp_dir):
        """Test children_of function with prefixed IDs."""
        project_root = temp_dir / "planning"

        # Create project structure
        project_dir = project_root / "projects" / "P-user-auth"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# User Auth Project")

        epic_dir = project_dir / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Authentication Epic")

        # Test with prefixed ID
        result = children_of("project", "P-user-auth", project_root)

        # Should work the same as without prefix
        assert len(result) == 1
        assert epic_file in result

    def test_children_of_paths_sorted(self, temp_dir):
        """Test that children_of returns paths in sorted order."""
        project_root = temp_dir / "planning"

        # Create project with multiple children
        project_dir = project_root / "projects" / "P-test"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Test Project")

        # Create epics with names that would sort differently
        epic_z_dir = project_dir / "epics" / "E-z-epic"
        epic_z_dir.mkdir(parents=True)
        epic_z_file = epic_z_dir / "epic.md"
        epic_z_file.write_text("# Z Epic")

        epic_a_dir = project_dir / "epics" / "E-a-epic"
        epic_a_dir.mkdir(parents=True)
        epic_a_file = epic_a_dir / "epic.md"
        epic_a_file.write_text("# A Epic")

        # Test finding children
        result = children_of("project", "test", project_root)

        # Should be sorted alphabetically
        assert len(result) == 2
        assert result[0] == epic_a_file  # A should come before Z
        assert result[1] == epic_z_file

    def test_children_of_invalid_kind_error(self, temp_dir):
        """Test that invalid kind raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind 'invalid'"):
            children_of("invalid", "some-id", project_root)

    def test_children_of_empty_kind_error(self, temp_dir):
        """Test that empty kind raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind ''"):
            children_of("", "some-id", project_root)

    def test_children_of_empty_id_error(self, temp_dir):
        """Test that empty ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            children_of("project", "", project_root)

    def test_children_of_whitespace_id_error(self, temp_dir):
        """Test that whitespace-only ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            children_of("project", "   ", project_root)

    def test_children_of_nonexistent_project_error(self, temp_dir):
        """Test that non-existent project raises FileNotFoundError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Project with ID 'nonexistent' not found"):
            children_of("project", "nonexistent", project_root)

    def test_children_of_nonexistent_epic_error(self, temp_dir):
        """Test that non-existent epic raises FileNotFoundError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Epic with ID 'nonexistent' not found"):
            children_of("epic", "nonexistent", project_root)

    def test_children_of_nonexistent_feature_error(self, temp_dir):
        """Test that non-existent feature raises FileNotFoundError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Feature with ID 'nonexistent' not found"):
            children_of("feature", "nonexistent", project_root)

    def test_children_of_complex_hierarchy(self, temp_dir):
        """Test children_of with a complex multi-level hierarchy."""
        project_root = temp_dir / "planning"

        # Create complex project structure
        project_dir = project_root / "projects" / "P-ecommerce"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Ecommerce Project")

        # Epic 1 with features and tasks
        epic1_dir = project_dir / "epics" / "E-user-management"
        epic1_dir.mkdir(parents=True)
        epic1_file = epic1_dir / "epic.md"
        epic1_file.write_text("# User Management Epic")

        feature1_dir = epic1_dir / "features" / "F-user-profile"
        feature1_dir.mkdir(parents=True)
        feature1_file = feature1_dir / "feature.md"
        feature1_file.write_text("# User Profile Feature")

        task1_dir = feature1_dir / "tasks-open"
        task1_dir.mkdir()
        task1_file = task1_dir / "T-update-avatar.md"
        task1_file.write_text("# Update Avatar Task")

        # Epic 2 with different structure
        epic2_dir = project_dir / "epics" / "E-payment"
        epic2_dir.mkdir(parents=True)
        epic2_file = epic2_dir / "epic.md"
        epic2_file.write_text("# Payment Epic")

        feature2_dir = epic2_dir / "features" / "F-checkout"
        feature2_dir.mkdir(parents=True)
        feature2_file = feature2_dir / "feature.md"
        feature2_file.write_text("# Checkout Feature")

        task2_dir = feature2_dir / "tasks-done"
        task2_dir.mkdir()
        task2_file = task2_dir / "2025-07-13T19:12:00-05:00-T-process-payment.md"
        task2_file.write_text("# Process Payment Task")

        # Test finding all children of project
        result = children_of("project", "ecommerce", project_root)

        # Should return all descendant paths
        expected_paths = [
            epic1_file,
            epic2_file,
            feature1_file,
            feature2_file,
            task1_file,
            task2_file,
        ]
        assert len(result) == len(expected_paths)
        for path in expected_paths:
            assert path in result

    def test_children_of_edge_cases(self, temp_dir):
        """Test children_of with edge cases like empty directories."""
        project_root = temp_dir / "planning"

        # Create project with empty subdirectories
        project_dir = project_root / "projects" / "P-test"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Test Project")

        # Create empty epics directory
        epics_dir = project_dir / "epics"
        epics_dir.mkdir()

        # Create epic with empty features directory
        epic_dir = epics_dir / "E-test-epic"
        epic_dir.mkdir()
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Test Epic")

        features_dir = epic_dir / "features"
        features_dir.mkdir()

        # Test finding children
        result = children_of("project", "test", project_root)

        # Should return only the epic (no features or tasks)
        assert len(result) == 1
        assert epic_file in result

    def test_children_of_tasks_both_directories(self, temp_dir):
        """Test children_of includes tasks from both open and done directories."""
        project_root = temp_dir / "planning"

        # Create feature with tasks in both directories
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

        # Create tasks in both directories
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_open_dir.mkdir()
        task_open_file = tasks_open_dir / "T-implement-jwt.md"
        task_open_file.write_text("# Implement JWT Task")

        tasks_done_dir = feature_dir / "tasks-done"
        tasks_done_dir.mkdir()
        task_done_file = tasks_done_dir / "2025-07-13T19:12:00-05:00-T-setup-auth.md"
        task_done_file.write_text("# Setup Auth Task")

        # Test finding children of feature
        result = children_of("feature", "login", project_root)

        # Should include tasks from both directories
        assert len(result) == 2
        assert task_open_file in result
        assert task_done_file in result

    def test_children_of_id_prefix_stripping(self, temp_dir):
        """Test that children_of properly strips ID prefixes."""
        project_root = temp_dir / "planning"

        # Create project structure
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Test Project")

        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Test Epic")

        # Test all prefixes are stripped
        test_cases = [
            ("P-test-project", "project"),
            ("E-test-project", "project"),  # Wrong prefix but should still work
            ("F-test-project", "project"),
            ("T-test-project", "project"),
            ("test-project", "project"),  # No prefix
        ]

        for test_id, kind in test_cases:
            result = children_of(kind, test_id, project_root)
            assert len(result) == 1
            assert epic_file in result
