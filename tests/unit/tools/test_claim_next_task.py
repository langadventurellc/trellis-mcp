"""Tests for claim_next_task core functionality and tool interface."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastmcp import Client

from trellis_mcp.claim_next_task import claim_next_task
from trellis_mcp.exceptions.no_available_task import NoAvailableTask
from trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel
from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


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
        schema_version="1.1",
        prerequisites=prerequisites or [],
    )


class TestClaimNextTaskPriorityOrdering:
    """Test priority ordering functionality of claim_next_task."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_high_priority_selected_first(self, mock_scan, mock_unblocked, mock_write):
        """Test that high priority tasks are selected before normal/low priority."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create tasks with different priorities
        high_task = create_test_task("T-high", Priority.HIGH, base_time, title="High priority")
        normal_task = create_test_task(
            "T-normal", Priority.NORMAL, base_time, title="Normal priority"
        )
        low_task = create_test_task("T-low", Priority.LOW, base_time, title="Low priority")

        mock_scan.return_value = [low_task, normal_task, high_task]  # Mixed order
        mock_unblocked.return_value = True  # All unblocked

        result = claim_next_task("/test/project")

        # High priority task should be selected
        assert result.id == "T-high"
        assert result.priority == Priority.HIGH
        assert result.status == StatusEnum.IN_PROGRESS
        mock_write.assert_called_once_with(result, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_normal_priority_selected_when_no_high(self, mock_scan, mock_unblocked, mock_write):
        """Test that normal priority tasks are selected when no high priority available."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        normal_task = create_test_task("T-normal", Priority.NORMAL, base_time)
        low_task = create_test_task("T-low", Priority.LOW, base_time)

        mock_scan.return_value = [low_task, normal_task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        assert result.id == "T-normal"
        assert result.priority == Priority.NORMAL

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_older_task_selected_when_priorities_equal(self, mock_scan, mock_unblocked, mock_write):
        """Test that older tasks are selected first when priorities are equal."""
        older_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        newer_time = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

        newer_task = create_test_task("T-newer", Priority.NORMAL, newer_time, title="Newer task")
        older_task = create_test_task("T-older", Priority.NORMAL, older_time, title="Older task")

        mock_scan.return_value = [newer_task, older_task]  # Newer first in list
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        # Older task should be selected despite being later in list
        assert result.id == "T-older"
        assert result.created == older_time

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_complex_priority_and_date_ordering(self, mock_scan, mock_unblocked, mock_write):
        """Test complex scenarios with mixed priorities and dates."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create variety of tasks with different priorities and dates
        low_newer = create_test_task("T-low-new", Priority.LOW, base_time + timedelta(hours=1))
        high_older = create_test_task("T-high-old", Priority.HIGH, base_time)
        normal_middle = create_test_task(
            "T-normal-mid", Priority.NORMAL, base_time + timedelta(minutes=30)
        )
        high_newer = create_test_task("T-high-new", Priority.HIGH, base_time + timedelta(hours=2))

        mock_scan.return_value = [low_newer, normal_middle, high_newer, high_older]
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
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_task_with_no_prerequisites_is_claimable(self, mock_scan, mock_unblocked, mock_write):
        """Test that tasks with no prerequisites can be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, prerequisites=[])

        mock_scan.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        assert result.id == "T-001"
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_task_with_completed_prerequisites_is_claimable(
        self, mock_scan, mock_unblocked, mock_write
    ):
        """Test that tasks with all prerequisites completed can be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-002", Priority.NORMAL, base_time, prerequisites=["T-001"])

        mock_scan.return_value = [task]
        mock_unblocked.return_value = True  # Simulate all prereqs completed

        result = claim_next_task("/test/project")

        assert result.id == "T-002"
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_task_with_incomplete_prerequisites_is_not_claimable(self, mock_scan, mock_unblocked):
        """Test that tasks with incomplete prerequisites cannot be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task("T-002", Priority.HIGH, base_time, prerequisites=["T-001"])

        mock_scan.return_value = [blocked_task]
        mock_unblocked.return_value = False  # Simulate incomplete prereqs

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No unblocked tasks available" in str(exc_info.value)
        mock_unblocked.assert_called_once_with(blocked_task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_mixed_blocked_and_unblocked_tasks(self, mock_scan, mock_unblocked, mock_write):
        """Test that only unblocked tasks are considered for claiming."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        blocked_high = create_test_task(
            "T-blocked", Priority.HIGH, base_time, prerequisites=["T-prereq"]
        )
        unblocked_normal = create_test_task(
            "T-unblocked", Priority.NORMAL, base_time, prerequisites=[]
        )

        mock_scan.return_value = [blocked_high, unblocked_normal]

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
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_status_changes_to_in_progress(self, mock_scan, mock_unblocked, mock_write):
        """Test that status changes from OPEN to IN_PROGRESS."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, status=StatusEnum.OPEN)

        mock_scan.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        assert result.status == StatusEnum.IN_PROGRESS
        assert task.status == StatusEnum.IN_PROGRESS  # Original task modified

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_updated_timestamp_reflects_claim_time(self, mock_scan, mock_unblocked, mock_write):
        """Test that updated timestamp is set to current time when claiming."""
        # Use naive datetime to match claim_next_task behavior
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        task = create_test_task("T-001", Priority.NORMAL, base_time)
        original_updated = task.updated

        mock_scan.return_value = [task]
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
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_worktree_field_set_when_provided(self, mock_scan, mock_unblocked, mock_write):
        """Test that worktree field is set when worktree_path is provided."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, worktree=None)

        mock_scan.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project", worktree_path="/workspace/feature-branch")

        assert result.worktree == "/workspace/feature-branch"
        assert task.worktree == "/workspace/feature-branch"  # Original task modified

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_worktree_field_remains_none_when_not_provided(
        self, mock_scan, mock_unblocked, mock_write
    ):
        """Test that worktree field remains None when worktree_path is not provided."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time, worktree=None)

        mock_scan.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")  # No worktree_path provided

        assert result.worktree is None
        assert task.worktree is None

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_atomic_file_write_called(self, mock_scan, mock_unblocked, mock_write):
        """Test that atomic file write is called with updated task and project root."""
        # Use naive datetime to match claim_next_task behavior
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        task = create_test_task("T-001", Priority.NORMAL, base_time)

        mock_scan.return_value = [task]
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

    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_no_open_tasks_raises_exception(self, mock_scan):
        """Test that NoAvailableTask is raised when no open tasks exist."""
        mock_scan.return_value = []

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No open tasks available in backlog" in str(exc_info.value)

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_claiming_when_no_tasks_unblocked_raises_no_available_task(
        self, mock_scan, mock_unblocked
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

        mock_scan.return_value = [high_task, normal_task, low_task]
        mock_unblocked.return_value = False  # All tasks are blocked

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No unblocked tasks available" in str(exc_info.value)
        # Verify is_unblocked was called for each task
        assert mock_unblocked.call_count == 3

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_no_unblocked_tasks_raises_exception(self, mock_scan, mock_unblocked):
        """Test that NoAvailableTask is raised when all tasks are blocked."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-001", Priority.NORMAL, base_time, prerequisites=["T-prereq"]
        )

        mock_scan.return_value = [blocked_task]
        mock_unblocked.return_value = False  # All tasks blocked

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project")

        assert "No unblocked tasks available - all open tasks have incomplete prerequisites" in str(
            exc_info.value
        )

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_filters_out_non_open_tasks(self, mock_scan, mock_unblocked, mock_write):
        """Test that only OPEN tasks are considered for claiming."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        in_progress_task = create_test_task(
            "T-prog", Priority.HIGH, base_time, status=StatusEnum.IN_PROGRESS
        )
        done_task = create_test_task("T-done", Priority.HIGH, base_time, status=StatusEnum.DONE)
        open_task = create_test_task("T-open", Priority.NORMAL, base_time, status=StatusEnum.OPEN)

        mock_scan.return_value = [in_progress_task, done_task, open_task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")

        # Should only consider the OPEN task
        assert result.id == "T-open"
        mock_unblocked.assert_called_once_with(open_task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_project_root_path_conversion(self, mock_scan, mock_unblocked, mock_write):
        """Test that project_root string is properly converted to Path object."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time)

        mock_scan.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")  # String path

        # Verify Path object passed to dependencies
        # Since /test/project doesn't have a planning directory, resolve_project_roots
        # assumes it IS the planning directory, so scanning root is /test
        mock_scan.assert_called_once_with(Path("/test"))
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))
        mock_write.assert_called_once_with(result, Path("/test/project"))


class TestClaimNextTaskToolInterface:
    """Test claimNextTask tool interface, specifically scope parameter functionality."""

    @pytest.mark.asyncio
    async def test_empty_scope_parameter_maintains_existing_behavior(self, temp_dir):
        """Test that empty scope parameter maintains existing behavior (backward compatibility)."""
        # Create server and client
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test with empty scope parameter - should get NoAvailableTask error
            # This verifies that validation passes and the function is called
            with pytest.raises(Exception) as exc_info:
                await client.call_tool("claimNextTask", {"projectRoot": str(temp_dir), "scope": ""})

            # Should get the expected NoAvailableTask error, not a validation error
            assert "No open tasks available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_valid_scope_parameter_validation(self, temp_dir):
        """Test that valid scope parameters are accepted and validated."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test valid project scope - should get scope validation error since scope doesn't exist
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "scope": "P-valid-project"}
                )
            assert "Scope object not found" in str(exc_info.value)

            # Test valid epic scope
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "scope": "E-valid-epic"}
                )
            assert "Scope object not found" in str(exc_info.value)

            # Test valid feature scope
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "scope": "F-valid-feature"}
                )
            assert "Scope object not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_scope_parameter_validation(self, temp_dir):
        """Test that invalid scope parameters are rejected with proper error messages."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test invalid scope format (no prefix)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "scope": "invalid-scope"}
                )
            assert "Invalid scope parameter" in str(exc_info.value)

            # Test invalid scope format (wrong prefix)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "scope": "T-task-scope"}
                )
            assert "Invalid scope parameter" in str(exc_info.value)

            # Test invalid scope format (special characters)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "scope": "P-invalid@scope"}
                )
            assert "Invalid scope parameter" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_scope_parameter_with_worktree(self, temp_dir):
        """Test that scope parameter works correctly with worktree parameter."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test that both scope and worktree parameters are accepted
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": str(temp_dir),
                        "scope": "P-test-project",
                        "worktree": "/workspace/feature-branch",
                    },
                )

            # Should get scope validation error since scope doesn't exist
            assert "Scope object not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_project_root_validation(self, temp_dir):
        """Test that missing projectRoot parameter is properly validated."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test empty projectRoot
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": "", "scope": "P-test-project"}
                )
            assert "Project root cannot be empty" in str(exc_info.value)

            # Test whitespace-only projectRoot
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": "   ", "scope": "P-test-project"}
                )
            assert "Project root cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_scope_parameter_passed_to_core_function(self, temp_dir):
        """Test that scope parameter is properly passed from tool to core function."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            # Mock core function to raise NoAvailableTask to verify it was called with scope
            mock_core.side_effect = NoAvailableTask("No tasks available")

            async with Client(server) as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "claimNextTask", {"projectRoot": str(temp_dir), "scope": "F-test-feature"}
                    )

                # Verify core function was called with scope parameter
                mock_core.assert_called_once_with(str(temp_dir), "", "F-test-feature", None, False)

                # Should get NoAvailableTask, not validation error
                assert "No tasks available" in str(exc_info.value)


class TestClaimNextTaskScopeFiltering:
    """Test scope filtering functionality in the core claim_next_task function."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.filter_by_scope")
    @patch("trellis_mcp.claim_next_task.validate_scope_exists")
    def test_scope_filtering_uses_filter_by_scope(
        self, mock_validate, mock_filter, mock_unblocked, mock_write
    ):
        """Test that providing scope uses filter_by_scope instead of scan_tasks."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time)

        mock_validate.return_value = None  # Valid scope
        mock_filter.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project", scope="F-test-feature")

        # Verify scope validation was called with scanning_root
        mock_validate.assert_called_once_with(Path("/test"), "F-test-feature")

        # Verify filter_by_scope was called instead of scan_tasks
        mock_filter.assert_called_once_with(Path("/test"), "F-test-feature")

        assert result.id == "T-001"
        assert result.status == StatusEnum.IN_PROGRESS

    @patch("trellis_mcp.claim_next_task.scan_tasks")
    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    def test_no_scope_uses_scan_tasks(self, mock_unblocked, mock_write, mock_scan):
        """Test that no scope parameter maintains existing scan_tasks behavior."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-001", Priority.NORMAL, base_time)

        mock_scan.return_value = [task]
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project")  # No scope parameter

        # Verify scan_tasks was called (backward compatibility)
        mock_scan.assert_called_once_with(Path("/test"))

        assert result.id == "T-001"
        assert result.status == StatusEnum.IN_PROGRESS

    @patch("trellis_mcp.claim_next_task.validate_scope_exists")
    def test_invalid_scope_raises_validation_error(self, mock_validate):
        """Test that invalid scope raises ValidationError with specific message."""
        mock_validate.side_effect = ValidationError(
            errors=["Scope object not found: F-nonexistent"],
            error_codes=[ValidationErrorCode.INVALID_FIELD],
        )

        with pytest.raises(ValidationError) as exc_info:
            claim_next_task("/test/project", scope="F-nonexistent")

        assert "Scope object not found: F-nonexistent" in str(exc_info.value)
        mock_validate.assert_called_once_with(Path("/test"), "F-nonexistent")


class TestClaimNextTaskDirectClaiming:
    """Test direct task claiming by ID functionality."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_direct_task_claiming_success(self, mock_find, mock_unblocked, mock_write):
        """Test successful direct task claiming by ID."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        target_task = create_test_task("T-target", Priority.NORMAL, base_time, title="Target task")

        mock_find.return_value = target_task
        mock_unblocked.return_value = True

        result = claim_next_task("/test/project", task_id="T-target")

        assert result.id == "T-target"
        assert result.status == StatusEnum.IN_PROGRESS
        mock_find.assert_called_once_with(Path("/test"), "T-target")
        mock_unblocked.assert_called_once_with(target_task, Path("/test/project"))
        mock_write.assert_called_once_with(result, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_direct_task_claiming_not_found(self, mock_find):
        """Test direct task claiming when task ID is not found."""
        mock_find.return_value = None

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project", task_id="T-nonexistent")

        assert "Task not found: T-nonexistent" in str(exc_info.value)
        mock_find.assert_called_once_with(Path("/test"), "T-nonexistent")

    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_direct_task_claiming_wrong_status(self, mock_find):
        """Test direct task claiming when task has wrong status."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        in_progress_task = create_test_task(
            "T-busy", Priority.NORMAL, base_time, status=StatusEnum.IN_PROGRESS
        )

        mock_find.return_value = in_progress_task

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project", task_id="T-busy")

        assert "Task T-busy is not available for claiming (status: in-progress)" in str(
            exc_info.value
        )

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_direct_task_claiming_blocked_prerequisites(self, mock_find, mock_unblocked):
        """Test direct task claiming when task has incomplete prerequisites."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-blocked", Priority.NORMAL, base_time, prerequisites=["T-prereq"]
        )

        mock_find.return_value = blocked_task
        mock_unblocked.return_value = False

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_next_task("/test/project", task_id="T-blocked")

        assert "Task T-blocked cannot be claimed - prerequisites not completed" in str(
            exc_info.value
        )

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_direct_task_claiming_with_worktree(self, mock_find, mock_unblocked, mock_write):
        """Test direct task claiming with worktree parameter."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        target_task = create_test_task("T-target", Priority.NORMAL, base_time)

        mock_find.return_value = target_task
        mock_unblocked.return_value = True

        result = claim_next_task(
            "/test/project", worktree_path="/workspace/feature", task_id="T-target"
        )

        assert result.id == "T-target"
        assert result.status == StatusEnum.IN_PROGRESS
        assert result.worktree == "/workspace/feature"

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_empty_task_id_uses_priority_selection(self, mock_scan, mock_unblocked, mock_write):
        """Test that empty task_id parameter maintains existing priority-based behavior."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create fresh task objects for each test to avoid mutation issues
        def create_fresh_task():
            return create_test_task("T-001", Priority.NORMAL, base_time)

        mock_unblocked.return_value = True

        # Test with empty string
        task1 = create_fresh_task()
        mock_scan.return_value = [task1]
        result = claim_next_task("/test/project", task_id="")
        assert result.id == "T-001"

        # Test with None
        task2 = create_fresh_task()
        mock_scan.return_value = [task2]
        result = claim_next_task("/test/project", task_id=None)
        assert result.id == "T-001"

        # Test with whitespace
        task3 = create_fresh_task()
        mock_scan.return_value = [task3]
        result = claim_next_task("/test/project", task_id="   ")
        assert result.id == "T-001"


class TestClaimNextTaskToolInterfaceTaskId:
    """Test claimNextTask tool interface with taskId parameter."""

    @pytest.mark.asyncio
    async def test_empty_task_id_parameter_maintains_existing_behavior(self, temp_dir):
        """Test that empty taskId parameter maintains existing behavior (backward compatibility)."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test with empty taskId parameter - should get NoAvailableTask error
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "taskId": ""}
                )

            # Should get the expected NoAvailableTask error, not a validation error
            assert "No open tasks available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_task_id_parameter_passed_to_core_function(self, temp_dir):
        """Test that taskId parameter is properly passed from tool to core function."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            # Mock core function to raise NoAvailableTask to verify it was called with task_id
            mock_core.side_effect = NoAvailableTask("Task not found")

            async with Client(server) as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "claimNextTask", {"projectRoot": str(temp_dir), "taskId": "T-test-task"}
                    )

                # Verify core function was called with task_id parameter
                mock_core.assert_called_once_with(str(temp_dir), "", None, "T-test-task", False)

                # Should get NoAvailableTask, not validation error
                assert "Task not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_task_id_with_scope_and_worktree(self, temp_dir):
        """Test that taskId parameter works correctly with scope and worktree parameters."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            mock_core.side_effect = NoAvailableTask("Task not found")

            async with Client(server) as client:
                with pytest.raises(Exception):
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "taskId": "T-test-task",
                            "scope": "F-test-feature",
                            "worktree": "/workspace/feature-branch",
                        },
                    )

                # Verify all parameters are passed correctly
                mock_core.assert_called_once_with(
                    str(temp_dir),
                    "/workspace/feature-branch",
                    "F-test-feature",
                    "T-test-task",
                    False,
                )


class TestTaskResolutionFunction:
    """Test the _find_task_by_id helper function."""

    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_find_task_by_id_success(self, mock_scan):
        """Test successful task finding by ID."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task1 = create_test_task("T-001", Priority.NORMAL, base_time)
        task2 = create_test_task("T-002", Priority.HIGH, base_time)
        target_task = create_test_task("T-target", Priority.LOW, base_time)

        mock_scan.return_value = [task1, task2, target_task]

        from trellis_mcp.claim_next_task import _find_task_by_id

        result = _find_task_by_id(Path("/test"), "T-target")

        assert result is target_task
        assert result is not None
        assert result.id == "T-target"

    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_find_task_by_id_not_found(self, mock_scan):
        """Test task finding when ID doesn't exist."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task1 = create_test_task("T-001", Priority.NORMAL, base_time)
        task2 = create_test_task("T-002", Priority.HIGH, base_time)

        mock_scan.return_value = [task1, task2]

        from trellis_mcp.claim_next_task import _find_task_by_id

        result = _find_task_by_id(Path("/test"), "T-nonexistent")

        assert result is None

    @patch("trellis_mcp.claim_next_task.scan_tasks")
    def test_find_task_by_id_empty_list(self, mock_scan):
        """Test task finding when no tasks exist."""
        mock_scan.return_value = []

        from trellis_mcp.claim_next_task import _find_task_by_id

        result = _find_task_by_id(Path("/test"), "T-any")

        assert result is None


class TestClaimNextTaskForceClaimParameter:
    """Test force_claim parameter functionality in claimNextTask tool interface."""

    @pytest.mark.asyncio
    async def test_force_claim_false_maintains_existing_behavior(self, temp_dir):
        """Test that force_claim=False maintains existing behavior (backward compatibility)."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test with force_claim=False - should get NoAvailableTask error
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "force_claim": False}
                )

            # Should get the expected NoAvailableTask error, not a validation error
            assert "No open tasks available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_force_claim_requires_task_id(self, temp_dir):
        """Test that force_claim=True requires taskId to be specified."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test force_claim=True without taskId
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "force_claim": True}
                )
            assert "force_claim parameter requires taskId to be specified" in str(exc_info.value)

            # Test force_claim=True with empty taskId
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {"projectRoot": str(temp_dir), "force_claim": True, "taskId": ""},
                )
            assert "force_claim parameter requires taskId to be specified" in str(exc_info.value)

            # Test force_claim=True with whitespace-only taskId
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {"projectRoot": str(temp_dir), "force_claim": True, "taskId": "   "},
                )
            assert "force_claim parameter requires taskId to be specified" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_force_claim_incompatible_with_scope(self, temp_dir):
        """Test that force_claim=True is incompatible with scope parameter."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test force_claim=True with project scope
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": str(temp_dir),
                        "force_claim": True,
                        "taskId": "T-test-task",
                        "scope": "P-test-project",
                    },
                )
            assert "force_claim parameter is incompatible with scope parameter" in str(
                exc_info.value
            )

            # Test force_claim=True with epic scope
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": str(temp_dir),
                        "force_claim": True,
                        "taskId": "T-test-task",
                        "scope": "E-test-epic",
                    },
                )
            assert "force_claim parameter is incompatible with scope parameter" in str(
                exc_info.value
            )

            # Test force_claim=True with feature scope
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": str(temp_dir),
                        "force_claim": True,
                        "taskId": "T-test-task",
                        "scope": "F-test-feature",
                    },
                )
            assert "force_claim parameter is incompatible with scope parameter" in str(
                exc_info.value
            )

    @pytest.mark.asyncio
    async def test_force_claim_valid_with_task_id_only(self, temp_dir):
        """Test that force_claim=True with taskId (and no scope) passes validation."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            # Mock core function to raise NoAvailableTask to verify it was called
            mock_core.side_effect = NoAvailableTask("Task not found")

            async with Client(server) as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "force_claim": True,
                            "taskId": "T-test-task",
                        },
                    )

                # Should get NoAvailableTask from core function, not validation error
                assert "Task not found" in str(exc_info.value)
                # Verify core function was called (validation passed)
                mock_core.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_claim_with_worktree(self, temp_dir):
        """Test that force_claim works correctly with worktree parameter."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            mock_core.side_effect = NoAvailableTask("Task not found")

            async with Client(server) as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "force_claim": True,
                            "taskId": "T-test-task",
                            "worktree": "/workspace/hotfix",
                        },
                    )

                # Should pass validation and call core function
                assert "Task not found" in str(exc_info.value)
                mock_core.assert_called_once_with(
                    str(temp_dir), "/workspace/hotfix", None, "T-test-task", True
                )

    @pytest.mark.asyncio
    async def test_force_claim_parameter_passed_to_core_function(self, temp_dir):
        """Test that force_claim parameter validation allows call to core function."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            # Mock core function to verify it was called with correct parameters
            mock_core.side_effect = NoAvailableTask("Task not found")

            async with Client(server) as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "force_claim": True,
                            "taskId": "T-urgent-task",
                            "worktree": "/workspace/emergency",
                        },
                    )

                # Verify validation passed and core function was called
                # Verify force_claim parameter is properly passed to core function
                mock_core.assert_called_once_with(
                    str(temp_dir), "/workspace/emergency", None, "T-urgent-task", True
                )
                assert "Task not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_force_claim_validation_error_context(self, temp_dir):
        """Test that force_claim validation errors include proper context."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            # Test validation error context for missing taskId
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask", {"projectRoot": str(temp_dir), "force_claim": True}
                )

            error_message = str(exc_info.value)
            assert "force_claim parameter requires taskId to be specified" in error_message

            # Test validation error context for scope incompatibility
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": str(temp_dir),
                        "force_claim": True,
                        "taskId": "T-test",
                        "scope": "F-test",
                    },
                )

            error_message = str(exc_info.value)
            assert "force_claim parameter is incompatible with scope parameter" in error_message


class TestClaimNextTaskForceClaimImplementation:
    """Test force_claim parameter implementation and integration with core logic."""

    @pytest.mark.asyncio
    async def test_force_claim_parameter_passed_to_core_function(self, temp_dir):
        """Test that force_claim parameter is properly passed to core claiming logic."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            # Mock core function to verify it receives force_claim parameter
            mock_core.side_effect = NoAvailableTask("Task not found")

            async with Client(server) as client:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "taskId": "T-test-task",
                            "force_claim": True,
                            "worktree": "/workspace/test",
                        },
                    )

                # Verify core function was called with force_claim=True
                mock_core.assert_called_once_with(
                    str(temp_dir), "/workspace/test", None, "T-test-task", True
                )
                assert "Task not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_force_claim_false_passed_to_core_function(self, temp_dir):
        """Test that force_claim=False is properly passed to core claiming logic."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            mock_core.side_effect = NoAvailableTask("No tasks available")

            async with Client(server) as client:
                with pytest.raises(Exception):
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "taskId": "T-test-task",
                            "force_claim": False,
                        },
                    )

                # Verify core function was called with force_claim=False
                mock_core.assert_called_once_with(str(temp_dir), "", None, "T-test-task", False)

    @pytest.mark.asyncio
    async def test_force_claim_default_false_passed_to_core_function(self, temp_dir):
        """Test that omitted force_claim parameter defaults to False in core function."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            mock_core.side_effect = NoAvailableTask("No tasks available")

            async with Client(server) as client:
                with pytest.raises(Exception):
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "taskId": "T-test-task",
                            # force_claim omitted - should default to False
                        },
                    )

                # Verify core function was called with force_claim=False (default)
                mock_core.assert_called_once_with(str(temp_dir), "", None, "T-test-task", False)

    @pytest.mark.asyncio
    async def test_force_claim_with_priority_claiming_still_passes_false(self, temp_dir):
        """Test that force_claim=False is passed to core function for priority-based claiming."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        with patch("trellis_mcp.tools.claim_next_task.claim_next_task") as mock_core:
            mock_core.side_effect = NoAvailableTask("No tasks available")

            async with Client(server) as client:
                with pytest.raises(Exception):
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": str(temp_dir),
                            "force_claim": False,
                            # No taskId - should use priority-based claiming
                        },
                    )

                # Verify core function was called with force_claim=False for priority claiming
                mock_core.assert_called_once_with(str(temp_dir), "", None, None, False)
