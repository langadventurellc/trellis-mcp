"""Tests for complete_task file movement functionality."""

from trellis_mcp.complete_task import complete_task
from trellis_mcp.io_utils import write_markdown, read_markdown
from trellis_mcp.schema.status_enum import StatusEnum


def test_complete_task_moves_file_to_done(tmp_path):
    """Test that complete_task actually moves the file to tasks-done directory."""
    # Create a minimal project structure
    project_root = tmp_path / "planning"
    feature_dir = (
        project_root
        / "projects"
        / "P-test-project"
        / "epics"
        / "E-test-epic"
        / "features"
        / "F-test-feature"
    )
    task_open_dir = feature_dir / "tasks-open"
    task_done_dir = feature_dir / "tasks-done"

    # Create directories
    task_open_dir.mkdir(parents=True)
    task_done_dir.mkdir(parents=True)

    # Create the required parent files for path resolution to work
    # Create project.md
    project_file = project_root / "projects" / "P-test-project" / "project.md"
    project_file.parent.mkdir(parents=True, exist_ok=True)
    project_yaml = {
        "kind": "project",
        "id": "test-project",
        "parent": None,
        "status": "open",
        "title": "Test project",
        "priority": "normal",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T12:00:00Z",
        "schema_version": "1.0",
    }
    write_markdown(project_file, project_yaml, "# Test Project")

    # Create epic.md
    epic_file = project_root / "projects" / "P-test-project" / "epics" / "E-test-epic" / "epic.md"
    epic_file.parent.mkdir(parents=True, exist_ok=True)
    epic_yaml = {
        "kind": "epic",
        "id": "test-epic",
        "parent": "P-test-project",
        "status": "open",
        "title": "Test epic",
        "priority": "normal",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T12:00:00Z",
        "schema_version": "1.0",
    }
    write_markdown(epic_file, epic_yaml, "# Test Epic")

    # Create feature.md
    feature_file = feature_dir / "feature.md"
    feature_yaml = {
        "kind": "feature",
        "id": "test-feature",
        "parent": "E-test-epic",
        "status": "open",
        "title": "Test feature",
        "priority": "normal",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T12:00:00Z",
        "schema_version": "1.0",
    }
    write_markdown(feature_file, feature_yaml, "# Test Feature")

    # Create a test task file in tasks-open
    task_file = task_open_dir / "T-test-task.md"
    task_yaml = {
        "kind": "task",
        "id": "test-task",
        "parent": "F-test-feature",
        "status": "in-progress",
        "title": "Test task for completion",
        "priority": "normal",
        "worktree": "/some/path",
        "created": "2025-01-01T12:00:00Z",
        "updated": "2025-01-01T12:00:00Z",
        "schema_version": "1.0",
        "prerequisites": [],
    }
    task_body = "# Test Task\n\nThis is a test task."

    write_markdown(task_file, task_yaml, task_body)

    # Verify the file exists in tasks-open
    assert task_file.exists()

    # Complete the task
    result = complete_task(project_root, "test-task")

    # Verify the result
    assert result.status == StatusEnum.DONE
    assert result.worktree is None
    assert result.id == "test-task"
    assert result.title == "Test task for completion"

    # Verify the original file is removed
    assert not task_file.exists()

    # Verify a file was created in tasks-done with timestamp prefix
    done_files = list(task_done_dir.glob("*-T-test-task.md"))
    assert len(done_files) == 1

    done_file = done_files[0]
    assert done_file.name.endswith("-T-test-task.md")
    # Check timestamp format (YYYYMMDD_HHMMSS)
    timestamp_part = done_file.name.split("-T-")[0]
    assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS
    assert timestamp_part.count("_") == 1

    # Verify the moved file has correct YAML front-matter (S-06 requirement)
    done_yaml, done_body = read_markdown(done_file)
    assert done_yaml["status"] == "done"
    assert done_yaml["worktree"] is None
    assert done_yaml["id"] == "test-task"
    assert done_yaml["title"] == "Test task for completion"
    assert done_body == task_body  # Body should be preserved
