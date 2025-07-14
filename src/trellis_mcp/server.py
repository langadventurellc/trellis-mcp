"""Trellis MCP Server Factory.

Creates and configures the FastMCP server instance for the Trellis MCP application.
Provides server setup with basic tools and resources for project management.
"""

from __future__ import annotations

from fastmcp import FastMCP

from .settings import Settings


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

    @server.tool
    def health_check() -> dict[str, str]:
        """Check server health and return status information.

        Returns basic server health information including server name,
        schema version, and planning root directory.
        """
        return {
            "status": "healthy",
            "server": "Trellis MCP Server",
            "schema_version": settings.schema_version,
            "planning_root": str(settings.planning_root),
        }

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

    return server
