"""S-08 Unit tests: happy path, prereq-open error, wrong-status error.

Focused unit tests specifically covering the three core scenarios requested in S-08.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import pytest

from trellis_mcp.complete_task import complete_task
from trellis_mcp.exceptions.invalid_status_for_completion import InvalidStatusForCompletion
from trellis_mcp.exceptions.prerequisites_not_complete import PrerequisitesNotComplete
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.task import TaskModel
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.kind_enum import KindEnum


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


class TestCompleteTaskS08Core:
    """S-08 Unit tests: happy path, prereq-open error, wrong-status error."""

    @patch("trellis_mcp.complete_task._check_and_update_parent_feature_status")
    @patch("trellis_mcp.complete_task._move_task_to_done")
    @patch("trellis_mcp.complete_task.is_unblocked")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_happy_path_task_completion(
        self, mock_id_to_path, mock_parse, mock_is_unblocked, mock_move, mock_update_parent
    ):
        """Test successful task completion (happy path)."""
        # Setup: Task in valid status with no prerequisites
        mock_task = create_test_task("test-task", StatusEnum.IN_PROGRESS, "Test task")
        completed_task = create_test_task("test-task", StatusEnum.DONE, "Test task")

        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_parse.return_value = mock_task
        mock_is_unblocked.return_value = True  # No prerequisite issues
        mock_move.return_value = completed_task

        # Execute
        result = complete_task("/fake/project", "T-test-task")

        # Verify successful completion
        assert result.status == StatusEnum.DONE
        assert result.id == "test-task"
        mock_move.assert_called_once()
        mock_update_parent.assert_called_once()

    @patch("trellis_mcp.complete_task.is_unblocked")
    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_prereq_open_error(self, mock_id_to_path, mock_parse, mock_is_unblocked):
        """Test PrerequisitesNotComplete error when prerequisites are not done."""
        # Setup: Task with incomplete prerequisites
        mock_task = create_test_task(
            "test-task",
            StatusEnum.IN_PROGRESS,
            "Test task",
            prerequisites=["T-prereq-1", "T-prereq-2"],
        )

        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_parse.return_value = mock_task
        mock_is_unblocked.return_value = False  # Prerequisites not complete

        # Execute and verify exception
        with pytest.raises(PrerequisitesNotComplete) as exc_info:
            complete_task("/fake/project", "T-test-task")

        # Verify error details
        assert "test-task" in str(exc_info.value)
        assert "prerequisites" in str(exc_info.value)
        assert "not yet done" in str(exc_info.value)

    @patch("trellis_mcp.complete_task.parse_object")
    @patch("trellis_mcp.complete_task.id_to_path")
    def test_wrong_status_error(self, mock_id_to_path, mock_parse):
        """Test InvalidStatusForCompletion error when task has wrong status."""
        # Setup: Task with invalid status for completion
        mock_task = create_test_task("test-task", StatusEnum.OPEN, "Test task")

        mock_id_to_path.return_value = Path("/fake/path/task.md")
        mock_parse.return_value = mock_task

        # Execute and verify exception
        with pytest.raises(InvalidStatusForCompletion) as exc_info:
            complete_task("/fake/project", "T-test-task")

        # Verify error details
        assert "test-task" in str(exc_info.value)
        assert "open" in str(exc_info.value)
        assert "in-progress" in str(exc_info.value)
        assert "review" in str(exc_info.value)
