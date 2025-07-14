"""Path resolution utilities for Trellis MCP objects.

Provides functions for converting object IDs to filesystem paths within the
hierarchical project structure (Projects → Epics → Features → Tasks).
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from .fs_utils import find_object_path

# Valid object kinds in the Trellis MCP hierarchy
VALID_KINDS: Final[set[str]] = {"project", "epic", "feature", "task"}


def id_to_path(project_root: Path, kind: str, obj_id: str) -> Path:
    """Convert an object ID to its filesystem path within the project structure.

    Maps Trellis MCP object IDs to their corresponding filesystem paths based on
    the hierarchical structure: Projects → Epics → Features → Tasks.

    This function uses the shared find_object_path utility to locate objects
    within the directory structure.

    Args:
        project_root: Root directory of the planning structure (e.g., ./planning)
        kind: The object kind ('project', 'epic', 'feature', or 'task')
        obj_id: The object ID (without prefix, e.g., 'user-auth' not 'P-user-auth')

    Returns:
        Path object pointing to the appropriate file:
        - project: planning/projects/P-{id}/project.md
        - epic: planning/projects/P-{parent}/epics/E-{id}/epic.md
        - feature: planning/projects/P-{parent}/epics/E-{parent}/features/F-{id}/feature.md
        - task: planning/projects/P-{parent}/epics/E-{parent}/features/F-{parent}/tasks-open/
                T-{id}.md
                or planning/projects/P-{parent}/epics/E-{parent}/features/F-{parent}/tasks-done/
                {timestamp}-T-{id}.md

    Raises:
        ValueError: If kind is not supported or obj_id is empty
        FileNotFoundError: If the object with the given ID cannot be found

    Example:
        >>> project_root = Path("./planning")
        >>> id_to_path(project_root, "project", "user-auth")
        Path('planning/projects/P-user-auth/project.md')
        >>> id_to_path(project_root, "task", "implement-jwt")
        Path('planning/projects/P-user-auth/epics/E-auth/features/F-login/tasks-open/T-implement-jwt.md')

    Note:
        For tasks, this function will return the path to the actual file location,
        checking both tasks-open and tasks-done directories to find where the task exists.
    """
    # Use the shared utility to find the object path
    result_path = find_object_path(kind, obj_id, project_root)

    if result_path is None:
        # Clean the ID for error message (remove any existing prefix if present)
        clean_id = obj_id.strip()
        if clean_id.startswith(("P-", "E-", "F-", "T-")):
            clean_id = clean_id[2:]

        # Provide more specific error messages based on the kind and project structure
        if kind == "project":
            raise FileNotFoundError(f"Project with ID '{clean_id}' not found")
        elif kind == "epic":
            projects_dir = project_root / "projects"
            if not projects_dir.exists():
                raise FileNotFoundError(
                    f"Epic with ID '{clean_id}' not found: projects directory does not exist"
                )
            raise FileNotFoundError(f"Epic with ID '{clean_id}' not found")
        elif kind == "feature":
            projects_dir = project_root / "projects"
            if not projects_dir.exists():
                raise FileNotFoundError(
                    f"Feature with ID '{clean_id}' not found: projects directory does not exist"
                )
            raise FileNotFoundError(f"Feature with ID '{clean_id}' not found")
        elif kind == "task":
            projects_dir = project_root / "projects"
            if not projects_dir.exists():
                raise FileNotFoundError(
                    f"Task with ID '{clean_id}' not found: projects directory does not exist"
                )
            raise FileNotFoundError(f"Task with ID '{clean_id}' not found")

    # At this point, result_path is guaranteed to be a Path object
    # because we would have raised an exception if it was None
    assert result_path is not None, "result_path should not be None at this point"
    return result_path


def resolve_path_for_new_object(
    kind: str, obj_id: str, parent_id: str | None, project_root: Path, status: str | None = None
) -> Path:
    """Resolve the filesystem path for a new Trellis MCP object.

    Constructs the appropriate filesystem path for creating a new object based on
    the Trellis MCP hierarchical structure. Unlike id_to_path, this function is
    designed for path construction during object creation and doesn't require
    the target object to already exist.

    Args:
        kind: The object kind ('project', 'epic', 'feature', or 'task')
        obj_id: The object ID (without prefix, e.g., 'user-auth' not 'P-user-auth')
        parent_id: Parent object ID (required for epics, features, tasks)
        project_root: Root directory of the planning structure
        status: Object status (affects task directory and filename, optional)

    Returns:
        Path object pointing to where the new object file should be created:
        - project: planning/projects/P-{id}/project.md
        - epic: planning/projects/P-{parent}/epics/E-{id}/epic.md
        - feature: planning/projects/P-{parent}/epics/E-{parent}/features/F-{id}/feature.md
        - task: planning/projects/P-{parent}/epics/E-{parent}/features/F-{parent}/tasks-{status}/
                {filename}.md

    Raises:
        ValueError: If kind is not supported, obj_id is empty, or required parent is missing
        FileNotFoundError: If parent object cannot be found (for features and tasks)

    Example:
        >>> project_root = Path("./planning")
        >>> resolve_path_for_new_object("project", "user-auth", None, project_root)
        Path('planning/projects/P-user-auth/project.md')
        >>> resolve_path_for_new_object("epic", "authentication", "user-auth", project_root)
        Path('planning/projects/P-user-auth/epics/E-authentication/epic.md')
        >>> resolve_path_for_new_object("task", "impl-jwt", "login", project_root, "open")
        Path('planning/projects/P-user-auth/epics/E-auth/features/F-login/tasks-open/T-impl-jwt.md')

    Note:
        For tasks, the status parameter determines:
        - Directory: tasks-open (default) or tasks-done (if status="done")
        - Filename: T-{id}.md (open) or {timestamp}-T-{id}.md (done)
    """
    # Validate inputs
    if not kind or kind not in VALID_KINDS:
        raise ValueError(f"Invalid kind '{kind}'. Must be one of: {VALID_KINDS}")

    if not obj_id or not obj_id.strip():
        raise ValueError("Object ID cannot be empty")

    # Clean the ID (remove any existing prefix if present)
    clean_id = obj_id.strip()
    if clean_id.startswith(("P-", "E-", "F-", "T-")):
        clean_id = clean_id[2:]

    # Build path based on kind
    if kind == "project":
        return project_root / "projects" / f"P-{clean_id}" / "project.md"

    elif kind == "epic":
        if parent_id is None:
            raise ValueError("Parent is required for epic objects")
        # Remove prefix if present to get clean parent ID
        parent_clean = parent_id.replace("P-", "") if parent_id.startswith("P-") else parent_id
        return (
            project_root / "projects" / f"P-{parent_clean}" / "epics" / f"E-{clean_id}" / "epic.md"
        )

    elif kind == "feature":
        if parent_id is None:
            raise ValueError("Parent is required for feature objects")
        # Remove prefix if present to get clean parent ID
        parent_clean = parent_id.replace("E-", "") if parent_id.startswith("E-") else parent_id
        # Find the parent epic's path to determine the project
        try:
            epic_path = id_to_path(project_root, "epic", parent_clean)
            # Extract project directory from epic path
            project_dir = epic_path.parts[epic_path.parts.index("projects") + 1]
            return (
                project_root
                / "projects"
                / project_dir
                / "epics"
                / f"E-{parent_clean}"
                / "features"
                / f"F-{clean_id}"
                / "feature.md"
            )
        except FileNotFoundError:
            raise ValueError(f"Parent epic '{parent_id}' not found")

    elif kind == "task":
        if parent_id is None:
            raise ValueError("Parent is required for task objects")
        # Remove prefix if present to get clean parent ID
        parent_clean = parent_id.replace("F-", "") if parent_id.startswith("F-") else parent_id
        # Find the parent feature's path to determine the project and epic
        try:
            feature_path = id_to_path(project_root, "feature", parent_clean)
            # Extract project and epic directories from feature path
            project_dir = feature_path.parts[feature_path.parts.index("projects") + 1]
            epic_dir = feature_path.parts[feature_path.parts.index("epics") + 1]

            # Determine task directory based on status
            task_dir = "tasks-done" if status == "done" else "tasks-open"

            # Determine filename based on status
            if status == "done":
                # Use timestamp prefix for done tasks
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}-T-{clean_id}.md"
            else:
                # Use simple format for open tasks
                filename = f"T-{clean_id}.md"

            return (
                project_root
                / "projects"
                / project_dir
                / "epics"
                / epic_dir
                / "features"
                / f"F-{parent_clean}"
                / task_dir
                / filename
            )
        except FileNotFoundError:
            raise ValueError(f"Parent feature '{parent_id}' not found")

    else:
        raise ValueError(f"Invalid kind: {kind}")


def path_to_id(file_path: Path) -> tuple[str, str]:
    """Convert a filesystem path to object kind and ID.

    This function performs the reverse mapping of id_to_path(), taking a filesystem
    path and returning the object kind and ID.

    Args:
        file_path: Path to the object file

    Returns:
        tuple[str, str]: (kind, obj_id) where kind is 'project', 'epic', 'feature', 'task'
                         and obj_id is the clean ID without prefix

    Raises:
        ValueError: If the path doesn't match expected Trellis MCP structure
        FileNotFoundError: If the file doesn't exist

    Example:
        >>> path = Path("planning/projects/P-user-auth/project.md")
        >>> path_to_id(path)
        ('project', 'user-auth')
        >>> path = Path("planning/projects/P-user-auth/epics/E-auth/features/F-login/tasks-open/T-implement-jwt.md")  # noqa: E501
        >>> path_to_id(path)
        ('task', 'implement-jwt')
    """
    # Validate input
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Convert to absolute path and get parts
    abs_path = file_path.resolve()
    parts = abs_path.parts

    # Find the filename to determine object type
    filename = abs_path.name

    # Determine kind based on filename and path structure
    if filename == "project.md":
        # Project: planning/projects/P-{id}/project.md
        kind = "project"
        # Find the project directory (P-{id})
        for part in parts:
            if part.startswith("P-"):
                project_id = part[2:]  # Remove P- prefix
                return kind, project_id
        raise ValueError(f"Could not find project ID in path: {file_path}")

    elif filename == "epic.md":
        # Epic: planning/projects/P-{parent}/epics/E-{id}/epic.md
        kind = "epic"
        # Find the epic directory (E-{id})
        for part in parts:
            if part.startswith("E-"):
                epic_id = part[2:]  # Remove E- prefix
                return kind, epic_id
        raise ValueError(f"Could not find epic ID in path: {file_path}")

    elif filename == "feature.md":
        # Feature: planning/projects/P-{parent}/epics/E-{parent}/features/F-{id}/feature.md
        kind = "feature"
        # Find the feature directory (F-{id})
        for part in parts:
            if part.startswith("F-"):
                feature_id = part[2:]  # Remove F- prefix
                return kind, feature_id
        raise ValueError(f"Could not find feature ID in path: {file_path}")

    elif filename.startswith("T-") and filename.endswith(".md"):
        # Task in tasks-open: .../tasks-open/T-{id}.md
        kind = "task"
        task_id = filename[2:-3]  # Remove T- prefix and .md suffix
        return kind, task_id

    elif filename.endswith(".md") and "-T-" in filename:
        # Task in tasks-done: .../tasks-done/{timestamp}-T-{id}.md
        kind = "task"
        # Find the T- prefix and extract ID
        t_index = filename.rfind("-T-")
        if t_index != -1:
            task_id = filename[t_index + 3 : -3]  # Remove -T- prefix and .md suffix
            return kind, task_id
        raise ValueError(f"Could not parse task ID from filename: {filename}")

    else:
        raise ValueError(f"Unrecognized file type: {filename}")
