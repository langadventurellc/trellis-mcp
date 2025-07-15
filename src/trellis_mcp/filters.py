"""Filtering utilities for Trellis MCP tasks and objects."""

from pathlib import Path
from typing import Iterator

from .markdown_loader import load_markdown
from .models.filter_params import FilterParams
from .object_parser import parse_object
from .schema.task import TaskModel


def filter_by_scope(root: Path, scope_id: str) -> Iterator[TaskModel]:
    """Filter tasks by scope (project, epic, or feature).

    Args:
        root: Path to the project root containing planning/ directory
        scope_id: ID of the scope to filter by (project/epic/feature ID)

    Yields:
        TaskModel: Tasks that belong to the specified scope

    Note:
        Scope filtering works hierarchically:
        - Project scope includes all tasks in all epics/features under that project
        - Epic scope includes all tasks in all features under that epic
        - Feature scope includes all tasks directly under that feature
        - Also matches tasks where scope_id is the direct parent
    """
    # Validate and resolve project root to prevent path traversal
    project_root = root.resolve()
    planning_dir = project_root / "planning"

    if not planning_dir.exists() or not planning_dir.is_dir():
        return

    projects_dir = planning_dir / "projects"
    if not projects_dir.exists() or not projects_dir.is_dir():
        return

    # Traverse the directory structure: projects -> epics -> features -> tasks
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir() or not project_dir.name.startswith("P-"):
            continue

        project_id = project_dir.name  # Keep the P- prefix for comparison

        epics_dir = project_dir / "epics"
        if not epics_dir.exists() or not epics_dir.is_dir():
            continue

        for epic_dir in epics_dir.iterdir():
            if not epic_dir.is_dir() or not epic_dir.name.startswith("E-"):
                continue

            epic_id = epic_dir.name  # Keep the E- prefix for comparison

            features_dir = epic_dir / "features"
            if not features_dir.exists() or not features_dir.is_dir():
                continue

            for feature_dir in features_dir.iterdir():
                if not feature_dir.is_dir() or not feature_dir.name.startswith("F-"):
                    continue

                feature_id = feature_dir.name  # Keep the F- prefix for comparison

                # Check both tasks-open and tasks-done directories
                for task_dir_name in ["tasks-open", "tasks-done"]:
                    task_dir = feature_dir / task_dir_name
                    if not task_dir.exists() or not task_dir.is_dir():
                        continue

                    for task_file in task_dir.iterdir():
                        if not task_file.is_file() or not task_file.name.endswith(".md"):
                            continue

                        # Security check: ensure file is within project root
                        if not task_file.resolve().is_relative_to(project_root):
                            continue

                        try:
                            # Load and parse task YAML front-matter
                            yaml_dict, _ = load_markdown(task_file)
                        except Exception:
                            # Skip files that can't be parsed
                            continue

                        # Apply scope filtering
                        task_parent = yaml_dict.get("parent", "")
                        if (
                            scope_id == project_id
                            or scope_id == epic_id
                            or scope_id == feature_id
                            or scope_id == task_parent
                        ):
                            # Parse into TaskModel and yield
                            try:
                                task_obj = parse_object(task_file)
                                if isinstance(task_obj, TaskModel):
                                    yield task_obj
                            except Exception:
                                # Skip unparseable tasks gracefully
                                continue


def apply_filters(tasks: Iterator[TaskModel], filter_params: FilterParams) -> Iterator[TaskModel]:
    """Apply status and priority filters to a collection of tasks.

    Args:
        tasks: Iterator of TaskModel objects to filter
        filter_params: FilterParams object specifying status and priority filters

    Yields:
        TaskModel: Tasks that match the specified filter criteria

    Note:
        - If filter_params.status is empty, no status filtering is applied
        - If filter_params.priority is empty, no priority filtering is applied
        - Both filters are applied as logical AND (task must match both if specified)
        - Tasks that fail to parse are gracefully skipped
    """
    for task in tasks:
        try:
            # Apply status filter if specified
            if filter_params.status and task.status not in filter_params.status:
                continue

            # Apply priority filter if specified
            if filter_params.priority and task.priority not in filter_params.priority:
                continue

            # Task matches all specified filters
            yield task
        except Exception:
            # Skip tasks that fail to process gracefully
            continue
