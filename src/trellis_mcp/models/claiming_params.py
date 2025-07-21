"""Parameter validation model for claimNextTask operations.

Defines the ClaimingParams model used to validate parameters for claimNextTask
operations, implementing mutual exclusivity rules and parameter combination logic.
"""

import re
from typing import Optional

from pydantic import Field, field_validator, model_validator

from ..schema.base import TrellisBaseModel


class ClaimingParams(TrellisBaseModel):
    """Parameter validation model for claimNextTask operations.

    Implements mutual exclusivity rules, parameter combination logic, and format
    validation for all claimNextTask parameters. Provides structured validation
    with clear error messages for each validation rule violation.

    Attributes:
        project_root: Root directory for planning structure (required)
        worktree: Optional worktree identifier to stamp on claimed task
        scope: Optional scope ID to filter by hierarchical boundaries (P-, E-, F- prefixed)
        task_id: Optional task ID to claim directly (T- prefixed or standalone format)
        force_claim: Boolean to bypass prerequisite and status validation (only valid with task_id)
    """

    project_root: str = Field(
        description="Root directory for planning structure (required)",
    )

    worktree: str = Field(
        default="",
        description="Optional worktree identifier to stamp on claimed task",
    )

    scope: Optional[str] = Field(
        default=None,
        description="Optional scope ID to filter by hierarchical boundaries (P-, E-, F- prefixed)",
    )

    task_id: Optional[str] = Field(
        default=None,
        description="Optional task ID to claim directly (T- prefixed or standalone format)",
    )

    force_claim: bool = Field(
        default=False,
        description="Boolean to bypass validation (only valid with task_id)",
    )

    @field_validator("project_root")
    @classmethod
    def validate_project_root_not_empty(cls, v: str) -> str:
        """Validate that project_root is not empty or whitespace-only.

        Args:
            v: The project_root value to validate

        Returns:
            The validated project_root value

        Raises:
            ValueError: If project_root is empty or whitespace-only
        """
        if not v or not v.strip():
            raise ValueError("Project root cannot be empty")
        return v.strip()

    @field_validator("scope")
    @classmethod
    def validate_scope_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate that scope ID follows P-, E-, F- prefix pattern.

        Reuses the same validation logic as FilterParams for consistency.

        Args:
            v: The scope ID value to validate

        Returns:
            The validated scope ID or None

        Raises:
            ValueError: If scope ID format is invalid
        """
        if v is None:
            return v

        # Use empty string check before regex validation
        scope_value = v.strip()
        if not scope_value:
            return None

        if not re.match(r"^[PEF]-[A-Za-z0-9_-]+$", scope_value):
            raise ValueError(
                f"Invalid scope ID format: {scope_value}. " "Must use P-, E-, or F- prefix"
            )
        return scope_value

    @field_validator("task_id")
    @classmethod
    def validate_task_id_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate that task_id follows T- prefix or standalone format.

        Uses existing task ID validation patterns for consistency with
        the rest of the system.

        Args:
            v: The task_id value to validate

        Returns:
            The validated task_id or None

        Raises:
            ValueError: If task_id format is invalid
        """
        if v is None:
            return v

        # Use empty string check before format validation
        task_id_value = v.strip()
        if not task_id_value:
            return None

        # Import validation function from existing module
        from ..task_resolver import validate_task_id_format
        from ..utils.normalize_id import normalize_id

        try:
            # Normalize the task ID (remove T- prefix if present) for validation
            normalized_id = normalize_id(task_id_value, "task")
            if not normalized_id or not validate_task_id_format(normalized_id):
                raise ValueError(f"Invalid task ID format: {task_id_value}")
        except Exception as e:
            raise ValueError(f"Invalid task ID format: {task_id_value}. {str(e)}")

        return task_id_value

    @model_validator(mode="after")
    def validate_parameter_combinations(self) -> "ClaimingParams":
        """Validate parameter combination rules across fields.

        Implements mutual exclusivity and parameter interaction rules:
        1. scope and task_id cannot both be specified
        2. force_claim=True only valid when task_id is specified

        Returns:
            The validated ClaimingParams instance

        Raises:
            ValueError: If parameter combination rules are violated
        """
        # Check mutual exclusivity: scope and task_id cannot both be specified
        if self.scope and self.task_id:
            raise ValueError(
                "Cannot specify both scope and task_id parameters. "
                "Use scope for filtering tasks within boundaries, or task_id for direct claiming."
            )

        # Check force_claim scope: only valid when task_id is specified
        if self.force_claim and not self.task_id:
            raise ValueError(
                "force_claim parameter requires task_id to be specified. "
                "Force claiming only applies to direct task claiming operations."
            )

        return self
