"""Markdown loader for parsing front-matter from markdown files.

Provides functionality to load markdown files with YAML front-matter and
separate the front-matter dictionary from the markdown body content.
"""

import re
from pathlib import Path
from typing import Any

import yaml


def load_markdown(path: str | Path) -> tuple[dict[str, Any], str]:
    """Load markdown file and parse YAML front-matter.

    Parses a markdown file with YAML front-matter delimited by '---' lines.
    The front-matter must be at the beginning of the file and is parsed using
    yaml.safe_load for security.

    Args:
        path: Path to the markdown file to load.

    Returns:
        A tuple containing:
        - frontmatter_dict: Dictionary of parsed YAML front-matter
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
        >>> frontmatter, body = load_markdown('task.md')
        >>> frontmatter['title']
        'My Task'
        >>> body.strip()
        'This is the task description.'
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        raise OSError(f"Cannot read markdown file {file_path}: {e}") from e

    # Check if file starts with front-matter delimiter
    if not content.startswith("---"):
        # No front-matter, return empty dict and full content as body
        return {}, content

    # Find the closing front-matter delimiter
    # Use regex to find the second occurrence of '---' on its own line
    front_matter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(front_matter_pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        raise ValueError(
            f"Invalid front-matter format in {file_path}: "
            "Front-matter must be delimited by '---' lines"
        )

    # Extract front-matter YAML and body content
    yaml_content = match.group(1)
    body_content = content[match.end() :]

    # Parse YAML front-matter
    try:
        frontmatter_dict = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in front-matter of {file_path}: {e}") from e

    # Ensure we return a dictionary
    if not isinstance(frontmatter_dict, dict):
        raise ValueError(
            f"Front-matter must be a YAML object/dictionary in {file_path}, "
            f"got {type(frontmatter_dict).__name__}"
        )

    return frontmatter_dict, body_content
