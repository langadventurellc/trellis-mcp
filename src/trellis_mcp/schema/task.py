"""Task model for Trellis MCP.

Defines the schema for task objects in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum
from .status_enum import StatusEnum


class TaskModel(BaseSchemaModel):
    """Schema model for task objects.

    Tasks are the leaf objects in the Trellis MCP hierarchy.
    They are contained within features and represent actionable work items.
    """

    kind: KindEnum = Field(KindEnum.TASK, description="Must be 'task'")

    @field_validator("parent")
    @classmethod
    def validate_task_parent(cls, v: str | None) -> str | None:
        """Validate that tasks have a parent.

        Tasks must have a parent feature ID.
        """
        if v is None:
            raise ValueError("Tasks must have a parent feature ID")
        return v

    @field_validator("status")
    @classmethod
    def validate_task_status(cls, v: StatusEnum) -> StatusEnum:
        """Validate that task status is one of the allowed values.

        Tasks can have status: open, in-progress, review, done
        """
        allowed_statuses = {
            StatusEnum.OPEN,
            StatusEnum.IN_PROGRESS,
            StatusEnum.REVIEW,
            StatusEnum.DONE,
        }
        if v not in allowed_statuses:
            allowed_values = ", ".join(s.value for s in allowed_statuses)
            raise ValueError(f"Invalid status '{v}' for task. Must be one of: {allowed_values}")
        return v
