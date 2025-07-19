"""Exception classes for validation operations.

This module defines custom exception classes used throughout the validation
system for different types of validation errors.
"""

from typing import Any


def _determine_object_type_label(obj_id: str, obj_data: dict[str, Any] | None) -> str:
    """Determine the type label for an object in cycle detection.

    For tasks, returns 'standalone' or 'hierarchical' based on parent field.
    For other objects, returns the kind (project, epic, feature).

    Args:
        obj_id: The object ID
        obj_data: The object data dictionary, or None if not available

    Returns:
        String label for the object type
    """
    if not obj_data:
        return "unknown"

    obj_kind = obj_data.get("kind", "unknown")

    if obj_kind == "task":
        # For tasks, determine if standalone or hierarchical
        parent = obj_data.get("parent")
        if parent is None or parent == "":
            return "standalone"
        else:
            return "hierarchical"
    else:
        # For other objects, return the kind
        return obj_kind


class CircularDependencyError(ValueError):
    """Exception raised when a circular dependency is detected in prerequisites."""

    def __init__(
        self, cycle_path: list[str], objects_data: dict[str, dict[str, Any]] | None = None
    ):
        """Initialize circular dependency error.

        Args:
            cycle_path: List of object IDs that form the cycle
            objects_data: Optional dictionary mapping object IDs to their data for enhanced context
        """
        self.cycle_path = cycle_path
        self.objects_data = objects_data

        if objects_data is not None:
            # Create enhanced cycle string with type information
            cycle_parts = []
            for obj_id in cycle_path:
                obj_data = objects_data.get(obj_id)
                type_label = _determine_object_type_label(obj_id, obj_data)
                cycle_parts.append(f"{obj_id} ({type_label})")
            cycle_str = " → ".join(cycle_parts)
        else:
            # Fallback to simple format for backward compatibility
            cycle_str = " -> ".join(cycle_path)

        super().__init__(f"Circular dependency detected: {cycle_str}")


class TrellisValidationError(Exception):
    """Custom validation error that can hold multiple error messages."""

    def __init__(self, errors: list[str]):
        """Initialize validation error.

        Args:
            errors: List of validation error messages
        """
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")
