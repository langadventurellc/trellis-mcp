"""Tests for filesystem utilities module."""

import tempfile
from pathlib import Path

import pytest

from trellis_mcp.fs_utils import ensure_parent_dirs


class TestEnsureParentDirs:
    """Test cases for ensure_parent_dirs function."""

    def test_ensure_parent_dirs_creates_nested_directories(self):
        """Test that ensure_parent_dirs creates all necessary parent directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a deeply nested file path
            target_file = (
                tmp_path / "planning" / "projects" / "P-test" / "epics" / "E-auth" / "epic.md"
            )

            # Ensure parent directories don't exist initially
            assert not target_file.parent.exists()

            # Call ensure_parent_dirs
            ensure_parent_dirs(target_file)

            # Verify all parent directories were created
            assert target_file.parent.exists()
            assert target_file.parent.is_dir()
            assert (tmp_path / "planning" / "projects" / "P-test" / "epics" / "E-auth").exists()

            # Verify the file itself was not created
            assert not target_file.exists()

    def test_ensure_parent_dirs_handles_existing_directories(self):
        """Test that ensure_parent_dirs works correctly when directories already exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create some directories first
            existing_dir = tmp_path / "planning" / "projects"
            existing_dir.mkdir(parents=True)

            # Create a file path that extends the existing structure
            target_file = existing_dir / "P-test" / "epics" / "E-auth" / "epic.md"

            # Call ensure_parent_dirs
            ensure_parent_dirs(target_file)

            # Verify directories were created
            assert target_file.parent.exists()
            assert target_file.parent.is_dir()

            # Verify existing directories are still there
            assert existing_dir.exists()

    def test_ensure_parent_dirs_handles_single_level_directory(self):
        """Test ensure_parent_dirs with a file that needs only one parent directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Simple file path with one parent
            target_file = tmp_path / "test_dir" / "file.txt"

            # Call ensure_parent_dirs
            ensure_parent_dirs(target_file)

            # Verify parent directory was created
            assert target_file.parent.exists()
            assert target_file.parent.is_dir()
            assert not target_file.exists()

    def test_ensure_parent_dirs_handles_file_in_existing_directory(self):
        """Test ensure_parent_dirs when the parent directory already exists."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # File in the existing temp directory
            target_file = tmp_path / "file.txt"

            # Call ensure_parent_dirs (parent already exists)
            ensure_parent_dirs(target_file)

            # Verify parent directory still exists
            assert target_file.parent.exists()
            assert target_file.parent.is_dir()

    def test_ensure_parent_dirs_handles_root_path(self):
        """Test ensure_parent_dirs with a file at root level."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # File directly in the temp directory (root for our test)
            target_file = tmp_path / "file.txt"

            # Call ensure_parent_dirs
            ensure_parent_dirs(target_file)

            # Verify parent directory exists (it should be the temp dir itself)
            assert target_file.parent.exists()
            assert target_file.parent == tmp_path

    def test_ensure_parent_dirs_with_invalid_type_raises_error(self):
        """Test that ensure_parent_dirs raises TypeError for non-Path objects."""
        with pytest.raises(TypeError, match="Expected pathlib.Path object"):
            ensure_parent_dirs("not/a/path/object")  # type: ignore

        with pytest.raises(TypeError, match="Expected pathlib.Path object"):
            ensure_parent_dirs(123)  # type: ignore

    def test_ensure_parent_dirs_creates_trellis_structure(self):
        """Test ensure_parent_dirs with actual Trellis MCP directory structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Test all different object types in the Trellis hierarchy
            test_cases = [
                # Project file
                tmp_path / "planning" / "projects" / "P-web-app" / "project.md",
                # Epic file
                tmp_path
                / "planning"
                / "projects"
                / "P-web-app"
                / "epics"
                / "E-user-auth"
                / "epic.md",
                # Feature file
                tmp_path
                / "planning"
                / "projects"
                / "P-web-app"
                / "epics"
                / "E-user-auth"
                / "features"
                / "F-login"
                / "feature.md",
                # Task in tasks-open
                tmp_path
                / "planning"
                / "projects"
                / "P-web-app"
                / "epics"
                / "E-user-auth"
                / "features"
                / "F-login"
                / "tasks-open"
                / "T-implement-jwt.md",
                # Task in tasks-done
                tmp_path
                / "planning"
                / "projects"
                / "P-web-app"
                / "epics"
                / "E-user-auth"
                / "features"
                / "F-login"
                / "tasks-done"
                / "2025-07-14T10:30:00-T-setup-db.md",
            ]

            for target_file in test_cases:
                # Ensure parent directories are created
                ensure_parent_dirs(target_file)

                # Verify parent directory exists
                assert target_file.parent.exists(), f"Failed to create parent for {target_file}"
                assert target_file.parent.is_dir(), f"Parent is not a directory for {target_file}"

                # Verify the file itself was not created
                assert not target_file.exists(), f"File was unexpectedly created: {target_file}"

    def test_ensure_parent_dirs_can_be_called_multiple_times(self):
        """Test that ensure_parent_dirs can be called multiple times without error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            target_file = tmp_path / "planning" / "projects" / "P-test" / "project.md"

            # Call multiple times
            ensure_parent_dirs(target_file)
            ensure_parent_dirs(target_file)
            ensure_parent_dirs(target_file)

            # Should still work correctly
            assert target_file.parent.exists()
            assert target_file.parent.is_dir()

    def test_ensure_parent_dirs_preserves_existing_files(self):
        """Test that ensure_parent_dirs doesn't affect existing files in parent directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a file in a directory
            existing_dir = tmp_path / "planning" / "projects"
            existing_dir.mkdir(parents=True)
            existing_file = existing_dir / "existing.txt"
            existing_file.write_text("test content")

            # Create a new file path that uses the same parent structure
            new_file = existing_dir / "P-test" / "project.md"

            # Call ensure_parent_dirs
            ensure_parent_dirs(new_file)

            # Verify existing file is still there
            assert existing_file.exists()
            assert existing_file.read_text() == "test content"

            # Verify new parent directory was created
            assert new_file.parent.exists()
