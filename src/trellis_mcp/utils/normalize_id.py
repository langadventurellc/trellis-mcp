"""ID normalization utilities for Trellis MCP objects.

Provides functions for normalizing object IDs across all object types (Project, Epic,
Feature, Task) by removing prefixes and applying consistent formatting. This module
enables consistent ID lookup operations across the hierarchical object structure.

Key Features:
- Cross-object-type ID normalization (P-, E-, F-, T- prefixed objects)
- ID format validation for all object types
- ID normalization for consistent lookup operations
- Integration with existing ID cleaning utilities for consistency
- Comprehensive validation following existing patterns

This module supports both hierarchical objects (within project/epic/feature structure)
and standalone tasks, providing unified ID normalization across all object types.
"""

import re
from typing import Final

from .id_utils import clean_prerequisite_id

# Valid object kind prefixes mapping
KIND_PREFIXES: Final[dict[str, str]] = {
    "project": "P-",
    "epic": "E-",
    "feature": "F-",
    "task": "T-",
}


def normalize_id(obj_id: str, kind: str) -> str:
    """Normalize object ID for consistent lookup operations.

    Cleans and normalizes object IDs by removing kind-specific prefix if present and
    applying consistent formatting. Handles all object types (project, epic, feature, task)
    with their respective prefixes (P-, E-, F-, T-).

    Args:
        obj_id: Raw object ID to normalize
        kind: Object kind ('project', 'epic', 'feature', or 'task')

    Returns:
        Normalized object ID without prefix (clean ID)

    Raises:
        ValueError: If kind is invalid or not supported

    Example:
        >>> normalize_id("T-implement-auth", "task")
        'implement-auth'
        >>> normalize_id("P-web-platform", "project")
        'web-platform'
        >>> normalize_id("implement-auth", "task")
        'implement-auth'
        >>> normalize_id("  F-user-management  ", "feature")
        'user-management'
        >>> normalize_id("", "task")
        ''

    Note:
        This function uses existing ID cleaning utilities to ensure
        consistency with the rest of the codebase. The returned ID
        can be used directly with find_object_path and other utilities.
    """
    from ..types import VALID_KINDS

    if not kind or kind not in VALID_KINDS:
        raise ValueError(f"Invalid kind '{kind}'. Must be one of: {VALID_KINDS}")

    if not obj_id:
        return ""

    # Strip whitespace and convert to lowercase for consistency
    cleaned_id = obj_id.strip().lower()

    # Additional normalization for consistency
    # Remove any remaining whitespace that might be in the middle
    normalized_id = re.sub(r"\s+", "-", cleaned_id)

    # Remove any non-allowed characters and convert underscores to hyphens
    normalized_id = re.sub(r"[^a-z0-9-]", "", normalized_id.replace("_", "-"))

    # Use existing prerequisite ID cleaning utility to handle prefix removal
    # This removes the kind-specific prefix if present and handles edge cases
    normalized_id = clean_prerequisite_id(normalized_id)

    # Handle nested prefixes by repeatedly cleaning until no more prefixes
    # This handles cases like "t-t-task-name" or malformed IDs
    expected_prefix = KIND_PREFIXES[kind].lower()
    max_iterations = 10  # Prevent infinite loops
    iteration_count = 0

    while normalized_id.startswith(expected_prefix[:-1]) and iteration_count < max_iterations:
        previous_id = normalized_id
        normalized_id = clean_prerequisite_id(normalized_id)
        iteration_count += 1

        # If no change occurred, break to prevent infinite loop
        if normalized_id == previous_id:
            break

    # Clean up multiple consecutive hyphens
    normalized_id = re.sub(r"-+", "-", normalized_id)

    # Remove leading/trailing hyphens
    normalized_id = normalized_id.strip("-")

    return normalized_id
