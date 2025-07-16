"""Claim next task tool for Trellis MCP server.

Provides functionality to claim the next highest-priority open task with all
prerequisites completed, setting its status to in-progress.
"""

from fastmcp import FastMCP

from ..claim_next_task import claim_next_task
from ..exceptions.no_available_task import NoAvailableTask
from ..path_resolver import id_to_path, resolve_project_roots
from ..settings import Settings
from ..validation import TrellisValidationError


def create_claim_next_task_tool(settings: Settings):
    """Create a claimNextTask tool configured with the provided settings.

    Args:
        settings: Server configuration settings

    Returns:
        Configured claimNextTask tool function
    """
    mcp = FastMCP()

    @mcp.tool
    def claimNextTask(
        projectRoot: str,
        worktree: str | None = None,
    ) -> dict[str, str | dict[str, str]]:
        """Claim the next highest-priority open task with all prerequisites completed.

        Atomically selects the highest-priority open task (where all prerequisites
        have status='done'), sets its status to 'in-progress', and optionally
        stamps the worktree field.

        Tasks are sorted by priority (high=1, normal=2, low=3) then by creation date.
        Only tasks with status='open' and completed prerequisites are eligible.

        Args:
            projectRoot: Root directory for the planning structure
            worktree: Optional worktree identifier to stamp on the claimed task

        Returns:
            Dictionary containing the claimed task data and file path, or error info

        Raises:
            TrellisValidationError: If no eligible tasks are available
            OSError: If file operations fail
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # Call the core claim_next_task function
        try:
            claimed_task = claim_next_task(projectRoot, worktree)
        except NoAvailableTask as e:
            raise TrellisValidationError([str(e)])
        except Exception as e:
            raise TrellisValidationError([f"Failed to claim task: {str(e)}"])

        # Convert TaskModel to the expected dictionary format
        _, planning_root = resolve_project_roots(projectRoot)
        task_file_path = id_to_path(planning_root, "task", claimed_task.id)

        # Build task dictionary in the format expected by the API
        task_dict = {
            "id": claimed_task.id,
            "title": claimed_task.title,
            "status": claimed_task.status.value,
            "priority": str(claimed_task.priority),
            "parent": claimed_task.parent or "",
            "file_path": str(task_file_path),
            "created": claimed_task.created.isoformat(),
            "updated": claimed_task.updated.isoformat(),
        }

        # Return the claimed task info in the expected format
        return {
            "task": task_dict,
            "claimed_status": "in-progress",
            "worktree": worktree if worktree is not None else "",
            "file_path": str(task_file_path),
        }

    return claimNextTask
