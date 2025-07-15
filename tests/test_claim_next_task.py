"""Tests for claim_next_task core functionality."""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
import pytest

from trellis_mcp.claim_next_task import claim_next_task
from trellis_mcp.exceptions.no_available_task import NoAvailableTask
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.task import TaskModel
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.kind_enum import KindEnum


def create_test_task(
    task_id: str,
    priority: Priority,
    created: datetime,
    status: StatusEnum = StatusEnum.OPEN,
    title: str = "Test task",
    prerequisites: list[str] | None = None,
    worktree: str | None = None,
) -> TaskModel:
    """Create a test TaskModel with specified fields."""
    return TaskModel(
        kind=KindEnum.TASK,
        id=task_id,
        parent="F-test-feature",
        status=status,
        title=title,
        priority=priority,
        worktree=worktree,
        created=created,
        updated=created,
        schema_version="1.0",
        prerequisites=prerequisites or [],
    )


class TestClaimNextTaskPriorityOrdering:
    """Test priority ordering functionality of claim_next_task."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_high_priority_selected_first(self, mock_load, mock_unblocked, mock_write):
        """Test that high priority tasks are selected before normal/low priority."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create tasks with different priorities
        high_task = create_test_task("T-high", Priority.HIGH, base_time, title="High priority")
        normal_task = create_test_task(
            "T-normal", Priority.NORMAL, base_time, title="Normal priority"
        )
        low_task = create_test_task("T-low", Priority.LOW, base_time, title="Low priority")

        mock_load.return_value = [low_task, normal_task, high_task]  # Mixed order
        mock_unblocked.return_value = True  # All unblocked

        result = claim_next_task("/test/project")

        # High priority task should be selected
        assert result.id == "T-high"
        assert result.priority == Priority.HIGH
        assert result.status == StatusEnum.IN_PROGRESS
        mock_write.assert_called_once_with(result, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_normal_priority_selected_when_no_high(self, mock_load, mock_unblocked, mock_write):
        """Test that normal priority tasks are selected when no high priority available."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        normal_task = create_test_task("T-normal", Priority.NORMAL, base_time)
        low_task = create_test_task("T-low", Priority.LOW, base_time)

        mock_load.return_value = [low_task, normal_task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        assert result.id == "T-normal"
        assert result.priority == Priority.NORMAL

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_older_task_selected_when_priorities_equal(self, mock_load, mock_unblocked, mock_write):
        """Test that older tasks are selected first when priorities are equal."""
        older_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        newer_time = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

        newer_task = create_test_task("T-newer", Priority.NORMAL, newer_time, title="Newer task")
        older_task = create_test_task("T-older", Priority.NORMAL, older_time, title="Older task")

        mock_load.return_value = [newer_task, older_task]  # Newer first in list
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        # Older task should be selected despite being later in list
        assert result.id == "T-older"
        assert result.created == older_time

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_complex_priority_and_date_ordering(self, mock_load, mock_unblocked, mock_write):
        """Test complex scenarios with mixed priorities and dates."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create variety of tasks with different priorities and dates
        low_newer = create_test_task("T-low-new", Priority.LOW, base_time + timedelta(hours=1))
        high_older = create_test_task("T-high-old", Priority.HIGH, base_time)
        normal_middle = create_test_task(
            "T-normal-mid", Priority.NORMAL, base_time + timedelta(minutes=30)
        )
        high_newer = create_test_task("T-high-new", Priority.HIGH, base_time + timedelta(hours=2))

        mock_load.return_value = [low_newer, normal_middle, high_newer, high_older]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        # Should select oldest high priority task
        assert result.id == "T-high-old"
        assert result.priority == Priority.HIGH
        assert result.created == base_time


class TestClaimNextTaskPrerequisiteBlocking:
    """Test prerequisite blocking functionality of claim_next_task."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_task_with_no_prerequisites_is_claimable(self, mock_load, mock_unblocked, mock_write):
        """Test that tasks with no prerequisites can be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, prerequisites=[])

        mock_load.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        assert result.id == "T-001"
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_task_with_completed_prerequisites_is_claimable(
        self, mock_load, mock_unblocked, mock_write
    ):
        """Test that tasks with all prerequisites completed can be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-002", Priority.NORMAL, base_time, prerequisites=["T-001"])

        mock_load.return_value = [task]
        mock_unblocked.return_value = True  # Simulate all prereqs completed

        result = claim_next_task("/test/project")

        assert result.id == "T-002"
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_task_with_incomplete_prerequisites_is_not_claimable(self, mock_load, mock_unblocked):
        """Test that tasks with incomplete prerequisites cannot be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task("T-002", Priority.HIGH, base_time, prerequisites=["T-001"])

        mock_load.return_value = [blocked_task]
        mock_unblocked.return_value = False  # Simulate incomplete prereqs

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No unblocked tasks available" in str(exc_info.value)
        mock_unblocked.assert_called_once_with(blocked_task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_mixed_blocked_and_unblocked_tasks(self, mock_load, mock_unblocked, mock_write):
        """Test that only unblocked tasks are considered for claiming."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        blocked_high = create_test_task(
            "T-blocked", Priority.HIGH, base_time, prerequisites=["T-prereq"]
        )
        unblocked_normal = create_test_task(
            "T-unblocked", Priority.NORMAL, base_time, prerequisites=[]
        )

        mock_load.return_value = [blocked_high, unblocked_normal]

        # Mock is_unblocked to return False for blocked, True for unblocked
        def mock_unblocked_side_effect(task, project_root):
            return task.id == "T-unblocked"

        mock_unblocked.side_effect = mock_unblocked_side_effect

        result = claim_next_task("/test/project")

        # Should select unblocked task even though blocked has higher priority
        assert result.id == "T-unblocked"
        assert mock_unblocked.call_count == 2


class TestClaimNextTaskYAMLUpdateFields:
    """Test YAML field update functionality of claim_next_task."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_status_changes_to_in_progress(self, mock_load, mock_unblocked, mock_write):
        """Test that status changes from OPEN to IN_PROGRESS."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, status=StatusEnum.OPEN)

        mock_load.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        assert result.status == StatusEnum.IN_PROGRESS
        assert task.status == StatusEnum.IN_PROGRESS  # Original task modified

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_updated_timestamp_reflects_claim_time(self, mock_load, mock_unblocked, mock_write):
        """Test that updated timestamp is set to current time when claiming."""
        # Use naive datetime to match claim_next_task behavior
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        task = create_test_task("T-001", Priority.NORMAL, base_time)
        original_updated = task.updated

        mock_load.return_value = [task]
        mock_unblocked.return_value = True

        # Claim the task
        claim_start = datetime.now()
        result = claim_next_task("/test/project")
        claim_end = datetime.now()

        # Updated timestamp should be current time (within reasonable range)
        assert result.updated > original_updated
        assert claim_start <= result.updated <= claim_end

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_worktree_field_set_when_provided(self, mock_load, mock_unblocked, mock_write):
        """Test that worktree field is set when worktree_path is provided."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, worktree=None)

        mock_load.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project", worktree_path="/workspace/feature-branch")

        assert result.worktree == "/workspace/feature-branch"
        assert task.worktree == "/workspace/feature-branch"  # Original task modified

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_worktree_field_remains_none_when_not_provided(
        self, mock_load, mock_unblocked, mock_write
    ):
        """Test that worktree field remains None when worktree_path is not provided."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, worktree=None)

        mock_load.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")  # No worktree_path provided

        assert result.worktree is None
        assert task.worktree is None

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_atomic_file_write_called(self, mock_load, mock_unblocked, mock_write):
        """Test that atomic file write is called with updated task and project root."""
        # Use naive datetime to match claim_next_task behavior
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        task = create_test_task("T-001", Priority.NORMAL, base_time)

        mock_load.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project", "/workspace/feature")

        # Verify write_object called with updated task and correct project root
        mock_write.assert_called_once_with(result, Path("/test/project"))

        # Verify task has all expected updates
        written_task = mock_write.call_args[0][0]
        assert written_task.status == StatusEnum.IN_PROGRESS
        assert written_task.worktree == "/workspace/feature"
        assert written_task.updated > base_time


class TestClaimNextTaskEdgeCases:
    """Test edge cases and error conditions for claim_next_task."""

    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_no_open_tasks_raises_exception(self, mock_load):
        """Test that NoAvailableTask is raised when no open tasks exist."""
        mock_load.return_value = []

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No open tasks available in backlog" in str(exc_info.value)

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_claiming_when_no_tasks_unblocked_raises_no_available_task(
        self, mock_load, mock_unblocked
    ):
        """Test that NoAvailableTask is raised when no tasks are unblocked (C-08)."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create multiple tasks with different priorities, all blocked
        high_task = create_test_task(
            "T-high", Priority.HIGH, base_time, prerequisites=["T-prereq1"]
        )
        normal_task = create_test_task(
            "T-normal", Priority.NORMAL, base_time, prerequisites=["T-prereq2"]
        )
        low_task = create_test_task("T-low", Priority.LOW, base_time, prerequisites=["T-prereq3"])

        mock_load.return_value = [high_task, normal_task, low_task]
        mock_unblocked.return_value = False  # All tasks are blocked

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No unblocked tasks available" in str(exc_info.value)
        # Verify is_unblocked was called for each task
        assert mock_unblocked.call_count == 3

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_no_unblocked_tasks_raises_exception(self, mock_load, mock_unblocked):
        """Test that NoAvailableTask is raised when all tasks are blocked."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-001", Priority.NORMAL, base_time, prerequisites=["T-prereq"]
        )

        mock_load.return_value = [blocked_task]
        mock_unblocked.return_value = False  # All tasks blocked

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No unblocked tasks available - all open tasks have incomplete prerequisites" in str(
            exc_info.value
        )

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_filters_out_non_open_tasks(self, mock_load, mock_unblocked, mock_write):
        """Test that only OPEN tasks are considered for claiming."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        in_progress_task = create_test_task(
            "T-prog", Priority.HIGH, base_time, status=StatusEnum.IN_PROGRESS
        )
        done_task = create_test_task("T-done", Priority.HIGH, base_time, status=StatusEnum.DONE)
        open_task = create_test_task("T-open", Priority.NORMAL, base_time, status=StatusEnum.OPEN)

        mock_load.return_value = [in_progress_task, done_task, open_task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        # Should only consider the OPEN task
        assert result.id == "T-open"
        mock_unblocked.assert_called_once_with(open_task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.load_backlog_tasks")
    def test_project_root_path_conversion(self, mock_load, mock_unblocked, mock_write):
        """Test that project_root string is properly converted to Path object."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time)

        mock_load.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")  # String path

        # Verify Path object passed to dependencies
        mock_load.assert_called_once_with(Path("/test/project"))
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))
        mock_write.assert_called_once_with(result, Path("/test/project"))
