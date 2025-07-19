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
