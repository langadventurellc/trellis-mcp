"""Epic model for Trellis MCP.

Defines the schema for epic objects in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum
from .status_enum import StatusEnum


class EpicModel(BaseSchemaModel):
    """Schema model for epic objects.

    Epics are mid-level objects in the Trellis MCP hierarchy.
    They are contained within projects and contain features.
    """

    kind: KindEnum = Field(KindEnum.EPIC, description="Must be 'epic'")

    @field_validator("parent")
    @classmethod
    def validate_epic_parent(cls, v: str | None) -> str | None:
        """Validate that epics have a parent.

        Epics must have a parent project ID.
        """
        if v is None:
            raise ValueError("Epics must have a parent project ID")
        return v

    @field_validator("status")
    @classmethod
    def validate_epic_status(cls, v: StatusEnum) -> StatusEnum:
        """Validate that epic status is one of the allowed values.

        Epics can have status: draft, in-progress, done
        """
        allowed_statuses = {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE}
        if v not in allowed_statuses:
            allowed_values = ", ".join(s.value for s in allowed_statuses)
            raise ValueError(f"Invalid status '{v}' for epic. Must be one of: {allowed_values}")
        return v
