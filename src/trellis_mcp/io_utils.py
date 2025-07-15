"""I/O utilities for Trellis MCP markdown file operations.

This module provides utilities for reading and writing markdown files with YAML front-matter.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

from .markdown_loader import load_markdown


def read_markdown(path: str | Path) -> Tuple[Dict[str, Any], str]:
    """Read markdown file and parse YAML front-matter.

    Parses a markdown file with YAML front-matter delimited by '---' lines.
    The front-matter must be at the beginning of the file and is parsed using
    yaml.safe_load for security.

    Args:
        path: Path to the markdown file to read.

    Returns:
        A tuple containing:
        - yaml_dict: Dictionary of parsed YAML front-matter
        - body_str: The remaining markdown content after front-matter

    Raises:
        FileNotFoundError: If the specified file does not exist.
        OSError: If the file cannot be read.
        yaml.YAMLError: If the YAML front-matter is invalid.
        ValueError: If the front-matter format is invalid.

    Example:
        >>> # For a file with content:
        >>> # ---
        >>> # title: My Task
        >>> # status: open
        >>> # ---
        >>> # This is the task description.
        >>> yaml_dict, body_str = read_markdown('task.md')
        >>> yaml_dict['title']
        'My Task'
        >>> body_str.strip()
        'This is the task description.'
    """
    return load_markdown(path)


def write_markdown(path: str | Path, yaml_dict: Dict[str, Any], body_str: str) -> None:
    """Write markdown file with YAML front-matter.

    Creates a markdown file with YAML front-matter delimited by '---' lines.
    The front-matter is serialized using yaml.safe_dump with pretty-printing.
    The write operation is atomic - uses a temporary file and atomic move.

    Args:
        path: Path to the markdown file to write.
        yaml_dict: Dictionary to serialize as YAML front-matter.
        body_str: The markdown content to write after front-matter.

    Raises:
        OSError: If there are permission issues creating directories or files.
        IOError: If there are issues writing to the filesystem.

    Example:
        >>> yaml_dict = {
        ...     'title': 'My Task',
        ...     'status': 'open',
        ...     'priority': 'high'
        ... }
        >>> body_str = 'This is the task description.'
        >>> write_markdown('task.md', yaml_dict, body_str)
        >>> # Creates file with content:
        >>> # ---
        >>> # title: My Task
        >>> # status: open
        >>> # priority: high
        >>> # ---
        >>> # This is the task description.
    """
    target_path = Path(path)

    # Serialize YAML front-matter
    front_matter = _serialize_yaml_dict(yaml_dict)
    yaml_content = yaml.safe_dump(
        front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )

    # Format as markdown with YAML front-matter
    markdown_content = f"---\n{yaml_content}---\n{body_str}"

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Get the directory where the target file should be written
    target_dir = target_path.parent

    # Create a temporary file in the same directory for atomic operation
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


def _serialize_yaml_dict(yaml_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize dictionary for YAML output.

    Handles datetime objects, enums, and None values properly.

    Args:
        yaml_dict: Dictionary to serialize for YAML

    Returns:
        Dictionary with properly serialized values for YAML
    """
    from .models.common import Priority

    serialized = {}

    for key, value in yaml_dict.items():
        if value is None:
            serialized[key] = None
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, Priority):
            # Special handling for Priority enum to get string representation
            serialized[key] = str(value)
        elif hasattr(value, "value"):  # Other enum objects
            serialized[key] = value.value
        else:
            serialized[key] = value

    return serialized
