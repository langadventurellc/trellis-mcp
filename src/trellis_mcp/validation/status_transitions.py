"""Status transition validation functions.

This module provides functions to validate status transitions according
to the Trellis MCP lifecycle specifications.
"""

from ..schema.kind_enum import KindEnum
from ..schema.status_enum import StatusEnum


def enforce_status_transition(
    old: str | StatusEnum, new: str | StatusEnum, kind: str | KindEnum
) -> bool:
    """Enforce status transition rules per lifecycle table.

    Validates that the transition from old status to new status is allowed
    for the given object kind according to the lifecycle specifications.

    This function now delegates to the Pydantic schema model validation
    to maintain centralized transition logic in the schema models.

    Args:
        old: The current status (string or StatusEnum)
        new: The new status to transition to (string or StatusEnum)
        kind: The object kind (string or KindEnum)

    Returns:
        True if the transition is valid

    Raises:
        ValueError: If the transition is invalid for the given kind
    """
    # Import here to avoid circular imports
    from ..schema import get_model_class_for_kind

    # Convert string parameters to enums
    if isinstance(old, str):
        try:
            old_status = StatusEnum(old)
        except ValueError:
            raise ValueError(f"Invalid old status '{old}'. Must be a valid StatusEnum value.")
    else:
        old_status = old

    if isinstance(new, str):
        try:
            new_status = StatusEnum(new)
        except ValueError:
            raise ValueError(f"Invalid new status '{new}'. Must be a valid StatusEnum value.")
    else:
        new_status = new

    if isinstance(kind, str):
        try:
            kind_enum = KindEnum(kind)
        except ValueError:
            raise ValueError(f"Invalid kind '{kind}'. Must be a valid KindEnum value.")
    else:
        kind_enum = kind

    # Get the appropriate schema model class for this kind
    try:
        model_class = get_model_class_for_kind(kind_enum)
    except ValueError as e:
        raise ValueError(f"Could not get model class for kind '{kind_enum}': {e}")

    # Delegate to the schema model's transition validation
    return model_class.validate_status_transition(old_status, new_status)
