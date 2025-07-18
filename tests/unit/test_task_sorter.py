"""Tests for task sorting utilities."""

from datetime import datetime, timedelta, timezone

from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel
from trellis_mcp.task_sorter import sort_tasks_by_priority


def create_test_task(
    task_id: str,
    priority: Priority,
    created: datetime,
    title: str = "Test task",
) -> TaskModel:
    """Create a test TaskModel with minimal required fields."""
    return TaskModel(
        kind=KindEnum.TASK,
        id=task_id,
        parent="F-test-feature",
        status=StatusEnum.OPEN,
        title=title,
        priority=priority,
        worktree=None,
        created=created,
        updated=created,
        schema_version="1.1",
    )


class TestSortTasksByPriority:
    """Test cases for sort_tasks_by_priority function."""

    def test_empty_list(self):
        """Test sorting an empty list returns empty list."""
        result = sort_tasks_by_priority([])
        assert result == []

    def test_single_task(self):
        """Test sorting a single task returns the same task."""
        task = create_test_task(
            "T-test-001",
            Priority.NORMAL,
            datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        result = sort_tasks_by_priority([task])
        assert result == [task]

    def test_priority_ordering(self):
        """Test tasks are sorted by priority: high, normal, low."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create tasks with different priorities (in reverse order)
        low_task = create_test_task("T-low", Priority.LOW, base_time, "Low priority")
        normal_task = create_test_task("T-normal", Priority.NORMAL, base_time, "Normal priority")
        high_task = create_test_task("T-high", Priority.HIGH, base_time, "High priority")

        # Sort in reverse priority order
        tasks = [low_task, normal_task, high_task]
        result = sort_tasks_by_priority(tasks)

        # Should be sorted high -> normal -> low
        assert result == [high_task, normal_task, low_task]
        assert [task.priority for task in result] == [Priority.HIGH, Priority.NORMAL, Priority.LOW]

    def test_creation_date_ordering_same_priority(self):
        """Test tasks with same priority are sorted by creation date (older first)."""
        # Create tasks with same priority but different creation dates
        newer_time = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        older_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        newer_task = create_test_task("T-newer", Priority.NORMAL, newer_time, "Newer task")
        older_task = create_test_task("T-older", Priority.NORMAL, older_time, "Older task")

        # Add in reverse chronological order
        tasks = [newer_task, older_task]
        result = sort_tasks_by_priority(tasks)

        # Should be sorted older first
        assert result == [older_task, newer_task]
        assert result[0].created < result[1].created

    def test_mixed_priority_and_date_ordering(self):
        """Test complex sorting with mixed priorities and dates."""
        # Create a variety of tasks with different priorities and dates
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        tasks = [
            create_test_task(
                "T-low-new", Priority.LOW, base_time + timedelta(hours=1), "Low priority, newer"
            ),
            create_test_task("T-high-old", Priority.HIGH, base_time, "High priority, older"),
            create_test_task(
                "T-normal-mid",
                Priority.NORMAL,
                base_time + timedelta(hours=1),
                "Normal priority, middle",
            ),
            create_test_task(
                "T-high-new", Priority.HIGH, base_time + timedelta(hours=1), "High priority, newer"
            ),
            create_test_task("T-low-old", Priority.LOW, base_time, "Low priority, older"),
        ]

        result = sort_tasks_by_priority(tasks)

        # Verify priority ordering
        priorities = [task.priority for task in result]
        assert priorities == [
            Priority.HIGH,
            Priority.HIGH,
            Priority.NORMAL,
            Priority.LOW,
            Priority.LOW,
        ]

        # Verify that within same priority, older tasks come first
        high_tasks = [task for task in result if task.priority == Priority.HIGH]
        assert high_tasks[0].created <= high_tasks[1].created

        low_tasks = [task for task in result if task.priority == Priority.LOW]
        assert low_tasks[0].created <= low_tasks[1].created

    def test_original_list_not_modified(self):
        """Test that the original list is not modified during sorting."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        original_tasks = [
            create_test_task("T-002", Priority.LOW, base_time),
            create_test_task("T-001", Priority.HIGH, base_time),
        ]
        original_order = original_tasks.copy()

        result = sort_tasks_by_priority(original_tasks)

        # Original list should be unchanged
        assert original_tasks == original_order
        # Result should be different (sorted)
        assert result != original_tasks
        assert result[0].priority == Priority.HIGH
        assert result[1].priority == Priority.LOW

    def test_multiple_same_priority_and_date(self):
        """Test sorting when tasks have identical priority and creation dates."""
        same_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task1 = create_test_task("T-001", Priority.NORMAL, same_time, "Task 1")
        task2 = create_test_task("T-002", Priority.NORMAL, same_time, "Task 2")
        task3 = create_test_task("T-003", Priority.NORMAL, same_time, "Task 3")

        tasks = [task2, task3, task1]
        result = sort_tasks_by_priority(tasks)

        # All tasks should have same priority and time
        assert len(result) == 3
        assert all(task.priority == Priority.NORMAL for task in result)
        assert all(task.created == same_time for task in result)
        # Order among identical sort keys is stable but not guaranteed
        # Check that all original tasks are present by comparing IDs
        result_ids = {task.id for task in result}
        original_ids = {task.id for task in tasks}
        assert result_ids == original_ids

    def test_microsecond_precision_sorting(self):
        """Test sorting with microsecond precision in creation dates."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create tasks with microsecond differences
        task1 = create_test_task("T-001", Priority.NORMAL, base_time, "First")
        task2 = create_test_task(
            "T-002", Priority.NORMAL, base_time.replace(microsecond=1000), "Second"
        )
        task3 = create_test_task(
            "T-003", Priority.NORMAL, base_time.replace(microsecond=2000), "Third"
        )

        tasks = [task3, task1, task2]
        result = sort_tasks_by_priority(tasks)

        assert result == [task1, task2, task3]
        assert result[0].created < result[1].created < result[2].created
