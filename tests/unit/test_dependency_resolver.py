"""Tests for dependency resolver functionality."""

from datetime import datetime
from unittest.mock import patch

from trellis_mcp.dependency_resolver import is_unblocked
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


class TestIsUnblocked:
    """Test cases for the is_unblocked function."""

    def test_no_prerequisites_is_unblocked(self):
        """Task with no prerequisites should be unblocked."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-001",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value={}):
            assert is_unblocked(task) is True

    def test_empty_prerequisites_list_is_unblocked(self):
        """Task with empty prerequisites list should be unblocked."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-002",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value={}):
            assert is_unblocked(task) is True

    def test_all_prerequisites_done_is_unblocked(self):
        """Task with all prerequisites completed should be unblocked."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-003",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["setup-db", "create-auth"],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {
            "setup-db": {"status": "done", "kind": "task"},
            "create-auth": {"status": "done", "kind": "task"},
        }

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            assert is_unblocked(task) is True

    def test_some_prerequisites_incomplete_is_blocked(self):
        """Task with some incomplete prerequisites should be blocked."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-004",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["setup-db", "create-auth"],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {
            "setup-db": {"status": "done", "kind": "task"},
            "create-auth": {"status": "in-progress", "kind": "task"},
        }

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            assert is_unblocked(task) is False

    def test_missing_prerequisite_is_blocked(self):
        """Task with missing prerequisite should be blocked."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-005",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["setup-db", "missing-task"],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {
            "setup-db": {"status": "done", "kind": "task"}
            # "missing-task" is not in the objects
        }

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            assert is_unblocked(task) is False

    def test_prerequisite_with_t_prefix_is_cleaned(self):
        """Prerequisites with T- prefix should be cleaned and checked properly."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-006",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["T-001", "T-002"],  # With T- prefixes
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {
            "001": {"status": "done", "kind": "task"},  # Cleaned IDs in storage
            "002": {"status": "done", "kind": "task"},
        }

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            with patch("trellis_mcp.dependency_resolver.clean_prerequisite_id") as mock_clean:
                # Mock the cleaning function to remove T- prefix
                mock_clean.side_effect = lambda x: x[2:] if x.startswith("T-") else x
                assert is_unblocked(task) is True

    def test_prerequisite_without_status_is_blocked(self):
        """Prerequisite without status field should block the task."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-007",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["no-status-task"],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {"no-status-task": {"kind": "task"}}  # No status field

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            assert is_unblocked(task) is False

    def test_prerequisite_with_review_status_is_blocked(self):
        """Prerequisites in review status should still block the task."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-008",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["in-review-task"],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {"in-review-task": {"status": "review", "kind": "task"}}

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            assert is_unblocked(task) is False

    def test_mixed_prerequisite_states_with_one_incomplete(self):
        """Task with mix of complete/incomplete prerequisites should be blocked."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-009",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["done-task", "open-task", "in-progress-task"],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {
            "done-task": {"status": "done", "kind": "task"},
            "open-task": {"status": "open", "kind": "task"},
            "in-progress-task": {"status": "in-progress", "kind": "task"},
        }

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            assert is_unblocked(task) is False

    def test_single_prerequisite_done_is_unblocked(self):
        """Task with single completed prerequisite should be unblocked."""
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task-010",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=["single-task"],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        mock_objects = {"single-task": {"status": "done", "kind": "task"}}

        with patch("trellis_mcp.dependency_resolver.get_all_objects", return_value=mock_objects):
            assert is_unblocked(task) is True
