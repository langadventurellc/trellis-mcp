"""Tests for system-level exception classes.

This module consolidates system-level exception tests:
- NoAvailableTask - System-level task availability errors
"""

import pytest

from src.trellis_mcp.exceptions.no_available_task import NoAvailableTask


class TestNoAvailableTask:
    """Test cases for NoAvailableTask exception class."""

    def test_no_available_task_can_be_raised(self):
        """Test that NoAvailableTask can be raised and caught."""
        with pytest.raises(NoAvailableTask):
            raise NoAvailableTask("No tasks available to claim")

    def test_no_available_task_with_message(self):
        """Test that NoAvailableTask correctly stores message."""
        error = NoAvailableTask("No unblocked tasks available in the backlog")
        assert str(error) == "No unblocked tasks available in the backlog"

    def test_no_available_task_inherits_from_exception(self):
        """Test that NoAvailableTask inherits from Exception."""
        error = NoAvailableTask("Test error")
        assert isinstance(error, Exception)

    def test_no_available_task_no_message(self):
        """Test that NoAvailableTask can be created without message."""
        error = NoAvailableTask()
        assert str(error) == ""

    def test_no_available_task_empty_backlog_scenario(self):
        """Test NoAvailableTask for empty backlog scenario."""
        error = NoAvailableTask("No open tasks exist in the backlog")

        assert str(error) == "No open tasks exist in the backlog"
        assert "backlog" in str(error)
        assert "open tasks" in str(error)

    def test_no_available_task_blocked_tasks_scenario(self):
        """Test NoAvailableTask for blocked tasks scenario."""
        error = NoAvailableTask(
            "All open tasks have incomplete prerequisites. "
            "3 tasks are blocked waiting for dependencies."
        )

        assert "prerequisites" in str(error)
        assert "blocked" in str(error)
        assert "dependencies" in str(error)
        assert "3 tasks" in str(error)

    def test_no_available_task_with_context_details(self):
        """Test NoAvailableTask with detailed context information."""
        error = NoAvailableTask(
            "No available tasks found. Checked 15 tasks: "
            "5 in-progress, 3 review, 4 done, 3 blocked by prerequisites."
        )

        assert "15 tasks" in str(error)
        assert "in-progress" in str(error)
        assert "review" in str(error)
        assert "done" in str(error)
        assert "blocked by prerequisites" in str(error)

    def test_no_available_task_with_project_context(self):
        """Test NoAvailableTask with project context."""
        project_id = "P-user-management"
        error = NoAvailableTask(f"No available tasks in project {project_id}")

        assert str(error) == f"No available tasks in project {project_id}"
        assert "P-user-management" in str(error)

    def test_no_available_task_exception_behavior(self):
        """Test that NoAvailableTask behaves like a standard exception."""
        error = NoAvailableTask("No tasks available")

        # Should be able to access args
        assert error.args == ("No tasks available",)

        # Should be able to raise and catch as Exception
        with pytest.raises(Exception):
            raise error

    def test_no_available_task_multiple_args(self):
        """Test NoAvailableTask with multiple arguments."""
        error = NoAvailableTask("No tasks available", "backlog empty", "all tasks completed")

        assert error.args == ("No tasks available", "backlog empty", "all tasks completed")
        assert "No tasks available" in str(error)

    def test_no_available_task_with_statistics(self):
        """Test NoAvailableTask with backlog statistics."""
        error = NoAvailableTask(
            "Task claim failed: 0 open tasks, 8 in-progress, 12 completed, 4 blocked"
        )

        assert "Task claim failed" in str(error)
        assert "0 open tasks" in str(error)
        assert "8 in-progress" in str(error)
        assert "12 completed" in str(error)
        assert "4 blocked" in str(error)
