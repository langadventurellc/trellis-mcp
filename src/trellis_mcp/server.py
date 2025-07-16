"""Trellis MCP Server Factory.

Creates and configures the FastMCP server instance for the Trellis MCP application.
Provides server setup with basic tools and resources for project management.
"""

from fastmcp import FastMCP

from .json_rpc_logging_middleware import JsonRpcLoggingMiddleware
from .logger import write_event
from .prune_logs import prune_logs
from .settings import Settings
from .tools.claim_next_task import create_claim_next_task_tool
from .tools.complete_task import create_complete_task_tool
from .tools.create_object import create_create_object_tool
from .tools.get_next_reviewable_task import create_get_next_reviewable_task_tool
from .tools.get_object import create_get_object_tool
from .tools.health_check import create_health_check_tool
from .tools.list_backlog import create_list_backlog_tool
from .tools.update_object import create_update_object_tool


def create_server(settings: Settings) -> FastMCP:
    """Create and configure a FastMCP server instance.

    Creates a Trellis MCP server with basic tools and resources for hierarchical
    project management. Server is configured using the provided settings.

    Args:
        settings: Configuration settings for server setup

    Returns:
        Configured FastMCP server instance ready to run
    """
    # Create server with descriptive name and instructions
    server = FastMCP(
        name="Trellis MCP Server",
        instructions="""
        This is the Trellis MCP Server implementing the Trellis MCP v1.0 specification.
        It provides file-backed hierarchical project management with the structure:
        Projects → Epics → Features → Tasks

        The server manages planning data stored as Markdown files with YAML front-matter
        in a nested directory structure under the planning root directory.
        """,
    )

    # Create and register health check tool
    health_check = create_health_check_tool(settings)
    server.add_tool(health_check)

    # Create and register createObject tool
    create_object = create_create_object_tool(settings)
    server.add_tool(create_object)

    # Create and register getObject tool
    get_object = create_get_object_tool(settings)
    server.add_tool(get_object)

    # Create and register updateObject tool
    update_object = create_update_object_tool(settings)
    server.add_tool(update_object)

    # Create and register listBacklog tool
    list_backlog = create_list_backlog_tool(settings)
    server.add_tool(list_backlog)

    # Create and register claimNextTask tool
    claim_next_task_tool = create_claim_next_task_tool(settings)
    server.add_tool(claim_next_task_tool)

    # Create and register completeTask tool
    complete_task_tool = create_complete_task_tool(settings)
    server.add_tool(complete_task_tool)

    # Create and register getNextReviewableTask tool
    get_next_reviewable_task_tool = create_get_next_reviewable_task_tool(settings)
    server.add_tool(get_next_reviewable_task_tool)

    @server.resource("info://server")
    def server_info() -> dict[str, str | int | bool]:
        """Provide server configuration and runtime information.

        Returns current server configuration including transport settings,
        directory structure, and operational parameters.
        """
        return {
            "name": "Trellis MCP Server",
            "version": settings.schema_version,
            "host": settings.host,
            "port": settings.port,
            "log_level": settings.log_level,
            "planning_root": str(settings.planning_root),
            "debug_mode": settings.debug_mode,
            "auto_create_dirs": settings.auto_create_dirs,
        }

    # Register JSON-RPC logging middleware
    server.add_middleware(JsonRpcLoggingMiddleware(settings))

    # Prune old log files at startup if retention is configured
    if settings.log_retention_days > 0:
        try:
            prune_logs(settings)
        except Exception as e:
            # Log the error but don't prevent server startup
            write_event(
                "ERROR", "Log pruning failed during startup", settings=settings, error=str(e)
            )

    return server
