"""Tests for Trellis MCP CLI commands."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from trellis_mcp.cli import cli
from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum


def create_sample_task_file(
    task_dir: Path,
    task_id: str,
    title: str,
    status: StatusEnum = StatusEnum.OPEN,
    priority: Priority = Priority.NORMAL,
    parent: str = "F-001-sample-feature",
) -> Path:
    """Create a sample task file for testing."""
    task_file = task_dir / f"T-{task_id}.md"
    created_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    updated_time = datetime(2025, 1, 1, 12, 30, 0, tzinfo=timezone.utc)

    content = f"""---
kind: {KindEnum.TASK.value}
id: "{task_id}"
parent: "{parent}"
status: {status.value}
title: "{title}"
priority: {priority.value}
worktree: null
created: {created_time.isoformat()}
updated: {updated_time.isoformat()}
schema_version: "1.0"
prerequisites: []
---

# {title}

Task content goes here.
"""
    task_file.write_text(content)
    return task_file


@pytest.fixture
def planning_structure_with_tasks(temp_dir: Path) -> Path:
    """Create a planning structure with multiple tasks for testing."""
    planning_dir = temp_dir / "planning"
    planning_dir.mkdir()

    # Create project structure
    project_dir = planning_dir / "projects" / "P-001-sample-project"
    project_dir.mkdir(parents=True)

    # Create epic
    epic_dir = project_dir / "epics" / "E-001-sample-epic"
    epic_dir.mkdir(parents=True)

    # Create features
    feature1_dir = epic_dir / "features" / "F-001-feature-one"
    feature1_dir.mkdir(parents=True)
    (feature1_dir / "tasks-open").mkdir()
    (feature1_dir / "tasks-done").mkdir()

    feature2_dir = epic_dir / "features" / "F-002-feature-two"
    feature2_dir.mkdir(parents=True)
    (feature2_dir / "tasks-open").mkdir()
    (feature2_dir / "tasks-done").mkdir()

    # Create sample tasks
    # Feature 1 tasks
    create_sample_task_file(
        feature1_dir / "tasks-open",
        "001",
        "High priority open task",
        StatusEnum.OPEN,
        Priority.HIGH,
        "F-001-feature-one",
    )
    create_sample_task_file(
        feature1_dir / "tasks-open",
        "002",
        "Normal priority in-progress task",
        StatusEnum.IN_PROGRESS,
        Priority.NORMAL,
        "F-001-feature-one",
    )
    create_sample_task_file(
        feature1_dir / "tasks-done",
        "003",
        "Low priority done task",
        StatusEnum.DONE,
        Priority.LOW,
        "F-001-feature-one",
    )

    # Feature 2 tasks
    create_sample_task_file(
        feature2_dir / "tasks-open",
        "004",
        "Normal priority review task",
        StatusEnum.REVIEW,
        Priority.NORMAL,
        "F-002-feature-two",
    )
    create_sample_task_file(
        feature2_dir / "tasks-open",
        "005",
        "High priority open task",
        StatusEnum.OPEN,
        Priority.HIGH,
        "F-002-feature-two",
    )

    return temp_dir


class TestBacklogCLI:
    """Test the backlog CLI command."""

    def test_backlog_no_filters(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command with no filters returns only open tasks by default."""
        runner = CliRunner()

        # Run the CLI command
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog"],  # Use no config file
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        # Check command succeeded
        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)
        assert "tasks" in output_data

        # Should have 2 tasks (by default only open tasks are returned)
        # Only tasks 001 and 005 have "open" status, others are filtered out
        tasks = output_data["tasks"]
        assert len(tasks) == 2

        # Check that tasks are sorted by priority (high first)
        task_priorities = [task["priority"] for task in tasks]
        high_tasks = [p for p in task_priorities if p == "high"]
        normal_tasks = [p for p in task_priorities if p == "normal"]
        low_tasks = [p for p in task_priorities if p == "low"]

        # Verify priority ordering: 2 high, 0 normal, 0 low (only open tasks returned)
        assert len(high_tasks) == 2
        assert len(normal_tasks) == 0
        assert len(low_tasks) == 0

    def test_backlog_status_filter(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command with status filter."""
        runner = CliRunner()

        # Filter for only open tasks
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog", "--status", "open"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        assert result.exit_code == 0

        output_data = json.loads(result.output)
        tasks = output_data["tasks"]

        # Should only have 2 open tasks
        assert len(tasks) == 2
        for task in tasks:
            assert task["status"] == "open"

    def test_backlog_priority_filter(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command with priority filter."""
        runner = CliRunner()

        # Filter for only high priority tasks
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog", "--priority", "high"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        assert result.exit_code == 0

        output_data = json.loads(result.output)
        tasks = output_data["tasks"]

        # Should only have 2 high priority tasks
        assert len(tasks) == 2
        for task in tasks:
            assert task["priority"] == "high"

    def test_backlog_scope_filter(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command with scope filter."""
        runner = CliRunner()

        # Filter for only feature F-001 tasks
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog", "--scope", "F-001-feature-one"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        assert result.exit_code == 0

        output_data = json.loads(result.output)
        tasks = output_data["tasks"]

        # Should only have 1 task from feature F-001 (only open tasks by default)
        # Task 001 is open, task 002 is in-progress, task 003 is done
        assert len(tasks) == 1
        for task in tasks:
            assert task["parent"] == "F-001-feature-one"

    def test_backlog_combined_filters(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command with multiple filters combined."""
        runner = CliRunner()

        # Filter for high priority open tasks
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog", "--status", "open", "--priority", "high"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        assert result.exit_code == 0

        output_data = json.loads(result.output)
        tasks = output_data["tasks"]

        # Should only have 2 tasks that are both high priority AND open
        assert len(tasks) == 2
        for task in tasks:
            assert task["status"] == "open"
            assert task["priority"] == "high"

    def test_backlog_invalid_status(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command with invalid status value."""
        runner = CliRunner()

        # Try to use an invalid status
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog", "--status", "invalid-status"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        # Should fail with non-zero exit code
        assert result.exit_code != 0
        assert "invalid-status" in result.output.lower()

    def test_backlog_invalid_priority(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command with invalid priority value."""
        runner = CliRunner()

        # Try to use an invalid priority
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog", "--priority", "invalid-priority"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        # Should fail with non-zero exit code
        assert result.exit_code != 0
        assert "invalid-priority" in result.output.lower()

    def test_backlog_empty_results(self, planning_structure_with_tasks: Path) -> None:
        """Test backlog command when filters return no results."""
        runner = CliRunner()

        # Filter for a combination that should return no results
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog", "--status", "done", "--priority", "high"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        assert result.exit_code == 0

        output_data = json.loads(result.output)
        tasks = output_data["tasks"]

        # Should return empty list
        assert len(tasks) == 0

    def test_backlog_json_format(self, planning_structure_with_tasks: Path) -> None:
        """Test that backlog command outputs valid JSON."""
        runner = CliRunner()

        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog"],
            env={"MCP_PLANNING_ROOT": str(planning_structure_with_tasks)},
        )

        assert result.exit_code == 0

        # Should be valid JSON
        output_data = json.loads(result.output)

        # Should have the expected structure
        assert "tasks" in output_data
        assert isinstance(output_data["tasks"], list)

        # Each task should have the expected fields
        for task in output_data["tasks"]:
            required_fields = [
                "id",
                "title",
                "status",
                "priority",
                "parent",
                "file_path",
                "created",
                "updated",
            ]
            for field in required_fields:
                assert field in task
                assert isinstance(task[field], str)
