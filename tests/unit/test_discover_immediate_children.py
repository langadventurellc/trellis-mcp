"""Tests for discover_immediate_children function from path resolution utilities.

Tests the discover_immediate_children function that finds immediate child objects
with metadata within the hierarchical project structure.
"""

import pytest

from trellis_mcp.path_resolver import discover_immediate_children


class TestDiscoverImmediateChildren:
    """Test cases for the discover_immediate_children function."""

    def test_project_immediate_children_epics_only(self, temp_dir):
        """Test finding immediate children of a project (epics only, not recursive)."""
        project_root = temp_dir / "planning"

        # Create project with epics and nested hierarchy
        project_dir = project_root / "projects" / "P-user-auth"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n"
            "kind: project\n"
            "id: user-auth\n"
            "title: User Authentication Project\n"
            "status: in-progress\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# User Auth Project"
        )

        # Create epic 1
        epic1_dir = project_dir / "epics" / "E-authentication"
        epic1_dir.mkdir(parents=True)
        epic1_file = epic1_dir / "epic.md"
        epic1_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: authentication\n"
            "title: Authentication Epic\n"
            "status: in-progress\n"
            "created: '2025-01-02T10:00:00Z'\n"
            "---\n"
            "# Authentication Epic"
        )

        # Create epic 2
        epic2_dir = project_dir / "epics" / "E-authorization"
        epic2_dir.mkdir(parents=True)
        epic2_file = epic2_dir / "epic.md"
        epic2_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: authorization\n"
            "title: Authorization Epic\n"
            "status: open\n"
            "created: '2025-01-03T10:00:00Z'\n"
            "---\n"
            "# Authorization Epic"
        )

        # Create nested feature and task (should NOT be returned for immediate children)
        feature_dir = epic1_dir / "features" / "F-login"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text(
            "---\n"
            "kind: feature\n"
            "id: login\n"
            "title: Login Feature\n"
            "status: in-progress\n"
            "created: '2025-01-04T10:00:00Z'\n"
            "---\n"
            "# Login Feature"
        )

        # Test finding immediate children of project
        result = discover_immediate_children("project", "user-auth", project_root)

        # Should return only immediate epics (not features or tasks)
        assert len(result) == 2

        # Check epic 1 metadata
        epic1_metadata = next((child for child in result if child["id"] == "authentication"), None)
        assert epic1_metadata is not None
        assert epic1_metadata["title"] == "Authentication Epic"
        assert epic1_metadata["status"] == "in-progress"
        assert epic1_metadata["kind"] == "epic"
        assert epic1_metadata["created"] == "2025-01-02T10:00:00Z"
        assert str(epic1_file) in epic1_metadata["file_path"]

        # Check epic 2 metadata
        epic2_metadata = next((child for child in result if child["id"] == "authorization"), None)
        assert epic2_metadata is not None
        assert epic2_metadata["title"] == "Authorization Epic"
        assert epic2_metadata["status"] == "open"
        assert epic2_metadata["kind"] == "epic"
        assert epic2_metadata["created"] == "2025-01-03T10:00:00Z"
        assert str(epic2_file) in epic2_metadata["file_path"]

        # Should be sorted by creation date (oldest first)
        assert result[0]["id"] == "authentication"  # 2025-01-02
        assert result[1]["id"] == "authorization"  # 2025-01-03

    def test_epic_immediate_children_features_only(self, temp_dir):
        """Test finding immediate children of an epic (features only, not recursive)."""
        project_root = temp_dir / "planning"

        # Create epic with features and nested tasks
        epic_dir = project_root / "projects" / "P-user-auth" / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: authentication\n"
            "title: Authentication Epic\n"
            "status: in-progress\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Authentication Epic"
        )

        # Create feature 1
        feature1_dir = epic_dir / "features" / "F-login"
        feature1_dir.mkdir(parents=True)
        feature1_file = feature1_dir / "feature.md"
        feature1_file.write_text(
            "---\n"
            "kind: feature\n"
            "id: login\n"
            "title: Login Feature\n"
            "status: in-progress\n"
            "created: '2025-01-02T10:00:00Z'\n"
            "---\n"
            "# Login Feature"
        )

        # Create feature 2
        feature2_dir = epic_dir / "features" / "F-registration"
        feature2_dir.mkdir(parents=True)
        feature2_file = feature2_dir / "feature.md"
        feature2_file.write_text(
            "---\n"
            "kind: feature\n"
            "id: registration\n"
            "title: Registration Feature\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Registration Feature"
        )

        # Create nested task (should NOT be returned for immediate children)
        task_dir = feature1_dir / "tasks-open"
        task_dir.mkdir()
        task_file = task_dir / "T-implement-jwt.md"
        task_file.write_text(
            "---\n"
            "kind: task\n"
            "id: implement-jwt\n"
            "title: Implement JWT\n"
            "status: open\n"
            "created: '2025-01-03T10:00:00Z'\n"
            "---\n"
            "# Implement JWT Task"
        )

        # Test finding immediate children of epic
        result = discover_immediate_children("epic", "authentication", project_root)

        # Should return only immediate features (not tasks)
        assert len(result) == 2

        # Check sorted by creation date (oldest first)
        assert result[0]["id"] == "registration"  # 2025-01-01
        assert result[1]["id"] == "login"  # 2025-01-02

        # Check feature metadata
        for feature_metadata in result:
            assert feature_metadata["kind"] == "feature"
            assert "file_path" in feature_metadata
            if feature_metadata["id"] == "login":
                assert feature_metadata["title"] == "Login Feature"
                assert feature_metadata["status"] == "in-progress"
            elif feature_metadata["id"] == "registration":
                assert feature_metadata["title"] == "Registration Feature"
                assert feature_metadata["status"] == "open"

    def test_feature_immediate_children_tasks_only(self, temp_dir):
        """Test finding immediate children of a feature (tasks only from both directories)."""
        project_root = temp_dir / "planning"

        # Create feature with tasks in both open and done directories
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
        feature_file.write_text(
            "---\n"
            "kind: feature\n"
            "id: login\n"
            "title: Login Feature\n"
            "status: in-progress\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Login Feature"
        )

        # Create open task
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_open_dir.mkdir()
        task_open_file = tasks_open_dir / "T-implement-jwt.md"
        task_open_file.write_text(
            "---\n"
            "kind: task\n"
            "id: implement-jwt\n"
            "title: Implement JWT\n"
            "status: open\n"
            "created: '2025-01-02T10:00:00Z'\n"
            "---\n"
            "# Implement JWT Task"
        )

        # Create done task
        tasks_done_dir = feature_dir / "tasks-done"
        tasks_done_dir.mkdir()
        task_done_file = tasks_done_dir / "2025-07-13T19:12:00-05:00-T-setup-auth.md"
        task_done_file.write_text(
            "---\n"
            "kind: task\n"
            "id: setup-auth\n"
            "title: Setup Authentication\n"
            "status: done\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Setup Auth Task"
        )

        # Test finding immediate children of feature
        result = discover_immediate_children("feature", "login", project_root)

        # Should return both tasks
        assert len(result) == 2

        # Check sorted by creation date (oldest first)
        assert result[0]["id"] == "setup-auth"  # 2025-01-01
        assert result[1]["id"] == "implement-jwt"  # 2025-01-02

        # Check task metadata
        for task_metadata in result:
            assert task_metadata["kind"] == "task"
            assert "file_path" in task_metadata
            if task_metadata["id"] == "implement-jwt":
                assert task_metadata["title"] == "Implement JWT"
                assert task_metadata["status"] == "open"
            elif task_metadata["id"] == "setup-auth":
                assert task_metadata["title"] == "Setup Authentication"
                assert task_metadata["status"] == "done"

    def test_task_immediate_children_empty(self, temp_dir):
        """Test that tasks have no immediate children."""
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
        task_file.write_text(
            "---\n"
            "kind: task\n"
            "id: implement-jwt\n"
            "title: Implement JWT\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Implement JWT Task"
        )

        # Test finding children of task
        result = discover_immediate_children("task", "implement-jwt", project_root)

        # Should return empty list
        assert result == []

    def test_empty_parent_collections(self, temp_dir):
        """Test parents with no children return empty lists."""
        project_root = temp_dir / "planning"

        # Create empty project
        project_dir = project_root / "projects" / "P-empty"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n"
            "kind: project\n"
            "id: empty\n"
            "title: Empty Project\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Empty Project"
        )

        # Create empty epic
        epic_dir = project_root / "projects" / "P-test" / "epics" / "E-empty"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: empty\n"
            "title: Empty Epic\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Empty Epic"
        )

        # Create empty feature
        feature_dir = (
            project_root / "projects" / "P-test2" / "epics" / "E-test" / "features" / "F-empty"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text(
            "---\n"
            "kind: feature\n"
            "id: empty\n"
            "title: Empty Feature\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Empty Feature"
        )

        # Test all empty collections
        assert discover_immediate_children("project", "empty", project_root) == []
        assert discover_immediate_children("epic", "empty", project_root) == []
        assert discover_immediate_children("feature", "empty", project_root) == []

    def test_metadata_parsing_with_defaults(self, temp_dir):
        """Test metadata extraction handles missing fields gracefully."""
        project_root = temp_dir / "planning"

        # Create project with minimal metadata
        project_dir = project_root / "projects" / "P-minimal"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n" "kind: project\n" "id: minimal\n" "---\n" "# Minimal Project"
        )

        # Create epic with partial metadata
        epic_dir = project_dir / "epics" / "E-partial"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: partial\n"
            "title: Partial Epic\n"
            "---\n"
            "# Partial Epic (missing status and created)"
        )

        # Test finding children with missing fields
        result = discover_immediate_children("project", "minimal", project_root)

        assert len(result) == 1
        epic_metadata = result[0]
        assert epic_metadata["id"] == "partial"
        assert epic_metadata["title"] == "Partial Epic"
        assert epic_metadata["status"] == ""  # Default for missing field
        assert epic_metadata["created"] == ""  # Default for missing field
        assert epic_metadata["kind"] == "epic"
        assert "file_path" in epic_metadata

    def test_corrupted_files_handled_gracefully(self, temp_dir):
        """Test that corrupted child files don't stop discovery."""
        project_root = temp_dir / "planning"

        # Create project
        project_dir = project_root / "projects" / "P-test"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n"
            "kind: project\n"
            "id: test\n"
            "title: Test Project\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Test Project"
        )

        # Create valid epic
        epic1_dir = project_dir / "epics" / "E-valid"
        epic1_dir.mkdir(parents=True)
        epic1_file = epic1_dir / "epic.md"
        epic1_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: valid\n"
            "title: Valid Epic\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Valid Epic"
        )

        # Create corrupted epic file (invalid YAML)
        epic2_dir = project_dir / "epics" / "E-corrupted"
        epic2_dir.mkdir(parents=True)
        epic2_file = epic2_dir / "epic.md"
        epic2_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: corrupted\n"
            "invalid: yaml: [unclosed\n"
            "---\n"
            "# Corrupted Epic"
        )

        # Test finding children - should return only valid epic
        result = discover_immediate_children("project", "test", project_root)

        assert len(result) == 1
        assert result[0]["id"] == "valid"
        assert result[0]["title"] == "Valid Epic"

    def test_id_prefix_handling(self, temp_dir):
        """Test that function handles IDs with and without prefixes."""
        project_root = temp_dir / "planning"

        # Create project structure
        project_dir = project_root / "projects" / "P-user-auth"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n"
            "kind: project\n"
            "id: P-user-auth\n"  # ID with prefix in YAML
            "title: User Auth Project\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# User Auth Project"
        )

        epic_dir = project_dir / "epics" / "E-authentication"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: E-authentication\n"  # ID with prefix in YAML
            "title: Authentication Epic\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Authentication Epic"
        )

        # Test with prefixed ID parameter
        result = discover_immediate_children("project", "P-user-auth", project_root)
        assert len(result) == 1
        assert result[0]["id"] == "authentication"  # Should strip prefix from returned ID

        # Test with non-prefixed ID parameter
        result = discover_immediate_children("project", "user-auth", project_root)
        assert len(result) == 1
        assert result[0]["id"] == "authentication"  # Should strip prefix from returned ID

    def test_invalid_kind_error(self, temp_dir):
        """Test that invalid kind raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind 'invalid'"):
            discover_immediate_children("invalid", "some-id", project_root)

    def test_empty_kind_error(self, temp_dir):
        """Test that empty kind raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind ''"):
            discover_immediate_children("", "some-id", project_root)

    def test_empty_id_error(self, temp_dir):
        """Test that empty ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            discover_immediate_children("project", "", project_root)

    def test_whitespace_id_error(self, temp_dir):
        """Test that whitespace-only ID raises ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            discover_immediate_children("project", "   ", project_root)

    def test_nonexistent_parent_errors(self, temp_dir):
        """Test that non-existent parent objects raise FileNotFoundError."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="Project with ID 'nonexistent' not found"):
            discover_immediate_children("project", "nonexistent", project_root)

        with pytest.raises(FileNotFoundError, match="Epic with ID 'nonexistent' not found"):
            discover_immediate_children("epic", "nonexistent", project_root)

        with pytest.raises(FileNotFoundError, match="Feature with ID 'nonexistent' not found"):
            discover_immediate_children("feature", "nonexistent", project_root)

    def test_security_validation_path_traversal(self, temp_dir):
        """Test that path traversal attempts are blocked."""
        project_root = temp_dir / "planning"

        # Test various path traversal attempts
        malicious_ids = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "normal-id/../../../etc/passwd",
            "normal-id\\..\\..\\windows",
        ]

        for malicious_id in malicious_ids:
            with pytest.raises(ValueError, match="Invalid .* ID"):
                discover_immediate_children("project", malicious_id, project_root)

    def test_complex_hierarchy_immediate_only(self, temp_dir):
        """Test that function returns only immediate children, not deep descendants."""
        project_root = temp_dir / "planning"

        # Create deep hierarchy
        project_dir = project_root / "projects" / "P-ecommerce"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n"
            "kind: project\n"
            "id: ecommerce\n"
            "title: Ecommerce Project\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Ecommerce Project"
        )

        # Epic level
        epic_dir = project_dir / "epics" / "E-user-management"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: user-management\n"
            "title: User Management Epic\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# User Management Epic"
        )

        # Feature level (should NOT be returned for project children)
        feature_dir = epic_dir / "features" / "F-user-profile"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text(
            "---\n"
            "kind: feature\n"
            "id: user-profile\n"
            "title: User Profile Feature\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# User Profile Feature"
        )

        # Task level (should NOT be returned for project children)
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()
        task_file = task_dir / "T-update-avatar.md"
        task_file.write_text(
            "---\n"
            "kind: task\n"
            "id: update-avatar\n"
            "title: Update Avatar Task\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Update Avatar Task"
        )

        # Test project children - should return only epic
        result = discover_immediate_children("project", "ecommerce", project_root)
        assert len(result) == 1
        assert result[0]["id"] == "user-management"
        assert result[0]["kind"] == "epic"

        # Test epic children - should return only feature
        result = discover_immediate_children("epic", "user-management", project_root)
        assert len(result) == 1
        assert result[0]["id"] == "user-profile"
        assert result[0]["kind"] == "feature"

        # Test feature children - should return only task
        result = discover_immediate_children("feature", "user-profile", project_root)
        assert len(result) == 1
        assert result[0]["id"] == "update-avatar"
        assert result[0]["kind"] == "task"

    def test_sort_order_by_creation_date(self, temp_dir):
        """Test that results are sorted by creation date (oldest first)."""
        project_root = temp_dir / "planning"

        # Create project
        project_dir = project_root / "projects" / "P-test"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n"
            "kind: project\n"
            "id: test\n"
            "title: Test Project\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Test Project"
        )

        # Create epics with different creation dates
        epic_new_dir = project_dir / "epics" / "E-newest"
        epic_new_dir.mkdir(parents=True)
        epic_new_file = epic_new_dir / "epic.md"
        epic_new_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: newest\n"
            "title: Newest Epic\n"
            "status: open\n"
            "created: '2025-01-03T10:00:00Z'\n"  # Newest
            "---\n"
            "# Newest Epic"
        )

        epic_old_dir = project_dir / "epics" / "E-oldest"
        epic_old_dir.mkdir(parents=True)
        epic_old_file = epic_old_dir / "epic.md"
        epic_old_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: oldest\n"
            "title: Oldest Epic\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"  # Oldest
            "---\n"
            "# Oldest Epic"
        )

        epic_mid_dir = project_dir / "epics" / "E-middle"
        epic_mid_dir.mkdir(parents=True)
        epic_mid_file = epic_mid_dir / "epic.md"
        epic_mid_file.write_text(
            "---\n"
            "kind: epic\n"
            "id: middle\n"
            "title: Middle Epic\n"
            "status: open\n"
            "created: '2025-01-02T10:00:00Z'\n"  # Middle
            "---\n"
            "# Middle Epic"
        )

        # Test finding children
        result = discover_immediate_children("project", "test", project_root)

        # Should be sorted by creation date (oldest first)
        assert len(result) == 3
        assert result[0]["id"] == "oldest"  # 2025-01-01
        assert result[1]["id"] == "middle"  # 2025-01-02
        assert result[2]["id"] == "newest"  # 2025-01-03

    def test_performance_timing(self, temp_dir):
        """Test basic performance requirements for small collections."""
        import time

        project_root = temp_dir / "planning"

        # Create project with moderate number of children
        project_dir = project_root / "projects" / "P-performance-test"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text(
            "---\n"
            "kind: project\n"
            "id: performance-test\n"
            "title: Performance Test Project\n"
            "status: open\n"
            "created: '2025-01-01T10:00:00Z'\n"
            "---\n"
            "# Performance Test Project"
        )

        # Create 10 epics (small collection)
        for i in range(10):
            epic_dir = project_dir / "epics" / f"E-epic-{i:02d}"
            epic_dir.mkdir(parents=True)
            epic_file = epic_dir / "epic.md"
            epic_file.write_text(
                f"---\n"
                f"kind: epic\n"
                f"id: epic-{i:02d}\n"
                f"title: Epic {i:02d}\n"
                f"status: open\n"
                f"created: '2025-01-01T{10 + i}:00:00Z'\n"
                f"---\n"
                f"# Epic {i:02d}"
            )

        # Test performance
        start_time = time.time()
        result = discover_immediate_children("project", "performance-test", project_root)
        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000

        # Should complete in under 50ms for small collections (per requirements)
        assert execution_time_ms < 50, f"Execution took {execution_time_ms:.2f}ms, should be < 50ms"

        # Should return all 10 epics
        assert len(result) == 10

        # Should be sorted correctly
        for i, epic_metadata in enumerate(result):
            assert epic_metadata["id"] == f"epic-{i:02d}"
