"""Task ID resolution utilities for cross-system lookup.

Provides functions for resolving task IDs across both hierarchical (T- prefixed)
and standalone task systems. This module enables direct task claiming operations
by locating specific tasks by ID and returning their file paths and metadata.

Key Features:
- Cross-system task ID resolution (hierarchical and standalone)
- ID format validation for both T- prefixed and standalone formats
- ID normalization for consistent lookup operations
- Integration with existing scanner infrastructure for efficiency
- Comprehensive security validation following existing patterns

This module is foundational for the direct task claiming feature, enabling
users to claim specific tasks by ID through the claimNextTask tool.
"""

import re
from pathlib import Path
from typing import Optional

from .utils.fs_utils import find_object_path
from .utils.id_utils import clean_prerequisite_id, validate_id_charset


def resolve_task_by_id(project_root: str, task_id: str) -> Optional[Path]:
    """Resolve task ID to file path across both task systems.

    Locates a specific task by ID in both hierarchical (within project/epic/feature
    structure) and standalone task systems. Uses existing scanning infrastructure
    for efficient task discovery with comprehensive security validation.

    Args:
        project_root: Root directory for the planning structure
        task_id: Task ID to resolve (T- prefixed or standalone format)

    Returns:
        Path to task file if found, None if not found

    Raises:
        ValueError: If task_id is invalid format or contains dangerous patterns
        ValueError: If security validation fails

    Example:
        >>> resolve_task_by_id("./planning", "T-implement-auth")
        Path('planning/projects/P-web/epics/E-auth/features/F-login/tasks-open/T-implement-auth.md')
        >>> resolve_task_by_id("./planning", "implement-auth")  # same result
        Path('planning/projects/P-web/epics/E-auth/features/F-login/tasks-open/T-implement-auth.md')
        >>> resolve_task_by_id("./planning", "T-standalone-task")
        Path('planning/tasks-open/T-standalone-task.md')
        >>> resolve_task_by_id("./planning", "nonexistent-task")
        None

    Note:
        This function searches both hierarchical and standalone task systems,
        automatically detecting the appropriate task type. Standalone tasks
        (in planning/tasks-*) are checked first for efficiency.
    """
    # Validate input parameters
    if not project_root or not project_root.strip():
        raise ValueError("Project root cannot be empty")

    if not task_id or not task_id.strip():
        raise ValueError("Task ID cannot be empty")

    # Normalize the task ID for consistent lookup
    normalized_id = normalize_task_id(task_id)

    # Validate the normalized task ID format (check if normalization produced valid result)
    if not normalized_id or not validate_task_id_format(normalized_id):
        raise ValueError(f"Invalid task ID format: {task_id}")

    # Apply security validation using existing patterns
    from .validation.field_validation import validate_standalone_task_path_parameters
    from .validation.security import validate_standalone_task_path_security

    validation_errors = validate_standalone_task_path_parameters(normalized_id)
    if validation_errors:
        raise ValueError(f"Task ID validation failed: {validation_errors[0]}")

    security_errors = validate_standalone_task_path_security(normalized_id, project_root)
    if security_errors:
        raise ValueError(f"Security validation failed: {security_errors[0]}")

    # Convert project_root to Path and resolve to prevent path traversal
    project_root_path = Path(project_root).resolve()

    # Get the path resolution root (handles both project/planning and planning-only structures)
    from .path_resolver import resolve_project_roots

    _, path_resolution_root = resolve_project_roots(project_root_path)

    # Use existing find_object_path utility for efficient cross-system lookup
    # This function already handles both hierarchical and standalone task discovery
    result_path = find_object_path("task", normalized_id, path_resolution_root)

    return result_path


def validate_task_id_format(task_id: str) -> bool:
    """Validate task ID format for both hierarchical and standalone tasks.

    Checks that the task ID meets format requirements for both T- prefixed
    hierarchical tasks and standalone task IDs. Ensures ID contains only
    allowed characters and meets length constraints.

    Args:
        task_id: Task ID to validate (normalized, without T- prefix)

    Returns:
        True if task ID format is valid, False otherwise

    Example:
        >>> validate_task_id_format("implement-auth")
        True
        >>> validate_task_id_format("implement_auth")  # underscores not allowed
        False
        >>> validate_task_id_format("Implement-Auth")  # uppercase not allowed
        False
        >>> validate_task_id_format("")  # empty not allowed
        False
        >>> validate_task_id_format("very-long-task-id-that-exceeds-maximum-length-limits")
        False

    Note:
        This function validates the normalized task ID (without T- prefix).
        Use normalize_task_id() first to clean the ID before validation.
    """
    if not task_id or not task_id.strip():
        return False

    # Use existing ID validation utilities
    # Check character set (lowercase letters, numbers, hyphens only)
    if not validate_id_charset(task_id):
        return False

    # Check length constraints (use same limits as other objects)
    from .utils.id_utils import validate_id_length

    if not validate_id_length(task_id):
        return False

    # Additional task-specific validation patterns
    # Ensure ID doesn't start or end with hyphen
    if task_id.startswith("-") or task_id.endswith("-"):
        return False

    # Ensure no consecutive hyphens
    if "--" in task_id:
        return False

    # Ensure contains at least one non-hyphen character
    if task_id.replace("-", "") == "":
        return False

    return True


def normalize_task_id(task_id: str) -> str:
    """Normalize task ID for consistent lookup operations.

    Cleans and normalizes task IDs by removing T- prefix if present and
    applying consistent formatting. Handles both hierarchical (T- prefixed)
    and standalone task ID formats.

    Args:
        task_id: Raw task ID to normalize

    Returns:
        Normalized task ID without prefix (clean ID)

    Example:
        >>> normalize_task_id("T-implement-auth")
        'implement-auth'
        >>> normalize_task_id("implement-auth")
        'implement-auth'
        >>> normalize_task_id("  T-task-name  ")
        'task-name'
        >>> normalize_task_id("")
        ''

    Note:
        This function uses existing ID cleaning utilities to ensure
        consistency with the rest of the codebase. The returned ID
        can be used directly with find_object_path and other utilities.
    """
    if not task_id:
        return ""

    # Strip whitespace and convert to lowercase for consistency
    cleaned_id = task_id.strip().lower()

    # Additional normalization for consistency
    # Remove any remaining whitespace that might be in the middle
    normalized_id = re.sub(r"\s+", "-", cleaned_id)

    # Remove any non-allowed characters and convert underscores to hyphens
    normalized_id = re.sub(r"[^a-z0-9-]", "", normalized_id.replace("_", "-"))

    # Use existing prerequisite ID cleaning utility to handle T- prefix removal
    # This removes T- prefix if present and handles edge cases
    normalized_id = clean_prerequisite_id(normalized_id)

    # Handle nested T- prefixes by repeatedly cleaning until no more T- prefixes
    while normalized_id.startswith("t-"):
        normalized_id = clean_prerequisite_id(normalized_id)

    # Clean up multiple consecutive hyphens
    normalized_id = re.sub(r"-+", "-", normalized_id)

    # Remove leading/trailing hyphens
    normalized_id = normalized_id.strip("-")

    return normalized_id
