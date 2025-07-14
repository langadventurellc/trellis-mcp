"""Base schema model for Trellis MCP objects.

Provides common fields and validation for all Trellis MCP schema objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field, ValidationInfo, field_validator

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

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: StatusEnum, info: ValidationInfo) -> StatusEnum:
        """Validate that status is allowed for the object kind.

        Uses the info.data.get("kind") pattern to determine object type dynamically.
        """

        # Get the object kind from the model data
        if hasattr(info, "data") and info.data:
            object_kind = info.data.get("kind")
            if object_kind:
                # Convert string to enum if needed
                if isinstance(object_kind, str):
                    try:
                        object_kind = KindEnum(object_kind)
                    except ValueError:
                        # If kind is invalid, let the kind field validator handle it
                        return v

                # Validate status for the specific kind
                # Define allowed statuses per kind
                allowed_statuses = {
                    KindEnum.PROJECT: {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE},
                    KindEnum.EPIC: {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE},
                    KindEnum.FEATURE: {StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE},
                    KindEnum.TASK: {
                        StatusEnum.OPEN,
                        StatusEnum.IN_PROGRESS,
                        StatusEnum.REVIEW,
                        StatusEnum.DONE,
                    },
                }

                valid_statuses = allowed_statuses.get(object_kind, set())
                if v not in valid_statuses:
                    valid_values = ", ".join(s.value for s in valid_statuses)
                    raise ValueError(
                        f"Invalid status '{v}' for {object_kind.value.lower()}. "
                        f"Must be one of: {valid_values}"
                    )

        return v

    @field_validator("parent")
    @classmethod
    def validate_parent(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate parent existence and constraints for the object kind.

        Uses the info.data.get("kind") pattern to determine object type dynamically.
        Note: This validator checks basic parent constraints but cannot validate
        filesystem existence without project_root context.
        """
        # Get the object kind from the model data
        if hasattr(info, "data") and info.data:
            object_kind = info.data.get("kind")
            if object_kind:
                # Convert string to enum if needed
                if isinstance(object_kind, str):
                    try:
                        object_kind = KindEnum(object_kind)
                    except ValueError:
                        # If kind is invalid, let the kind field validator handle it
                        return v

                # Validate parent constraints based on object kind
                if object_kind == KindEnum.PROJECT:
                    if v is not None:
                        raise ValueError("Projects cannot have a parent")
                elif object_kind == KindEnum.EPIC:
                    if v is None:
                        raise ValueError("Epics must have a parent project ID")
                elif object_kind == KindEnum.FEATURE:
                    if v is None:
                        raise ValueError("Features must have a parent epic ID")
                elif object_kind == KindEnum.TASK:
                    if v is None:
                        raise ValueError("Tasks must have a parent feature ID")

        return v
