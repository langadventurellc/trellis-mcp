"""Path resolution utilities for Trellis MCP objects.

Provides functions for converting object IDs to filesystem paths within the
hierarchical project structure (Projects → Epics → Features → Tasks).
"""

from pathlib import Path

from .types import VALID_KINDS
from .utils.fs_utils import find_object_path


def resolve_project_roots(project_root: str | Path) -> tuple[Path, Path]:
    """Resolve scanning root and path resolution root from project root.

    Handles two different project structure scenarios:
    1. Project root contains planning directory: projectRoot/planning/projects/...
    2. Project root IS the planning directory: projectRoot/projects/...

    This centralizes the path resolution logic used by both CLI and server components.

    Args:
        project_root: Root directory path (either containing planning/ or being the planning dir)

    Returns:
        tuple[Path, Path]: (scanning_root, path_resolution_root) where:
        - scanning_root: Root directory for scanning tasks (used by scanner.py)
        - path_resolution_root: Root directory for resolving task IDs to paths (used by id_to_path)

    Example:
        >>> # Case 1: project_root contains planning directory
        >>> resolve_project_roots("/project/root")
        (Path('/project/root'), Path('/project/root/planning'))

        >>> # Case 2: project_root IS the planning directory
        >>> resolve_project_roots("/project/root/planning")
        (Path('/project/root'), Path('/project/root/planning'))
    """
    project_root_path = Path(project_root)

    if (project_root_path / "planning").exists():
        # projectRoot contains planning directory
        scanning_root = project_root_path
        path_resolution_root = project_root_path / "planning"
    else:
        # projectRoot IS the planning directory
        scanning_root = project_root_path.parent
        path_resolution_root = project_root_path

    return scanning_root, path_resolution_root


def id_to_path(project_root: Path, kind: str, obj_id: str) -> Path:
    """Convert an object ID to its filesystem path within the project structure.

    Maps Trellis MCP object IDs to their corresponding filesystem paths based on
    the hierarchical structure: Projects → Epics → Features → Tasks.

    This function uses the shared find_object_path utility to locate objects
    within the directory structure. For tasks, it supports both hierarchy-based
    and standalone task discovery.

    Args:
        project_root: Root directory of the planning structure (e.g., ./planning)
        kind: The object kind ('project', 'epic', 'feature', or 'task')
        obj_id: The object ID (without prefix, e.g., 'user-auth' not 'P-user-auth')

    Returns:
        Path object pointing to the appropriate file:
        - project: planning/projects/P-{id}/project.md
        - epic: planning/projects/P-{parent}/epics/E-{id}/epic.md
        - feature: planning/projects/P-{parent}/epics/E-{parent}/features/F-{id}/feature.md
        - task (hierarchy): planning/projects/P-{parent}/epics/E-{parent}/features/
                F-{parent}/tasks-open/T-{id}.md
                or planning/projects/P-{parent}/epics/E-{parent}/features/
                F-{parent}/tasks-done/{timestamp}-T-{id}.md
        - task (standalone): planning/tasks-open/T-{id}.md
                or planning/tasks-done/{timestamp}-T-{id}.md

    Raises:
        ValueError: If kind is not supported or obj_id is empty
        FileNotFoundError: If the object with the given ID cannot be found

    Example:
        >>> project_root = Path("./planning")
        >>> id_to_path(project_root, "project", "user-auth")
        Path('planning/projects/P-user-auth/project.md')
        >>> id_to_path(project_root, "task", "implement-jwt")
        Path('planning/projects/P-user-auth/epics/E-auth/features/F-login/tasks-open/T-implement-jwt.md')
        >>> id_to_path(project_root, "task", "standalone-task")
        Path('planning/tasks-open/T-standalone-task.md')

    Note:
        For tasks, this function searches standalone task directories first (tasks-open
        and tasks-done at the root level), then falls back to hierarchical search if
        not found. This ensures standalone tasks take priority over hierarchy tasks
        with the same ID.
    """
    # Validate inputs for security and data integrity
    if not kind or kind not in VALID_KINDS:
        raise ValueError(f"Invalid kind '{kind}'. Must be one of: {VALID_KINDS}")

    if not obj_id or not obj_id.strip():
        raise ValueError("Object ID cannot be empty")

    # For tasks, validate input parameters to prevent path traversal attacks
    if kind == "task":
        from .validation.field_validation import validate_standalone_task_path_parameters
        from .validation.security import validate_standalone_task_path_security

        validation_errors = validate_standalone_task_path_parameters(obj_id)
        if validation_errors:
            # Use the first error for the exception message
            raise ValueError(f"Invalid task ID: {validation_errors[0]}")

        # Enhanced security validation for standalone task paths
        security_errors = validate_standalone_task_path_security(obj_id, str(project_root))
        if security_errors:
            # Use the first error for the exception message
            raise ValueError(f"Security validation failed: {security_errors[0]}")

    # Use the shared utility to find the object path
    result_path = find_object_path(kind, obj_id, project_root)

    # Additional security validation for the resolved path
    if kind == "task" and result_path:
        from .validation.security import validate_path_boundaries

        boundary_errors = validate_path_boundaries(str(result_path), str(project_root))
        if boundary_errors:
            # Use the first error for the exception message
            raise ValueError(f"Path boundary validation failed: {boundary_errors[0]}")

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
        parent_id: Parent object ID (required for epics, features; optional for tasks to
            support standalone tasks; use empty string or None for no parent)
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

    # For tasks, validate input parameters to prevent path traversal attacks
    if kind == "task":
        from .validation.field_validation import validate_standalone_task_path_parameters
        from .validation.security import validate_standalone_task_path_security

        validation_errors = validate_standalone_task_path_parameters(obj_id, status)
        if validation_errors:
            # Use the first error for the exception message with consistent format
            raise ValueError(f"Invalid task ID: {validation_errors[0]}")

        # Enhanced security validation for standalone task paths
        security_errors = validate_standalone_task_path_security(obj_id, str(project_root))
        if security_errors:
            # Use the first error for the exception message
            raise ValueError(f"Security validation failed: {security_errors[0]}")

    # Clean the ID (remove any existing prefix if present)
    clean_id = obj_id.strip()
    if clean_id.startswith(("P-", "E-", "F-", "T-")):
        clean_id = clean_id[2:]

    # Get the correct path resolution root
    _, path_resolution_root = resolve_project_roots(project_root)

    # Build path based on kind
    if kind == "project":
        return path_resolution_root / "projects" / f"P-{clean_id}" / "project.md"

    elif kind == "epic":
        if parent_id is None or not parent_id.strip():
            raise ValueError("Parent is required for epic objects")
        # Remove prefix if present to get clean parent ID
        parent_clean = parent_id.replace("P-", "") if parent_id.startswith("P-") else parent_id
        return (
            path_resolution_root
            / "projects"
            / f"P-{parent_clean}"
            / "epics"
            / f"E-{clean_id}"
            / "epic.md"
        )

    elif kind == "feature":
        if parent_id is None or not parent_id.strip():
            raise ValueError("Parent is required for feature objects")
        # Remove prefix if present to get clean parent ID
        parent_clean = parent_id.replace("E-", "") if parent_id.startswith("E-") else parent_id
        # Find the parent epic's path to determine the project
        try:
            epic_path = id_to_path(project_root, "epic", parent_clean)
            # Extract project directory from epic path
            project_dir = epic_path.parts[epic_path.parts.index("projects") + 1]
            return (
                path_resolution_root
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
        if parent_id is None or not parent_id.strip():
            # Standalone task: place in root tasks directory
            # These are tasks that exist independently of any feature hierarchy
            # and are stored directly under planning/tasks-open or planning/tasks-done
            task_dir = "tasks-done" if status == "done" else "tasks-open"

            # Determine filename based on status
            if status == "done":
                # For completed tasks, prefix with timestamp for chronological ordering
                # Format: YYYYMMDD_HHMMSS-T-{task-id}.md
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}-T-{clean_id}.md"
            else:
                # For open tasks, use simple format for easy identification
                # Format: T-{task-id}.md
                filename = f"T-{clean_id}.md"

            # Return path: planning/tasks-{open|done}/[timestamp-]T-{task-id}.md
            return path_resolution_root / task_dir / filename
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
                path_resolution_root
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
    path and returning the object kind and ID. Supports both hierarchy-based and
    standalone task structures.

    Args:
        file_path: Path to the object file

    Returns:
        tuple[str, str]: (kind, obj_id) where kind is 'project', 'epic', 'feature', 'task'
                         and obj_id is the clean ID without prefix

    Raises:
        ValueError: If the path doesn't match expected Trellis MCP structure or contains
                   invalid characters in task ID
        FileNotFoundError: If the file doesn't exist

    Example:
        >>> path = Path("planning/projects/P-user-auth/project.md")
        >>> path_to_id(path)
        ('project', 'user-auth')
        >>> path = Path("planning/projects/P-user-auth/epics/E-auth/features/F-login/tasks-open/T-implement-jwt.md")  # noqa: E501
        >>> path_to_id(path)
        ('task', 'implement-jwt')
        >>> path = Path("planning/tasks-open/T-standalone-task.md")  # noqa: E501
        >>> path_to_id(path)
        ('task', 'standalone-task')
        >>> path = Path("planning/tasks-done/20250718_143000-T-completed-task.md")  # noqa: E501
        >>> path_to_id(path)
        ('task', 'completed-task')
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
        # Works for both standalone and hierarchy-based tasks
        kind = "task"
        task_id = filename[2:-3]  # Remove T- prefix and .md suffix

        # Validate task ID format for security
        if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
            raise ValueError(f"Invalid task ID format: {task_id}")

        return kind, task_id

    elif filename.endswith(".md") and "-T-" in filename:
        # Task in tasks-done: .../tasks-done/{timestamp}-T-{id}.md
        # Works for both standalone and hierarchy-based tasks
        kind = "task"
        # Find the T- prefix and extract ID
        t_index = filename.rfind("-T-")
        if t_index != -1:
            task_id = filename[t_index + 3 : -3]  # Remove -T- prefix and .md suffix

            # Validate task ID format for security
            if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
                raise ValueError(f"Invalid task ID format: {task_id}")

            return kind, task_id
        raise ValueError(f"Could not parse task ID from filename: {filename}")

    else:
        raise ValueError(f"Unrecognized file type: {filename}")


def children_of(kind: str, obj_id: str, project_root: Path) -> list[Path]:
    """Find all descendant paths for a given object in the hierarchical structure.

    Returns a list of filesystem paths for all descendant objects (children,
    grandchildren, etc.) of the specified object. The hierarchical relationships
    are: Project → Epic → Feature → Task.

    Args:
        kind: The object kind ('project', 'epic', 'feature', or 'task')
        obj_id: The object ID (without prefix, e.g., 'user-auth' not 'P-user-auth')
        project_root: Root directory of the planning structure

    Returns:
        List of Path objects pointing to descendant files. For:
        - project: All epics, features, and tasks under the project
        - epic: All features and tasks under the epic
        - feature: All tasks under the feature
        - task: Empty list (tasks have no children)

    Raises:
        ValueError: If kind is not supported or obj_id is empty
        FileNotFoundError: If the parent object cannot be found

    Example:
        >>> project_root = Path("./planning")
        >>> children_of("project", "user-auth", project_root)
        [Path('planning/projects/P-user-auth/epics/E-authentication/epic.md'),
         Path('planning/projects/P-user-auth/epics/E-authentication/features/F-login/feature.md'),
         ...]
        >>> children_of("task", "implement-jwt", project_root)
        []  # Tasks have no children
    """
    # Validate inputs
    if not kind or kind not in VALID_KINDS:
        raise ValueError(f"Invalid kind '{kind}'. Must be one of: {VALID_KINDS}")

    if not obj_id or not obj_id.strip():
        raise ValueError("Object ID cannot be empty")

    # Validate input parameters to prevent path traversal attacks for all object types
    from .validation.field_validation import _validate_task_id_security

    # Use task ID security validation for all object types (same security concerns)
    security_errors = _validate_task_id_security(obj_id.strip())
    if security_errors:
        # Use the first error for the exception message
        raise ValueError(f"Invalid {kind} ID: {security_errors[0]}")

    # For tasks, additional validation
    if kind == "task":
        from .validation.field_validation import validate_standalone_task_path_parameters
        from .validation.security import validate_standalone_task_path_security

        validation_errors = validate_standalone_task_path_parameters(obj_id)
        if validation_errors:
            # Use the first error for the exception message
            raise ValueError(f"Invalid task ID: {validation_errors[0]}")

        # Enhanced security validation for standalone task paths
        task_security_errors = validate_standalone_task_path_security(obj_id, str(project_root))
        if task_security_errors:
            # Use the first error for the exception message
            raise ValueError(f"Security validation failed: {task_security_errors[0]}")

    # Clean the ID (remove any existing prefix if present)
    clean_id = obj_id.strip()
    if clean_id.startswith(("P-", "E-", "F-", "T-")):
        clean_id = clean_id[2:]

    # Tasks have no children
    if kind == "task":
        return []

    # Find the parent object's path to locate its directory
    parent_path = find_object_path(kind, clean_id, project_root)
    if parent_path is None:
        if kind == "project":
            raise FileNotFoundError(f"Project with ID '{clean_id}' not found")
        elif kind == "epic":
            raise FileNotFoundError(f"Epic with ID '{clean_id}' not found")
        elif kind == "feature":
            raise FileNotFoundError(f"Feature with ID '{clean_id}' not found")

    # At this point, parent_path is guaranteed to be a Path object
    # because we would have raised an exception if it was None
    assert parent_path is not None, "parent_path should not be None at this point"

    # Get the parent directory containing the children
    parent_dir = parent_path.parent
    descendant_paths = []

    # Collect all descendant paths based on the parent kind
    if kind == "project":
        # For projects, find all epics, features, and tasks
        epics_dir = parent_dir / "epics"
        if epics_dir.exists():
            for epic_dir in epics_dir.iterdir():
                if epic_dir.is_dir() and epic_dir.name.startswith("E-"):
                    # Add epic file
                    epic_file = epic_dir / "epic.md"
                    if epic_file.exists():
                        descendant_paths.append(epic_file)

                    # Add features and tasks under this epic
                    features_dir = epic_dir / "features"
                    if features_dir.exists():
                        for feature_dir in features_dir.iterdir():
                            if feature_dir.is_dir() and feature_dir.name.startswith("F-"):
                                # Add feature file
                                feature_file = feature_dir / "feature.md"
                                if feature_file.exists():
                                    descendant_paths.append(feature_file)

                                # Add tasks under this feature
                                _add_tasks_from_feature(feature_dir, descendant_paths)

    elif kind == "epic":
        # For epics, find all features and tasks
        features_dir = parent_dir / "features"
        if features_dir.exists():
            for feature_dir in features_dir.iterdir():
                if feature_dir.is_dir() and feature_dir.name.startswith("F-"):
                    # Add feature file
                    feature_file = feature_dir / "feature.md"
                    if feature_file.exists():
                        descendant_paths.append(feature_file)

                    # Add tasks under this feature
                    _add_tasks_from_feature(feature_dir, descendant_paths)

    elif kind == "feature":
        # For features, find all tasks
        _add_tasks_from_feature(parent_dir, descendant_paths)

    # Sort paths for consistent ordering
    descendant_paths.sort(key=lambda p: str(p))
    return descendant_paths


def discover_immediate_children(kind: str, obj_id: str, project_root: Path) -> list[dict[str, str]]:
    """Find immediate child objects with metadata.

    Discovers only immediate child objects (not recursive descendants) for a given
    parent object and returns their metadata. Unlike children_of(), this function
    returns rich metadata about each child rather than just file paths.

    Args:
        kind: The parent object kind ('project', 'epic', 'feature', or 'task')
        obj_id: The parent object ID (without prefix, e.g., 'user-auth' not 'P-user-auth')
        project_root: Root directory of the planning structure

    Returns:
        List of dictionaries with structure:
        {
            "id": str,        # Clean child ID (without prefix)
            "title": str,     # Child object title
            "status": str,    # Child object status
            "kind": str,      # Child object type
            "created": str,   # ISO timestamp
            "file_path": str  # Path to child file
        }

        For parent-child relationships:
        - project → epics: Scan {project_dir}/epics/E-*/epic.md files only
        - epic → features: Scan {epic_dir}/features/F-*/feature.md files only
        - feature → tasks: Scan {feature_dir}/tasks-open/T-*.md and
                         {feature_dir}/tasks-done/*-T-*.md files only
        - task → []: Tasks have no children, return empty list

    Raises:
        ValueError: If kind is not supported, obj_id is empty, or security validation fails
        FileNotFoundError: If the parent object cannot be found

    Example:
        >>> project_root = Path("./planning")
        >>> discover_immediate_children("project", "user-auth", project_root)
        [{"id": "authentication", "title": "User Authentication", "status": "in-progress",
          "kind": "epic", "created": "2025-01-01T10:00:00Z", "file_path": "..."}]
        >>> discover_immediate_children("task", "implement-jwt", project_root)
        []  # Tasks have no children
    """
    # Validate inputs using same patterns as children_of()
    if not kind or kind not in VALID_KINDS:
        raise ValueError(f"Invalid kind '{kind}'. Must be one of: {VALID_KINDS}")

    if not obj_id or not obj_id.strip():
        raise ValueError("Object ID cannot be empty")

    # Validate input parameters to prevent path traversal attacks for all object types
    from .validation.field_validation import _validate_task_id_security

    # Use task ID security validation for all object types (same security concerns)
    security_errors = _validate_task_id_security(obj_id.strip())
    if security_errors:
        # Use the first error for the exception message
        raise ValueError(f"Invalid {kind} ID: {security_errors[0]}")

    # For tasks, additional validation
    if kind == "task":
        from .validation.field_validation import validate_standalone_task_path_parameters
        from .validation.security import validate_standalone_task_path_security

        validation_errors = validate_standalone_task_path_parameters(obj_id)
        if validation_errors:
            # Use the first error for the exception message
            raise ValueError(f"Invalid task ID: {validation_errors[0]}")

        # Enhanced security validation for standalone task paths
        task_security_errors = validate_standalone_task_path_security(obj_id, str(project_root))
        if task_security_errors:
            # Use the first error for the exception message
            raise ValueError(f"Security validation failed: {task_security_errors[0]}")

    # Clean the ID (remove any existing prefix if present)
    clean_id = obj_id.strip()
    if clean_id.startswith(("P-", "E-", "F-", "T-")):
        clean_id = clean_id[2:]

    # Tasks have no children
    if kind == "task":
        return []

    # Find the parent object's path to locate its directory
    parent_path = find_object_path(kind, clean_id, project_root)
    if parent_path is None:
        if kind == "project":
            raise FileNotFoundError(f"Project with ID '{clean_id}' not found")
        elif kind == "epic":
            raise FileNotFoundError(f"Epic with ID '{clean_id}' not found")
        elif kind == "feature":
            raise FileNotFoundError(f"Feature with ID '{clean_id}' not found")

    # At this point, parent_path is guaranteed to be a Path object
    assert parent_path is not None, "parent_path should not be None at this point"

    # Check cache before file system scanning
    from .children.cache import get_children_cache

    cache = get_children_cache()
    cached_children = cache.get_children(parent_path)
    if cached_children is not None:
        return cached_children

    # Cache miss - proceed with file system scan
    # Get the parent directory containing the children
    parent_dir = parent_path.parent
    children_metadata = []

    # Import markdown loader for metadata parsing
    from .markdown_loader import load_markdown

    # Collect immediate children based on the parent kind
    if kind == "project":
        # For projects, find only immediate epics
        epics_dir = parent_dir / "epics"
        if epics_dir.exists():
            for epic_dir in epics_dir.iterdir():
                if epic_dir.is_dir() and epic_dir.name.startswith("E-"):
                    epic_file = epic_dir / "epic.md"
                    if epic_file.exists():
                        child_metadata = _extract_child_metadata(epic_file, "epic", load_markdown)
                        if child_metadata:
                            children_metadata.append(child_metadata)

    elif kind == "epic":
        # For epics, find only immediate features
        features_dir = parent_dir / "features"
        if features_dir.exists():
            for feature_dir in features_dir.iterdir():
                if feature_dir.is_dir() and feature_dir.name.startswith("F-"):
                    feature_file = feature_dir / "feature.md"
                    if feature_file.exists():
                        child_metadata = _extract_child_metadata(
                            feature_file, "feature", load_markdown
                        )
                        if child_metadata:
                            children_metadata.append(child_metadata)

    elif kind == "feature":
        # For features, find only immediate tasks
        _add_immediate_tasks_metadata(parent_dir, children_metadata, load_markdown)

    # Sort results by creation date (oldest first) for consistent ordering
    children_metadata.sort(key=lambda child: child.get("created", ""))

    # Store results in cache after successful discovery
    try:
        cache.set_children(parent_path, children_metadata)
    except Exception as e:
        # Cache storage failure should not break children discovery
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to cache children for {parent_path}: {e}")

    return children_metadata


def _extract_child_metadata(
    child_path: Path, child_kind: str, load_markdown_func
) -> dict[str, str] | None:
    """Extract metadata from a child object file.

    Args:
        child_path: Path to the child object file
        child_kind: Kind of the child object ('epic', 'feature', 'task')
        load_markdown_func: Function to load markdown with YAML front-matter

    Returns:
        Dictionary with child metadata or None if extraction fails
    """
    try:
        yaml_data, _ = load_markdown_func(child_path)

        # Extract clean ID (remove prefix if present)
        raw_id = yaml_data.get("id", "")
        if raw_id.startswith(("P-", "E-", "F-", "T-")):
            clean_id = raw_id[2:]
        else:
            clean_id = raw_id

        return {
            "id": clean_id,
            "title": yaml_data.get("title", ""),
            "status": yaml_data.get("status", ""),
            "kind": child_kind,
            "created": yaml_data.get("created", ""),
            "file_path": str(child_path),
        }
    except Exception:
        # Handle missing fields gracefully with defaults - don't let parsing errors stop discovery
        return None


def _add_immediate_tasks_metadata(
    feature_dir: Path, children_metadata: list[dict[str, str]], load_markdown_func
) -> None:
    """Add immediate task metadata from a feature directory to the children list.

    Args:
        feature_dir: Path to the feature directory
        children_metadata: List to append task metadata to
        load_markdown_func: Function to load markdown with YAML front-matter
    """
    # Check tasks-open directory
    tasks_open_dir = feature_dir / "tasks-open"
    if tasks_open_dir.exists():
        for task_file in tasks_open_dir.iterdir():
            if (
                task_file.is_file()
                and task_file.name.startswith("T-")
                and task_file.name.endswith(".md")
            ):
                task_metadata = _extract_child_metadata(task_file, "task", load_markdown_func)
                if task_metadata:
                    children_metadata.append(task_metadata)

    # Check tasks-done directory
    tasks_done_dir = feature_dir / "tasks-done"
    if tasks_done_dir.exists():
        for task_file in tasks_done_dir.iterdir():
            if task_file.is_file() and task_file.name.endswith(".md") and "-T-" in task_file.name:
                task_metadata = _extract_child_metadata(task_file, "task", load_markdown_func)
                if task_metadata:
                    children_metadata.append(task_metadata)


def _add_tasks_from_feature(feature_dir: Path, descendant_paths: list[Path]) -> None:
    """Helper function to add all tasks from a feature directory to the descendant paths list.

    Args:
        feature_dir: Path to the feature directory
        descendant_paths: List to append task paths to
    """
    # Check tasks-open directory
    tasks_open_dir = feature_dir / "tasks-open"
    if tasks_open_dir.exists():
        for task_file in tasks_open_dir.iterdir():
            if (
                task_file.is_file()
                and task_file.name.startswith("T-")
                and task_file.name.endswith(".md")
            ):
                descendant_paths.append(task_file)

    # Check tasks-done directory
    tasks_done_dir = feature_dir / "tasks-done"
    if tasks_done_dir.exists():
        for task_file in tasks_done_dir.iterdir():
            if task_file.is_file() and task_file.name.endswith(".md") and "-T-" in task_file.name:
                descendant_paths.append(task_file)


def construct_standalone_task_path(
    obj_id: str, status: str | None, project_root: str | Path
) -> Path:
    """Construct the filesystem path for a standalone task.

    Creates the complete filesystem path for a standalone task based on its ID and status.
    This is a dedicated helper function for standalone task path construction that follows
    the existing patterns in resolve_path_for_new_object().

    Args:
        obj_id: The task ID (without T- prefix, e.g., 'implement-auth')
        status: The task status ('open', 'done', None defaults to 'open')
        project_root: Root directory of the project (can be project root or planning root)

    Returns:
        Path object pointing to the standalone task file:
        - For open tasks: planning/tasks-open/T-{obj_id}.md
        - For done tasks: planning/tasks-done/{timestamp}-T-{obj_id}.md

    Raises:
        ValueError: If obj_id is empty or contains invalid characters
        ValueError: If validation fails (input validation or security checks)

    Example:
        >>> construct_standalone_task_path("implement-auth", "open", "./planning")
        Path('planning/tasks-open/T-implement-auth.md')
        >>> construct_standalone_task_path("implement-auth", "done", "./planning")
        Path('planning/tasks-done/20250718_143000-T-implement-auth.md')

    Note:
        This function applies the same validation and security checks as the main
        path resolution functions to ensure consistent behavior and security.
    """
    # Validate inputs
    if not obj_id or not obj_id.strip():
        raise ValueError("Task ID cannot be empty")

    # Validate input parameters to prevent path traversal attacks
    from .validation.field_validation import validate_standalone_task_path_parameters
    from .validation.security import validate_standalone_task_path_security

    validation_errors = validate_standalone_task_path_parameters(obj_id, status)
    if validation_errors:
        raise ValueError(f"Invalid task ID: {validation_errors[0]}")

    # Enhanced security validation for standalone task paths
    security_errors = validate_standalone_task_path_security(obj_id, str(project_root))
    if security_errors:
        raise ValueError(f"Security validation failed: {security_errors[0]}")

    # Clean the ID (remove any existing prefix if present)
    clean_id = obj_id.strip()
    if clean_id.startswith("T-"):
        clean_id = clean_id[2:]

    # Get the correct path resolution root
    _, path_resolution_root = resolve_project_roots(project_root)

    # Determine task directory and filename based on status
    task_dir = "tasks-done" if status == "done" else "tasks-open"
    filename = get_standalone_task_filename(clean_id, status)

    # Return the complete path
    return path_resolution_root / task_dir / filename


def get_standalone_task_filename(obj_id: str, status: str | None) -> str:
    """Generate the filename for a standalone task based on its ID and status.

    Creates the appropriate filename for a standalone task file following the
    existing naming conventions used in the codebase.

    Args:
        obj_id: The task ID (without T- prefix, e.g., 'implement-auth')
        status: The task status ('open', 'done', None defaults to 'open')

    Returns:
        String filename for the task:
        - For open tasks: T-{obj_id}.md
        - For done tasks: {timestamp}-T-{obj_id}.md

    Example:
        >>> get_standalone_task_filename("implement-auth", "open")
        'T-implement-auth.md'
        >>> get_standalone_task_filename("implement-auth", "done")
        '20250718_143000-T-implement-auth.md'

    Note:
        This function encapsulates the filename generation logic that was previously
        embedded in resolve_path_for_new_object() to make it reusable and testable.
    """
    # Clean the ID (remove any existing prefix if present)
    clean_id = obj_id.strip()
    if clean_id.startswith("T-"):
        clean_id = clean_id[2:]

    # Generate filename based on status
    if status == "done":
        # For completed tasks, prefix with timestamp for chronological ordering
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}-T-{clean_id}.md"
    else:
        # For open tasks, use simple format for easy identification
        return f"T-{clean_id}.md"


def ensure_standalone_task_directory(project_root: str | Path, status: str | None) -> Path:
    """Ensure the standalone task directory exists and return its path.

    Creates the appropriate directory for standalone tasks if it doesn't exist.
    Uses the existing fs_utils.ensure_parent_dirs() for safe directory creation.

    Args:
        project_root: Root directory of the project (can be project root or planning root)
        status: The task status ('open', 'done', None defaults to 'open')

    Returns:
        Path object pointing to the standalone task directory:
        - For open tasks: planning/tasks-open/
        - For done tasks: planning/tasks-done/

    Raises:
        OSError: If directory creation fails due to permissions or other issues

    Example:
        >>> ensure_standalone_task_directory("./planning", "open")
        Path('planning/tasks-open')
        >>> ensure_standalone_task_directory("./planning", "done")
        Path('planning/tasks-done')

    Note:
        This function uses the existing fs_utils.ensure_parent_dirs() utility
        to maintain consistency with the rest of the codebase.
    """
    # Get the correct path resolution root
    _, path_resolution_root = resolve_project_roots(project_root)

    # Determine task directory based on status
    task_dir_name = "tasks-done" if status == "done" else "tasks-open"
    task_dir = path_resolution_root / task_dir_name

    # Use existing utility to ensure directory exists
    from .utils.fs_utils import ensure_parent_dirs

    ensure_parent_dirs(task_dir / "dummy.md")  # Create the directory structure
    return task_dir
