"""Task scanner for walking the nested planning tree and yielding task front-matters."""

from pathlib import Path
from typing import Iterator

from .object_parser import parse_object
from .schema.task import TaskModel


def scan_tasks(project_root: Path) -> Iterator[TaskModel]:
    """
    Walk the nested planning tree and yield task front-matters.

    Traverses the hierarchy: planning/projects/P-*/epics/E-*/features/F-*/tasks-open/
    and tasks-done/ directories, parsing YAML front-matter from each task file.

    Args:
        project_root: Root path of the project containing planning/ directory

    Yields:
        TaskModel: Parsed task objects with front-matter data

    Note:
        Gracefully handles missing directories and unparseable files by skipping them.
        Files are validated to ensure they stay within the project root.
    """
    # Validate and resolve project root to prevent path traversal
    project_root = project_root.resolve()
    planning_dir = project_root / "planning"

    if not planning_dir.exists() or not planning_dir.is_dir():
        return

    projects_dir = planning_dir / "projects"
    if not projects_dir.exists() or not projects_dir.is_dir():
        return

    # Walk the nested hierarchy: projects -> epics -> features -> tasks
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        epics_dir = project_dir / "epics"
        if not epics_dir.exists() or not epics_dir.is_dir():
            continue

        for epic_dir in epics_dir.iterdir():
            if not epic_dir.is_dir():
                continue

            features_dir = epic_dir / "features"
            if not features_dir.exists() or not features_dir.is_dir():
                continue

            for feature_dir in features_dir.iterdir():
                if not feature_dir.is_dir():
                    continue

                # Scan both tasks-open and tasks-done directories
                for task_dir_name in ["tasks-open", "tasks-done"]:
                    task_dir = feature_dir / task_dir_name
                    if not task_dir.exists() or not task_dir.is_dir():
                        continue

                    for task_file in task_dir.iterdir():
                        if not task_file.is_file() or not task_file.suffix == ".md":
                            continue

                        # Security check: ensure file is within project root
                        if not task_file.resolve().is_relative_to(project_root):
                            continue

                        try:
                            task_obj = parse_object(task_file)
                            if isinstance(task_obj, TaskModel):
                                yield task_obj
                        except Exception:
                            # Skip unparseable files gracefully
                            continue
