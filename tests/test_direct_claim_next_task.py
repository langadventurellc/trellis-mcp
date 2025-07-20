"""Tests for direct task claiming functionality."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from trellis_mcp.claim_next_task import claim_specific_task
from trellis_mcp.exceptions.no_available_task import NoAvailableTask
from trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


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


class TestDirectClaimingSuccess:
    """Test successful direct claiming scenarios."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_claim_specific_task_success(self, mock_find, mock_unblocked, mock_write):
        """Test successful direct task claiming by ID."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        target_task = create_test_task("T-target", Priority.NORMAL, base_time, title="Target task")

        mock_find.return_value = target_task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "T-target")

        # Verify task was claimed correctly
        assert result.id == "T-target"
        assert result.status == StatusEnum.IN_PROGRESS
        assert result.title == "Target task"

        # Verify function calls
        mock_find.assert_called_once_with(Path("/test"), "T-target")
        mock_unblocked.assert_called_once_with(target_task, Path("/test/project"))
        mock_write.assert_called_once_with(result, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_claim_specific_task_with_worktree(self, mock_find, mock_unblocked, mock_write):
        """Test direct task claiming with worktree assignment."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        target_task = create_test_task("T-target", Priority.NORMAL, base_time)

        mock_find.return_value = target_task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "T-target", "/workspace/feature")

        # Verify worktree assignment
        assert result.worktree == "/workspace/feature"

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_claim_specific_task_hierarchical_task(self, mock_find, mock_unblocked, mock_write):
        """Test claiming hierarchical task (T- prefixed)."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        hierarchical_task = create_test_task("T-hierarchical-task", Priority.HIGH, base_time)

        mock_find.return_value = hierarchical_task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "T-hierarchical-task")

        assert result.id == "T-hierarchical-task"
        assert result.status == StatusEnum.IN_PROGRESS

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_claim_specific_task_standalone_task(self, mock_find, mock_unblocked, mock_write):
        """Test claiming standalone task."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        standalone_task = create_test_task("standalone-task", Priority.NORMAL, base_time)
        standalone_task.parent = None  # Standalone tasks have no parent

        mock_find.return_value = standalone_task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "standalone-task")

        assert result.id == "standalone-task"
        assert result.status == StatusEnum.IN_PROGRESS


class TestDirectClaimingValidation:
    """Test validation and error handling in direct claiming."""

    def test_empty_task_id_raises_validation_error(self):
        """Test that empty task ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            claim_specific_task("/test/project", "")

        assert "Task ID cannot be empty" in str(exc_info.value)
        assert exc_info.value.error_codes[0] == ValidationErrorCode.MISSING_REQUIRED_FIELD

    def test_whitespace_task_id_raises_validation_error(self):
        """Test that whitespace-only task ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            claim_specific_task("/test/project", "   ")

        assert "Task ID cannot be empty" in str(exc_info.value)

    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_task_not_found_raises_no_available_task(self, mock_find):
        """Test that non-existent task ID raises NoAvailableTask."""
        mock_find.return_value = None

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_specific_task("/test/project", "T-nonexistent")

        assert "Task not found: T-nonexistent" in str(exc_info.value)
        mock_find.assert_called_once_with(Path("/test"), "T-nonexistent")

    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_task_wrong_status_raises_no_available_task(self, mock_find):
        """Test that task with wrong status raises NoAvailableTask."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        in_progress_task = create_test_task(
            "T-busy", Priority.NORMAL, base_time, status=StatusEnum.IN_PROGRESS
        )

        mock_find.return_value = in_progress_task

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_specific_task("/test/project", "T-busy")

        assert "Task T-busy is not available for claiming (status: in-progress)" in str(
            exc_info.value
        )

    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_task_blocked_prerequisites_raises_no_available_task(self, mock_find, mock_unblocked):
        """Test that task with incomplete prerequisites raises NoAvailableTask."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-blocked", Priority.NORMAL, base_time, prerequisites=["T-prereq"]
        )

        mock_find.return_value = blocked_task
        mock_unblocked.return_value = False

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_specific_task("/test/project", "T-blocked")

        assert "Task T-blocked cannot be claimed - prerequisites not completed" in str(
            exc_info.value
        )
        mock_unblocked.assert_called_once_with(blocked_task, Path("/test/project"))


class TestDirectClaimingStatusValidation:
    """Test status validation for various task states."""

    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_cannot_claim_done_task(self, mock_find):
        """Test that completed tasks cannot be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        done_task = create_test_task("T-done", Priority.NORMAL, base_time, status=StatusEnum.DONE)

        mock_find.return_value = done_task

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_specific_task("/test/project", "T-done")

        assert "Task T-done is not available for claiming (status: done)" in str(exc_info.value)

    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_cannot_claim_review_task(self, mock_find):
        """Test that tasks in review cannot be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        review_task = create_test_task(
            "T-review", Priority.NORMAL, base_time, status=StatusEnum.REVIEW
        )

        mock_find.return_value = review_task

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_specific_task("/test/project", "T-review")

        assert "Task T-review is not available for claiming (status: review)" in str(exc_info.value)


class TestDirectClaimingPrerequisiteValidation:
    """Test prerequisite validation in direct claiming."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_task_with_no_prerequisites_claimable(self, mock_find, mock_unblocked, mock_write):
        """Test that tasks with no prerequisites can be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-no-prereqs", Priority.NORMAL, base_time, prerequisites=[])

        mock_find.return_value = task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "T-no-prereqs")

        assert result.id == "T-no-prereqs"
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_task_with_completed_prerequisites_claimable(
        self, mock_find, mock_unblocked, mock_write
    ):
        """Test that tasks with all prerequisites completed can be claimed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task(
            "T-with-prereqs", Priority.NORMAL, base_time, prerequisites=["T-completed"]
        )

        mock_find.return_value = task
        mock_unblocked.return_value = True  # Simulate all prereqs completed

        result = claim_specific_task("/test/project", "T-with-prereqs")

        assert result.id == "T-with-prereqs"
        mock_unblocked.assert_called_once_with(task, Path("/test/project"))


class TestDirectClaimingAtomicOperations:
    """Test atomic operation behavior in direct claiming."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_status_updated_atomically(self, mock_find, mock_unblocked, mock_write):
        """Test that task status is updated to IN_PROGRESS atomically."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-atomic", Priority.NORMAL, base_time, status=StatusEnum.OPEN)

        mock_find.return_value = task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "T-atomic")

        # Verify status change
        assert result.status == StatusEnum.IN_PROGRESS
        assert task.status == StatusEnum.IN_PROGRESS  # Original object modified

        # Verify atomic write was called
        mock_write.assert_called_once_with(result, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_updated_timestamp_reflects_claim_time(self, mock_find, mock_unblocked, mock_write):
        """Test that updated timestamp is set to current time when claiming."""
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        task = create_test_task("T-timestamp", Priority.NORMAL, base_time)
        original_updated = task.updated

        mock_find.return_value = task
        mock_unblocked.return_value = True

        # Claim the task
        claim_start = datetime.now()
        result = claim_specific_task("/test/project", "T-timestamp")
        claim_end = datetime.now()

        # Updated timestamp should be current time (within reasonable range)
        assert result.updated > original_updated
        assert claim_start <= result.updated <= claim_end


class TestDirectClaimingCrossSystemSupport:
    """Test cross-system compatibility (hierarchical and standalone tasks)."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_claim_task_across_both_systems(self, mock_find, mock_unblocked, mock_write):
        """Test that claiming works across both hierarchical and standalone systems."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Test hierarchical task claiming
        hierarchical_task = create_test_task("T-hierarchical", Priority.NORMAL, base_time)

        mock_find.return_value = hierarchical_task
        mock_unblocked.return_value = True

        result_h = claim_specific_task("/test/project", "T-hierarchical")
        assert result_h.id == "T-hierarchical"

        # Test standalone task claiming
        standalone_task = create_test_task("standalone-task", Priority.NORMAL, base_time)
        standalone_task.parent = None

        mock_find.return_value = standalone_task

        result_s = claim_specific_task("/test/project", "standalone-task")
        assert result_s.id == "standalone-task"

        # Verify both use same underlying infrastructure
        assert mock_find.call_count == 2
        assert mock_unblocked.call_count == 2
        assert mock_write.call_count == 2


class TestDirectClaimingResponseFormat:
    """Test response format compliance."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_response_format_matches_specification(self, mock_find, mock_unblocked, mock_write):
        """Test that response format matches the specification exactly."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task(
            "T-response", Priority.HIGH, base_time, title="Response Format Test"
        )

        mock_find.return_value = task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "T-response", "/workspace/test")

        # Verify response is a TaskModel
        assert isinstance(result, TaskModel)

        # Verify task object properties
        assert result.id == "T-response"
        assert result.status == StatusEnum.IN_PROGRESS
        assert result.title == "Response Format Test"
        assert result.priority == Priority.HIGH
        assert result.worktree == "/workspace/test"


class TestDirectClaimingEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_task_id_whitespace_trimming(self, mock_find, mock_unblocked, mock_write):
        """Test that task ID whitespace is properly trimmed."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-trimmed", Priority.NORMAL, base_time)

        mock_find.return_value = task
        mock_unblocked.return_value = True

        # Test with leading/trailing whitespace
        result = claim_specific_task("/test/project", "  T-trimmed  ")

        assert result.id == "T-trimmed"
        # Verify _find_task_by_id was called with trimmed ID
        mock_find.assert_called_once_with(Path("/test"), "T-trimmed")

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_empty_worktree_parameter(self, mock_find, mock_unblocked, mock_write):
        """Test behavior with empty worktree parameter."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-empty-worktree", Priority.NORMAL, base_time, worktree=None)

        mock_find.return_value = task
        mock_unblocked.return_value = True

        result = claim_specific_task("/test/project", "T-empty-worktree", "")

        # Worktree should remain None when empty string provided
        assert result.worktree is None


class TestDirectClaimingForceClaimBypass:
    """Test force claim functionality for bypassing prerequisites."""

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_force_claim_bypasses_prerequisite_validation(self, mock_find, mock_write):
        """Test that force_claim=True bypasses prerequisite validation."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-blocked", Priority.NORMAL, base_time, prerequisites=["T-incomplete"]
        )

        mock_find.return_value = blocked_task

        # Should succeed with force_claim=True even when prerequisites are incomplete
        result = claim_specific_task("/test/project", "T-blocked", force_claim=True)

        assert result.id == "T-blocked"
        assert result.status == StatusEnum.IN_PROGRESS

        # Verify is_unblocked was NOT called when force_claim=True
        # (we don't mock is_unblocked, so if it were called and returned False,
        # this would raise NoAvailableTask)
        mock_write.assert_called_once_with(result, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.is_unblocked")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_force_claim_false_maintains_prerequisite_validation(
        self, mock_find, mock_unblocked, mock_write
    ):
        """Test that force_claim=False maintains normal prerequisite validation."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-blocked", Priority.NORMAL, base_time, prerequisites=["T-incomplete"]
        )

        mock_find.return_value = blocked_task
        mock_unblocked.return_value = False  # Simulate incomplete prerequisites

        with pytest.raises(NoAvailableTask) as exc_info:
            claim_specific_task("/test/project", "T-blocked", force_claim=False)

        assert "Task T-blocked cannot be claimed - prerequisites not completed" in str(
            exc_info.value
        )
        mock_unblocked.assert_called_once_with(blocked_task, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_force_claim_with_no_prerequisites_works_normally(self, mock_find, mock_write):
        """Test that force_claim=True works correctly for tasks with no prerequisites."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task_no_prereqs = create_test_task(
            "T-no-prereqs", Priority.NORMAL, base_time, prerequisites=[]
        )

        mock_find.return_value = task_no_prereqs

        result = claim_specific_task("/test/project", "T-no-prereqs", force_claim=True)

        assert result.id == "T-no-prereqs"
        assert result.status == StatusEnum.IN_PROGRESS
        mock_write.assert_called_once_with(result, Path("/test/project"))

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.logging.warning")
    @patch("trellis_mcp.validation.get_all_objects")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_force_claim_logs_warning_for_incomplete_prerequisites(
        self, mock_find, mock_get_objects, mock_log_warning, mock_write
    ):
        """Test that force_claim logs warning when bypassing incomplete prerequisites."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-blocked", Priority.NORMAL, base_time, prerequisites=["T-incomplete", "T-missing"]
        )

        mock_find.return_value = blocked_task
        # Mock get_all_objects to simulate incomplete prerequisites
        # Note: clean_prerequisite_id removes T- prefix, so "T-incomplete" becomes "incomplete"
        mock_get_objects.return_value = {
            "incomplete": {"status": "in-progress"},  # Not done
            # "missing" is not in the dict, so it's missing
        }

        result = claim_specific_task("/test/project", "T-blocked", force_claim=True)

        assert result.id == "T-blocked"
        assert result.status == StatusEnum.IN_PROGRESS

        # Verify warning was logged with details about incomplete prerequisites
        mock_log_warning.assert_called_once()
        warning_call = mock_log_warning.call_args[0][0]
        assert "Force claiming task T-blocked with incomplete prerequisites" in warning_call
        assert "T-incomplete" in warning_call
        assert "T-missing" in warning_call

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task.logging.warning")
    @patch("trellis_mcp.validation.get_all_objects")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_force_claim_logs_audit_failure_gracefully(
        self, mock_find, mock_get_objects, mock_log_warning, mock_write
    ):
        """Test that force_claim handles audit logging failures gracefully."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        blocked_task = create_test_task(
            "T-blocked", Priority.NORMAL, base_time, prerequisites=["T-incomplete"]
        )

        mock_find.return_value = blocked_task
        # Simulate error in audit logging
        mock_get_objects.side_effect = Exception("Audit check failed")

        # Should still succeed with force claim despite audit logging failure
        result = claim_specific_task("/test/project", "T-blocked", force_claim=True)

        assert result.id == "T-blocked"
        assert result.status == StatusEnum.IN_PROGRESS

        # Verify fallback warning was logged
        mock_log_warning.assert_called_once()
        warning_call = mock_log_warning.call_args[0][0]
        assert "Force claiming task T-blocked" in warning_call
        assert "Could not determine prerequisite status for audit" in warning_call

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.validation.get_all_objects")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_force_claim_with_completed_prerequisites_no_warning(
        self, mock_find, mock_get_objects, mock_write
    ):
        """Test that force_claim with completed prerequisites doesn't log warnings."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task_with_prereqs = create_test_task(
            "T-with-prereqs", Priority.NORMAL, base_time, prerequisites=["T-completed"]
        )

        mock_find.return_value = task_with_prereqs
        # Mock all prerequisites as completed (note: clean_prerequisite_id removes T- prefix)
        mock_get_objects.return_value = {"completed": {"status": "done"}}

        with patch("trellis_mcp.claim_next_task.logging.warning") as mock_log_warning:
            result = claim_specific_task("/test/project", "T-with-prereqs", force_claim=True)

            assert result.id == "T-with-prereqs"
            assert result.status == StatusEnum.IN_PROGRESS

            # No warning should be logged when all prerequisites are completed
            mock_log_warning.assert_not_called()

    @patch("trellis_mcp.claim_next_task.write_object")
    @patch("trellis_mcp.claim_next_task._find_task_by_id")
    def test_force_claim_default_parameter_is_false(self, mock_find, mock_write):
        """Test that force_claim parameter defaults to False."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        task = create_test_task("T-test", Priority.NORMAL, base_time, prerequisites=[])

        mock_find.return_value = task

        # Call without force_claim parameter (should default to False)
        result = claim_specific_task("/test/project", "T-test")

        assert result.id == "T-test"
        assert result.status == StatusEnum.IN_PROGRESS
        # No prerequisites to check, so this should work fine
