"""Tests for filtering utilities."""

import tempfile
from pathlib import Path

import pytest

from trellis_mcp.filters import apply_filters, filter_by_scope
from trellis_mcp.models.filter_params import FilterParams
from trellis_mcp.schema.task import TaskModel


@pytest.fixture
def sample_project_structure():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create the planning directory structure
        planning_dir = temp_path / "planning" / "projects"

        # Project P-test-project
        project_dir = planning_dir / "P-test-project" / "epics"

        # Epic E-test-epic
        epic_dir = project_dir / "E-test-epic" / "features"

        # Feature F-test-feature
        feature_dir = epic_dir / "F-test-feature"
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_done_dir = feature_dir / "tasks-done"

        # Create all directories
        tasks_open_dir.mkdir(parents=True)
        tasks_done_dir.mkdir(parents=True)

        # Create task files with YAML front-matter
        task1_content = """---
kind: task
id: task-1
parent: F-test-feature
status: open
title: Test Task 1
priority: high
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

This is test task 1.
"""

        task2_content = """---
kind: task
id: task-2
parent: F-test-feature
status: in-progress
title: Test Task 2
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

This is test task 2.
"""

        task3_content = """---
kind: task
id: task-3
parent: F-test-feature
status: done
title: Test Task 3
priority: low
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

This is test task 3.
"""

        # Write task files
        (tasks_open_dir / "T-task-1.md").write_text(task1_content)
        (tasks_open_dir / "T-task-2.md").write_text(task2_content)
        (tasks_done_dir / "2025-07-13T19:30:00-T-task-3.md").write_text(task3_content)

        # Create another feature with a task
        feature2_dir = epic_dir / "F-another-feature"
        tasks_open2_dir = feature2_dir / "tasks-open"
        tasks_open2_dir.mkdir(parents=True)

        task4_content = """---
kind: task
id: task-4
parent: F-another-feature
status: open
title: Test Task 4
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

This is test task 4.
"""

        (tasks_open2_dir / "T-task-4.md").write_text(task4_content)

        # Create another epic with tasks
        epic2_dir = project_dir / "E-another-epic" / "features"
        feature3_dir = epic2_dir / "F-feature-in-epic2"
        tasks_open3_dir = feature3_dir / "tasks-open"
        tasks_open3_dir.mkdir(parents=True)

        task5_content = """---
kind: task
id: task-5
parent: F-feature-in-epic2
status: review
title: Test Task 5
priority: high
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

This is test task 5.
"""

        (tasks_open3_dir / "T-task-5.md").write_text(task5_content)

        # Create another project
        project2_dir = planning_dir / "P-another-project" / "epics"
        epic3_dir = project2_dir / "E-epic-in-project2" / "features"
        feature4_dir = epic3_dir / "F-feature-in-project2"
        tasks_open4_dir = feature4_dir / "tasks-open"
        tasks_open4_dir.mkdir(parents=True)

        task6_content = """---
kind: task
id: task-6
parent: F-feature-in-project2
status: open
title: Test Task 6
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

This is test task 6.
"""

        (tasks_open4_dir / "T-task-6.md").write_text(task6_content)

        yield temp_path


def test_filter_by_project_scope(sample_project_structure):
    """Test filtering tasks by project scope."""
    tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))

    # Should include all tasks from the test project (tasks 1-5)
    task_ids = [task.id for task in tasks]
    assert "task-1" in task_ids
    assert "task-2" in task_ids
    assert "task-3" in task_ids
    assert "task-4" in task_ids
    assert "task-5" in task_ids
    assert "task-6" not in task_ids  # This is in another project

    assert len(tasks) == 5


def test_filter_by_epic_scope(sample_project_structure):
    """Test filtering tasks by epic scope."""
    tasks = list(filter_by_scope(sample_project_structure, "E-test-epic"))

    # Should include tasks 1-4 (from features in test-epic)
    task_ids = [task.id for task in tasks]
    assert "task-1" in task_ids
    assert "task-2" in task_ids
    assert "task-3" in task_ids
    assert "task-4" in task_ids
    assert "task-5" not in task_ids  # This is in another epic
    assert "task-6" not in task_ids  # This is in another project

    assert len(tasks) == 4


def test_filter_by_feature_scope(sample_project_structure):
    """Test filtering tasks by feature scope."""
    tasks = list(filter_by_scope(sample_project_structure, "F-test-feature"))

    # Should include only tasks 1-3 (directly under test-feature)
    task_ids = [task.id for task in tasks]
    assert "task-1" in task_ids
    assert "task-2" in task_ids
    assert "task-3" in task_ids
    assert "task-4" not in task_ids  # This is in another feature
    assert "task-5" not in task_ids  # This is in another epic
    assert "task-6" not in task_ids  # This is in another project

    assert len(tasks) == 3


def test_filter_by_direct_parent_match(sample_project_structure):
    """Test filtering by direct parent ID match."""
    tasks = list(filter_by_scope(sample_project_structure, "F-another-feature"))

    # Should include only task-4 (has F-another-feature as parent)
    task_ids = [task.id for task in tasks]
    assert task_ids == ["task-4"]
    assert len(tasks) == 1


def test_filter_by_nonexistent_scope(sample_project_structure):
    """Test filtering with a non-existent scope ID."""
    tasks = list(filter_by_scope(sample_project_structure, "F-nonexistent"))

    # Should return no tasks
    assert len(tasks) == 0


def test_filter_empty_scope_id(sample_project_structure):
    """Test filtering with empty scope ID."""
    tasks = list(filter_by_scope(sample_project_structure, ""))

    # Should return no tasks
    assert len(tasks) == 0


def test_filter_with_invalid_project_root():
    """Test filtering with invalid project root."""
    invalid_path = Path("/nonexistent/path")
    tasks = list(filter_by_scope(invalid_path, "P-test-project"))

    # Should return no tasks
    assert len(tasks) == 0


def test_filter_with_missing_planning_dir():
    """Test filtering with project root that has no planning directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        tasks = list(filter_by_scope(temp_path, "P-test-project"))

        # Should return no tasks
        assert len(tasks) == 0


def test_filter_includes_both_open_and_done_tasks(sample_project_structure):
    """Test that filtering includes tasks from both tasks-open and tasks-done directories."""
    tasks = list(filter_by_scope(sample_project_structure, "F-test-feature"))

    # Should include tasks from both directories
    statuses = [task.status.value for task in tasks]
    assert "open" in statuses
    assert "in-progress" in statuses
    assert "done" in statuses


def test_filter_returns_task_model_objects(sample_project_structure):
    """Test that filter returns proper TaskModel objects."""
    tasks = list(filter_by_scope(sample_project_structure, "F-test-feature"))

    # All returned objects should be TaskModel instances
    for task in tasks:
        assert isinstance(task, TaskModel)
        assert hasattr(task, "id")
        assert hasattr(task, "parent")
        assert hasattr(task, "status")
        assert hasattr(task, "title")
        assert hasattr(task, "priority")


def test_filter_handles_malformed_files_gracefully():
    """Test that filter handles malformed markdown files gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create basic structure
        feature_dir = (
            temp_path
            / "planning"
            / "projects"
            / "P-test"
            / "epics"
            / "E-test"
            / "features"
            / "F-test"
        )
        tasks_dir = feature_dir / "tasks-open"
        tasks_dir.mkdir(parents=True)

        # Create a malformed task file
        (tasks_dir / "T-bad-task.md").write_text("This is not valid YAML front-matter")

        # Create a valid task file
        valid_task = """---
kind: task
id: good-task
parent: F-test
status: open
title: Good Task
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

This is a good task.
"""
        (tasks_dir / "T-good-task.md").write_text(valid_task)

        # Should only return the valid task, ignoring the malformed one
        tasks = list(filter_by_scope(temp_path, "F-test"))
        assert len(tasks) == 1
        assert tasks[0].id == "good-task"


def test_apply_filters_no_filters(sample_project_structure):
    """Test apply_filters with empty FilterParams (no filtering)."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    filter_params = FilterParams()

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should return all tasks unchanged
    assert len(filtered_tasks) == len(all_tasks)
    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids
    assert "task-2" in task_ids
    assert "task-3" in task_ids
    assert "task-4" in task_ids
    assert "task-5" in task_ids


def test_apply_filters_status_only(sample_project_structure):
    """Test apply_filters with status filter only."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    filter_params = FilterParams(status=["open"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should only return tasks with 'open' status
    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids  # status: open
    assert "task-2" not in task_ids  # status: in-progress
    assert "task-3" not in task_ids  # status: done
    assert "task-4" in task_ids  # status: open
    assert "task-5" not in task_ids  # status: review
    assert len(filtered_tasks) == 2


def test_apply_filters_priority_only(sample_project_structure):
    """Test apply_filters with priority filter only."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    filter_params = FilterParams(priority=["high"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should only return tasks with 'high' priority
    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids  # priority: high
    assert "task-2" not in task_ids  # priority: normal
    assert "task-3" not in task_ids  # priority: low
    assert "task-4" not in task_ids  # priority: normal
    assert "task-5" in task_ids  # priority: high
    assert len(filtered_tasks) == 2


def test_apply_filters_multiple_status_values(sample_project_structure):
    """Test apply_filters with multiple status values."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    filter_params = FilterParams(status=["open", "done"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should return tasks with either 'open' or 'done' status
    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids  # status: open
    assert "task-2" not in task_ids  # status: in-progress
    assert "task-3" in task_ids  # status: done
    assert "task-4" in task_ids  # status: open
    assert "task-5" not in task_ids  # status: review
    assert len(filtered_tasks) == 3


def test_apply_filters_multiple_priority_values(sample_project_structure):
    """Test apply_filters with multiple priority values."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    filter_params = FilterParams(priority=["high", "normal"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should return tasks with either 'high' or 'normal' priority
    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids  # priority: high
    assert "task-2" in task_ids  # priority: normal
    assert "task-3" not in task_ids  # priority: low
    assert "task-4" in task_ids  # priority: normal
    assert "task-5" in task_ids  # priority: high
    assert len(filtered_tasks) == 4


def test_apply_filters_combined_status_and_priority(sample_project_structure):
    """Test apply_filters with both status and priority filters (logical AND)."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    filter_params = FilterParams(status=["open"], priority=["high"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should only return tasks that are both 'open' AND 'high' priority
    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids  # status: open, priority: high ✓
    assert "task-2" not in task_ids  # status: in-progress, priority: normal ✗
    assert "task-3" not in task_ids  # status: done, priority: low ✗
    assert "task-4" not in task_ids  # status: open, priority: normal ✗ (wrong priority)
    assert "task-5" not in task_ids  # status: review, priority: high ✗ (wrong status)
    assert len(filtered_tasks) == 1


def test_apply_filters_no_matching_tasks(sample_project_structure):
    """Test apply_filters when no tasks match the criteria."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    # Use valid status that doesn't match any tasks in our test data
    filter_params = FilterParams(status=["draft"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should return no tasks (no tasks have draft status in our test data)
    assert len(filtered_tasks) == 0


def test_apply_filters_empty_task_list():
    """Test apply_filters with empty task list."""
    filter_params = FilterParams(status=["open"], priority=["high"])

    filtered_tasks = list(apply_filters(iter([]), filter_params))

    # Should return no tasks
    assert len(filtered_tasks) == 0


def test_apply_filters_preserves_task_properties(sample_project_structure):
    """Test that apply_filters preserves all task properties."""
    all_tasks = list(filter_by_scope(sample_project_structure, "F-test-feature"))
    filter_params = FilterParams(status=["open"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should preserve all task properties
    assert len(filtered_tasks) == 1
    task = filtered_tasks[0]
    assert isinstance(task, TaskModel)
    assert task.id == "task-1"
    assert task.status.value == "open"
    assert task.priority.name == "HIGH"
    assert task.title == "Test Task 1"
    assert task.parent == "F-test-feature"


def test_apply_filters_string_values_in_filter_params(sample_project_structure):
    """Test apply_filters with string values in FilterParams (should be converted to enums)."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))
    filter_params = FilterParams(status=["open", "done"], priority=["high", "normal"])

    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    # Should work correctly with string values converted to enums
    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids  # status: open, priority: high ✓
    assert "task-2" not in task_ids  # status: in-progress ✗ (not in status filter)
    assert "task-3" not in task_ids  # status: done, priority: low ✗ (priority not in filter)
    assert "task-4" in task_ids  # status: open, priority: normal ✓
    assert "task-5" not in task_ids  # status: review ✗ (not in status filter)

    # Should have task-1 (open+high) and task-4 (open+normal)
    assert len(filtered_tasks) == 2


def test_apply_filters_comprehensive_combined_matrix(sample_project_structure):
    """Test apply_filters with comprehensive status and priority combinations."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))

    # Test multiple status values + multiple priority values (full matrix)
    filter_params = FilterParams(
        status=["open", "in-progress", "review"], priority=["high", "normal"]
    )
    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" in task_ids  # status: open, priority: high ✓
    assert "task-2" in task_ids  # status: in-progress, priority: normal ✓
    assert "task-3" not in task_ids  # status: done ✗ (not in status filter)
    assert "task-4" in task_ids  # status: open, priority: normal ✓
    assert "task-5" in task_ids  # status: review, priority: high ✓
    assert len(filtered_tasks) == 4


def test_apply_filters_empty_status_with_priority_filter(sample_project_structure):
    """Test apply_filters with empty status list but priority filter applied."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))

    # Empty status = no status filtering, only priority filtering
    filter_params = FilterParams(status=[], priority=["low"])
    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" not in task_ids  # priority: high ✗
    assert "task-2" not in task_ids  # priority: normal ✗
    assert "task-3" in task_ids  # priority: low ✓
    assert "task-4" not in task_ids  # priority: normal ✗
    assert "task-5" not in task_ids  # priority: high ✗
    assert len(filtered_tasks) == 1


def test_apply_filters_priority_empty_with_status_filter(sample_project_structure):
    """Test apply_filters with empty priority list but status filter applied."""
    all_tasks = list(filter_by_scope(sample_project_structure, "P-test-project"))

    # Empty priority = no priority filtering, only status filtering
    filter_params = FilterParams(status=["done"], priority=[])
    filtered_tasks = list(apply_filters(iter(all_tasks), filter_params))

    task_ids = [task.id for task in filtered_tasks]
    assert "task-1" not in task_ids  # status: open ✗
    assert "task-2" not in task_ids  # status: in-progress ✗
    assert "task-3" in task_ids  # status: done ✓
    assert "task-4" not in task_ids  # status: open ✗
    assert "task-5" not in task_ids  # status: review ✗
    assert len(filtered_tasks) == 1


def test_filter_by_scope_additional_security_path_check():
    """Test filter_by_scope with additional path traversal security scenarios."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create basic structure
        planning_dir = temp_path / "planning" / "projects"
        project_dir = planning_dir / "P-test" / "epics" / "E-test" / "features" / "F-test"
        tasks_dir = project_dir / "tasks-open"
        tasks_dir.mkdir(parents=True)

        # Create a task file
        task_content = """---
kind: task
id: test-task
parent: F-test
status: open
title: Test Task
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

Test task content.
"""
        (tasks_dir / "T-test-task.md").write_text(task_content)

        # Test with path traversal attempts in scope_id
        tasks1 = list(filter_by_scope(temp_path, "../../../etc/passwd"))
        assert len(tasks1) == 0  # Should not return any tasks

        tasks2 = list(filter_by_scope(temp_path, ""))
        assert len(tasks2) == 0  # Empty scope should return no tasks

        # Valid scope should work
        tasks3 = list(filter_by_scope(temp_path, "F-test"))
        assert len(tasks3) == 1


def test_apply_filters_iterator_error_propagation():
    """Test that apply_filters propagates iterator errors as expected."""

    class FailingTaskIterator:
        """Iterator that fails partway through iteration."""

        def __init__(self, tasks):
            self.tasks = tasks
            self.index = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.index >= len(self.tasks):
                raise StopIteration
            if self.index == 1:  # Fail on second item
                raise ValueError("Simulated iterator error")
            task = self.tasks[self.index]
            self.index += 1
            return task

    # Create mock tasks (we'll use valid TaskModel objects)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create minimal structure for getting real TaskModel objects
        planning_dir = temp_path / "planning" / "projects"
        project_dir = planning_dir / "P-test" / "epics" / "E-test" / "features" / "F-test"
        tasks_dir = project_dir / "tasks-open"
        tasks_dir.mkdir(parents=True)

        # Create task files
        for i in range(3):
            task_content = f"""---
kind: task
id: task-{i}
parent: F-test
status: open
title: Test Task {i}
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---

Test task {i} content.
"""
            (tasks_dir / f"T-task-{i}.md").write_text(task_content)

        # Get real TaskModel objects
        real_tasks = list(filter_by_scope(temp_path, "F-test"))
        assert len(real_tasks) == 3

        # Test with failing iterator - should propagate the error
        failing_iterator = FailingTaskIterator(real_tasks)
        filter_params = FilterParams(status=["open"])

        # Iterator errors should propagate (not be caught by apply_filters)
        with pytest.raises(ValueError, match="Simulated iterator error"):
            list(apply_filters(failing_iterator, filter_params))
