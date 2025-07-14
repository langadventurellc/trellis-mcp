"""Task model for Trellis MCP.

Defines the schema for task objects in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from pydantic import Field

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum


class TaskModel(BaseSchemaModel):
    """Schema model for task objects.

    Tasks are the leaf objects in the Trellis MCP hierarchy.
    They are contained within features and represent actionable work items.
    """

    kind: KindEnum = Field(KindEnum.TASK, description="Must be 'task'")
