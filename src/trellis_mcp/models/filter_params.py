"""Filter parameters for backlog listing operations.

Defines the FilterParams model used to filter tasks in listBacklog operations
based on status and priority criteria.
"""

from typing import Sequence

from pydantic import Field, field_validator

from ..models.common import Priority
from ..schema.base import TrellisBaseModel
from ..schema.status_enum import StatusEnum


class FilterParams(TrellisBaseModel):
    """Filter parameters for backlog listing operations.

    Supports filtering tasks by status and priority values. Empty lists
    mean no filtering is applied for that criteria.

    Attributes:
        status: List of status values to filter by (empty = no status filtering)
        priority: List of priority values to filter by (empty = no priority filtering)
    """

    status: Sequence[StatusEnum | str] = Field(
        default=[],
        description="List of status values to filter by (empty = no status filtering)",
    )

    priority: Sequence[Priority | str] = Field(
        default=[],
        description="List of priority values to filter by (empty = no priority filtering)",
    )

    @field_validator("status", mode="before")
    @classmethod
    def validate_status_list(cls, v: Sequence[StatusEnum | str] | None) -> list[StatusEnum]:
        """Validate that all status values are valid StatusEnum values."""
        if v is None:
            return []

        # Convert all values to StatusEnum (Pydantic will handle string conversion)
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(StatusEnum(item))
            else:
                result.append(item)
        return result

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority_list(cls, v: Sequence[Priority | str] | None) -> list[Priority]:
        """Validate that all priority values are valid Priority values."""
        if v is None:
            return []

        # Convert all values to Priority (using the _missing_ method for string conversion)
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(Priority(item))
            else:
                result.append(item)
        return result
