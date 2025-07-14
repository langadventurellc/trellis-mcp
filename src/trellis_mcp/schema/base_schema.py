"""Base schema model for Trellis MCP objects.

Provides common fields and validation for all Trellis MCP schema objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field

from .base import TrellisBaseModel
from .kind_enum import KindEnum
from .priority_enum import PriorityEnum
from .status_enum import StatusEnum


class BaseSchemaModel(TrellisBaseModel):
    """Base schema model for all Trellis MCP objects.

    Provides common fields that are shared across all object types:
    projects, epics, features, and tasks.
    """

    kind: KindEnum = Field(..., description="The type of object")
    id: str = Field(..., description="Unique identifier for the object")
    parent: Optional[str] = Field(None, description="Parent object ID (absent for projects)")
    status: StatusEnum = Field(..., description="Current status of the object")
    title: str = Field(..., description="Human-readable title")
    priority: PriorityEnum = Field(
        PriorityEnum.NORMAL, description="Priority level (default: normal)"
    )
    prerequisites: List[str] = Field(
        default_factory=list, description="List of prerequisite object IDs"
    )
    worktree: Optional[str] = Field(None, description="Optional worktree path for development")
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")
    schema_version: Literal["1.0"] = Field("1.0", description="Schema version (must be 1.0)")
