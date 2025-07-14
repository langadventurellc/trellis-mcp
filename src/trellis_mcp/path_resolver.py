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
