"""List backlog tool for Trellis MCP server.

Lists tasks filtered by scope, status, and priority using modular task scanner,
filters, and sorting components to efficiently find and filter tasks across
the entire project hierarchy.
"""

from fastmcp import FastMCP

from ..filters import apply_filters, filter_by_scope
from ..models.filter_params import FilterParams
from ..models.task_sort_key import task_sort_key
from ..path_resolver import id_to_path, resolve_project_roots
from ..scanner import scan_tasks
from ..settings import Settings


def create_list_backlog_tool(settings: Settings):
    """Create a listBacklog tool configured with the provided settings.

    Args:
        settings: Server configuration settings

    Returns:
        Configured listBacklog tool function
    """
    mcp = FastMCP()

    @mcp.tool
    def listBacklog(
        projectRoot: str,
        scope: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        sortByPriority: bool = True,
    ):
        """List tasks filtered by scope, status, and priority.

        Uses the modular task scanner, filters, and sorting components to efficiently
        find and filter tasks across the entire project hierarchy.

        Args:
            projectRoot: Root directory for the planning structure
            scope: Optional scope ID to filter tasks by parent (project/epic/feature ID)
            status: Optional status filter ('open', 'in-progress', 'review', 'done')
            priority: Optional priority filter ('high', 'normal', 'low')
            sortByPriority: Whether to sort tasks by priority and creation date (default: True)

        Returns:
            Dictionary with structure:
            {
                "tasks": [
                    {
                        "id": str,           # Clean task ID
                        "title": str,        # Task title
                        "status": str,       # Task status
                        "priority": str,     # Task priority
                        "parent": str,       # Parent feature ID
                        "file_path": str,    # Path to task file
                        "created": str,      # Creation timestamp
                        "updated": str,      # Last update timestamp
                    },
                    ...
                ]
            }

        Raises:
            ValueError: If projectRoot is empty or invalid
            OSError: If there are file system access issues
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # Resolve project roots using centralized utility
        scanning_root, path_resolution_root = resolve_project_roots(projectRoot)

        # Create FilterParams from individual parameters, handling validation gracefully
        try:
            filter_status = [status] if status else []
            filter_priority = [priority] if priority else []
            filter_params = FilterParams(status=filter_status, priority=filter_priority)
        except Exception:
            # If validation fails (e.g., invalid status/priority), return empty results
            return {"tasks": []}

        # Get tasks using modular components
        if scope:
            # Use scope filtering if provided
            tasks_iterator = filter_by_scope(scanning_root, scope)
        else:
            # Use scanner to get all tasks
            tasks_iterator = scan_tasks(scanning_root)

        # Apply status and priority filters
        filtered_tasks = apply_filters(tasks_iterator, filter_params)

        # Convert to list and sort if requested
        tasks_list = list(filtered_tasks)
        if sortByPriority:
            tasks_list.sort(key=task_sort_key)

        # Convert TaskModel objects to JSON-serializable format
        result_tasks = []
        for task in tasks_list:
            try:
                # Resolve file path - use path_resolution_root for path resolution
                task_file_path = id_to_path(path_resolution_root, "task", task.id)

                task_data = {
                    "id": f"T-{task.id}" if not task.id.startswith("T-") else task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": str(task.priority),
                    "parent": task.parent or "",
                    "file_path": str(task_file_path),
                    "created": task.created.isoformat(),
                    "updated": task.updated.isoformat(),
                }
                result_tasks.append(task_data)
            except Exception:
                # Skip tasks that can't be processed
                continue

        return {"tasks": result_tasks}

    return listBacklog
