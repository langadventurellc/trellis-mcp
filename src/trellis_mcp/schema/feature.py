"""Feature model for Trellis MCP.

Defines the schema for feature objects in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum
from .status_enum import StatusEnum


class FeatureModel(BaseSchemaModel):
    """Schema model for feature objects.

    Features are mid-level objects in the Trellis MCP hierarchy.
    They are contained within epics and contain tasks.
    """

    kind: KindEnum = Field(KindEnum.FEATURE, description="Must be 'feature'")

    @field_validator("parent")
    @classmethod
    def validate_feature_parent(cls, v: str | None) -> str | None:
        """Validate that features have a parent.

        Features must have a parent epic ID.
        """
        if v is None:
            raise ValueError("Features must have a parent epic ID")
        return v

    @field_validator("status")
    @classmethod
    def validate_feature_status(cls, v: StatusEnum) -> StatusEnum:
        """Validate that feature status is one of the allowed values.

        Features can have status: draft, in-progress, done
        """
        allowed_statuses = {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE}
        if v not in allowed_statuses:
            allowed_values = ", ".join(s.value for s in allowed_statuses)
            raise ValueError(f"Invalid status '{v}' for feature. Must be one of: {allowed_values}")
        return v
