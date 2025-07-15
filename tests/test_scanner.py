"""Tests for the task scanner module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from trellis_mcp.models.common import Priority
from trellis_mcp.scanner import scan_tasks
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


class TestScanTasks:
    """Test the scan_tasks function."""

    def test_scan_tasks_empty_directory(self, tmp_path: Path):
        """Test scanning an empty directory returns no tasks."""
        tasks = list(scan_tasks(tmp_path))
        assert tasks == []

    def test_scan_tasks_no_planning_directory(self, tmp_path: Path):
        """Test scanning directory without planning/ returns no tasks."""
        # Create some other directory structure
        (tmp_path / "other").mkdir()
        tasks = list(scan_tasks(tmp_path))
        assert tasks == []

    def test_scan_tasks_no_projects_directory(self, tmp_path: Path):
        """Test scanning with planning/ but no projects/ returns no tasks."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()
        tasks = list(scan_tasks(tmp_path))
        assert tasks == []

    def test_scan_tasks_with_sample_structure(self, tmp_path: Path):
        """Test scanning with proper directory structure and sample tasks."""
        # Create the nested directory structure
        project_dir = tmp_path / "planning/projects/P-test-project"
        epic_dir = project_dir / "epics/E-test-epic"
        feature_dir = epic_dir / "features/F-test-feature"
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_done_dir = feature_dir / "tasks-done"

        tasks_open_dir.mkdir(parents=True)
        tasks_done_dir.mkdir(parents=True)

        # Create sample task files
        task1_content = """---
kind: task
id: T-test-task-1
parent: F-test-feature
status: open
title: Test Task 1
priority: high
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema: 1.0
---

# Test Task 1
This is a test task.
"""

        task2_content = """---
kind: task
id: T-test-task-2
parent: F-test-feature
status: done
title: Test Task 2
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema: 1.0
---

# Test Task 2
This is another test task.
"""

        # Write task files
        (tasks_open_dir / "T-test-task-1.md").write_text(task1_content)
        (tasks_done_dir / "2025-07-13T19-12-00-T-test-task-2.md").write_text(task2_content)

        # Mock the parse_object function to return TaskModel instances
        with patch("trellis_mcp.scanner.parse_object") as mock_parse:
            mock_task1 = TaskModel(
                kind=KindEnum.TASK,
                id="T-test-task-1",
                parent="F-test-feature",
                status=StatusEnum.OPEN,
                title="Test Task 1",
                priority=Priority.HIGH,
                worktree=None,
                created=datetime(2025, 7, 13, 19, 12, 0),
                updated=datetime(2025, 7, 13, 19, 12, 0),
                schema_version="1.0",
            )
            mock_task2 = TaskModel(
                kind=KindEnum.TASK,
                id="T-test-task-2",
                parent="F-test-feature",
                status=StatusEnum.DONE,
                title="Test Task 2",
                priority=Priority.NORMAL,
                worktree=None,
                created=datetime(2025, 7, 13, 19, 12, 0),
                updated=datetime(2025, 7, 13, 19, 12, 0),
                schema_version="1.0",
            )

            mock_parse.side_effect = [mock_task1, mock_task2]

            tasks = list(scan_tasks(tmp_path))

            assert len(tasks) == 2
            assert tasks[0].id == "T-test-task-1"
            assert tasks[1].id == "T-test-task-2"
            assert mock_parse.call_count == 2

    def test_scan_tasks_skips_non_markdown_files(self, tmp_path: Path):
        """Test that scanner skips non-markdown files."""
        # Create the nested directory structure
        tasks_open_dir = (
            tmp_path / "planning/projects/P-test/epics/E-test/features/F-test/tasks-open"
        )
        tasks_open_dir.mkdir(parents=True)

        # Create various file types
        (tasks_open_dir / "task.md").write_text("---\nkind: task\n---\n# Task")
        (tasks_open_dir / "readme.txt").write_text("Not a markdown file")
        (tasks_open_dir / "config.json").write_text('{"key": "value"}')
        (tasks_open_dir / "script.py").write_text("print('hello')")

        with patch("trellis_mcp.scanner.parse_object") as mock_parse:
            mock_task = TaskModel(
                kind=KindEnum.TASK,
                id="T-test-task",
                parent="F-test",
                status=StatusEnum.OPEN,
                title="Test Task",
                priority=Priority.NORMAL,
                worktree=None,
                created=datetime(2025, 7, 13, 19, 12, 0),
                updated=datetime(2025, 7, 13, 19, 12, 0),
                schema_version="1.0",
            )
            mock_parse.return_value = mock_task

            tasks = list(scan_tasks(tmp_path))

            # Should only process the .md file
            assert len(tasks) == 1
            assert mock_parse.call_count == 1

    def test_scan_tasks_handles_parse_errors_gracefully(self, tmp_path: Path):
        """Test that scanner handles parse errors gracefully."""
        # Create the nested directory structure
        tasks_open_dir = (
            tmp_path / "planning/projects/P-test/epics/E-test/features/F-test/tasks-open"
        )
        tasks_open_dir.mkdir(parents=True)

        # Create valid and invalid task files
        (tasks_open_dir / "valid-task.md").write_text("---\nkind: task\n---\n# Valid Task")
        (tasks_open_dir / "invalid-task.md").write_text("Not valid YAML front-matter")

        with patch("trellis_mcp.scanner.parse_object") as mock_parse:
            mock_task = TaskModel(
                kind=KindEnum.TASK,
                id="T-valid-task",
                parent="F-test",
                status=StatusEnum.OPEN,
                title="Valid Task",
                priority=Priority.NORMAL,
                worktree=None,
                created=datetime(2025, 7, 13, 19, 12, 0),
                updated=datetime(2025, 7, 13, 19, 12, 0),
                schema_version="1.0",
            )

            # First call succeeds, second call raises exception
            mock_parse.side_effect = [mock_task, Exception("Parse error")]

            tasks = list(scan_tasks(tmp_path))

            # Should only return the valid task, skip the invalid one
            assert len(tasks) == 1
            assert tasks[0].id == "T-valid-task"

    def test_scan_tasks_path_traversal_security(self, tmp_path: Path):
        """Test that scanner prevents path traversal attacks."""
        # Create the nested directory structure
        tasks_open_dir = (
            tmp_path / "planning/projects/P-test/epics/E-test/features/F-test/tasks-open"
        )
        tasks_open_dir.mkdir(parents=True)

        # Create a symlink that points outside the project root
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        malicious_file = outside_dir / "malicious.md"
        malicious_file.write_text("---\nkind: task\n---\n# Malicious Task")

        # Create symlink pointing to outside file
        symlink_path = tasks_open_dir / "symlink.md"
        symlink_path.symlink_to(malicious_file)

        with patch("trellis_mcp.scanner.parse_object") as mock_parse:
            mock_parse.return_value = TaskModel(
                kind=KindEnum.TASK,
                id="T-malicious",
                parent="F-test",
                status=StatusEnum.OPEN,
                title="Malicious Task",
                priority=Priority.NORMAL,
                worktree=None,
                created=datetime(2025, 7, 13, 19, 12, 0),
                updated=datetime(2025, 7, 13, 19, 12, 0),
                schema_version="1.0",
            )

            tasks = list(scan_tasks(tmp_path))

            # Should skip the symlink pointing outside project root
            assert len(tasks) == 0
            assert mock_parse.call_count == 0

    def test_scan_tasks_skips_directories_in_task_dirs(self, tmp_path: Path):
        """Test that scanner skips directories within task directories."""
        # Create the nested directory structure
        tasks_open_dir = (
            tmp_path / "planning/projects/P-test/epics/E-test/features/F-test/tasks-open"
        )
        tasks_open_dir.mkdir(parents=True)

        # Create a directory within tasks-open
        subdir = tasks_open_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.md").write_text("---\nkind: task\n---\n# Task in subdir")

        # Create a proper task file
        (tasks_open_dir / "task.md").write_text("---\nkind: task\n---\n# Proper Task")

        with patch("trellis_mcp.scanner.parse_object") as mock_parse:
            mock_task = TaskModel(
                kind=KindEnum.TASK,
                id="T-proper-task",
                parent="F-test",
                status=StatusEnum.OPEN,
                title="Proper Task",
                priority=Priority.NORMAL,
                worktree=None,
                created=datetime(2025, 7, 13, 19, 12, 0),
                updated=datetime(2025, 7, 13, 19, 12, 0),
                schema_version="1.0",
            )
            mock_parse.return_value = mock_task

            tasks = list(scan_tasks(tmp_path))

            # Should only process the file, not the directory
            assert len(tasks) == 1
            assert mock_parse.call_count == 1

    def test_scan_tasks_filters_non_task_objects(self, tmp_path: Path):
        """Test that scanner only yields TaskModel objects."""
        # Create the nested directory structure
        tasks_open_dir = (
            tmp_path / "planning/projects/P-test/epics/E-test/features/F-test/tasks-open"
        )
        tasks_open_dir.mkdir(parents=True)

        # Create task files
        (tasks_open_dir / "task1.md").write_text("---\nkind: task\n---\n# Task 1")
        (tasks_open_dir / "task2.md").write_text("---\nkind: task\n---\n# Task 2")

        with patch("trellis_mcp.scanner.parse_object") as mock_parse:
            mock_task = TaskModel(
                kind=KindEnum.TASK,
                id="T-task-1",
                parent="F-test",
                status=StatusEnum.OPEN,
                title="Task 1",
                priority=Priority.NORMAL,
                worktree=None,
                created=datetime(2025, 7, 13, 19, 12, 0),
                updated=datetime(2025, 7, 13, 19, 12, 0),
                schema_version="1.0",
            )

            # Mock parse_object to return a TaskModel for first call, non-TaskModel for second
            mock_non_task = Mock()
            mock_non_task.__class__ = Mock  # Make it not a TaskModel
            mock_parse.side_effect = [mock_task, mock_non_task]

            tasks = list(scan_tasks(tmp_path))

            # Should only yield the TaskModel object
            assert len(tasks) == 1
            assert tasks[0].id == "T-task-1"
