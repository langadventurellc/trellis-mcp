"""Object dumper for Trellis MCP - converts model instances to markdown with YAML front-matter."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from trellis_mcp.fs_utils import ensure_parent_dirs
from trellis_mcp.object_parser import TrellisObjectModel
from trellis_mcp.path_resolver import id_to_path


def dump_object(model: TrellisObjectModel) -> str:
    """
    Convert a Trellis object model to markdown string with YAML front-matter.

    Args:
        model: A Trellis object model instance (Project, Epic, Feature, or Task)

    Returns:
        Markdown string with YAML front-matter and empty body

    Example:
        >>> from trellis_mcp.schema import TaskModel
        >>> from datetime import datetime
        >>> task = TaskModel(
        ...     kind="task",
        ...     id="T-001",
        ...     parent="F-001",
        ...     status="open",
        ...     title="Sample Task",
        ...     created=datetime.now(),
        ...     updated=datetime.now()
        ... )
        >>> markdown = dump_object(task)
        >>> print(markdown)
        ---
        kind: task
        id: T-001
        parent: F-001
        status: open
        title: Sample Task
        priority: normal
        prerequisites: []
        worktree: null
        created: 2025-01-01T00:00:00.000000
        updated: 2025-01-01T00:00:00.000000
        schema_version: '1.0'
        ---

    """
    return dump_object_with_body(model, "")


def dump_object_with_body(model: TrellisObjectModel, body: str) -> str:
    """
    Convert a Trellis object model to markdown string with YAML front-matter and custom body.

    Args:
        model: A Trellis object model instance (Project, Epic, Feature, or Task)
        body: The markdown body content to include after the front-matter

    Returns:
        Markdown string with YAML front-matter and provided body content

    Example:
        >>> from trellis_mcp.schema import TaskModel
        >>> from datetime import datetime
        >>> task = TaskModel(
        ...     kind="task",
        ...     id="T-001",
        ...     parent="F-001",
        ...     status="open",
        ...     title="Sample Task",
        ...     created=datetime.now(),
        ...     updated=datetime.now()
        ... )
        >>> body = "This is the task description."
        >>> markdown = dump_object_with_body(task, body)
        >>> print(markdown)
        ---
        kind: task
        id: T-001
        parent: F-001
        status: open
        title: Sample Task
        priority: normal
        prerequisites: []
        worktree: null
        created: 2025-01-01T00:00:00.000000
        updated: 2025-01-01T00:00:00.000000
        schema_version: '1.0'
        ---
        This is the task description.

    """
    # Create a copy for serialization (timestamp should be updated by caller if needed)
    model_dict = model.model_dump()

    # Convert to dictionary with proper serialization
    front_matter = _serialize_model_dict(model_dict)

    # Convert to YAML string
    yaml_content = yaml.safe_dump(
        front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )

    # Format as markdown with YAML front-matter and body
    markdown_content = f"---\n{yaml_content}---\n{body}"

    return markdown_content


def _serialize_model_dict(model_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Serialize model dictionary for YAML output.

    Handles datetime objects, enums, and None values properly.
    Excludes None values for optional fields that weren't explicitly set.

    Args:
        model_dict: Dictionary representation of the model

    Returns:
        Dictionary with properly serialized values for YAML
    """
    serialized = {}

    # Fields that should be excluded when None (optional fields)
    optional_fields = {"worktree"}

    for key, value in model_dict.items():
        if value is None and key in optional_fields:
            # Skip None values for optional fields to avoid cluttering YAML
            continue
        elif value is None:
            serialized[key] = None
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif hasattr(value, "value"):  # Enum objects
            # Use string representation for Priority enum to preserve "high"/"normal"/"low"
            # instead of numeric values
            from .models.common import Priority

            if isinstance(value, Priority):
                serialized[key] = str(value)
            else:
                serialized[key] = value.value
        else:
            serialized[key] = value

    return serialized


def write_object(model: TrellisObjectModel, project_root: Path) -> None:
    """
    Atomically write a Trellis object model to the filesystem.

    This function converts the model to markdown format using dump_object()
    and writes it to the appropriate location based on the object's kind and ID.
    If the file already exists, it preserves the existing body content while
    updating the front-matter. The write operation is atomic - it uses a temporary
    file in the same directory and then replaces the target file.

    Args:
        model: A Trellis object model instance (Project, Epic, Feature, or Task)
        project_root: Root directory of the planning structure

    Raises:
        ValueError: If the object kind or ID is invalid
        FileNotFoundError: If the target object cannot be found for existing objects
        OSError: If there are permission issues creating directories or files
        IOError: If there are issues writing to the filesystem

    Example:
        >>> from trellis_mcp.schema import TaskModel
        >>> from datetime import datetime
        >>> from pathlib import Path
        >>>
        >>> task = TaskModel(
        ...     kind="task",
        ...     id="T-001",
        ...     parent="F-001",
        ...     status="open",
        ...     title="Sample Task",
        ...     created=datetime.now(),
        ...     updated=datetime.now()
        ... )
        >>> project_root = Path("./planning")
        >>> write_object(task, project_root)
        # Task is now atomically written to the filesystem

    Note:
        This function will create parent directories as needed. The write operation
        is atomic - if the function fails, the target file will be left in its
        original state (if it existed) or will not be created (if it didn't exist).
        When updating existing files, the body content is preserved.
    """
    # Get the target file path based on the object's kind and ID
    target_path = id_to_path(project_root, model.kind.value, model.id)

    # Ensure parent directories exist
    ensure_parent_dirs(target_path)

    # Check if file already exists and preserve body content
    existing_body = ""
    if target_path.exists():
        try:
            from .io_utils import read_markdown

            _, existing_body = read_markdown(target_path)
        except Exception:
            # If we can't read the existing file, use empty body
            existing_body = ""

    # Get the markdown content with preserved body
    markdown_content = dump_object_with_body(model, existing_body)

    # Get the directory where the target file should be written
    target_dir = target_path.parent

    # Create a temporary file in the same directory for atomic operation
    # Using the same directory ensures the move operation is atomic
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=target_dir,
            prefix=f".{target_path.name}.",
            suffix=".tmp",
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(markdown_content)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Ensure data is written to disk
            temp_file_path = temp_file.name

        # Atomically replace the target file
        os.replace(temp_file_path, target_path)

    except Exception as e:
        # Clean up the temporary file if it was created
        if temp_file is not None:
            temp_file_path = temp_file.name
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass  # File may already be gone
        raise e
