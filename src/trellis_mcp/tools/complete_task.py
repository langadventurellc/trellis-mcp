"""Complete task tool for Trellis MCP server.

Provides functionality to complete a task that is in in-progress or review status,
with optional log entry and file change tracking.
"""

from fastmcp import FastMCP

from ..complete_task import complete_task
from ..exceptions.invalid_status_for_completion import InvalidStatusForCompletion
from ..path_resolver import id_to_path, resolve_project_roots
from ..settings import Settings
from ..validation import TrellisValidationError


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

        Args:
            projectRoot: Root directory for the planning structure
            taskId: ID of the task to complete (with or without T- prefix)
            summary: Summary text for the log entry (empty string to skip logging)
            filesChanged: List of relative file paths that were changed

        Returns:
            Dictionary containing the validated task data and file path

        Raises:
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
            raise ValueError("Project root cannot be empty")

        if not taskId or not taskId.strip():
            raise ValueError("Task ID cannot be empty")

        # Call the core complete_task function
        try:
            validated_task = complete_task(projectRoot, taskId, summary, filesChanged)
        except InvalidStatusForCompletion as e:
            raise TrellisValidationError([str(e)])
        except FileNotFoundError as e:
            raise TrellisValidationError([f"Task not found: {str(e)}"])
        except Exception as e:
            raise TrellisValidationError([f"Failed to validate task for completion: {str(e)}"])

        # Resolve the task file path for response
        _, planning_root = resolve_project_roots(projectRoot)
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
