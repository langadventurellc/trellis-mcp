"""Filesystem utilities for Trellis MCP.

Provides utilities for filesystem operations required by the Trellis MCP server,
including directory creation, path handling, and object discovery.
"""

import shutil
from pathlib import Path

from ..types import VALID_KINDS


def ensure_parent_dirs(path: Path) -> None:
    """Ensure that all parent directories for the given path exist.

    Creates all intermediate directories in the path if they don't already exist.
    This is useful when creating new object files in the hierarchical Trellis MCP
    structure, ensuring that the parent directories exist before writing the file.

    Args:
        path: The target file path for which to ensure parent directories exist.
               This should be a pathlib.Path object pointing to a file (not a directory).

    Raises:
        TypeError: If path is not a pathlib.Path object
        OSError: If there are permission issues creating the directories

    Example:
        >>> target_file = Path("planning/projects/P-user-auth/epics/E-auth/epic.md")
        >>> ensure_parent_dirs(target_file)
        # Creates: planning/projects/P-user-auth/epics/E-auth/ (if they don't exist)

        >>> task_file = Path(
        ...     "planning/projects/P-web/epics/E-ui/features/F-login/tasks-open/T-impl.md"
        ... )
        >>> ensure_parent_dirs(task_file)
        # Creates all nested directories up to tasks-open/ (if they don't exist)

    Note:
        This function is safe to call repeatedly - it will not raise errors if the
        directories already exist (uses exist_ok=True).
    """
    # Validate input type
    if not isinstance(path, Path):
        raise TypeError(f"Expected pathlib.Path object, got {type(path)}")

    # Get the parent directory of the target file
    parent_dir = path.parent

    # Create all intermediate directories if they don't exist
    # parents=True creates intermediate directories as needed
    # exist_ok=True prevents errors if directories already exist
    parent_dir.mkdir(parents=True, exist_ok=True)


def find_object_path(kind: str, obj_id: str, project_root: Path) -> Path | None:
    """Find the filesystem path for an object with the given ID.

    This function performs a directory scan to locate an object of the specified
    kind and ID within the hierarchical Trellis MCP structure. This is the shared
    utility function used by both id_utils._id_exists() and path_resolver.id_to_path().

    Args:
        kind: The object kind ('project', 'epic', 'feature', or 'task')
        obj_id: The object ID (without prefix, e.g., 'user-auth' not 'P-user-auth')
        project_root: Root directory of the planning structure

    Returns:
        Path object pointing to the file if found, None if not found

    Raises:
        ValueError: If kind is not supported or obj_id is empty

    Example:
        >>> project_root = Path("./planning")
        >>> find_object_path("project", "user-auth", project_root)
        Path('planning/projects/P-user-auth/project.md')
        >>> find_object_path("task", "nonexistent", project_root)
        None

    Note:
        For tasks, this function checks both tasks-open and tasks-done directories,
        preferring tasks-open if the same ID exists in both locations.
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
        file_path = project_root / "projects" / f"P-{clean_id}" / "project.md"
        return file_path if file_path.exists() else None

    elif kind == "epic":
        # Scan all projects to find this epic
        projects_dir = project_root / "projects"
        if not projects_dir.exists():
            return None

        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                epic_file = project_dir / "epics" / f"E-{clean_id}" / "epic.md"
                if epic_file.exists():
                    return epic_file

        return None

    elif kind == "feature":
        # Scan all projects and epics to find this feature
        projects_dir = project_root / "projects"
        if not projects_dir.exists():
            return None

        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                epics_dir = project_dir / "epics"
                if epics_dir.exists():
                    for epic_dir in epics_dir.iterdir():
                        if epic_dir.is_dir():
                            feature_file = epic_dir / "features" / f"F-{clean_id}" / "feature.md"
                            if feature_file.exists():
                                return feature_file

        return None

    elif kind == "task":
        # First check for standalone tasks at the root level
        # Check tasks-open first (prefer open tasks)
        open_task = project_root / "tasks-open" / f"T-{clean_id}.md"
        if open_task.exists():
            return open_task

        # Check tasks-done (files have timestamp prefixes)
        done_dir = project_root / "tasks-done"
        if done_dir.exists():
            for done_file in done_dir.iterdir():
                if done_file.is_file() and done_file.name.endswith(f"-T-{clean_id}.md"):
                    return done_file

        # Then scan all projects, epics, and features to find hierarchical tasks
        projects_dir = project_root / "projects"
        if not projects_dir.exists():
            return None

        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                epics_dir = project_dir / "epics"
                if epics_dir.exists():
                    for epic_dir in epics_dir.iterdir():
                        if epic_dir.is_dir():
                            features_dir = epic_dir / "features"
                            if features_dir.exists():
                                for feature_dir in features_dir.iterdir():
                                    if feature_dir.is_dir():
                                        # Check tasks-open first (prefer open tasks)
                                        open_task = feature_dir / "tasks-open" / f"T-{clean_id}.md"
                                        if open_task.exists():
                                            return open_task

                                        # Check tasks-done (files have timestamp prefixes)
                                        done_dir = feature_dir / "tasks-done"
                                        if done_dir.exists():
                                            for done_file in done_dir.iterdir():
                                                if done_file.is_file() and done_file.name.endswith(
                                                    f"-T-{clean_id}.md"
                                                ):
                                                    return done_file

        return None

    # This should never be reached due to validation above
    raise ValueError(f"Unsupported kind: {kind}")


def recursive_delete(path: Path, dry_run: bool = False) -> list[Path]:
    """Recursively delete a directory or file with optional dry-run mode.

    Provides a safe way to recursively delete files and directories with a dry-run
    option to preview what would be deleted. Returns a list of paths that were
    deleted (or would be deleted in dry-run mode).

    Args:
        path: Path to the file or directory to delete
        dry_run: If True, don't actually delete anything, just return what would be deleted

    Returns:
        List of Path objects that were deleted (or would be deleted in dry-run mode).
        The paths are returned in the order they would be processed (children before parents).

    Raises:
        TypeError: If path is not a pathlib.Path object
        ValueError: If path is empty or contains invalid characters
        OSError: If there are permission issues accessing or deleting files (not in dry-run mode)
        FileNotFoundError: If the path doesn't exist

    Example:
        >>> # Dry-run mode - preview what would be deleted
        >>> target_dir = Path("planning/projects/P-old-project")
        >>> paths_to_delete = recursive_delete(target_dir, dry_run=True)
        >>> print(f"Would delete {len(paths_to_delete)} items")

        >>> # Actual deletion
        >>> deleted_paths = recursive_delete(target_dir, dry_run=False)
        >>> print(f"Deleted {len(deleted_paths)} items")

    Security Notes:
        - Validates input path to prevent directory traversal attacks
        - Only allows deletion of paths that exist and are accessible
        - Uses shutil.rmtree for safe directory removal
    """
    # Validate input type
    if not isinstance(path, Path):
        raise TypeError(f"Expected pathlib.Path object, got {type(path)}")

    # Convert to absolute path to prevent relative path issues
    abs_path = path.resolve()

    # Check if path exists
    if not abs_path.exists():
        raise FileNotFoundError(f"Path does not exist: {abs_path}")

    # Security check - ensure path is reasonable and doesn't contain dangerous patterns
    path_str = str(abs_path)
    if ".." in path_str or path_str.startswith("/") and len(path_str.split("/")) < 3:
        raise ValueError(f"Invalid or potentially dangerous path: {abs_path}")

    # Collect all paths that will be deleted
    paths_to_delete = []

    if abs_path.is_file():
        # Single file deletion
        paths_to_delete.append(abs_path)
        if not dry_run:
            abs_path.unlink()
    elif abs_path.is_dir():
        # Directory deletion - collect all paths first
        for root, dirs, files in abs_path.walk():
            # Add files first (depth-first traversal)
            for file in files:
                file_path = root / file
                paths_to_delete.append(file_path)

            # Add directory itself
            paths_to_delete.append(root)

        # Sort by depth (deepest first) to ensure proper deletion order
        paths_to_delete.sort(key=lambda p: (len(p.parts), str(p)), reverse=True)

        if not dry_run:
            # Use shutil.rmtree for safe recursive directory removal
            shutil.rmtree(abs_path)
    else:
        raise ValueError(f"Path is neither a file nor directory: {abs_path}")

    return paths_to_delete
