"""Trellis MCP Server CLI.

Main command-line interface for the Trellis MCP server using Click.
Provides the foundation command group for all CLI operations.
"""

from pathlib import Path

import click

from .loader import ConfigLoader
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
