"""Tests for task sorting functionality.

This module consolidates tests for task sorting utilities including:
- task_sort_key: Function that generates sorting keys for tasks
- sort_tasks_by_priority: Function that sorts tasks by priority and creation date

Both functions work together to provide consistent task ordering across the system,
prioritizing tasks by priority level (high > normal > low) and then by creation
date (older first) within each priority level.
"""

from datetime import datetime, timedelta, timezone

from trellis_mcp.models import task_sort_key
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


class TestTaskSortKey:
    """Test cases for task_sort_key function."""

    def test_key_structure(self):
        """Test that sort key returns correct tuple structure."""
        task = create_test_task(
            "T-test-001",
            Priority.HIGH,
            datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        key = task_sort_key(task)

        # Should return tuple of (priority_rank, created_datetime)
        assert isinstance(key, tuple)
        assert len(key) == 2
        assert isinstance(key[0], int)  # priority_rank
        assert isinstance(key[1], datetime)  # created

    def test_priority_ordering(self):
        """Test that priority ranks are ordered correctly."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        high_task = create_test_task("T-high", Priority.HIGH, base_time)
        normal_task = create_test_task("T-normal", Priority.NORMAL, base_time)
        low_task = create_test_task("T-low", Priority.LOW, base_time)

        high_key = task_sort_key(high_task)
        normal_key = task_sort_key(normal_task)
        low_key = task_sort_key(low_task)

        # High priority should have lowest rank value
        assert high_key[0] < normal_key[0] < low_key[0]
        # All should have same created time
        assert high_key[1] == normal_key[1] == low_key[1] == base_time

    def test_creation_date_ordering(self):
        """Test that creation dates are ordered correctly."""
        older_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        newer_time = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

        older_task = create_test_task("T-older", Priority.NORMAL, older_time)
        newer_task = create_test_task("T-newer", Priority.NORMAL, newer_time)

        older_key = task_sort_key(older_task)
        newer_key = task_sort_key(newer_task)

        # Same priority rank
        assert older_key[0] == newer_key[0]
        # Older time should come first
        assert older_key[1] < newer_key[1]

    def test_sorting_with_key_function(self):
        """Test using the key function with Python's sorted()."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        tasks = [
            create_test_task("T-low", Priority.LOW, base_time),
            create_test_task("T-high", Priority.HIGH, base_time),
            create_test_task("T-normal", Priority.NORMAL, base_time),
        ]

        sorted_tasks = sorted(tasks, key=task_sort_key)

        # Should be sorted by priority: high, normal, low
        assert sorted_tasks[0].priority == Priority.HIGH
        assert sorted_tasks[1].priority == Priority.NORMAL
        assert sorted_tasks[2].priority == Priority.LOW

    def test_mixed_priority_and_date_sorting(self):
        """Test sorting with mixed priorities and dates."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        hour_later = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        tasks = [
            create_test_task("T-low-new", Priority.LOW, hour_later),
            create_test_task("T-high-old", Priority.HIGH, base_time),
            create_test_task("T-normal-new", Priority.NORMAL, hour_later),
            create_test_task("T-high-new", Priority.HIGH, hour_later),
            create_test_task("T-normal-old", Priority.NORMAL, base_time),
        ]

        sorted_tasks = sorted(tasks, key=task_sort_key)

        # Verify priority ordering
        priorities = [task.priority for task in sorted_tasks]
        assert priorities == [
            Priority.HIGH,
            Priority.HIGH,
            Priority.NORMAL,
            Priority.NORMAL,
            Priority.LOW,
        ]

        # Verify that within same priority, older tasks come first
        high_tasks = [task for task in sorted_tasks if task.priority == Priority.HIGH]
        assert high_tasks[0].created <= high_tasks[1].created

        normal_tasks = [task for task in sorted_tasks if task.priority == Priority.NORMAL]
        assert normal_tasks[0].created <= normal_tasks[1].created

    def test_comprehensive_mixed_priority_sorting(self):
        """Test comprehensive sorting with all priority levels and various creation times."""
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create a comprehensive set of tasks with mixed priorities and times
        tasks = [
            # HIGH priority tasks at different times
            create_test_task("T-high-oldest", Priority.HIGH, base_time),
            create_test_task("T-high-middle", Priority.HIGH, base_time + timedelta(hours=2)),
            create_test_task("T-high-newest", Priority.HIGH, base_time + timedelta(hours=4)),
            create_test_task("T-high-same-as-oldest", Priority.HIGH, base_time),
            # NORMAL priority tasks at different times
            create_test_task("T-normal-oldest", Priority.NORMAL, base_time + timedelta(minutes=30)),
            create_test_task("T-normal-middle", Priority.NORMAL, base_time + timedelta(hours=3)),
            create_test_task("T-normal-newest", Priority.NORMAL, base_time + timedelta(hours=5)),
            # LOW priority tasks at different times
            create_test_task("T-low-oldest", Priority.LOW, base_time + timedelta(minutes=15)),
            create_test_task("T-low-middle", Priority.LOW, base_time + timedelta(hours=1)),
            create_test_task("T-low-newest", Priority.LOW, base_time + timedelta(hours=6)),
            create_test_task(
                "T-low-same-as-oldest", Priority.LOW, base_time + timedelta(minutes=15)
            ),
        ]

        # Sort using the key function
        sorted_tasks = sorted(tasks, key=task_sort_key)

        # Verify priority grouping - all HIGH tasks should come first
        high_tasks = [task for task in sorted_tasks if task.priority == Priority.HIGH]
        normal_tasks = [task for task in sorted_tasks if task.priority == Priority.NORMAL]
        low_tasks = [task for task in sorted_tasks if task.priority == Priority.LOW]

        assert len(high_tasks) == 4
        assert len(normal_tasks) == 3
        assert len(low_tasks) == 4

        # Verify overall priority ordering
        priorities = [task.priority for task in sorted_tasks]
        expected_priority_pattern = [Priority.HIGH] * 4 + [Priority.NORMAL] * 3 + [Priority.LOW] * 4
        assert priorities == expected_priority_pattern

        # Verify chronological ordering within each priority group
        # HIGH priority tasks: should be in chronological order
        high_times = [task.created for task in high_tasks]
        sorted_high_times = sorted(high_times)
        assert high_times == sorted_high_times

        # NORMAL priority tasks: should be in chronological order
        normal_times = [task.created for task in normal_tasks]
        sorted_normal_times = sorted(normal_times)
        assert normal_times == sorted_normal_times

        # LOW priority tasks: should be in chronological order
        low_times = [task.created for task in low_tasks]
        sorted_low_times = sorted(low_times)
        assert low_times == sorted_low_times

        # Verify specific ordering within HIGH priority group
        # T-high-oldest and T-high-same-as-oldest should come first (same time)
        # T-high-middle should come next
        # T-high-newest should come last
        assert high_tasks[0].id in ["T-high-oldest", "T-high-same-as-oldest"]
        assert high_tasks[1].id in ["T-high-oldest", "T-high-same-as-oldest"]
        assert high_tasks[2].id == "T-high-middle"
        assert high_tasks[3].id == "T-high-newest"

        # Verify that identical creation times are handled consistently
        # Tasks with same priority and time should maintain stable ordering
        same_time_high_tasks = [task for task in high_tasks if task.created == base_time]
        assert len(same_time_high_tasks) == 2

        same_time_low_tasks = [
            task for task in low_tasks if task.created == base_time + timedelta(minutes=15)
        ]
        assert len(same_time_low_tasks) == 2


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
