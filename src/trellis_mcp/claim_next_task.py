"""Core task claiming logic for Trellis MCP.

Provides the core function for atomically claiming the next highest-priority
unblocked task from the backlog, supporting both hierarchical and standalone tasks.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast

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


def _find_task_by_id(project_root: Path, task_id: str) -> TaskModel | None:
    """Find a specific task by ID in the project.

    Searches both hierarchical and standalone tasks for the specified task ID.

    Args:
        project_root: Root directory of the planning structure
        task_id: Task ID to search for (T- prefixed or standalone format)

    Returns:
        TaskModel if found, None otherwise
    """
    # Load all tasks from both hierarchical and standalone locations
    all_tasks = list(scan_tasks(project_root))

    # Search for task with matching ID
    for task in all_tasks:
        if task.id == task_id:
            return task

    return None


def claim_specific_task(
    project_root: str | Path,
    task_id: str,
    worktree: str = "",
    force_claim: bool = False,
) -> TaskModel:
    """Claim a specific task by ID with validation and atomic updates.

    Locates a specific task by ID across both hierarchical and standalone task
    systems, validates its claimability, and claims it atomically by updating
    its status to 'in-progress'. When force_claim=True, bypasses prerequisite
    validation to allow claiming tasks with incomplete dependencies.

    Args:
        project_root: Root directory of the planning structure
        task_id: Task ID to claim directly (T- prefixed or standalone format)
        worktree: Optional worktree identifier to stamp on the claimed task
        force_claim: When True, bypasses prerequisite validation and allows
            claiming tasks with incomplete dependencies. Defaults to False.

    Returns:
        TaskModel: The updated task object with status=in-progress

    Raises:
        NoAvailableTask: If task not found, wrong status, or (when force_claim=False)
            prerequisites incomplete
        ValidationError: If task data is invalid
        OSError: If file operations fail

    Example:
        >>> task = claim_specific_task("./planning", "T-implement-auth", "/workspace/auth")
        >>> task.status
        <StatusEnum.IN_PROGRESS: 'in-progress'>
        >>> task.worktree
        '/workspace/auth'

        >>> # Force claim a task with incomplete prerequisites
        >>> task = claim_specific_task("./planning", "T-blocked-task", force_claim=True)
        >>> task.status
        <StatusEnum.IN_PROGRESS: 'in-progress'>
    """
    # Resolve project root to planning directory
    scanning_root, planning_root = resolve_project_roots(project_root)

    # Clean and validate task_id
    if not task_id or not task_id.strip():
        raise ValidationError(
            errors=["Task ID cannot be empty"],
            error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
            context={"field": "task_id"},
        )

    task_id = task_id.strip()

    # Find the specific task by ID
    target_task = _find_task_by_id(scanning_root, task_id)
    if not target_task:
        raise NoAvailableTask(f"Task not found: {task_id}")

    # Validate task is in open status
    if target_task.status != StatusEnum.OPEN:
        raise NoAvailableTask(
            f"Task {task_id} is not available for claiming (status: {target_task.status.value})"
        )

    # Validate task is unblocked (all prerequisites completed) unless force_claim=True
    if not force_claim:
        if not is_unblocked(target_task, planning_root):
            raise NoAvailableTask(f"Task {task_id} cannot be claimed - prerequisites not completed")
    else:
        # Log warning when bypassing prerequisite validation
        if target_task.prerequisites:
            incomplete_prereqs = []
            # Check which prerequisites are incomplete for audit logging
            try:
                from .utils.id_utils import clean_prerequisite_id
                from .validation import get_all_objects

                all_objects = cast(dict[str, dict[str, Any]], get_all_objects(planning_root))
                for prereq_id in target_task.prerequisites:
                    clean_prereq_id = clean_prerequisite_id(prereq_id)
                    if clean_prereq_id not in all_objects:
                        incomplete_prereqs.append(prereq_id)
                    elif all_objects[clean_prereq_id].get("status", "") != "done":
                        incomplete_prereqs.append(prereq_id)

                if incomplete_prereqs:
                    logging.warning(
                        f"Force claiming task {task_id} with incomplete prerequisites: "
                        f"{incomplete_prereqs}. Task dependency graph integrity maintained "
                        f"but business rules bypassed."
                    )
            except Exception as e:
                # If we can't check prerequisites for logging, still proceed with force claim
                # but log that we couldn't determine incomplete prerequisites
                logging.warning(
                    f"Force claiming task {task_id}. Could not determine prerequisite "
                    f"status for audit: {e}"
                )

    # Update task metadata
    target_task.status = StatusEnum.IN_PROGRESS
    target_task.updated = datetime.now()
    if worktree and worktree.strip():
        target_task.worktree = worktree.strip()

    # Atomically write the updated task to filesystem
    write_object(target_task, planning_root)

    return target_task


def claim_next_task(
    project_root: str | Path,
    worktree_path: str | None = None,
    scope: str | None = None,
    task_id: str | None = None,
    force_claim: bool = False,
) -> TaskModel:
    """Claim the next highest-priority unblocked task or a specific task by ID.

    Atomically selects the highest-priority open task where all prerequisites
    are completed, updates its status to 'in-progress', optionally stamps the
    worktree field, and writes the changes to disk.

    Supports both hierarchical tasks (under projects/epics/features) and
    standalone tasks (at the root level). Standalone tasks are prioritized
    over hierarchical tasks when both have the same priority.

    When task_id is provided, claims that specific task directly, bypassing
    priority-based selection. When scope is provided, only tasks within that
    scope boundary are eligible for claiming. When force_claim=True with task_id,
    bypasses prerequisite validation to allow claiming blocked tasks.

    Args:
        project_root: Root directory of the planning structure
        worktree_path: Optional worktree identifier to stamp on the claimed task
        scope: Optional scope ID (P-, E-, F-) to filter tasks by parent boundaries
        task_id: Optional task ID to claim directly (T- prefixed or standalone format)
        force_claim: When True, bypasses prerequisite validation for direct task claiming.
            Only valid when task_id is provided. Defaults to False.

    Returns:
        TaskModel: The updated task object with status=in-progress

    Raises:
        NoAvailableTask: If no unblocked tasks are available for claiming or task_id not found
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

        >>> # Force claim a blocked task
        >>> blocked_task = claim_next_task(project_root, task_id="T-blocked", force_claim=True)
        >>> print(f"Force claimed: {blocked_task.title}")
        Force claimed: Blocked task with incomplete prerequisites
    """
    # Resolve project root to planning directory
    scanning_root, planning_root = resolve_project_roots(project_root)

    # Handle direct task claiming by ID if task_id is provided
    if task_id and task_id.strip():
        # Route to dedicated direct claiming function
        return claim_specific_task(project_root, task_id.strip(), worktree_path or "", force_claim)

    # Validate scope if provided
    if scope and scope.strip():
        try:
            validate_scope_exists(scanning_root, scope.strip())
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
