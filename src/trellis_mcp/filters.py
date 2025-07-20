"""Filtering utilities for Trellis MCP tasks and objects."""

from pathlib import Path
from typing import Iterator

from .inference import KindInferenceEngine
from .markdown_loader import load_markdown
from .models.filter_params import FilterParams
from .object_parser import parse_object
from .schema.task import TaskModel


def validate_scope_exists(root: Path, scope_id: str) -> str:
    """Validate that a scope object exists using KindInferenceEngine.

    This function provides scope validation that can be called by tools
    before using filter_by_scope to ensure the scope exists.

    Args:
        root: Path to the project root containing planning/ directory
        scope_id: ID of the scope to validate (project/epic/feature ID)

    Returns:
        The validated scope kind ("project", "epic", "feature")

    Raises:
        ValidationError: If scope_id is invalid or scope object doesn't exist
    """
    project_root = root.resolve()
    planning_dir = project_root / "planning"

    if not planning_dir.exists() or not planning_dir.is_dir():
        from .exceptions import ValidationError, ValidationErrorCode

        raise ValidationError(
            errors=["Planning directory not found"],
            error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
        )

    inference_engine = KindInferenceEngine(planning_dir)
    return inference_engine.infer_kind(scope_id, validate=True)


def filter_by_scope(root: Path, scope_id: str) -> Iterator[TaskModel]:
    """Filter tasks by scope (project, epic, or feature).

    Hierarchical filtering: project scope includes all child tasks,
    epic scope includes tasks in child features, feature scope includes direct tasks.

    Standalone task filtering: project scope includes all standalone tasks,
    epic/feature scope filtering for standalone tasks requires metadata linkage.

    Note: This function does not validate scope existence for backwards compatibility.
    Use validate_scope_exists() before calling this function if validation is needed.

    Args:
        root: Path to the project root containing planning/ directory
        scope_id: ID of the scope to filter by (project/epic/feature ID)

    Yields:
        TaskModel: Tasks that belong to the specified scope
    """
    # Validate and resolve project root to prevent path traversal
    project_root = root.resolve()
    planning_dir = project_root / "planning"

    if not planning_dir.exists() or not planning_dir.is_dir():
        return

    projects_dir = planning_dir / "projects"
    # Note: projects_dir might not exist if there are only standalone tasks

    # Traverse the hierarchical structure: projects -> epics -> features -> tasks
    if projects_dir.exists() and projects_dir.is_dir():
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

    # Also scan standalone tasks at the root level
    # Project scope includes all standalone tasks (global project scope)
    if scope_id.startswith("P-"):
        for task_dir_name in ["tasks-open", "tasks-done"]:
            task_dir = planning_dir / task_dir_name
            if not task_dir.exists() or not task_dir.is_dir():
                continue

            for task_file in task_dir.iterdir():
                if not task_file.is_file() or not task_file.name.endswith(".md"):
                    continue

                # Security check: ensure file is within project root
                if not task_file.resolve().is_relative_to(project_root):
                    continue

                try:
                    # Parse into TaskModel and yield
                    task_obj = parse_object(task_file)
                    if isinstance(task_obj, TaskModel):
                        yield task_obj
                except Exception:
                    # Skip unparseable tasks gracefully
                    continue


def apply_filters(tasks: Iterator[TaskModel], filter_params: FilterParams) -> Iterator[TaskModel]:
    """Apply status and priority filters to a collection of tasks.

    Empty filter lists mean no filtering is applied. Both filters use logical AND.

    Args:
        tasks: Iterator of TaskModel objects to filter
        filter_params: FilterParams object specifying status and priority filters

    Yields:
        TaskModel: Tasks that match the specified filter criteria
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
