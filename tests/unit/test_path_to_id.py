"""Tests for path_to_id function and round-trip conversion from path resolution utilities.

Tests the path_to_id function that converts filesystem paths to object IDs and kinds,
and comprehensive round-trip conversion tests to ensure consistency between
id_to_path and path_to_id functions.
"""

import pytest

from trellis_mcp.path_resolver import id_to_path, path_to_id


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
