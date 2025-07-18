"""Base schema model for Trellis MCP objects.

Provides common fields and validation for all Trellis MCP schema objects.
"""

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import Field, ValidationInfo, field_validator, model_validator

from ..models.common import Priority
from .base import TrellisBaseModel
from .kind_enum import KindEnum
from .status_enum import StatusEnum


class BaseSchemaModel(TrellisBaseModel):
    """Base schema model for all Trellis MCP objects.

    Provides common fields that are shared across all object types:
    projects, epics, features, and tasks.
    """

    # Type annotation for transition matrix (overridden in subclasses)
    _valid_transitions: ClassVar[dict[StatusEnum, set[StatusEnum]]] = {}

    kind: KindEnum = Field(..., description="The type of object")
    id: str = Field(..., description="Unique identifier for the object")
    parent: str | None = Field(
        None, description="Parent object ID (absent for projects)", validate_default=True
    )
    status: StatusEnum = Field(..., description="Current status of the object")
    title: str = Field(..., description="Human-readable title")
    priority: Priority = Field(Priority.NORMAL, description="Priority level (default: normal)")
    prerequisites: list[str] = Field(
        default_factory=list, description="List of prerequisite object IDs"
    )
    worktree: str | None = Field(None, description="Optional worktree path for development")
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
                    KindEnum.PROJECT: {
                        StatusEnum.DRAFT,
                        StatusEnum.IN_PROGRESS,
                        StatusEnum.DONE,
                        StatusEnum.DELETED,
                    },
                    KindEnum.EPIC: {
                        StatusEnum.DRAFT,
                        StatusEnum.IN_PROGRESS,
                        StatusEnum.DONE,
                        StatusEnum.DELETED,
                    },
                    KindEnum.FEATURE: {
                        StatusEnum.DRAFT,
                        StatusEnum.IN_PROGRESS,
                        StatusEnum.DONE,
                        StatusEnum.DELETED,
                    },
                    KindEnum.TASK: {
                        StatusEnum.OPEN,
                        StatusEnum.IN_PROGRESS,
                        StatusEnum.REVIEW,
                        StatusEnum.DONE,
                        StatusEnum.DELETED,
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
    def validate_parent(cls, v: str | None, info: ValidationInfo) -> str | None:
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
                    # Tasks can now be standalone (parent=None) or hierarchy-based
                    # No validation error for None parent to support standalone tasks
                    pass

        return v

    @classmethod
    def validate_status_transition(cls, old_status: StatusEnum, new_status: StatusEnum) -> bool:
        """Validate status transition for this model class.

        Args:
            old_status: The current status
            new_status: The new status to transition to

        Returns:
            True if the transition is valid

        Raises:
            ValueError: If the transition is invalid
        """
        # If old and new are the same, transition is always valid
        if old_status == new_status:
            return True

        # Get transition matrix for this model class
        if not hasattr(cls, "_valid_transitions"):
            raise ValueError(
                f"No transition matrix defined for {cls.__name__}. "
                "This should not happen - check model definition."
            )

        valid_next_statuses: set[StatusEnum] = cls._valid_transitions.get(old_status, set())

        # Check if the new status is allowed
        if new_status not in valid_next_statuses:
            # Build helpful error message
            if valid_next_statuses:
                # Sort valid transitions for consistent error messages
                valid_values = ", ".join(
                    s.value for s in sorted(valid_next_statuses, key=lambda x: x.value)
                )
                # Extract kind from class name (e.g., "ProjectModel" -> "project")
                kind_name = cls.__name__.replace("Model", "").lower()
                raise ValueError(
                    f"Invalid status transition for {kind_name}: "
                    f"'{old_status.value}' cannot transition to '{new_status.value}'. "
                    f"Valid transitions: {valid_values}"
                )
            else:
                # Extract kind from class name
                kind_name = cls.__name__.replace("Model", "").lower()
                raise ValueError(
                    f"Invalid status transition for {kind_name}: "
                    f"'{old_status.value}' is a terminal status with no valid transitions."
                )

        return True

    @model_validator(mode="after")
    def validate_status_transitions_from_context(self) -> "BaseSchemaModel":
        """Validate status transitions when old status is available in context.

        This model validator checks for status transitions when the original status
        is provided in the validation context. This enables model-level validation
        for scenarios where the old status is known.
        """
        # Check if we have validation context with original status
        if (
            hasattr(self, "__pydantic_private__")
            and self.__pydantic_private__
            and "original_status" in self.__pydantic_private__
        ):
            original_status = self.__pydantic_private__["original_status"]
            if original_status and original_status != self.status:
                try:
                    # Convert string to enum if needed
                    if isinstance(original_status, str):
                        original_status = StatusEnum(original_status)

                    # Validate the transition using the model's transition matrix
                    self.__class__.validate_status_transition(original_status, self.status)
                except ValueError as e:
                    raise ValueError(f"Status transition validation failed: {str(e)}")

        return self
