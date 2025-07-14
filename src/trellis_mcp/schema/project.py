"""Project model for Trellis MCP.

Defines the schema for project objects in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum
from .status_enum import StatusEnum


class ProjectModel(BaseSchemaModel):
    """Schema model for project objects.

    Projects are the top-level objects in the Trellis MCP hierarchy.
    They contain epics and have no parent.
    """

    kind: KindEnum = Field(KindEnum.PROJECT, description="Must be 'project'")

    @field_validator("parent")
    @classmethod
    def validate_project_parent(cls, v: str | None) -> str | None:
        """Validate that projects have no parent.

        Projects are top-level objects and must have parent=None.
        """
        if v is not None:
            raise ValueError("Projects cannot have a parent")
        return v

    @field_validator("status")
    @classmethod
    def validate_project_status(cls, v: StatusEnum) -> StatusEnum:
        """Validate that project status is one of the allowed values.

        Projects can have status: draft, in-progress, done
        """
        allowed_statuses = {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE}
        if v not in allowed_statuses:
            allowed_values = ", ".join(s.value for s in allowed_statuses)
            raise ValueError(f"Invalid status '{v}' for project. Must be one of: {allowed_values}")
        return v
