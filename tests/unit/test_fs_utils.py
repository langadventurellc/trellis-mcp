"""Tests for filesystem utilities module."""

import tempfile
from pathlib import Path

import pytest

from trellis_mcp.utils.fs_utils import ensure_parent_dirs, recursive_delete


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


class TestRecursiveDelete:
    """Test cases for recursive_delete function."""

    def test_recursive_delete_single_file_dry_run(self):
        """Test recursive_delete with single file in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a test file
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")

            # Dry-run deletion
            deleted_paths = recursive_delete(test_file, dry_run=True)

            # Should return the file path
            assert len(deleted_paths) == 1
            assert deleted_paths[0] == test_file.resolve()

            # File should still exist after dry-run
            assert test_file.exists()

    def test_recursive_delete_single_file_actual(self):
        """Test recursive_delete with single file - actual deletion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a test file
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")

            # Actual deletion
            deleted_paths = recursive_delete(test_file, dry_run=False)

            # Should return the file path
            assert len(deleted_paths) == 1
            assert deleted_paths[0] == test_file.resolve()

            # File should be deleted
            assert not test_file.exists()

    def test_recursive_delete_empty_directory_dry_run(self):
        """Test recursive_delete with empty directory in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create an empty directory
            test_dir = tmp_path / "test_dir"
            test_dir.mkdir()

            # Dry-run deletion
            deleted_paths = recursive_delete(test_dir, dry_run=True)

            # Should return the directory path
            assert len(deleted_paths) == 1
            assert deleted_paths[0] == test_dir.resolve()

            # Directory should still exist after dry-run
            assert test_dir.exists()

    def test_recursive_delete_empty_directory_actual(self):
        """Test recursive_delete with empty directory - actual deletion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create an empty directory
            test_dir = tmp_path / "test_dir"
            test_dir.mkdir()

            # Actual deletion
            deleted_paths = recursive_delete(test_dir, dry_run=False)

            # Should return the directory path
            assert len(deleted_paths) == 1
            assert deleted_paths[0] == test_dir.resolve()

            # Directory should be deleted
            assert not test_dir.exists()

    def test_recursive_delete_nested_structure_dry_run(self):
        """Test recursive_delete with nested directory structure in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create nested structure
            test_dir = tmp_path / "test_dir"
            subdir1 = test_dir / "subdir1"
            subdir2 = test_dir / "subdir2"
            subdir1.mkdir(parents=True)
            subdir2.mkdir(parents=True)

            # Create files in different directories
            file1 = test_dir / "file1.txt"
            file2 = subdir1 / "file2.txt"
            file3 = subdir2 / "file3.txt"

            file1.write_text("content1")
            file2.write_text("content2")
            file3.write_text("content3")

            # Dry-run deletion
            deleted_paths = recursive_delete(test_dir, dry_run=True)

            # Should return all paths (3 files + 3 directories)
            assert len(deleted_paths) == 6

            # Files should be in the list
            expected_files = {file1.resolve(), file2.resolve(), file3.resolve()}
            expected_dirs = {test_dir.resolve(), subdir1.resolve(), subdir2.resolve()}

            deleted_files = {p for p in deleted_paths if p.is_file()}
            deleted_dirs = {p for p in deleted_paths if p.is_dir()}

            assert deleted_files == expected_files
            assert deleted_dirs == expected_dirs

            # Everything should still exist after dry-run
            assert test_dir.exists()
            assert subdir1.exists()
            assert subdir2.exists()
            assert file1.exists()
            assert file2.exists()
            assert file3.exists()

    def test_recursive_delete_nested_structure_actual(self):
        """Test recursive_delete with nested directory structure - actual deletion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create nested structure
            test_dir = tmp_path / "test_dir"
            subdir1 = test_dir / "subdir1"
            subdir2 = test_dir / "subdir2"
            subdir1.mkdir(parents=True)
            subdir2.mkdir(parents=True)

            # Create files in different directories
            file1 = test_dir / "file1.txt"
            file2 = subdir1 / "file2.txt"
            file3 = subdir2 / "file3.txt"

            file1.write_text("content1")
            file2.write_text("content2")
            file3.write_text("content3")

            # Actual deletion
            deleted_paths = recursive_delete(test_dir, dry_run=False)

            # Should return all paths (3 files + 3 directories)
            assert len(deleted_paths) == 6

            # Everything should be deleted
            assert not test_dir.exists()
            assert not subdir1.exists()
            assert not subdir2.exists()
            assert not file1.exists()
            assert not file2.exists()
            assert not file3.exists()

    def test_recursive_delete_trellis_structure_dry_run(self):
        """Test recursive_delete with Trellis MCP project structure in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create Trellis project structure
            project_dir = tmp_path / "P-test-project"
            epic_dir = project_dir / "epics" / "E-test-epic"
            feature_dir = epic_dir / "features" / "F-test-feature"
            tasks_open = feature_dir / "tasks-open"
            tasks_done = feature_dir / "tasks-done"

            # Create directories
            tasks_open.mkdir(parents=True)
            tasks_done.mkdir(parents=True)

            # Create files
            project_file = project_dir / "project.md"
            epic_file = epic_dir / "epic.md"
            feature_file = feature_dir / "feature.md"
            task_open = tasks_open / "T-open-task.md"
            task_done = tasks_done / "2025-07-15T10:00:00-T-done-task.md"

            project_file.write_text("project content")
            epic_file.write_text("epic content")
            feature_file.write_text("feature content")
            task_open.write_text("open task content")
            task_done.write_text("done task content")

            # Dry-run deletion of entire project
            deleted_paths = recursive_delete(project_dir, dry_run=True)

            # Should return all paths
            assert len(deleted_paths) > 0

            # All files should be in the list
            expected_files = {
                project_file.resolve(),
                epic_file.resolve(),
                feature_file.resolve(),
                task_open.resolve(),
                task_done.resolve(),
            }

            deleted_files = {p for p in deleted_paths if p.is_file()}
            assert expected_files.issubset(deleted_files)

            # Everything should still exist after dry-run
            assert project_dir.exists()
            assert epic_dir.exists()
            assert feature_dir.exists()
            assert tasks_open.exists()
            assert tasks_done.exists()
            assert project_file.exists()
            assert epic_file.exists()
            assert feature_file.exists()
            assert task_open.exists()
            assert task_done.exists()

    def test_recursive_delete_with_invalid_type_raises_error(self):
        """Test that recursive_delete raises TypeError for non-Path objects."""
        with pytest.raises(TypeError, match="Expected pathlib.Path object"):
            recursive_delete("not/a/path/object")  # type: ignore

        with pytest.raises(TypeError, match="Expected pathlib.Path object"):
            recursive_delete(123)  # type: ignore

    def test_recursive_delete_nonexistent_path_raises_error(self):
        """Test that recursive_delete raises FileNotFoundError for non-existent paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            nonexistent_path = tmp_path / "does_not_exist"

            with pytest.raises(FileNotFoundError, match="Path does not exist"):
                recursive_delete(nonexistent_path)

    def test_recursive_delete_handles_path_ordering(self):
        """Test that recursive_delete returns paths in correct deletion order."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create nested structure
            test_dir = tmp_path / "test_dir"
            subdir = test_dir / "subdir"
            subdir.mkdir(parents=True)

            # Create files
            file1 = test_dir / "file1.txt"
            file2 = subdir / "file2.txt"
            file1.write_text("content1")
            file2.write_text("content2")

            # Dry-run deletion
            deleted_paths = recursive_delete(test_dir, dry_run=True)

            # Verify that deeper paths come before shallower ones
            # (files before their containing directories)
            path_depths = [(len(p.parts), p) for p in deleted_paths]
            sorted_by_depth = sorted(path_depths, key=lambda x: x[0], reverse=True)

            # The returned paths should already be in the correct order
            assert [p for _, p in sorted_by_depth] == deleted_paths

    def test_recursive_delete_dry_run_preserves_permissions(self):
        """Test that dry-run mode doesn't modify file permissions or timestamps."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a test file
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")

            # Get original stats
            original_stat = test_file.stat()

            # Dry-run deletion
            recursive_delete(test_file, dry_run=True)

            # File should still exist and be unchanged
            assert test_file.exists()
            new_stat = test_file.stat()

            # Permissions and basic stats should be unchanged
            assert original_stat.st_mode == new_stat.st_mode
            assert original_stat.st_size == new_stat.st_size

    def test_recursive_delete_handles_special_characters(self):
        """Test recursive_delete with files containing special characters."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create files with special characters
            special_files = [
                tmp_path / "file with spaces.txt",
                tmp_path / "file-with-dashes.txt",
                tmp_path / "file_with_underscores.txt",
                tmp_path / "file.with.dots.txt",
            ]

            for file_path in special_files:
                file_path.write_text("content")

            # Create a directory to delete
            test_dir = tmp_path / "test_dir"
            test_dir.mkdir()

            # Move files to the directory
            for file_path in special_files:
                new_path = test_dir / file_path.name
                file_path.rename(new_path)

            # Dry-run deletion
            deleted_paths = recursive_delete(test_dir, dry_run=True)

            # Should handle all special characters correctly
            assert len(deleted_paths) == 5  # 4 files + 1 directory

            # All files should still exist after dry-run
            assert test_dir.exists()
            for file_path in special_files:
                new_path = test_dir / file_path.name
                assert new_path.exists()

    def test_recursive_delete_dry_run_matches_actual_deletion(self):
        """Test that dry-run returns identical deletion list to actual deletion."""

        # Helper function to create identical directory structure
        def create_test_structure(base_path: Path) -> Path:
            """Create identical nested structure for testing."""
            test_dir = base_path / "test_structure"

            # Create nested directories
            subdir1 = test_dir / "subdir1"
            subdir2 = test_dir / "subdir2"
            nested_dir = subdir1 / "nested"

            subdir1.mkdir(parents=True)
            subdir2.mkdir(parents=True)
            nested_dir.mkdir(parents=True)

            # Create files at different levels
            files = [
                test_dir / "root_file.txt",
                subdir1 / "file1.txt",
                subdir2 / "file2.txt",
                nested_dir / "deep_file.txt",
                test_dir / "another_root.md",
            ]

            for file_path in files:
                file_path.write_text(f"Content of {file_path.name}")

            return test_dir

        with tempfile.TemporaryDirectory() as tmp_dir1, tempfile.TemporaryDirectory() as tmp_dir2:
            tmp_path1 = Path(tmp_dir1)
            tmp_path2 = Path(tmp_dir2)

            # Create identical structures
            structure1 = create_test_structure(tmp_path1)
            structure2 = create_test_structure(tmp_path2)

            # Run dry-run on first structure
            dry_run_paths = recursive_delete(structure1, dry_run=True)

            # Run actual deletion on second structure
            actual_paths = recursive_delete(structure2, dry_run=False)

            # Verify dry-run structure still exists
            assert structure1.exists()

            # Verify actual deletion structure is gone
            assert not structure2.exists()

            # Both should return the same number of paths
            assert len(dry_run_paths) == len(actual_paths)

            # Convert paths to structure-relative names for comparison
            def get_structure_relative_names(paths: list[Path], base: Path) -> list[str]:
                """Get relative names from the structure base directory."""
                base_resolved = base.resolve()
                result = []
                for p in paths:
                    p_resolved = p.resolve()
                    if p_resolved == base_resolved:
                        result.append(".")  # The base directory itself
                    else:
                        # Get relative path from base directory
                        try:
                            rel_path = p_resolved.relative_to(base_resolved)
                            result.append(str(rel_path))
                        except ValueError:
                            # Path is not under base, use just the name
                            result.append(p_resolved.name)
                return result

            dry_run_names = get_structure_relative_names(dry_run_paths, structure1)
            actual_names = get_structure_relative_names(actual_paths, structure2)

            # Both lists should contain the same relative names in the same order
            assert dry_run_names == actual_names

            # Verify all paths are resolved absolute paths
            for path in dry_run_paths:
                assert path.is_absolute(), f"Path {path} should be absolute"
                assert path == path.resolve(), f"Path {path} should be resolved"

            for path in actual_paths:
                assert path.is_absolute(), f"Path {path} should be absolute"
                assert path == path.resolve(), f"Path {path} should be resolved"
