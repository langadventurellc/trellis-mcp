"""Core task completion logic for Trellis MCP.

Provides the core function for validating and completing tasks that are
in-progress or in review status.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Union
import os

from .exceptions.invalid_status_for_completion import InvalidStatusForCompletion
from .exceptions.prerequisites_not_complete import PrerequisitesNotComplete
from .dependency_resolver import is_unblocked
from .io_utils import read_markdown, write_markdown
from .object_parser import parse_object
from .path_resolver import id_to_path, resolve_path_for_new_object
from .schema.status_enum import StatusEnum
from .schema.task import TaskModel


def complete_task(
    project_root: Union[str, Path],
    task_id: str,
    summary: str | None = None,
    files_changed: list[str] | None = None,
) -> TaskModel:
    """Complete a task by validating prerequisites and moving to tasks-done.

    Loads the specified task, validates that it is in a valid status
    for completion (in-progress or review) and that all its prerequisites
    are completed (status=done). Then moves the task file to tasks-done
    directory with timestamp prefix, updates status to 'done', and clears
    the worktree field. If summary is provided, appends a log entry first.

    Args:
        project_root: Root directory of the planning structure
        task_id: ID of the task to complete (with or without T- prefix)
        summary: Optional summary text for the log entry
        files_changed: Optional list of relative file paths that were changed

    Returns:
        TaskModel: The completed task object with status=done

    Raises:
        InvalidStatusForCompletion: If task is not in in-progress or review status
        PrerequisitesNotComplete: If task has incomplete or missing prerequisites
        FileNotFoundError: If task with the given ID cannot be found
        ValueError: If task_id is invalid or empty
        ValidationError: If task data is malformed
        OSError: If file operations fail during completion

    Example:
        >>> from pathlib import Path
        >>> project_root = Path("./planning")
        >>> task = complete_task(
        ...     project_root,
        ...     "T-implement-auth",
        ...     summary="Implemented JWT authentication system",
        ...     files_changed=["src/auth.py", "tests/test_auth.py"]
        ... )
        >>> print(f"Completed task: {task.title}")
        Completed task: Implement JWT authentication
        >>> task.status
        <StatusEnum.DONE: 'done'>
    """
    # Convert to Path if string
    project_root_path = Path(project_root)

    # Clean the task ID (remove prefix if present)
    clean_task_id = task_id.strip()
    if not clean_task_id:
        raise ValueError("Task ID cannot be empty")

    if clean_task_id.startswith("T-"):
        clean_task_id = clean_task_id[2:]

    # Resolve the task file path
    try:
        task_file_path = id_to_path(project_root_path, "task", clean_task_id)
    except FileNotFoundError:
        raise FileNotFoundError(f"Task with ID '{task_id}' not found")
    except ValueError as e:
        raise ValueError(f"Invalid task ID '{task_id}': {e}")

    # Load and parse the task
    task = parse_object(task_file_path)

    # Ensure we got a TaskModel (defensive check)
    if not isinstance(task, TaskModel):
        raise ValueError(f"Object '{task_id}' is not a task")

    # Validate that task status allows completion
    valid_statuses = {StatusEnum.IN_PROGRESS, StatusEnum.REVIEW}
    if task.status not in valid_statuses:
        raise InvalidStatusForCompletion(
            f"Task '{task_id}' has status '{task.status.value}' but must be "
            f"'in-progress' or 'review' to be completed"
        )

    # Validate that all prerequisites are completed
    if not is_unblocked(task, project_root_path):
        raise PrerequisitesNotComplete(
            f"Task '{task_id}' cannot be completed because one or more "
            f"prerequisites are not yet done"
        )

    # Append log entry if summary is provided
    if summary is not None:
        _append_log_entry(task_file_path, summary, files_changed or [])

    # Now actually complete the task by moving to tasks-done and updating status
    completed_task = _move_task_to_done(project_root_path, task, task_file_path, clean_task_id)

    # Check if parent feature should be updated to done status
    if task.parent:
        _check_and_update_parent_feature_status(project_root_path, task.parent)

    return completed_task


def _append_log_entry(task_file_path: Path, summary: str, files_changed: list[str]) -> None:
    """Append a log entry to the task file.

    Reads the existing task file, finds the ### Log section, and appends
    a new entry with timestamp, summary, and list of changed files.

    Args:
        task_file_path: Path to the task markdown file
        summary: Summary text for the log entry
        files_changed: List of relative file paths that were changed

    Raises:
        OSError: If file operations fail
        ValueError: If the file format is invalid
    """
    # Read the current file content
    yaml_dict, body = read_markdown(task_file_path)

    # Generate timestamp in ISO format with Z suffix
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Format the log entry
    log_entry = f"\n**{timestamp}** - {summary}"
    if files_changed:
        files_list = ", ".join(f'"{file}"' for file in files_changed)
        log_entry += f"\n- filesChanged: [{files_list}]"

    # Find the ### Log section and append the entry
    if "### Log" in body:
        # Append to existing log section
        body += log_entry
    else:
        # Add log section if it doesn't exist
        body += f"\n\n### Log{log_entry}"

    # Write the updated content back to the file
    write_markdown(task_file_path, yaml_dict, body)


def _move_task_to_done(
    project_root: Path, task: TaskModel, current_path: Path, clean_task_id: str
) -> TaskModel:
    """Move a task file to tasks-done directory and update status to done.

    Reads the current task file, updates the YAML front-matter to set status=done
    and clear worktree field, generates the destination path with timestamp prefix,
    writes to new location, and removes the old file.

    Args:
        project_root: Root directory of the planning structure
        task: The current TaskModel object
        current_path: Current file path in tasks-open
        clean_task_id: Task ID without T- prefix

    Returns:
        TaskModel: Updated task model with status=done

    Raises:
        OSError: If file operations fail
        ValueError: If path resolution fails
    """
    # Read current file content
    yaml_dict, body = read_markdown(current_path)

    # Update the YAML front-matter for completion
    yaml_dict["status"] = "done"
    yaml_dict["worktree"] = None

    # Resolve destination path in tasks-done with timestamp prefix
    if task.parent is None:
        raise ValueError(f"Task '{clean_task_id}' has no parent feature")

    parent_clean = task.parent[2:] if task.parent.startswith("F-") else task.parent
    destination_path = resolve_path_for_new_object(
        kind="task",
        obj_id=clean_task_id,
        parent_id=parent_clean,
        project_root=project_root,
        status="done",
    )

    # Ensure the destination directory exists
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to new location with updated status
    write_markdown(destination_path, yaml_dict, body)

    # Remove the old file from tasks-open
    os.remove(current_path)

    # Create and return updated TaskModel
    updated_task = TaskModel(
        kind=task.kind,
        id=task.id,
        parent=task.parent,
        status=StatusEnum.DONE,
        title=task.title,
        priority=task.priority,
        worktree=None,  # Clear worktree field
        created=task.created,
        updated=datetime.now(timezone.utc),  # Update the modified timestamp
        schema_version=task.schema_version,
        prerequisites=task.prerequisites,
    )

    return updated_task


def _get_all_feature_tasks(project_root: Path, feature_id: str) -> list[TaskModel]:
    """Get all tasks (open and done) for a specific feature.

    Scans both tasks-open and tasks-done directories under the specified feature
    and returns all task objects found.

    Args:
        project_root: Root directory of the planning structure
        feature_id: Feature ID (with or without F- prefix)

    Returns:
        List of all TaskModel instances for the feature

    Raises:
        ValueError: If feature_id is invalid
        FileNotFoundError: If feature cannot be found
    """
    # Clean the feature ID (remove prefix if present)
    clean_feature_id = feature_id.strip()
    if clean_feature_id.startswith("F-"):
        clean_feature_id = clean_feature_id[2:]

    # Find the feature path to get its directory
    try:
        feature_path = id_to_path(project_root, "feature", clean_feature_id)
    except FileNotFoundError:
        raise FileNotFoundError(f"Feature with ID '{feature_id}' not found")

    feature_dir = feature_path.parent
    tasks = []

    # Scan tasks-open directory
    tasks_open_dir = feature_dir / "tasks-open"
    if tasks_open_dir.exists() and tasks_open_dir.is_dir():
        for task_file in tasks_open_dir.iterdir():
            if task_file.is_file() and task_file.name.endswith(".md"):
                try:
                    task_obj = parse_object(task_file)
                    if isinstance(task_obj, TaskModel):
                        tasks.append(task_obj)
                except Exception:
                    # Skip files that cannot be parsed
                    continue

    # Scan tasks-done directory
    tasks_done_dir = feature_dir / "tasks-done"
    if tasks_done_dir.exists() and tasks_done_dir.is_dir():
        for task_file in tasks_done_dir.iterdir():
            if task_file.is_file() and task_file.name.endswith(".md"):
                try:
                    task_obj = parse_object(task_file)
                    if isinstance(task_obj, TaskModel):
                        tasks.append(task_obj)
                except Exception:
                    # Skip files that cannot be parsed
                    continue

    return tasks


def _update_feature_status(project_root: Path, feature_id: str, new_status: str) -> None:
    """Update a feature's status in its YAML front-matter.

    Args:
        project_root: Root directory of the planning structure
        feature_id: Feature ID (with or without F- prefix)
        new_status: New status value

    Raises:
        FileNotFoundError: If feature cannot be found
        ValueError: If status transition is invalid
        OSError: If file operations fail
    """
    from datetime import datetime, timezone

    # Clean the feature ID (remove prefix if present)
    clean_feature_id = feature_id.strip()
    if clean_feature_id.startswith("F-"):
        clean_feature_id = clean_feature_id[2:]

    # Find and load the feature
    feature_path = id_to_path(project_root, "feature", clean_feature_id)
    yaml_dict, body = read_markdown(feature_path)

    # Update status and timestamp
    yaml_dict["status"] = new_status
    yaml_dict["updated"] = datetime.now(timezone.utc).isoformat()

    # Write back to file
    write_markdown(feature_path, yaml_dict, body)


def _check_and_update_parent_feature_status(project_root: Path, parent_feature_id: str) -> None:
    """Check if parent feature should be updated to done status when all tasks are complete.

    Loads all tasks for the parent feature and checks if they are all done.
    If so, and the feature is currently in-progress, updates it to done status.

    Args:
        project_root: Root directory of the planning structure
        parent_feature_id: Parent feature ID (with or without F- prefix)

    Raises:
        FileNotFoundError: If parent feature cannot be found
        OSError: If file operations fail
    """
    # Clean the parent feature ID
    clean_feature_id = parent_feature_id.strip()
    if clean_feature_id.startswith("F-"):
        clean_feature_id = clean_feature_id[2:]

    try:
        # Load the parent feature to check its current status
        feature_path = id_to_path(project_root, "feature", clean_feature_id)
        feature = parse_object(feature_path)

        # Only update if feature is currently in-progress
        if feature.status != StatusEnum.IN_PROGRESS:
            return

        # Get all tasks for this feature
        feature_tasks = _get_all_feature_tasks(project_root, clean_feature_id)

        # Check if all tasks are done
        if not feature_tasks:
            # No tasks in feature, don't update status
            return

        all_tasks_done = all(task.status == StatusEnum.DONE for task in feature_tasks)

        if all_tasks_done:
            # Update feature status to done
            _update_feature_status(project_root, clean_feature_id, "done")

    except FileNotFoundError:
        # Parent feature not found, skip update
        pass
    except Exception:
        # Any other error, skip update to avoid breaking task completion
        pass
