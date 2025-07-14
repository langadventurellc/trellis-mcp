"""Epic model for Trellis MCP.

Defines the schema for epic objects in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from pydantic import Field

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum
from .status_enum import StatusEnum


class EpicModel(BaseSchemaModel):
    """Schema model for epic objects.

    Epics are mid-level objects in the Trellis MCP hierarchy.
    They are contained within projects and contain features.
    """

    kind: KindEnum = Field(KindEnum.EPIC, description="Must be 'epic'")

    # Status transition matrix for epics
    _valid_transitions = {
        StatusEnum.DRAFT: {StatusEnum.IN_PROGRESS},
        StatusEnum.IN_PROGRESS: {StatusEnum.DONE},
        StatusEnum.DONE: set(),  # No transitions from done
    }
