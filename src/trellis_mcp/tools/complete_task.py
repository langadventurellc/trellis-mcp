"""Complete task tool for Trellis MCP server.

Provides functionality to complete a task that is in in-progress or review status,
with optional log entry and file change tracking.
"""

from fastmcp import FastMCP

from ..complete_task import complete_task
from ..exceptions.invalid_status_for_completion import InvalidStatusForCompletion
from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..path_resolver import id_to_path, resolve_project_roots
from ..settings import Settings


def create_complete_task_tool(settings: Settings):
    """Create a completeTask tool configured with the provided settings.

    Args:
        settings: Server configuration settings

    Returns:
        Configured completeTask tool function
    """
    mcp = FastMCP()

    @mcp.tool
    def completeTask(
        projectRoot: str,
        taskId: str,
        summary: str = "",
        filesChanged: list[str] = [],
    ) -> dict[str, str | dict[str, str]]:
        """Complete a task that is in in-progress or review status.

        Validates that the specified task is in a valid status for completion
        (in-progress or review) and optionally appends a log entry with summary
        and list of changed files. This is part of the task completion workflow.

        Supports cross-system dependency completion workflows, where completing this
        task may unblock dependent tasks across both hierarchical and standalone task
        systems. The system efficiently tracks which tasks become eligible after
        completion, enabling parallel development across different project structures.

        Args:
            projectRoot: Root directory for the planning structure
            taskId: ID of the task to complete (with or without T- prefix). Can be either
                a hierarchical task (within project/epic/feature) or standalone task.
            summary: Summary text for the log entry (empty string to skip logging)
            filesChanged: List of relative file paths that were changed

        Returns:
            Dictionary containing the validated task data and file path. Completing this
            task may unblock dependent tasks in both hierarchical and standalone systems.

        Raises:
            ValidationError: If cross-system completion validation fails, including:
                - INVALID_STATUS_TRANSITION: Task not in valid status for completion
                - INVALID_FIELD: Task not found in either hierarchical or standalone systems
                - Cross-system validation errors during completion processing
            TrellisValidationError: If task is not in valid status for completion
            FileNotFoundError: If task with the given ID cannot be found
            OSError: If file operations fail

        Example:
            >>> result = completeTask("./planning", "T-implement-auth")
            >>> result["task"]["status"]
            'in-progress'
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValidationError(
                errors=["Project root cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "projectRoot"},
            )

        if not taskId or not taskId.strip():
            raise ValidationError(
                errors=["Task ID cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "taskId"},
            )

        # Call the core complete_task function
        try:
            validated_task = complete_task(projectRoot, taskId, summary, filesChanged)
        except InvalidStatusForCompletion as e:
            raise ValidationError(
                errors=[str(e)],
                error_codes=[ValidationErrorCode.INVALID_STATUS_TRANSITION],
                context={"validation_type": "completion_status", "kind": "task"},
                object_id=taskId,
                object_kind="task",
            )
        except FileNotFoundError as e:
            raise ValidationError(
                errors=[f"Task not found: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "task_lookup", "kind": "task"},
                object_id=taskId,
                object_kind="task",
            )
        except Exception as e:
            raise ValidationError(
                errors=[f"Failed to validate task for completion: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "completion_validation", "kind": "task"},
                object_id=taskId,
                object_kind="task",
            )

        # Resolve the task file path for response
        _, planning_root = resolve_project_roots(projectRoot, ensure_planning_subdir=True)
        task_file_path = id_to_path(planning_root, "task", validated_task.id)

        # Build task dictionary in the format expected by the API
        task_dict = {
            "id": validated_task.id,
            "title": validated_task.title,
            "status": validated_task.status.value,
            "priority": str(validated_task.priority),
            "parent": validated_task.parent or "",
            "file_path": str(task_file_path),
            "created": validated_task.created.isoformat(),
            "updated": validated_task.updated.isoformat(),
        }

        # Return the validated task info in the expected format
        return {
            "task": task_dict,
            "validation_status": "ready_for_completion",
            "file_path": str(task_file_path),
        }

    return completeTask
