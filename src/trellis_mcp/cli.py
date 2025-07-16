"""Trellis MCP Server CLI.

Main command-line interface for the Trellis MCP server using Click.
Provides the foundation command group for all CLI operations.
"""

import json
from pathlib import Path

import click

from .complete_task import complete_task
from .filters import apply_filters, filter_by_scope
from .loader import ConfigLoader
from .models.filter_params import FilterParams
from .models.task_sort_key import task_sort_key
from .path_resolver import children_of, id_to_path, resolve_project_roots
from .prune_logs import prune_logs
from .scanner import scan_tasks
from .server import create_server


@click.group(
    name="trellis-mcp",
    help="Trellis MCP Server - File-backed project management for development agents",
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 100,
    },
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, readable=True),
    help="Path to configuration file (YAML or TOML)",
)
@click.option(
    "--debug/--no-debug",
    default=None,
    help="Enable debug mode with verbose logging",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    help="Set logging level",
)
@click.pass_context
def cli(ctx: click.Context, config: str | None, debug: bool | None, log_level: str | None) -> None:
    """Trellis MCP Server command-line interface.

    A file-backed MCP server implementing the Trellis MCP v1.0 specification
    for hierarchical project management (Projects → Epics → Features → Tasks).

    Configuration is loaded hierarchically: defaults → file → env → CLI flags.
    Use environment variables with MCP_ prefix to override settings.
    """
    # Ensure context object exists for subcommands
    ctx.ensure_object(dict)

    # Load configuration with hierarchical precedence
    config_loader = ConfigLoader()

    # Build CLI overrides for settings
    cli_overrides = {}
    if debug is not None:
        cli_overrides["debug_mode"] = debug
    if log_level is not None:
        cli_overrides["log_level"] = log_level.upper()

    # Load settings with configuration file and CLI overrides
    try:
        settings = config_loader.load_settings(config_file=config, **cli_overrides)
    except Exception as e:
        raise click.ClickException(f"Configuration error: {e}")

    # Store settings in context for subcommands
    ctx.obj["settings"] = settings

    # Enable debug mode if requested
    if settings.debug_mode:
        ctx.obj["debug"] = True


@cli.command()
@click.option(
    "--http",
    metavar="HOST:PORT",
    help="Enable HTTP transport with specified host and port (e.g., --http 127.0.0.1:8080)",
)
@click.pass_context
def serve(ctx: click.Context, http: str | None) -> None:
    """Start the Trellis MCP server.

    Starts the FastMCP server using STDIO transport by default, or HTTP transport
    if the --http flag is provided. The server provides hierarchical project management
    tools and resources according to the Trellis MCP v1.0 specification.

    Configuration is loaded from the main command's settings, including server name,
    transport options, and planning directory structure.
    """
    settings = ctx.obj["settings"]

    # Parse HTTP transport option if provided
    host, port = None, None
    if http:
        try:
            if ":" not in http:
                raise click.ClickException(
                    "HTTP option must be in HOST:PORT format (e.g., 127.0.0.1:8080)"
                )

            host_str, port_str = http.rsplit(":", 1)
            host = host_str.strip()
            port = int(port_str.strip())

            if not host:
                raise click.ClickException("Host cannot be empty")
            if not (1024 <= port <= 65535):
                raise click.ClickException("Port must be between 1024 and 65535")

        except ValueError:
            raise click.ClickException("Port must be a valid integer")

    try:
        # Create server instance with current settings
        server = create_server(settings)

        # Determine transport and print startup information
        if http:
            click.echo("Starting Trellis MCP Server...")
            click.echo("Transport: HTTP")
            click.echo(f"Host: {host}")
            click.echo(f"Port: {port}")
            click.echo(f"Planning root: {settings.planning_root}")
            click.echo(f"Log level: {settings.log_level}")

            if settings.debug_mode:
                click.echo("Debug mode: enabled")

            # Start server with HTTP transport
            server.run(transport="http", host=host, port=port)
        else:
            click.echo("Starting Trellis MCP Server...")
            click.echo("Transport: STDIO")
            click.echo(f"Planning root: {settings.planning_root}")
            click.echo(f"Log level: {settings.log_level}")

            if settings.debug_mode:
                click.echo("Debug mode: enabled")

            # Start server with STDIO transport (default)
            server.run(transport="stdio")

    except KeyboardInterrupt:
        click.echo("\nServer stopped by user")
    except Exception as e:
        if settings.debug_mode:
            raise
        raise click.ClickException(f"Server startup failed: {e}")


@cli.command()
@click.argument("path", type=click.Path(), required=False)
@click.pass_context
def init(ctx: click.Context, path: str | None) -> None:
    """Initialize a new Trellis planning directory structure.

    Creates the minimal directory structure required for Trellis MCP:
    planning/projects/

    PATH is optional and defaults to the current working directory.
    If PATH is provided, the planning structure will be created within that directory.

    Examples:
      trellis-mcp init              # Creates ./planning/projects/
      trellis-mcp init /path/to/my-project  # Creates /path/to/my-project/planning/projects/
    """
    settings = ctx.obj["settings"]

    # Determine the target directory
    if path:
        target_dir = Path(path).resolve()
    else:
        target_dir = Path.cwd()

    # Validate target directory
    if not target_dir.exists():
        raise click.ClickException(f"Target directory does not exist: {target_dir}")

    if not target_dir.is_dir():
        raise click.ClickException(f"Target path is not a directory: {target_dir}")

    # Create planning directory structure
    planning_dir = target_dir / settings.planning_root.name
    projects_dir = planning_dir / settings.projects_dir

    try:
        # Create directories with parents=True to handle intermediate directories
        projects_dir.mkdir(parents=True, exist_ok=True)

        # Provide user feedback
        click.echo(f"✓ Initialized Trellis planning structure in: {target_dir}")
        click.echo(f"  Created: {planning_dir.relative_to(target_dir)}/")
        click.echo(f"  Created: {projects_dir.relative_to(target_dir)}/")

        if settings.debug_mode:
            click.echo(f"Debug: Full planning path: {planning_dir}")
            click.echo(f"Debug: Full projects path: {projects_dir}")

    except PermissionError:
        raise click.ClickException(f"Permission denied: Cannot create directories in {target_dir}")
    except OSError as e:
        raise click.ClickException(f"Failed to create directory structure: {e}")


@cli.command()
@click.argument("task_id", type=str)
@click.option("--summary", "-s", type=str, help="Summary text for the log entry")
@click.option(
    "--files", "-f", multiple=True, help="File paths that were changed (can be used multiple times)"
)
@click.pass_context
def complete(ctx: click.Context, task_id: str, summary: str | None, files: tuple[str, ...]) -> None:
    """Complete a task that is in in-progress or review status.

    TASK_ID: ID of the task to complete (with or without T- prefix)

    Examples:
      trellis-mcp complete T-001 --summary "Fixed authentication bug"
      trellis-mcp complete 001 --summary "Added feature" --files src/auth.py \\
                                                          --files tests/test_auth.py
    """
    settings = ctx.obj["settings"]

    # Convert tuple to list for files_changed parameter
    files_changed = list(files) if files else []

    try:
        completed_task = complete_task(
            project_root=settings.planning_root,
            task_id=task_id,
            summary=summary or "",
            files_changed=files_changed,
        )

        click.echo(f"✓ Completed task: {completed_task.title}")
        click.echo(f"  Task ID: {completed_task.id}")
        click.echo(f"  Status: {completed_task.status.value}")

        if summary:
            click.echo(f"  Summary: {summary}")
        if files_changed:
            click.echo(f"  Files changed: {', '.join(files_changed)}")

    except Exception as e:
        if settings.debug_mode:
            raise
        raise click.ClickException(f"Failed to complete task: {e}")


@cli.command()
@click.option("--scope", type=str, help="Filter by scope ID (project/epic/feature)")
@click.option(
    "--status",
    type=click.Choice(["open", "in-progress", "review", "done"], case_sensitive=False),
    help="Filter by task status",
)
@click.option(
    "--priority",
    type=click.Choice(["high", "normal", "low"], case_sensitive=False),
    help="Filter by task priority",
)
@click.pass_context
def backlog(
    ctx: click.Context, scope: str | None, status: str | None, priority: str | None
) -> None:
    """List tasks from the backlog with optional filtering.

    Lists all tasks in the project hierarchy with optional filtering by scope,
    status, and priority. Output is JSON formatted for easy processing.

    Examples:
      trellis-mcp backlog                        # List all open tasks
      trellis-mcp backlog --scope F-001          # Tasks in feature F-001
      trellis-mcp backlog --status open          # Only open tasks
      trellis-mcp backlog --priority high        # Only high priority tasks
      trellis-mcp backlog --status review --priority high  # Combined filters
    """
    settings = ctx.obj["settings"]

    try:
        # Resolve project roots using centralized utility
        scanning_root, path_resolution_root = resolve_project_roots(settings.planning_root)

        # Create FilterParams from individual parameters, handling validation gracefully
        try:
            # Default to "open" tasks when no status filter is specified
            filter_status = [status] if status else ["open"]
            filter_priority = [priority] if priority else []
            filter_params = FilterParams(status=filter_status, priority=filter_priority)
        except Exception:
            # If validation fails (e.g., invalid status/priority), return empty results
            result = {"tasks": []}
            click.echo(json.dumps(result, indent=2))
            return

        # Get tasks using modular components
        if scope:
            # Use scope filtering if provided
            tasks_iterator = filter_by_scope(scanning_root, scope)
        else:
            # Use scanner to get all tasks
            tasks_iterator = scan_tasks(scanning_root)

        # Apply status and priority filters
        filtered_tasks = apply_filters(tasks_iterator, filter_params)

        # Convert to list and sort by priority
        tasks_list = list(filtered_tasks)
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

        result = {"tasks": result_tasks}
        click.echo(json.dumps(result, indent=2))

    except Exception as e:
        if settings.debug_mode:
            raise
        raise click.ClickException(f"Failed to list backlog: {e}")


@cli.command()
@click.argument(
    "kind", type=click.Choice(["project", "epic", "feature", "task"], case_sensitive=False)
)
@click.argument("object_id", type=str)
@click.option(
    "--force",
    is_flag=True,
    help="Force deletion even if object has protected children (tasks in in-progress or review)",
)
@click.pass_context
def delete(ctx: click.Context, kind: str, object_id: str, force: bool) -> None:
    """Delete a project, epic, feature, or task.

    Deletes the specified object and all its children. By default, deletion is
    blocked if the object has any child tasks with status 'in-progress' or 'review'.
    Use --force to override this safety check.

    KIND: Type of object to delete (project, epic, feature, task)
    OBJECT_ID: ID of the object to delete (with or without prefix)

    Examples:
      trellis-mcp delete project P-001
      trellis-mcp delete epic E-001 --force
      trellis-mcp delete feature F-001
      trellis-mcp delete task T-001
    """
    settings = ctx.obj["settings"]

    try:
        # Create server instance to access the updateObject tool
        server = create_server(settings)

        # Clean the object ID (remove prefix if present)
        clean_id = object_id.strip()
        if clean_id.startswith(("P-", "E-", "F-", "T-")):
            clean_id = clean_id[2:]

        # Get descendants to show count in confirmation
        try:
            child_paths = children_of(kind.lower(), clean_id, settings.planning_root)
            descendant_count = len(child_paths)
        except Exception:
            # If we can't get descendants, assume 0 (object might not exist yet)
            descendant_count = 0

        # Show confirmation prompt
        if descendant_count > 0:
            confirmation_msg = (
                f"⚠️  Delete {kind.capitalize()} {object_id} and "
                f"{descendant_count} descendants? [y/N]"
            )
        else:
            confirmation_msg = f"⚠️  Delete {kind.capitalize()} {object_id}? [y/N]"

        click.confirm(confirmation_msg, abort=True)

        # Call the updateObject tool through the client
        import asyncio

        from fastmcp import Client

        async def delete_object():
            async with Client(server) as client:
                result = await client.call_tool(
                    "updateObject",
                    {
                        "kind": kind.lower(),
                        "id": object_id,
                        "projectRoot": str(settings.planning_root),
                        "yamlPatch": {"status": "deleted"},
                        "force": force,
                    },
                )
                return result.data

        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a running loop, create a task and wait for it
            task = asyncio.create_task(delete_object())
            # This will run in the existing event loop
            result = loop.run_until_complete(task)
        except RuntimeError:
            # No running loop, use asyncio.run()
            result = asyncio.run(delete_object())

        # Extract cascade_deleted from result if it exists
        cascade_deleted = result.get("changes", {}).get("cascade_deleted", [])

        click.echo(f"✓ Deleted {kind} {object_id}")

        if cascade_deleted:
            click.echo(f"  Cascade deleted {len(cascade_deleted)} items:")
            for path in cascade_deleted:
                click.echo(f"    - {path}")

        if force:
            click.echo("  Used --force to override protected children")

    except click.Abort:
        # User cancelled the confirmation, exit gracefully
        return
    except Exception as e:
        if settings.debug_mode:
            raise
        raise click.ClickException(f"Failed to delete {kind} {object_id}: {e}")


@cli.command("prune-logs")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show which files would be removed without actually deleting them",
)
@click.option(
    "--retention-days",
    type=int,
    help="Override the configured retention period (must be > 0)",
)
@click.pass_context
def prune_logs_command(ctx: click.Context, dry_run: bool, retention_days: int | None) -> None:
    """Remove old log files based on retention policy.

    Scans the log directory for daily log files matching the pattern YYYY-MM-DD.log
    and removes those older than the configured retention period. Uses the configured
    log_retention_days setting by default, or the --retention-days override.

    The retention window is calculated from the current date minus retention_days.
    Only files matching the exact pattern YYYY-MM-DD.log are considered for removal.

    Examples:
      trellis-mcp prune-logs                        # Remove old files using configured retention
      trellis-mcp prune-logs --dry-run              # Show which files would be removed
      trellis-mcp prune-logs --retention-days 7     # Use 7-day retention instead of configured
      trellis-mcp prune-logs --dry-run --retention-days 14  # Preview with 14-day retention
    """
    settings = ctx.obj["settings"]

    # Override retention_days if provided
    if retention_days is not None:
        if retention_days <= 0:
            raise click.ClickException("Retention days must be greater than 0")

        # Create a new Settings instance with the override
        from .settings import Settings

        # Get all current settings as a dict and override log_retention_days
        settings_dict = settings.model_dump()
        settings_dict["log_retention_days"] = retention_days
        settings = Settings(**settings_dict)

    try:
        if dry_run:
            # Use the centralized prune_logs function with dry_run=True
            files_to_remove = prune_logs(settings, dry_run=True)

            # Type narrowing: we know dry_run=True returns list[Path]
            assert isinstance(files_to_remove, list), "dry_run=True should return list[Path]"

            # Show results
            click.echo(f"Using retention period: {settings.log_retention_days} days")
            click.echo(f"Log directory: {settings.log_dir}")
            click.echo(f"Files that would be removed: {len(files_to_remove)}")

            if files_to_remove:
                click.echo("Files to remove:")
                for file_path in sorted(files_to_remove):
                    click.echo(f"  - {file_path.name}")
            else:
                click.echo("No files match the removal criteria")

        else:
            # Actual pruning
            removed_count = prune_logs(settings, dry_run=False)

            click.echo("✓ Log pruning completed")
            click.echo(f"Files removed: {removed_count}")

            if settings.debug_mode:
                click.echo(f"Debug: Log directory: {settings.log_dir}")
                click.echo(f"Debug: Retention period: {settings.log_retention_days} days")

    except ValueError as e:
        raise click.ClickException(f"Configuration error: {e}")
    except OSError as e:
        raise click.ClickException(f"File system error: {e}")
    except Exception as e:
        if settings.debug_mode:
            raise
        raise click.ClickException(f"Failed to prune logs: {e}")
