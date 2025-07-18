"""Tests for backlog loader functionality."""

from pathlib import Path

from trellis_mcp.backlog_loader import load_backlog_tasks
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


class TestLoadBacklogTasks:
    """Test load_backlog_tasks function."""

    def test_load_empty_backlog(self, temp_dir: Path) -> None:
        """Test loading backlog when no planning directory exists."""
        result = load_backlog_tasks(temp_dir)
        assert result == []

    def test_load_backlog_no_projects(self, temp_dir: Path) -> None:
        """Test loading backlog when planning directory exists but no projects."""
        planning_dir = temp_dir / "planning"
        planning_dir.mkdir()

        result = load_backlog_tasks(planning_dir)
        assert result == []

    def test_load_backlog_no_tasks(self, sample_planning_structure: Path) -> None:
        """Test loading backlog when structure exists but no tasks."""
        result = load_backlog_tasks(sample_planning_structure)
        assert result == []

    def test_load_single_task(self, sample_planning_structure: Path) -> None:
        """Test loading backlog with a single task."""
        # Create a task file in the sample structure
        feature_dir = (
            sample_planning_structure
            / "projects"
            / "P-001-sample-project"
            / "epics"
            / "E-001-sample-epic"
            / "features"
            / "F-001-sample-feature"
        )
        tasks_open_dir = feature_dir / "tasks-open"

        task_file = tasks_open_dir / "T-001-sample-task.md"
        task_content = """---
kind: task
id: T-001-sample-task
parent: F-001-sample-feature
status: open
title: Sample Task
priority: high
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Sample Task

This is a sample task description.
"""
        task_file.write_text(task_content)

        result = load_backlog_tasks(sample_planning_structure)

        assert len(result) == 1
        assert isinstance(result[0], TaskModel)
        assert result[0].id == "T-001-sample-task"
        assert result[0].title == "Sample Task"
        assert result[0].status == StatusEnum.OPEN
        assert result[0].priority == Priority.HIGH
        assert result[0].parent == "F-001-sample-feature"

    def test_load_multiple_tasks_single_feature(self, sample_planning_structure: Path) -> None:
        """Test loading backlog with multiple tasks in one feature."""
        feature_dir = (
            sample_planning_structure
            / "projects"
            / "P-001-sample-project"
            / "epics"
            / "E-001-sample-epic"
            / "features"
            / "F-001-sample-feature"
        )
        tasks_open_dir = feature_dir / "tasks-open"

        # Create first task
        task1_file = tasks_open_dir / "T-001-first-task.md"
        task1_content = """---
kind: task
id: T-001-first-task
parent: F-001-sample-feature
status: open
title: First Task
priority: high
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

First task description.
"""
        task1_file.write_text(task1_content)

        # Create second task
        task2_file = tasks_open_dir / "T-002-second-task.md"
        task2_content = """---
kind: task
id: T-002-second-task
parent: F-001-sample-feature
status: in-progress
title: Second Task
priority: normal
prerequisites: ["T-001-first-task"]
worktree: /workspace/feature-branch
created: 2025-01-01T01:00:00Z
updated: 2025-01-01T02:00:00Z
schema_version: "1.1"
---

Second task description.
"""
        task2_file.write_text(task2_content)

        result = load_backlog_tasks(sample_planning_structure)

        assert len(result) == 2

        # Find tasks by ID (order not guaranteed)
        task_dict = {task.id: task for task in result}

        assert "T-001-first-task" in task_dict
        assert "T-002-second-task" in task_dict

        task1 = task_dict["T-001-first-task"]
        assert task1.title == "First Task"
        assert task1.status == StatusEnum.OPEN
        assert task1.priority == Priority.HIGH
        assert task1.prerequisites == []

        task2 = task_dict["T-002-second-task"]
        assert task2.title == "Second Task"
        assert task2.status == StatusEnum.IN_PROGRESS
        assert task2.priority == Priority.NORMAL
        assert task2.prerequisites == ["T-001-first-task"]
        assert task2.worktree == "/workspace/feature-branch"

    def test_load_tasks_multiple_features(self, temp_dir: Path) -> None:
        """Test loading backlog with tasks across multiple features."""
        # Create more complex structure
        planning_dir = temp_dir / "planning"

        # Project 1, Epic 1, Feature 1
        feature1_dir = (
            planning_dir
            / "projects"
            / "P-001-web-app"
            / "epics"
            / "E-001-auth"
            / "features"
            / "F-001-login"
        )
        feature1_dir.mkdir(parents=True)
        (feature1_dir / "tasks-open").mkdir()

        # Project 1, Epic 1, Feature 2
        feature2_dir = (
            planning_dir
            / "projects"
            / "P-001-web-app"
            / "epics"
            / "E-001-auth"
            / "features"
            / "F-002-registration"
        )
        feature2_dir.mkdir(parents=True)
        (feature2_dir / "tasks-open").mkdir()

        # Add task to feature 1
        task1_file = feature1_dir / "tasks-open" / "T-001-login-form.md"
        task1_content = """---
kind: task
id: T-001-login-form
parent: F-001-login
status: open
title: Create Login Form
priority: high
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

Create the login form component.
"""
        task1_file.write_text(task1_content)

        # Add task to feature 2
        task2_file = feature2_dir / "tasks-open" / "T-002-signup-form.md"
        task2_content = """---
kind: task
id: T-002-signup-form
parent: F-002-registration
status: open
title: Create Signup Form
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

Create the signup form component.
"""
        task2_file.write_text(task2_content)

        result = load_backlog_tasks(planning_dir)

        assert len(result) == 2

        # Find tasks by ID
        task_dict = {task.id: task for task in result}

        assert "T-001-login-form" in task_dict
        assert "T-002-signup-form" in task_dict

        assert task_dict["T-001-login-form"].title == "Create Login Form"
        assert task_dict["T-001-login-form"].parent == "F-001-login"
        assert task_dict["T-002-signup-form"].title == "Create Signup Form"
        assert task_dict["T-002-signup-form"].parent == "F-002-registration"

    def test_skip_invalid_files(self, sample_planning_structure: Path) -> None:
        """Test that invalid files are skipped gracefully."""
        feature_dir = (
            sample_planning_structure
            / "projects"
            / "P-001-sample-project"
            / "epics"
            / "E-001-sample-epic"
            / "features"
            / "F-001-sample-feature"
        )
        tasks_open_dir = feature_dir / "tasks-open"

        # Create a valid task
        valid_task_file = tasks_open_dir / "T-001-valid-task.md"
        valid_task_content = """---
kind: task
id: T-001-valid-task
parent: F-001-sample-feature
status: open
title: Valid Task
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

Valid task description.
"""
        valid_task_file.write_text(valid_task_content)

        # Create an invalid YAML file
        invalid_yaml_file = tasks_open_dir / "T-002-invalid.md"
        invalid_yaml_file.write_text("---\ninvalid: yaml: content\n---\nContent")

        # Create a non-markdown file
        non_md_file = tasks_open_dir / "README.txt"
        non_md_file.write_text("This is not a markdown file")

        # Create a file with wrong kind
        wrong_kind_file = tasks_open_dir / "T-003-wrong-kind.md"
        wrong_kind_content = """---
kind: project
id: T-003-wrong-kind
title: Wrong Kind
---

This has wrong kind.
"""
        wrong_kind_file.write_text(wrong_kind_content)

        result = load_backlog_tasks(sample_planning_structure)

        # Should only return the valid task
        assert len(result) == 1
        assert result[0].id == "T-001-valid-task"
        assert result[0].title == "Valid Task"

    def test_skip_tasks_done_directory(self, sample_planning_structure: Path) -> None:
        """Test that tasks-done directory is ignored."""
        feature_dir = (
            sample_planning_structure
            / "projects"
            / "P-001-sample-project"
            / "epics"
            / "E-001-sample-epic"
            / "features"
            / "F-001-sample-feature"
        )

        # Add task to tasks-open (should be included)
        tasks_open_dir = feature_dir / "tasks-open"
        open_task_file = tasks_open_dir / "T-001-open-task.md"
        open_task_content = """---
kind: task
id: T-001-open-task
parent: F-001-sample-feature
status: open
title: Open Task
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

Open task description.
"""
        open_task_file.write_text(open_task_content)

        # Add task to tasks-done (should be ignored)
        tasks_done_dir = feature_dir / "tasks-done"
        done_task_file = tasks_done_dir / "20250101_120000-T-002-done-task.md"
        done_task_content = """---
kind: task
id: T-002-done-task
parent: F-001-sample-feature
status: done
title: Done Task
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

Done task description.
"""
        done_task_file.write_text(done_task_content)

        result = load_backlog_tasks(sample_planning_structure)

        # Should only return the open task
        assert len(result) == 1
        assert result[0].id == "T-001-open-task"
        assert result[0].title == "Open Task"
