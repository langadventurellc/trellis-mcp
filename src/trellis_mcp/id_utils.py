"""ID utilities for Trellis MCP objects.

Provides functions for generating human-readable IDs from titles with proper
slugification, charset validation, and length constraints for the hierarchical
object structure (Projects → Epics → Features → Tasks).
"""

import re
from pathlib import Path
from typing import Final

from slugify import slugify

from .fs_utils import find_object_path

# Constants for ID validation
MAX_ID_LENGTH: Final[int] = 32
VALID_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9-]+$")


class DuplicateIDError(Exception):
    """Exception raised when an ID collision cannot be resolved.

    This exception is raised when generate_id() cannot create a unique ID
    even after trying multiple collision resolution strategies.
    """

    pass


def slugify_text(text: str) -> str:
    """Convert text to a URL-safe slug for use in object IDs.

    Creates a lowercase slug using only letters, numbers, and hyphens.
    Handles Unicode characters by transliterating them to ASCII equivalents.

    Args:
        text: The input text to slugify (e.g., "My Feature Title")

    Returns:
        A slugified string suitable for use in IDs (e.g., "my-feature-title")

    Example:
        >>> slugify_text("User Authentication System")
        'user-authentication-system'
        >>> slugify_text("C'est déjà l'été")
        'cest-deja-lete'
        >>> slugify_text("数据库连接")
        'shu-ju-ku-lian-jie'
    """
    if not text or not text.strip():
        return ""

    # Use python-slugify with strict ASCII output
    slug = slugify(
        text,
        lowercase=True,
        separator="-",
        max_length=MAX_ID_LENGTH,
        word_boundary=True,
        save_order=True,
    )

    return slug or ""


def validate_id_charset(obj_id: str) -> bool:
    """Validate that an ID contains only allowed characters.

    Checks that the ID contains only lowercase letters (a-z), numbers (0-9),
    and hyphens (-) as specified in the Trellis MCP specification.

    Args:
        obj_id: The ID to validate

    Returns:
        True if the ID contains only valid characters, False otherwise

    Example:
        >>> validate_id_charset("user-auth-system")
        True
        >>> validate_id_charset("user_auth_system")
        False
        >>> validate_id_charset("UserAuthSystem")
        False
        >>> validate_id_charset("user@auth")
        False
    """
    if not obj_id:
        return False

    return bool(VALID_ID_PATTERN.match(obj_id))


def validate_id_length(obj_id: str) -> bool:
    """Validate that an ID meets the maximum length constraint.

    Checks that the ID is not longer than the maximum allowed length
    of 32 characters as specified in the Trellis MCP specification.

    Args:
        obj_id: The ID to validate

    Returns:
        True if the ID length is within limits, False otherwise

    Example:
        >>> validate_id_length("user-auth")
        True
        >>> validate_id_length("a-very-long-id-that-exceeds-the-maximum-allowed-length-limit")
        False
        >>> validate_id_length("")
        True
    """
    return len(obj_id) <= MAX_ID_LENGTH


def generate_id(kind: str, title: str, project_root: Path = Path("./planning")) -> str:
    """Generate a unique ID for a Trellis MCP object.

    Creates a slug from the title and ensures it's unique by checking for
    existing files in the planning directory structure. If a collision is found,
    adds numeric suffixes (-1, -2, etc.) until a unique ID is generated.

    Args:
        kind: The object kind ('project', 'epic', 'feature', or 'task')
        title: The object title to convert to an ID
        project_root: Root directory of the planning structure

    Returns:
        A unique ID string that passes all validation checks

    Raises:
        DuplicateIDError: If a unique ID cannot be generated after 100 attempts
        ValueError: If kind is not supported or title is empty

    Example:
        >>> generate_id("project", "User Authentication System")
        'user-authentication-system'
        >>> generate_id("feature", "User Authentication System")  # if collision
        'user-authentication-system-1'
    """
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")

    valid_kinds = {"project", "epic", "feature", "task"}
    if kind not in valid_kinds:
        raise ValueError(f"Invalid kind '{kind}'. Must be one of: {valid_kinds}")

    # Generate base slug from title
    base_slug = slugify_text(title)
    if not base_slug:
        raise ValueError(f"Title '{title}' produces empty slug")

    # Validate base slug meets requirements
    if not validate_id_charset(base_slug) or not validate_id_length(base_slug):
        raise ValueError(f"Generated slug '{base_slug}' is invalid")

    # Try the base slug first
    if not _id_exists(kind, base_slug, project_root):
        return base_slug

    # Handle collisions with numeric suffixes
    max_attempts = 100
    for attempt in range(1, max_attempts + 1):
        suffix = f"-{attempt}"

        # Calculate available space for base slug
        available_length = MAX_ID_LENGTH - len(suffix)
        if available_length <= 0:
            raise DuplicateIDError(f"Cannot generate unique ID for '{title}': suffix too long")

        # Truncate base slug to make room for suffix
        truncated_slug = base_slug[:available_length]
        candidate_id = truncated_slug + suffix

        # Ensure the candidate meets validation requirements
        if not validate_id_charset(candidate_id) or not validate_id_length(candidate_id):
            continue

        # Check if this candidate is unique
        if not _id_exists(kind, candidate_id, project_root):
            return candidate_id

    # If we get here, we couldn't generate a unique ID
    raise DuplicateIDError(f"Cannot generate unique ID for '{title}' after {max_attempts} attempts")


def clean_prerequisite_id(prereq_id: str) -> str:
    """Clean prerequisite ID by removing prefix if present.

    Removes single-character prefixes (like P-, E-, F-, T-) from object IDs
    to get the clean ID for prerequisite graph processing. Handles edge cases
    like empty strings or malformed IDs gracefully.

    Args:
        prereq_id: The prerequisite ID to clean (e.g., "T-task-name")

    Returns:
        The clean ID without prefix (e.g., "task-name") or the original ID
        if no valid prefix is detected

    Example:
        >>> clean_prerequisite_id("T-task-name")
        'task-name'
        >>> clean_prerequisite_id("P-project-name")
        'project-name'
        >>> clean_prerequisite_id("task-name")
        'task-name'
        >>> clean_prerequisite_id("")
        ''
        >>> clean_prerequisite_id("T")
        'T'
    """
    if not prereq_id:
        return prereq_id

    # Check if ID has format "X-YYYY" where X is any single character
    if len(prereq_id) > 1 and prereq_id[1] == "-":
        return prereq_id[2:]  # Remove "X-" prefix

    return prereq_id  # Return as-is if no prefix detected


def _id_exists(kind: str, obj_id: str, project_root: Path) -> bool:
    """Check if an object with the given ID already exists.

    This function is a wrapper around the shared find_object_path utility,
    returning True if the object exists, False otherwise.

    Args:
        kind: The object kind ('project', 'epic', 'feature', or 'task')
        obj_id: The ID to check
        project_root: Root directory of the planning structure

    Returns:
        True if an object with this ID exists, False otherwise
    """
    return find_object_path(kind, obj_id, project_root) is not None
