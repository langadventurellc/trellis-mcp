"""Get next reviewable task tool for Trellis MCP server.

Provides functionality to find the next task that needs review, ordered by
oldest updated timestamp with priority as tiebreaker.
"""

from fastmcp import FastMCP

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..path_resolver import id_to_path, resolve_project_roots
from ..query import get_oldest_review
from ..settings import Settings


def create_get_next_reviewable_task_tool(settings: Settings):
    """Create a getNextReviewableTask tool configured with the provided settings.

    Args:
        settings: Server configuration settings

    Returns:
        Configured getNextReviewableTask tool function
    """
    mcp = FastMCP()

    @mcp.tool
    def getNextReviewableTask(
        projectRoot: str,
    ) -> dict[str, str | dict[str, str] | None]:
        """Get the next task that needs review, ordered by oldest updated timestamp.

        Finds the task in 'review' status with the oldest 'updated' timestamp across
        the entire project hierarchy. If multiple tasks have the same timestamp,
        priority is used as a tiebreaker (high > normal > low).

        Args:
            projectRoot: Root directory for the planning structure

        Returns:
            Dictionary containing the reviewable task data, or None if no reviewable tasks exist.
            Structure when task found:
            {
                "task": {
                    "id": str,           # Clean task ID (e.g., "implement-auth")
                    "title": str,        # Task title
                    "status": str,       # Task status ("review")
                    "priority": str,     # Task priority ("high", "normal", "low")
                    "parent": str | None,  # Parent feature ID (None for standalone tasks)
                    "file_path": str,    # Path to task file
                    "created": str,      # Creation timestamp
                    "updated": str,      # Last update timestamp
                }
            }

            When no reviewable tasks exist:
            {
                "task": None
            }

        Raises:
            ValueError: If projectRoot is empty or invalid
            TrellisValidationError: If there are issues accessing the project structure
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValidationError(
                errors=["Project root cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "projectRoot"},
            )

        # Resolve project roots to get planning directory
        _, planning_root = resolve_project_roots(projectRoot)

        # Call the query function to get the oldest reviewable task
        try:
            reviewable_task = get_oldest_review(planning_root)
        except Exception as e:
            raise ValidationError(
                errors=[f"Failed to query reviewable tasks: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "query_reviewable_tasks"},
                object_kind="task",
            )

        # Handle case where no reviewable tasks exist
        if reviewable_task is None:
            return {"task": None}

        # Convert TaskModel to dictionary format
        try:
            task_file_path = id_to_path(planning_root, "task", reviewable_task.id)
        except Exception as e:
            raise ValidationError(
                errors=[f"Failed to resolve task file path: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "path_resolution"},
                object_id=reviewable_task.id,
                object_kind="task",
            )

        # Build task dictionary in the format expected by the API
        task_dict = {
            "id": reviewable_task.id,
            "title": reviewable_task.title,
            "status": reviewable_task.status.value,
            "priority": str(reviewable_task.priority),
            "parent": reviewable_task.parent or "",
            "file_path": str(task_file_path),
            "created": reviewable_task.created.isoformat(),
            "updated": reviewable_task.updated.isoformat(),
        }

        # Return the reviewable task info
        return {"task": task_dict}

    return getNextReviewableTask
