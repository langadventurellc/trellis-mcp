"""Claim next task tool for Trellis MCP server.

Provides functionality to claim the next highest-priority open task with all
prerequisites completed, setting its status to in-progress.
"""

from fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError

from ..claim_next_task import claim_next_task
from ..exceptions.no_available_task import NoAvailableTask
from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..models.claiming_params import ClaimingParams
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
        taskId: str = "",
        force_claim: bool = False,
    ) -> dict[str, str | dict[str, str]]:
        """Claim the next highest-priority open task with all prerequisites completed.

        Enhanced with scope-based task filtering to limit claiming to specific hierarchical
        boundaries and direct task claiming by ID. Atomically selects the highest-priority
        open task (where all prerequisites have status='done'), sets its status to 'in-progress',
        and optionally stamps the worktree field.

        When taskId is provided, claims the specific task directly, bypassing priority-based
        selection.

        Supports cross-system prerequisite validation, checking prerequisites across
        both hierarchical tasks (within project/epic/feature structure) and standalone
        tasks. Only tasks with all cross-system prerequisites completed are eligible
        for claiming. Performance is optimized with multi-layer caching for efficient
        cross-system validation (typically 1-5ms warm, 50-200ms cold).

        Tasks are sorted by priority (high=1, normal=2, low=3) then by creation date.
        Only tasks with status='open' and completed prerequisites are eligible.

        Scope-Based Task Filtering:
        The scope parameter enables focused task claiming within specific project boundaries:

        - Project scope (P-*): Claims tasks from entire project hierarchy plus standalone tasks
        - Epic scope (E-*): Claims tasks only from epic and its features (excludes standalone)
        - Feature scope (F-*): Claims tasks only from specific feature (excludes standalone)
        - No scope: Claims highest priority task from anywhere (default behavior)

        Args:
            projectRoot: Root directory for the planning structure
            worktree: Optional worktree identifier to stamp on the claimed task
            scope: Optional hierarchical scope for task filtering. Format requirements:
                - P-<project-id>: Claim tasks within entire project (includes standalone tasks)
                - E-<epic-id>: Claim tasks within epic and its features (hierarchical only)
                - F-<feature-id>: Claim tasks only within specific feature (hierarchical only)
                - Empty/omitted: No scope filtering (existing behavior preserved)
            taskId: Optional task ID to claim directly (T- prefixed or standalone format).
                If provided, claims specific task instead of priority-based selection.
                Empty/omitted: Uses priority-based selection (existing behavior preserved)
            force_claim: Optional boolean to bypass normal claiming restrictions.
                When True, allows claiming tasks that would normally be blocked by incomplete
                prerequisites or non-open status. IMPORTANT: Only valid when taskId is specified.
                Incompatible with scope parameter. Default: False (maintains standard
                claiming behavior)

        Usage Examples:
            # Claim any available task (no scope filtering)
            claimNextTask(projectRoot="/path/to/planning")

            # Claim task within specific project scope
            claimNextTask(projectRoot="/path/to/planning", scope="P-ecommerce-platform")

            # Claim task within specific epic scope
            claimNextTask(projectRoot="/path/to/planning", scope="E-user-authentication")

            # Claim task within specific feature scope
            claimNextTask(projectRoot="/path/to/planning", scope="F-login-functionality")

            # Claim task with worktree assignment
            claimNextTask(
                projectRoot="/path/to/planning",
                scope="F-user-auth",
                worktree="feature/auth"
            )

            # Force claim specific task (bypasses normal restrictions)
            claimNextTask(
                projectRoot="/path/to/planning",
                taskId="T-urgent-fix",
                force_claim=True
            )

            # Force claim with worktree (emergency reassignment)
            claimNextTask(
                projectRoot="/path/to/planning",
                taskId="T-critical-bug",
                worktree="hotfix/critical",
                force_claim=True
            )

        Scope Boundary Behavior:
            - Project scope: Includes all child epics, features, tasks AND standalone tasks
            - Epic scope: Includes all child features and tasks (NO standalone tasks)
            - Feature scope: Includes only direct child tasks (NO standalone tasks)
            - Cross-system compatibility: Scope filtering works with mixed hierarchical and
              standalone environments

        Error Scenarios:
            - Invalid scope format: Must use P-, E-, or F- prefix with valid ID characters
            - Scope object not found: Specified scope ID doesn't exist in planning structure
            - No eligible tasks in scope: Scope contains no open tasks with completed prerequisites
            - Concurrent claiming: Task already claimed by another process

        Returns:
            Dictionary containing the claimed task data and file path:
            {
                "task": {
                    "id": str,           # Clean task ID
                    "title": str,        # Task title
                    "status": "in-progress",  # Always in-progress after claiming
                    "priority": str,     # Task priority level
                    "parent": str | None,     # Parent feature ID (None for standalone)
                    "file_path": str,    # Path to task markdown file
                    "created": str,      # ISO timestamp
                    "updated": str       # ISO timestamp
                },
                "claimed_status": "in-progress",
                "worktree": str,         # Worktree identifier if provided
                "file_path": str         # Path to claimed task file
            }

        Raises:
            ValidationError: If validation fails, including:
                - MISSING_REQUIRED_FIELD: Empty projectRoot parameter
                - INVALID_FIELD: Invalid scope format (must be P-, E-, or F- prefixed)
                - INVALID_FIELD: Scope object not found in planning structure
                - INVALID_FIELD: No eligible tasks available within scope boundaries
                - CROSS_SYSTEM_PREREQUISITE_INVALID: Task has invalid cross-system prerequisites
            TrellisValidationError: If no eligible tasks are available
            OSError: If file operations fail during claiming process

        Performance Considerations:
            - Scope filtering reduces task discovery overhead for large project hierarchies
            - Cross-system validation cached for 1-5ms response times (warm cache)
            - Project scope most efficient for mixed hierarchical/standalone environments
            - Feature scope most efficient for focused development work
        """
        # Validate parameters using ClaimingParams model
        try:
            claiming_params = ClaimingParams(
                project_root=projectRoot,
                worktree=worktree,
                scope=scope,
                task_id=taskId,
                force_claim=force_claim,
            )
        except PydanticValidationError as e:
            # Convert Pydantic validation errors to ValidationError format
            error_messages = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_msg = error["msg"]
                error_messages.append(f"{field_path}: {error_msg}")

            raise ValidationError(
                errors=error_messages,
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={
                    "validation_type": "parameter_validation",
                    "fields": [str(loc) for error in e.errors() for loc in error["loc"]],
                    "raw_errors": str(e),
                },
            ) from e

        # Call the core claim_next_task function with validated parameters
        try:
            # Pass validated parameters from ClaimingParams to core function
            claimed_task = claim_next_task(
                claiming_params.project_root,
                claiming_params.worktree,
                claiming_params.scope,
                claiming_params.task_id,
                claiming_params.force_claim,
            )
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
        _, planning_root = resolve_project_roots(projectRoot, ensure_planning_subdir=True)
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
