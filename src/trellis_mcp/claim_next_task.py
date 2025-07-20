"""Core task claiming logic for Trellis MCP.

Provides the core function for atomically claiming the next highest-priority
unblocked task from the backlog, supporting both hierarchical and standalone tasks.
"""

from datetime import datetime
from pathlib import Path

from .dependency_resolver import is_unblocked
from .exceptions.no_available_task import NoAvailableTask
from .exceptions.validation_error import ValidationError, ValidationErrorCode
from .filters import filter_by_scope, validate_scope_exists
from .object_dumper import write_object
from .path_resolver import resolve_project_roots
from .scanner import scan_tasks
from .schema.status_enum import StatusEnum
from .schema.task import TaskModel
from .task_sorter import sort_tasks_by_priority


def claim_next_task(
    project_root: str | Path, worktree_path: str | None = None, scope: str | None = None
) -> TaskModel:
    """Claim the next highest-priority unblocked task.

    Atomically selects the highest-priority open task where all prerequisites
    are completed, updates its status to 'in-progress', optionally stamps the
    worktree field, and writes the changes to disk.

    Supports both hierarchical tasks (under projects/epics/features) and
    standalone tasks (at the root level). Standalone tasks are prioritized
    over hierarchical tasks when both have the same priority.

    When scope is provided, only tasks within that scope boundary are eligible
    for claiming. Scope validation uses the kind inference engine.

    Args:
        project_root: Root directory of the planning structure
        worktree_path: Optional worktree identifier to stamp on the claimed task
        scope: Optional scope ID (P-, E-, F-) to filter tasks by parent boundaries

    Returns:
        TaskModel: The updated task object with status=in-progress

    Raises:
        NoAvailableTask: If no unblocked tasks are available for claiming
        ValidationError: If scope is invalid or task data is invalid
        OSError: If file operations fail

    Example:
        >>> from pathlib import Path
        >>> project_root = Path("./planning")
        >>> task = claim_next_task(project_root, "/workspace/feature-branch")
        >>> print(f"Claimed: {task.title}")
        Claimed: Implement JWT authentication
        >>> task.status
        <StatusEnum.IN_PROGRESS: 'in-progress'>
        >>> task.worktree
        '/workspace/feature-branch'

        >>> # Claim task within specific scope
        >>> scoped_task = claim_next_task(project_root, scope="F-user-auth")
        >>> print(f"Claimed within scope: {scoped_task.title}")
        Claimed within scope: Create login form
    """
    # Resolve project root to planning directory
    scanning_root, planning_root = resolve_project_roots(project_root)

    # Validate scope if provided
    if scope and scope.strip():
        try:
            validate_scope_exists(planning_root, scope.strip())
        except ValidationError:
            # Re-raise with more specific context for claiming
            raise ValidationError(
                errors=[f"Scope object not found: {scope.strip()}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"scope": scope.strip(), "operation": "claim_next_task"},
            )

    # Use scope-aware task discovery if scope provided
    if scope and scope.strip():
        all_tasks = list(filter_by_scope(scanning_root, scope.strip()))
    else:
        # Load all tasks from both hierarchical and standalone locations
        all_tasks = list(scan_tasks(scanning_root))

    # Filter to only open tasks (scanner returns all tasks, so we need to filter)
    open_tasks = [task for task in all_tasks if task.status == StatusEnum.OPEN]

    if not open_tasks:
        if scope and scope.strip():
            raise NoAvailableTask(f"No open tasks available within scope: {scope.strip()}")
        else:
            raise NoAvailableTask("No open tasks available in backlog")

    # Filter to only unblocked tasks (all prerequisites completed)
    unblocked_tasks = [task for task in open_tasks if is_unblocked(task, planning_root)]

    if not unblocked_tasks:
        if scope and scope.strip():
            raise NoAvailableTask(
                f"No unblocked tasks available within scope {scope.strip()} - "
                "all open tasks have incomplete prerequisites"
            )
        else:
            raise NoAvailableTask(
                "No unblocked tasks available - all open tasks have incomplete prerequisites"
            )

    # Sort by priority (high first) and creation date (older first)
    sorted_tasks = sort_tasks_by_priority(unblocked_tasks)

    # Select the first task (highest priority, oldest if tied)
    selected_task = sorted_tasks[0]

    # Update task metadata
    selected_task.status = StatusEnum.IN_PROGRESS
    selected_task.updated = datetime.now()
    if worktree_path and worktree_path.strip():
        selected_task.worktree = worktree_path

    # Atomically write the updated task to filesystem
    write_object(selected_task, planning_root)

    return selected_task
