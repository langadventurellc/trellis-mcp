"""Health check tool for Trellis MCP server.

Provides server health status and basic information including server name,
schema version, and planning root directory.
"""

from fastmcp import FastMCP

from ..settings import Settings


def create_health_check_tool(settings: Settings):
    """Create a health check tool configured with the provided settings.

    Args:
        settings: Server configuration settings

    Returns:
        Configured health check tool function
    """
    mcp = FastMCP()

    @mcp.tool
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

    return health_check
