"""Tests for complete_task core functionality."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from trellis_mcp.complete_task import complete_task
from trellis_mcp.exceptions.invalid_status_for_completion import InvalidStatusForCompletion
from trellis_mcp.exceptions.prerequisites_not_complete import PrerequisitesNotComplete
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


def create_test_task(
    task_id: str,
    status: StatusEnum,
    title: str = "Test task",
    priority: Priority = Priority.NORMAL,
    prerequisites: list[str] | None = None,
) -> TaskModel:
    """Create a test TaskModel with specified fields."""
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return TaskModel(
        kind=KindEnum.TASK,
        id=task_id,
        parent="F-test-feature",
        status=status,
        title=title,
        priority=priority,
        worktree=None,
        created=base_time,
        updated=base_time,
        schema_version="1.0",
        prerequisites=prerequisites or [],
    )


class TestCompleteTaskValidation:
    """Test task status validation functionality of complete_task."""

    @patch("trellis_mcp.complete_task._check_and_update_parent_feature_status")
    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_valid_status_in_progress(
        self, mock_id_to_path, mock_parse, mock_move, mock_update_parent
    ):
        """Test that in-progress status is valid for completion."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_move.return_value = completed_task

        # Call function
        result = complete_task("/fake/project", "T-test-task")

        # Verify
        assert result == completed_task
        assert result.status == StatusEnum.DONE
        mock_id_to_path.assert_called_once_with(Path("/fake/project"), "task", "test-task")
        mock_parse.assert_called_once_with(Path("/fake/path/task.md"))
        mock_move.assert_called_once()

    @patch("trellis_mcp.complete_task._check_and_update_parent_feature_status")
    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_valid_status_review(self, mock_id_to_path, mock_parse, mock_move, mock_update_parent):
        """Test that review status is valid for completion."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.REVIEW, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_move.return_value = completed_task

        # Call function
        result = complete_task("/fake/project", "T-test-task")

        # Verify
        assert result == completed_task
        assert result.status == StatusEnum.DONE
        mock_id_to_path.assert_called_once_with(Path("/fake/project"), "task", "test-task")
        mock_parse.assert_called_once_with(Path("/fake/path/task.md"))
        mock_move.assert_called_once()

    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_invalid_status_open(self, mock_id_to_path, mock_parse):
        """Test that open status is invalid for completion."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.OPEN, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")

        # Call function and expect exception
        with pytest.raises(InvalidStatusForCompletion) as exc_info:
            complete_task("/fake/project", "T-test-task")

        # Verify error message contains useful information
        assert "test-task" in str(exc_info.value)
        assert "open" in str(exc_info.value)
        assert "in-progress" in str(exc_info.value)
        assert "review" in str(exc_info.value)

    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_invalid_status_done(self, mock_id_to_path, mock_parse):
        """Test that done status is invalid for completion."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")

        # Call function and expect exception
        with pytest.raises(InvalidStatusForCompletion) as exc_info:
            complete_task("/fake/project", "T-test-task")

        # Verify error message
        assert "test-task" in str(exc_info.value)
        assert "done" in str(exc_info.value)
        assert "in-progress" in str(exc_info.value)
        assert "review" in str(exc_info.value)


class TestCompleteTaskInputValidation:
    """Test input validation for complete_task."""

    def test_empty_task_id(self):
        """Test that empty task ID raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            complete_task("/fake/project", "")

        assert "Task ID cannot be empty" in str(exc_info.value)

    def test_whitespace_only_task_id(self):
        """Test that whitespace-only task ID raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            complete_task("/fake/project", "   ")

        assert "Task ID cannot be empty" in str(exc_info.value)

    @patch("trellis_mcp.complete_task.id_to_path")
    def test_task_id_prefix_removal(self, mock_id_to_path):
        """Test that T- prefix is properly removed from task ID."""
        mock_id_to_path.side_effect = FileNotFoundError("Task not found")

        # Try with T- prefix
        with pytest.raises(FileNotFoundError):
            complete_task("/fake/project", "T-test-task")

        # Verify that clean ID (without T-) was passed to id_to_path
        mock_id_to_path.assert_called_with(Path("/fake/project"), "task", "test-task")

    @patch("trellis_mcp.complete_task.id_to_path")
    def test_task_id_without_prefix(self, mock_id_to_path):
        """Test that task ID without prefix works correctly."""
        mock_id_to_path.side_effect = FileNotFoundError("Task not found")

        # Try without T- prefix
        with pytest.raises(FileNotFoundError):
            complete_task("/fake/project", "test-task")

        # Verify that ID was passed as-is
        mock_id_to_path.assert_called_with(Path("/fake/project"), "task", "test-task")


class TestCompleteTaskErrorHandling:
    """Test error handling for complete_task."""

    @patch("trellis_mcp.complete_task.id_to_path")
    def test_task_not_found(self, mock_id_to_path):
        """Test that FileNotFoundError is raised when task doesn't exist."""
        mock_id_to_path.side_effect = FileNotFoundError("Path not found")

        with pytest.raises(FileNotFoundError) as exc_info:
            complete_task("/fake/project", "T-nonexistent")

        assert "T-nonexistent" in str(exc_info.value)

    @patch("trellis_mcp.complete_task.id_to_path")
    def test_invalid_task_id_format(self, mock_id_to_path):
        """Test that ValueError is raised for invalid task ID format."""
        mock_id_to_path.side_effect = ValueError("Invalid ID format")

        with pytest.raises(ValueError) as exc_info:
            complete_task("/fake/project", "invalid-id")

        assert "invalid-id" in str(exc_info.value)

    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_non_task_object(self, mock_id_to_path, mock_parse):
        """Test that ValueError is raised when object is not a task."""
        # Mock a non-task object (just use a string for simplicity)
        mock_parse.return_value = "not-a-task-model"
        mock_id_to_path.return_value = Path("/fake/path/feature.md")

        with pytest.raises(ValueError) as exc_info:
            complete_task("/fake/project", "F-not-a-task")

        assert "not a task" in str(exc_info.value)
        assert "F-not-a-task" in str(exc_info.value)


class TestCompleteTaskPathHandling:
    """Test path handling for complete_task."""

    @patch("trellis_mcp.complete_task._check_and_update_parent_feature_status")
    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_string_project_root(self, mock_id_to_path, mock_parse, mock_move, mock_update_parent):
        """Test that string project root is converted to Path."""
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS)
        completed_task = create_test_task("test-task", StatusEnum.DONE)
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_move.return_value = completed_task

        # Call with string project root
        result = complete_task("/fake/project", "T-test-task")

        # Verify Path object was passed to id_to_path
        mock_id_to_path.assert_called_once_with(Path("/fake/project"), "task", "test-task")
        assert result == completed_task

    @patch("trellis_mcp.complete_task._check_and_update_parent_feature_status")
    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_path_project_root(self, mock_id_to_path, mock_parse, mock_move, mock_update_parent):
        """Test that Path project root works correctly."""
        mock_task = create_test_task("test-task", StatusEnum.REVIEW)
        completed_task = create_test_task("test-task", StatusEnum.DONE)
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_move.return_value = completed_task

        # Call with Path project root
        result = complete_task(Path("/fake/project"), "T-test-task")

        # Verify Path object was passed to id_to_path
        mock_id_to_path.assert_called_once_with(Path("/fake/project"), "task", "test-task")
        assert result == completed_task


class TestCompleteTaskPrerequisites:
    """Test prerequisite validation functionality of complete_task."""

    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.is_unblocked")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_task_with_no_prerequisites(
        self, mock_id_to_path, mock_parse, mock_is_unblocked, mock_move
    ):
        """Test that task with no prerequisites passes validation."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS, prerequisites=[])
        completed_task = create_test_task("test-task", StatusEnum.DONE, prerequisites=[])
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True
        mock_move.return_value = completed_task

        # Call function
        result = complete_task("/fake/project", "T-test-task")

        # Verify
        assert result == completed_task
        mock_is_unblocked.assert_called_once_with(mock_task, Path("/fake/project"))

    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.is_unblocked")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_task_with_completed_prerequisites(
        self, mock_id_to_path, mock_parse, mock_is_unblocked, mock_move
    ):
        """Test that task with all completed prerequisites passes validation."""
        # Setup mocks
        mock_task = create_test_task(
            "test-task", StatusEnum.IN_PROGRESS, prerequisites=["T-prereq-1", "T-prereq-2"]
        )
        completed_task = create_test_task(
            "test-task", StatusEnum.DONE, prerequisites=["T-prereq-1", "T-prereq-2"]
        )
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True  # All prerequisites are done
        mock_move.return_value = completed_task

        # Call function
        result = complete_task("/fake/project", "T-test-task")

        # Verify
        assert result == completed_task
        mock_is_unblocked.assert_called_once_with(mock_task, Path("/fake/project"))

    @patch("trellis_mcp.complete_task.is_unblocked")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_task_with_incomplete_prerequisites(
        self, mock_id_to_path, mock_parse, mock_is_unblocked
    ):
        """Test that task with incomplete prerequisites raises PrerequisitesNotComplete."""
        # Setup mocks
        mock_task = create_test_task(
            "test-task", StatusEnum.IN_PROGRESS, prerequisites=["T-prereq-1", "T-prereq-2"]
        )
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = False  # Prerequisites are not all done

        # Call function and expect exception
        with pytest.raises(PrerequisitesNotComplete) as exc_info:
            complete_task("/fake/project", "T-test-task")

        # Verify error message contains useful information
        assert "test-task" in str(exc_info.value)
        assert "prerequisites" in str(exc_info.value)
        assert "not yet done" in str(exc_info.value)
        mock_is_unblocked.assert_called_once_with(mock_task, Path("/fake/project"))

    @patch("trellis_mcp.complete_task.is_unblocked")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_task_review_status_with_incomplete_prerequisites(
        self, mock_id_to_path, mock_parse, mock_is_unblocked
    ):
        """Test that task in review status with incomplete prerequisites raises exception."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.REVIEW, prerequisites=["T-prereq-1"])
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = False  # Prerequisites are not done

        # Call function and expect exception
        with pytest.raises(PrerequisitesNotComplete) as exc_info:
            complete_task("/fake/project", "T-test-task")

        # Verify error message
        assert "test-task" in str(exc_info.value)
        mock_is_unblocked.assert_called_once_with(mock_task, Path("/fake/project"))


class TestCompleteTaskLogAppending:
    """Test log appending functionality of complete_task."""

    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.write_markdown")
    @patch("trellis_mcp.complete_task.read_markdown")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    @patch("trellis_mcp.complete_task.is_unblocked")
    def test_complete_task_with_summary_appends_log(
        self,
        mock_is_unblocked,
        mock_id_to_path,
        mock_parse,
        mock_read_markdown,
        mock_write_markdown,
        mock_move,
    ):
        """Test that providing summary appends log entry to task file."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True
        mock_move.return_value = completed_task

        # Mock file content for log appending
        initial_yaml = {"kind": "task", "id": "test-task", "status": "in-progress"}
        initial_body = "This is a test task.\n\n### Log\n\nTask created."
        mock_read_markdown.return_value = (initial_yaml, initial_body)

        # Call complete_task with summary and files
        summary = "Implemented authentication feature"
        files_changed = ["src/auth.py", "tests/test_auth.py"]

        result = complete_task("/fake/project", "test-task", summary, files_changed)

        # Verify completed task is returned
        assert result == completed_task

        # Verify log entry was appended
        mock_write_markdown.assert_called_once()
        call_args = mock_write_markdown.call_args
        written_yaml, written_body = call_args[0][1], call_args[0][2]

        assert written_yaml == initial_yaml
        assert "Task created." in written_body
        assert "Implemented authentication feature" in written_body
        assert 'filesChanged: ["src/auth.py", "tests/test_auth.py"]' in written_body
        # Verify timestamp format (ISO with timezone)
        assert "**2025-07-15T" in written_body and "Z**" in written_body

    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.write_markdown")
    @patch("trellis_mcp.complete_task.read_markdown")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    @patch("trellis_mcp.complete_task.is_unblocked")
    def test_complete_task_with_summary_no_files(
        self,
        mock_is_unblocked,
        mock_id_to_path,
        mock_parse,
        mock_read_markdown,
        mock_write_markdown,
        mock_move,
    ):
        """Test that providing summary without files appends log entry correctly."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.REVIEW, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True
        mock_move.return_value = completed_task

        # Mock file content for log appending
        initial_yaml = {"kind": "task", "id": "test-task", "status": "review"}
        initial_body = "This is a test task.\n\n### Log\n\nTask created."
        mock_read_markdown.return_value = (initial_yaml, initial_body)

        # Call complete_task with summary only
        summary = "Fixed bug in validation logic"

        result = complete_task("/fake/project", "test-task", summary)

        # Verify completed task is returned
        assert result == completed_task

        # Verify log entry was appended without filesChanged
        mock_write_markdown.assert_called_once()
        call_args = mock_write_markdown.call_args
        written_yaml, written_body = call_args[0][1], call_args[0][2]

        assert written_yaml == initial_yaml
        assert "Task created." in written_body
        assert "Fixed bug in validation logic" in written_body
        assert "filesChanged:" not in written_body

    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.write_markdown")
    @patch("trellis_mcp.complete_task.read_markdown")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    @patch("trellis_mcp.complete_task.is_unblocked")
    def test_complete_task_without_summary_no_log_append(
        self,
        mock_is_unblocked,
        mock_id_to_path,
        mock_parse,
        mock_read_markdown,
        mock_write_markdown,
        mock_move,
    ):
        """Test that not providing summary does not append log entry."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True
        mock_move.return_value = completed_task

        # Call complete_task without summary
        result = complete_task("/fake/project", "test-task")

        # Verify completed task is returned
        assert result == completed_task

        # Verify no log append functions were called
        mock_read_markdown.assert_not_called()
        mock_write_markdown.assert_not_called()

    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.write_markdown")
    @patch("trellis_mcp.complete_task.read_markdown")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    @patch("trellis_mcp.complete_task.is_unblocked")
    def test_complete_task_creates_log_section_if_missing(
        self,
        mock_is_unblocked,
        mock_id_to_path,
        mock_parse,
        mock_read_markdown,
        mock_write_markdown,
        mock_move,
    ):
        """Test that log section is created if it doesn't exist."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True
        mock_move.return_value = completed_task

        # Mock file content without log section
        initial_yaml = {"kind": "task", "id": "test-task", "status": "in-progress"}
        initial_body = "This is a test task."
        mock_read_markdown.return_value = (initial_yaml, initial_body)

        # Call complete_task with summary
        summary = "Added new functionality"

        result = complete_task("/fake/project", "test-task", summary)

        # Verify completed task is returned
        assert result == completed_task

        # Verify log section was created and entry appended
        mock_write_markdown.assert_called_once()
        call_args = mock_write_markdown.call_args
        written_yaml, written_body = call_args[0][1], call_args[0][2]

        assert written_yaml == initial_yaml
        assert "### Log" in written_body
        assert "Added new functionality" in written_body


class TestCompleteTaskParentFeatureUpdate:
    """Test parent feature status update functionality when completing tasks."""

    @patch("trellis_mcp.complete_task._check_and_update_parent_feature_status")
    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    @patch("trellis_mcp.complete_task.is_unblocked")
    def test_complete_task_calls_parent_feature_update(
        self,
        mock_is_unblocked,
        mock_id_to_path,
        mock_parse,
        mock_move,
        mock_update_parent,
    ):
        """Test that completing a task triggers parent feature status check."""
        # Setup mocks
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True
        mock_move.return_value = completed_task

        # Call complete_task
        result = complete_task("/fake/project", "test-task")

        # Verify completed task is returned
        assert result == completed_task

        # Verify parent feature update was called with correct parent ID
        mock_update_parent.assert_called_once_with(Path("/fake/project"), "F-test-feature")

    @patch("trellis_mcp.complete_task._check_and_update_parent_feature_status")
    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    @patch("trellis_mcp.complete_task.is_unblocked")
    def test_complete_task_no_parent_no_update_call(
        self,
        mock_is_unblocked,
        mock_id_to_path,
        mock_parse,
        mock_move,
        mock_update_parent,
    ):
        """Test that completing a task with no parent doesn't trigger feature update."""
        # Create a task with no parent (using direct TaskModel construction)
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Mock the task to have no parent by bypassing validation
        mock_task = TaskModel.model_construct(
            kind=KindEnum.TASK,
            id="test-task",
            parent=None,  # Set to None
            status=StatusEnum.IN_PROGRESS,
            title="Test task",
            priority=Priority.NORMAL,
            worktree=None,
            created=base_time,
            updated=base_time,
            schema_version="1.0",
            prerequisites=[],
        )

        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")
        mock_parse.return_value = mock_task
        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_is_unblocked.return_value = True
        mock_move.return_value = completed_task

        # Call complete_task
        result = complete_task("/fake/project", "test-task")

        # Verify completed task is returned
        assert result == completed_task

        # Verify parent feature update was NOT called
        mock_update_parent.assert_not_called()

    @patch("trellis_mcp.complete_task._update_feature_status")
    @patch("trellis_mcp.complete_task._get_all_feature_tasks")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_check_and_update_parent_feature_all_tasks_done(
        self,
        mock_id_to_path,
        mock_parse,
        mock_get_tasks,
        mock_update_status,
    ):
        """Test feature status update when all tasks are done."""
        from trellis_mcp.complete_task import _check_and_update_parent_feature_status
        from trellis_mcp.schema.feature import FeatureModel
        from trellis_mcp.schema.kind_enum import KindEnum

        # Create a feature that's in-progress
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_feature = FeatureModel(
            kind=KindEnum.FEATURE,
            id="F-test-feature",
            parent="E-test-epic",
            status=StatusEnum.IN_PROGRESS,
            title="Test Feature",
            priority=Priority.NORMAL,
            worktree=None,
            created=base_time,
            updated=base_time,
            schema_version="1.0",
            prerequisites=[],
        )

        # Create some done tasks
        done_task1 = create_test_task("task1", StatusEnum.DONE, "Task 1")
        done_task2 = create_test_task("task2", StatusEnum.DONE, "Task 2")

        # Setup mocks
        mock_id_to_path.return_value = Path("/fake/feature.md")
        mock_parse.return_value = mock_feature
        mock_get_tasks.return_value = [done_task1, done_task2]

        # Call the function
        _check_and_update_parent_feature_status(Path("/fake/project"), "F-test-feature")

        # Verify feature status was updated to done
        mock_update_status.assert_called_once_with(Path("/fake/project"), "test-feature", "done")

    @patch("trellis_mcp.complete_task._update_feature_status")
    @patch("trellis_mcp.complete_task._get_all_feature_tasks")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_check_and_update_parent_feature_has_open_tasks(
        self,
        mock_id_to_path,
        mock_parse,
        mock_get_tasks,
        mock_update_status,
    ):
        """Test feature status NOT updated when some tasks are still open."""
        from trellis_mcp.complete_task import _check_and_update_parent_feature_status
        from trellis_mcp.schema.feature import FeatureModel
        from trellis_mcp.schema.kind_enum import KindEnum

        # Create a feature that's in-progress
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_feature = FeatureModel(
            kind=KindEnum.FEATURE,
            id="F-test-feature",
            parent="E-test-epic",
            status=StatusEnum.IN_PROGRESS,
            title="Test Feature",
            priority=Priority.NORMAL,
            worktree=None,
            created=base_time,
            updated=base_time,
            schema_version="1.0",
            prerequisites=[],
        )

        # Create mix of done and open tasks
        done_task = create_test_task("task1", StatusEnum.DONE, "Task 1")
        open_task = create_test_task("task2", StatusEnum.OPEN, "Task 2")

        # Setup mocks
        mock_id_to_path.return_value = Path("/fake/feature.md")
        mock_parse.return_value = mock_feature
        mock_get_tasks.return_value = [done_task, open_task]

        # Call the function
        _check_and_update_parent_feature_status(Path("/fake/project"), "F-test-feature")

        # Verify feature status was NOT updated
        mock_update_status.assert_not_called()

    @patch("trellis_mcp.complete_task._update_feature_status")
    @patch("trellis_mcp.complete_task._get_all_feature_tasks")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_check_and_update_parent_feature_already_done(
        self,
        mock_id_to_path,
        mock_parse,
        mock_get_tasks,
        mock_update_status,
    ):
        """Test feature status NOT updated when feature is already done."""
        from trellis_mcp.complete_task import _check_and_update_parent_feature_status
        from trellis_mcp.schema.feature import FeatureModel
        from trellis_mcp.schema.kind_enum import KindEnum

        # Create a feature that's already done
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_feature = FeatureModel(
            kind=KindEnum.FEATURE,
            id="F-test-feature",
            parent="E-test-epic",
            status=StatusEnum.DONE,  # Already done
            title="Test Feature",
            priority=Priority.NORMAL,
            worktree=None,
            created=base_time,
            updated=base_time,
            schema_version="1.0",
            prerequisites=[],
        )

        # Setup mocks
        mock_id_to_path.return_value = Path("/fake/feature.md")
        mock_parse.return_value = mock_feature

        # Call the function
        _check_and_update_parent_feature_status(Path("/fake/project"), "F-test-feature")

        # Verify feature tasks were not even checked
        mock_get_tasks.assert_not_called()
        mock_update_status.assert_not_called()
