"""Backlog loader for Trellis MCP.

Provides functionality to scan the planning directory structure and load all open tasks
from the tasks-open directories under all features.
"""

from pathlib import Path
from typing import List

from .object_parser import parse_object
from .schema.task import TaskModel


def load_backlog_tasks(project_root: Path) -> List[TaskModel]:
    """Load all open tasks from the backlog across all features.

    Scans the hierarchical project structure (Projects → Epics → Features → Tasks)
    and collects all tasks from tasks-open directories under features. Each task
    file is parsed into a TaskModel instance using the object parser.

    Args:
        project_root: Root directory of the planning structure (e.g., ./planning)

    Returns:
        List of TaskModel instances representing all open tasks in the backlog.
        Returns empty list if no tasks found or if planning structure doesn't exist.

    Example:
        >>> project_root = Path("./planning")
        >>> tasks = load_backlog_tasks(project_root)
        >>> len(tasks)
        5
        >>> tasks[0].title
        'Implement JWT authentication'
        >>> tasks[0].status
        <StatusEnum.OPEN: 'open'>

    Note:
        - Only scans tasks-open directories (not tasks-done)
        - Skips files that cannot be parsed (malformed YAML, invalid schema)
        - Maintains original file order within each feature directory
        - Task objects include all metadata: priority, prerequisites, status, etc.
    """
    tasks: List[TaskModel] = []

    # Check if projects directory exists
    projects_dir = project_root / "projects"
    if not projects_dir.exists() or not projects_dir.is_dir():
        return tasks

    # Scan all projects
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        # Scan epics within this project
        epics_dir = project_dir / "epics"
        if not epics_dir.exists() or not epics_dir.is_dir():
            continue

        for epic_dir in epics_dir.iterdir():
            if not epic_dir.is_dir():
                continue

            # Scan features within this epic
            features_dir = epic_dir / "features"
            if not features_dir.exists() or not features_dir.is_dir():
                continue

            for feature_dir in features_dir.iterdir():
                if not feature_dir.is_dir():
                    continue

                # Scan tasks-open directory within this feature
                tasks_open_dir = feature_dir / "tasks-open"
                if not tasks_open_dir.exists() or not tasks_open_dir.is_dir():
                    continue

                # Load all task files from tasks-open directory
                for task_file in tasks_open_dir.iterdir():
                    if not task_file.is_file() or not task_file.name.endswith(".md"):
                        continue

                    try:
                        # Parse the task file into a TaskModel
                        task_obj = parse_object(task_file)

                        # Ensure it's actually a TaskModel (defense against wrong file types)
                        if isinstance(task_obj, TaskModel):
                            tasks.append(task_obj)
                    except Exception:
                        # Skip files that cannot be parsed (malformed YAML, validation errors, etc.)
                        # This ensures the function is robust against corrupted or invalid files
                        continue

    return tasks
