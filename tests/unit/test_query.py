"""Tests for query utilities."""

from datetime import datetime

from trellis_mcp.io_utils import write_markdown
from trellis_mcp.models.common import Priority
from trellis_mcp.query import get_oldest_review, is_reviewable
from trellis_mcp.schema.feature import FeatureModel
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


def test_is_reviewable_with_review_status():
    """Test that is_reviewable returns True for objects with review status."""
    task = TaskModel(
        kind=KindEnum.TASK,
        id="T-test",
        parent="F-parent",
        status=StatusEnum.REVIEW,
        title="Test task",
        priority=Priority.NORMAL,
        worktree=None,
        created=datetime.now(),
        updated=datetime.now(),
        schema_version="1.0",
    )

    assert is_reviewable(task) is True


def test_is_reviewable_with_non_review_status():
    """Test that is_reviewable returns False for objects without review status."""
    # Test with open status
    task_open = TaskModel(
        kind=KindEnum.TASK,
        id="T-test-open",
        parent="F-parent",
        status=StatusEnum.OPEN,
        title="Test open task",
        priority=Priority.NORMAL,
        worktree=None,
        created=datetime.now(),
        updated=datetime.now(),
        schema_version="1.0",
    )

    assert is_reviewable(task_open) is False

    # Test with in-progress status
    task_in_progress = TaskModel(
        kind=KindEnum.TASK,
        id="T-test-progress",
        parent="F-parent",
        status=StatusEnum.IN_PROGRESS,
        title="Test in-progress task",
        priority=Priority.NORMAL,
        worktree=None,
        created=datetime.now(),
        updated=datetime.now(),
        schema_version="1.0",
    )

    assert is_reviewable(task_in_progress) is False

    # Test with done status
    task_done = TaskModel(
        kind=KindEnum.TASK,
        id="T-test-done",
        parent="F-parent",
        status=StatusEnum.DONE,
        title="Test done task",
        priority=Priority.NORMAL,
        worktree=None,
        created=datetime.now(),
        updated=datetime.now(),
        schema_version="1.0",
    )

    assert is_reviewable(task_done) is False


def test_is_reviewable_with_feature():
    """Test that is_reviewable returns False for features (which cannot have review status)."""
    feature = FeatureModel(
        kind=KindEnum.FEATURE,
        id="F-test",
        parent="E-parent",
        status=StatusEnum.IN_PROGRESS,
        title="Test feature",
        priority=Priority.NORMAL,
        worktree=None,
        created=datetime.now(),
        updated=datetime.now(),
        schema_version="1.0",
    )

    assert is_reviewable(feature) is False


def test_get_oldest_review_no_review_tasks(temp_dir):
    """Test get_oldest_review returns None when no review tasks exist."""
    planning_dir = temp_dir / "planning"

    # Test with no directory structure at all
    assert get_oldest_review(planning_dir) is None

    # Test with directory structure but no tasks
    feature_dir = planning_dir / "projects" / "P-test" / "epics" / "E-test" / "features" / "F-test"
    tasks_open_dir = feature_dir / "tasks-open"
    tasks_open_dir.mkdir(parents=True)

    assert get_oldest_review(planning_dir) is None

    # Test with tasks but none in review status
    task_yaml = {
        "kind": "task",
        "id": "test-task-open",
        "parent": "F-test",
        "status": "open",
        "title": "Open task",
        "priority": "normal",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T12:00:00Z",
        "schema_version": "1.0",
        "prerequisites": [],
    }
    write_markdown(tasks_open_dir / "T-test-task-open.md", task_yaml, "# Open Task")

    assert get_oldest_review(planning_dir) is None


def test_get_oldest_review_single_review_task(temp_dir):
    """Test get_oldest_review returns the single review task when only one exists."""
    planning_dir = temp_dir / "planning"
    feature_dir = planning_dir / "projects" / "P-test" / "epics" / "E-test" / "features" / "F-test"
    tasks_open_dir = feature_dir / "tasks-open"
    tasks_open_dir.mkdir(parents=True)

    # Create one task in review status
    task_yaml = {
        "kind": "task",
        "id": "test-task-review",
        "parent": "F-test",
        "status": "review",
        "title": "Review task",
        "priority": "normal",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T13:00:00Z",
        "schema_version": "1.0",
        "prerequisites": [],
    }
    write_markdown(tasks_open_dir / "T-test-task-review.md", task_yaml, "# Review Task")

    result = get_oldest_review(planning_dir)

    assert result is not None
    assert result.id == "test-task-review"
    assert result.status == StatusEnum.REVIEW
    assert result.title == "Review task"
    assert result.priority == Priority.NORMAL


def test_get_oldest_review_multiple_tasks_oldest_first(temp_dir):
    """Test get_oldest_review returns task with oldest updated timestamp."""
    planning_dir = temp_dir / "planning"
    feature_dir = planning_dir / "projects" / "P-test" / "epics" / "E-test" / "features" / "F-test"
    tasks_open_dir = feature_dir / "tasks-open"
    tasks_open_dir.mkdir(parents=True)

    # Create older task (should be selected)
    older_task_yaml = {
        "kind": "task",
        "id": "older-task",
        "parent": "F-test",
        "status": "review",
        "title": "Older review task",
        "priority": "normal",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T12:00:00Z",  # Older timestamp
        "schema_version": "1.0",
        "prerequisites": [],
    }
    write_markdown(tasks_open_dir / "T-older-task.md", older_task_yaml, "# Older Task")

    # Create newer task
    newer_task_yaml = {
        "kind": "task",
        "id": "newer-task",
        "parent": "F-test",
        "status": "review",
        "title": "Newer review task",
        "priority": "normal",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T14:00:00Z",  # Newer timestamp
        "schema_version": "1.0",
        "prerequisites": [],
    }
    write_markdown(tasks_open_dir / "T-newer-task.md", newer_task_yaml, "# Newer Task")

    result = get_oldest_review(planning_dir)

    assert result is not None
    assert result.id == "older-task"
    assert result.title == "Older review task"


def test_get_oldest_review_priority_tiebreaker(temp_dir):
    """Test get_oldest_review uses priority as tiebreaker when timestamps are equal."""
    planning_dir = temp_dir / "planning"
    feature_dir = planning_dir / "projects" / "P-test" / "epics" / "E-test" / "features" / "F-test"
    tasks_open_dir = feature_dir / "tasks-open"
    tasks_open_dir.mkdir(parents=True)

    same_timestamp = "2025-01-01T12:00:00Z"

    # Create low priority task
    low_task_yaml = {
        "kind": "task",
        "id": "low-priority-task",
        "parent": "F-test",
        "status": "review",
        "title": "Low priority task",
        "priority": "low",
        "created": same_timestamp,
        "updated": same_timestamp,
        "schema_version": "1.0",
        "prerequisites": [],
    }
    write_markdown(tasks_open_dir / "T-low-priority.md", low_task_yaml, "# Low Priority")

    # Create high priority task (should be selected)
    high_task_yaml = {
        "kind": "task",
        "id": "high-priority-task",
        "parent": "F-test",
        "status": "review",
        "title": "High priority task",
        "priority": "high",
        "created": same_timestamp,
        "updated": same_timestamp,
        "schema_version": "1.0",
        "prerequisites": [],
    }
    write_markdown(tasks_open_dir / "T-high-priority.md", high_task_yaml, "# High Priority")

    # Create normal priority task
    normal_task_yaml = {
        "kind": "task",
        "id": "normal-priority-task",
        "parent": "F-test",
        "status": "review",
        "title": "Normal priority task",
        "priority": "normal",
        "created": same_timestamp,
        "updated": same_timestamp,
        "schema_version": "1.0",
        "prerequisites": [],
    }
    write_markdown(tasks_open_dir / "T-normal-priority.md", normal_task_yaml, "# Normal Priority")

    result = get_oldest_review(planning_dir)

    assert result is not None
    assert result.id == "high-priority-task"
    assert result.priority == Priority.HIGH
