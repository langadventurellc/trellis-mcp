"""Feature model for Trellis MCP.

Defines the schema for feature objects in the Trellis MCP hierarchy.
"""

from pydantic import Field

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum
from .status_enum import StatusEnum


class FeatureModel(BaseSchemaModel):
    """Schema model for feature objects.

    Features are mid-level objects in the Trellis MCP hierarchy.
    They are contained within epics and contain tasks.
    """

    kind: KindEnum = Field(KindEnum.FEATURE, description="Must be 'feature'")

    # Status transition matrix for features
    _valid_transitions = {
        StatusEnum.DRAFT: {StatusEnum.IN_PROGRESS, StatusEnum.DELETED},
        StatusEnum.IN_PROGRESS: {StatusEnum.DONE, StatusEnum.DELETED},
        StatusEnum.DONE: {StatusEnum.DELETED},  # Only deletion allowed from done
    }
