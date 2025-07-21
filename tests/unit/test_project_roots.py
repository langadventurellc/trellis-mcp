"""Tests for resolve_project_roots function from path resolution utilities.

Tests the resolve_project_roots function that determines scanning and path
resolution roots for project hierarchy operations.
"""

from pathlib import Path

from trellis_mcp.path_resolver import resolve_project_roots


class TestResolveProjectRoots:
    """Test cases for the resolve_project_roots function."""

    def test_project_root_contains_planning_directory(self, tmp_path):
        """Test case where project root contains planning directory."""
        # Create structure: project_root/planning/projects/
        planning_dir = tmp_path / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Call resolve_project_roots
        scanning_root, path_resolution_root = resolve_project_roots(tmp_path)

        # Verify results
        assert scanning_root == tmp_path
        assert path_resolution_root == planning_dir

    def test_project_root_is_planning_directory(self, tmp_path):
        """Test case where project root IS the planning directory."""
        # Create structure: project_root/projects/ (no planning subdirectory)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir(parents=True)

        # Call resolve_project_roots
        scanning_root, path_resolution_root = resolve_project_roots(tmp_path)

        # Verify results
        assert scanning_root == tmp_path.parent
        assert path_resolution_root == tmp_path

    def test_string_path_input(self, tmp_path):
        """Test function works with string path input."""
        # Create structure: project_root/planning/projects/
        planning_dir = tmp_path / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Call resolve_project_roots with string path
        scanning_root, path_resolution_root = resolve_project_roots(str(tmp_path))

        # Verify results
        assert scanning_root == tmp_path
        assert path_resolution_root == planning_dir

    def test_pathlib_path_input(self, tmp_path):
        """Test function works with pathlib.Path input."""
        # Create structure: project_root/planning/projects/
        planning_dir = tmp_path / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Call resolve_project_roots with Path object
        scanning_root, path_resolution_root = resolve_project_roots(tmp_path)

        # Verify results
        assert scanning_root == tmp_path
        assert path_resolution_root == planning_dir

    def test_nonexistent_planning_directory_fallback(self, tmp_path):
        """Test fallback behavior when planning directory doesn't exist."""
        # Create empty directory (no planning subdirectory)

        # Call resolve_project_roots
        scanning_root, path_resolution_root = resolve_project_roots(tmp_path)

        # Verify results - should treat project_root as planning directory
        assert scanning_root == tmp_path.parent
        assert path_resolution_root == tmp_path

    def test_both_scenarios_return_path_objects(self, tmp_path):
        """Test that both return values are always Path objects."""
        # Test scenario 1: contains planning directory
        planning_dir = tmp_path / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        scanning_root1, path_resolution_root1 = resolve_project_roots(str(tmp_path))
        assert isinstance(scanning_root1, Path)
        assert isinstance(path_resolution_root1, Path)

        # Test scenario 2: is planning directory
        tmp_path2 = tmp_path / "scenario2"
        tmp_path2.mkdir()
        projects_dir2 = tmp_path2 / "projects"
        projects_dir2.mkdir()

        scanning_root2, path_resolution_root2 = resolve_project_roots(str(tmp_path2))
        assert isinstance(scanning_root2, Path)
        assert isinstance(path_resolution_root2, Path)

    def test_ensure_planning_subdir_false_preserves_existing_behavior(self, tmp_path):
        """Test that ensure_planning_subdir=False preserves existing behavior."""
        # Create structure: project_root/planning/projects/
        planning_dir = tmp_path / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Call with ensure_planning_subdir=False (should match default behavior)
        scanning_root, path_resolution_root = resolve_project_roots(
            tmp_path, ensure_planning_subdir=False
        )

        # Verify results match existing behavior
        assert scanning_root == tmp_path
        assert path_resolution_root == planning_dir

    def test_ensure_planning_subdir_true_with_project_root(self, tmp_path):
        """Test ensure_planning_subdir=True with project root creates planning subdirectory."""
        # Start with empty project root
        assert not (tmp_path / "planning").exists()

        # Call with ensure_planning_subdir=True
        scanning_root, path_resolution_root = resolve_project_roots(
            tmp_path, ensure_planning_subdir=True
        )

        # Verify results
        assert scanning_root == tmp_path
        assert path_resolution_root == tmp_path / "planning"
        assert (tmp_path / "planning").exists()
        assert (tmp_path / "planning").is_dir()

    def test_ensure_planning_subdir_true_with_planning_root(self, tmp_path):
        """Test ensure_planning_subdir=True with planning root uses it directly."""
        # Create planning directory
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir(parents=True)

        # Call with planning directory path and ensure_planning_subdir=True
        scanning_root, path_resolution_root = resolve_project_roots(
            planning_dir, ensure_planning_subdir=True
        )

        # Verify results
        assert scanning_root == tmp_path
        assert path_resolution_root == planning_dir

    def test_ensure_planning_subdir_creates_directory_when_missing(self, tmp_path):
        """Test that ensure_planning_subdir=True creates planning directory when missing."""
        # Verify planning directory doesn't exist initially
        planning_dir = tmp_path / "planning"
        assert not planning_dir.exists()

        # Call with ensure_planning_subdir=True
        scanning_root, path_resolution_root = resolve_project_roots(
            tmp_path, ensure_planning_subdir=True
        )

        # Verify directory was created
        assert planning_dir.exists()
        assert planning_dir.is_dir()
        assert scanning_root == tmp_path
        assert path_resolution_root == planning_dir

    def test_ensure_planning_subdir_with_existing_planning_directory(self, tmp_path):
        """Test ensure_planning_subdir=True with existing planning directory."""
        # Create existing planning directory with content
        planning_dir = tmp_path / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)
        test_file = projects_dir / "test.md"
        test_file.write_text("existing content")

        # Call with ensure_planning_subdir=True
        scanning_root, path_resolution_root = resolve_project_roots(
            tmp_path, ensure_planning_subdir=True
        )

        # Verify existing directory is preserved
        assert scanning_root == tmp_path
        assert path_resolution_root == planning_dir
        assert test_file.exists()
        assert test_file.read_text() == "existing content"

    def test_ensure_planning_subdir_deep_path_creation(self, tmp_path):
        """Test ensure_planning_subdir=True creates parent directories when needed."""
        # Create a nested path that doesn't exist
        deep_path = tmp_path / "level1" / "level2" / "project"

        # Call with ensure_planning_subdir=True (should create all parent dirs)
        scanning_root, path_resolution_root = resolve_project_roots(
            deep_path, ensure_planning_subdir=True
        )

        # Verify all directories were created
        assert scanning_root == deep_path
        assert path_resolution_root == deep_path / "planning"
        assert (deep_path / "planning").exists()
        assert (deep_path / "planning").is_dir()

    def test_ensure_planning_subdir_string_path_input(self, tmp_path):
        """Test ensure_planning_subdir=True works with string path input."""
        # Call with string path and ensure_planning_subdir=True
        scanning_root, path_resolution_root = resolve_project_roots(
            str(tmp_path), ensure_planning_subdir=True
        )

        # Verify results
        assert scanning_root == tmp_path
        assert path_resolution_root == tmp_path / "planning"
        assert (tmp_path / "planning").exists()

    def test_ensure_planning_subdir_pathlib_path_input(self, tmp_path):
        """Test ensure_planning_subdir=True works with pathlib.Path input."""
        # Call with Path object and ensure_planning_subdir=True
        scanning_root, path_resolution_root = resolve_project_roots(
            tmp_path, ensure_planning_subdir=True
        )

        # Verify results
        assert scanning_root == tmp_path
        assert path_resolution_root == tmp_path / "planning"
        assert (tmp_path / "planning").exists()

    def test_ensure_planning_subdir_returns_path_objects(self, tmp_path):
        """Test that ensure_planning_subdir=True always returns Path objects."""
        # Test both scenarios
        scanning_root1, path_resolution_root1 = resolve_project_roots(
            str(tmp_path), ensure_planning_subdir=True
        )
        assert isinstance(scanning_root1, Path)
        assert isinstance(path_resolution_root1, Path)

        planning_dir = tmp_path / "planning2"
        planning_dir.mkdir()
        scanning_root2, path_resolution_root2 = resolve_project_roots(
            planning_dir, ensure_planning_subdir=True
        )
        assert isinstance(scanning_root2, Path)
        assert isinstance(path_resolution_root2, Path)
