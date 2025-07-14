"""Feature model for Trellis MCP.

Defines the schema for feature objects in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from pydantic import Field

from .base_schema import BaseSchemaModel
from .kind_enum import KindEnum


class FeatureModel(BaseSchemaModel):
    """Schema model for feature objects.

    Features are mid-level objects in the Trellis MCP hierarchy.
    They are contained within epics and contain tasks.
    """

    kind: KindEnum = Field(KindEnum.FEATURE, description="Must be 'feature'")
