"""Tests for InvalidStatusForCompletion exception class."""

import pytest

from src.trellis_mcp.exceptions.invalid_status_for_completion import InvalidStatusForCompletion


class TestInvalidStatusForCompletion:
    """Test cases for InvalidStatusForCompletion exception class."""

    def test_invalid_status_for_completion_can_be_raised(self):
        """Test that InvalidStatusForCompletion can be raised and caught."""
        with pytest.raises(InvalidStatusForCompletion):
            raise InvalidStatusForCompletion("Test invalid status error")

    def test_invalid_status_for_completion_with_message(self):
        """Test that InvalidStatusForCompletion correctly stores message."""
        error = InvalidStatusForCompletion("Task T-123 is in 'done' status and cannot be completed")
        assert str(error) == "Task T-123 is in 'done' status and cannot be completed"

    def test_invalid_status_for_completion_inherits_from_exception(self):
        """Test that InvalidStatusForCompletion inherits from Exception."""
        error = InvalidStatusForCompletion("Test error")
        assert isinstance(error, Exception)

    def test_invalid_status_for_completion_no_message(self):
        """Test that InvalidStatusForCompletion can be created without message."""
        error = InvalidStatusForCompletion()
        assert str(error) == ""

    def test_invalid_status_for_completion_with_task_context(self):
        """Test InvalidStatusForCompletion with task-specific context."""
        task_id = "T-implement-feature"
        current_status = "done"
        valid_statuses = ["in-progress", "review"]

        message = (
            f"Cannot complete task {task_id} with status '{current_status}'. "
            f"Valid statuses: {', '.join(valid_statuses)}"
        )
        error = InvalidStatusForCompletion(message)

        assert str(error) == message
        assert "T-implement-feature" in str(error)
        assert "done" in str(error)
        assert "in-progress" in str(error)
        assert "review" in str(error)

    def test_invalid_status_for_completion_with_detailed_message(self):
        """Test InvalidStatusForCompletion with detailed error message."""
        error = InvalidStatusForCompletion(
            "Task completion blocked: Task T-add-validation is in 'open' status. "
            "Only tasks in 'in-progress' or 'review' status can be completed."
        )

        assert "Task completion blocked" in str(error)
        assert "T-add-validation" in str(error)
        assert "open" in str(error)
        assert "in-progress" in str(error)
        assert "review" in str(error)

    def test_invalid_status_for_completion_exception_behavior(self):
        """Test that InvalidStatusForCompletion behaves like a standard exception."""
        error = InvalidStatusForCompletion("Task completion error")

        # Should be able to access args
        assert error.args == ("Task completion error",)

        # Should be able to raise and catch as Exception
        with pytest.raises(Exception):
            raise error

    def test_invalid_status_for_completion_multiple_args(self):
        """Test InvalidStatusForCompletion with multiple arguments."""
        error = InvalidStatusForCompletion("Task T-123", "status: done", "expected: in-progress")

        assert error.args == ("Task T-123", "status: done", "expected: in-progress")
        assert "Task T-123" in str(error)
