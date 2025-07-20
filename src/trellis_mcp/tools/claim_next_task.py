"""Claim next task tool for Trellis MCP server.

Provides functionality to claim the next highest-priority open task with all
prerequisites completed, setting its status to in-progress.
"""

from fastmcp import FastMCP

from ..claim_next_task import claim_next_task
from ..exceptions.no_available_task import NoAvailableTask
from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..path_resolver import id_to_path, resolve_project_roots
from ..settings import Settings


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
        worktree: str = "",
        scope: str = "",
    ) -> dict[str, str | dict[str, str]]:
        """Claim the next highest-priority open task with all prerequisites completed.

        Atomically selects the highest-priority open task (where all prerequisites
        have status='done'), sets its status to 'in-progress', and optionally
        stamps the worktree field.

        Supports cross-system prerequisite validation, checking prerequisites across
        both hierarchical tasks (within project/epic/feature structure) and standalone
        tasks. Only tasks with all cross-system prerequisites completed are eligible
        for claiming. Performance is optimized with multi-layer caching for efficient
        cross-system validation (typically 1-5ms warm, 50-200ms cold).

        Tasks are sorted by priority (high=1, normal=2, low=3) then by creation date.
        Only tasks with status='open' and completed prerequisites are eligible.

        Args:
            projectRoot: Root directory for the planning structure
            worktree: Optional worktree identifier to stamp on the claimed task
            scope: Optional scope ID to filter tasks by parent (project/epic/feature ID).
                Supports cross-system scoping - can filter by hierarchical parents or
                show standalone tasks by omitting scope filter.

        Returns:
            Dictionary containing the claimed task data and file path, or error info.
            The returned task may have a mix of hierarchical and standalone prerequisites.

        Raises:
            ValidationError: If cross-system prerequisite validation fails, including:
                - CROSS_SYSTEM_PREREQUISITE_INVALID: Task has prerequisites that don't exist
                  in either hierarchical or standalone task systems
                - INVALID_FIELD: No eligible tasks available (all have incomplete prerequisites
                  or none exist in the cross-system task discovery)
            TrellisValidationError: If no eligible tasks are available
            OSError: If file operations fail
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValidationError(
                errors=["Project root cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "projectRoot"},
            )

        # Validate scope parameter format if provided
        scope_param = None
        if scope and scope.strip():
            from ..models.filter_params import FilterParams

            try:
                # Use FilterParams for consistent scope validation
                filter_params = FilterParams(scope=scope.strip())
                # Use the validated scope value from FilterParams
                scope_param = filter_params.scope
            except Exception as e:
                raise ValidationError(
                    errors=[f"Invalid scope parameter: {str(e)}"],
                    error_codes=[ValidationErrorCode.INVALID_FIELD],
                    context={"field": "scope", "value": scope},
                ) from e

        # Call the core claim_next_task function with validated scope parameter
        try:
            claimed_task = claim_next_task(projectRoot, worktree, scope_param)
        except NoAvailableTask as e:
            raise ValidationError(
                errors=[str(e)],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "task_availability", "kind": "task"},
                object_kind="task",
            )
        except Exception as e:
            raise ValidationError(
                errors=[f"Failed to claim task: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "task_claiming", "kind": "task"},
                object_kind="task",
            )

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
            "worktree": worktree,
            "file_path": str(task_file_path),
        }

    return claimNextTask
