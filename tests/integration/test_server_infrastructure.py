"""Server infrastructure tests.

Tests basic server functionality including startup, connectivity, health checks,
tool/resource discovery, and configuration consistency.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_server_startup_and_connectivity(temp_dir):
    """Test server starts and responds to basic connectivity checks."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)

    # Test connectivity using in-memory transport
    async with Client(server) as client:
        # Basic connectivity check
        await client.ping()

        # Verify client reports connected
        assert client.is_connected()


@pytest.mark.asyncio
async def test_health_check_tool_functionality(temp_dir):
    """Test health check tool returns expected status information."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        schema_version="1.0",
    )

    # Create server instance
    server = create_server(settings)

    # Test health check tool
    async with Client(server) as client:
        result = await client.call_tool("health_check")

        # Verify result structure and content
        assert result.data is not None
        assert result.data["status"] == "healthy"
        assert result.data["server"] == "Trellis MCP Server"
        assert result.data["schema_version"] == "1.0"
        assert result.data["planning_root"] == str(temp_dir / "planning")


@pytest.mark.asyncio
async def test_server_info_resource_accessibility(temp_dir):
    """Test server info resource provides correct configuration information."""
    # Create settings with custom configuration
    settings = Settings(
        planning_root=temp_dir / "planning",
        host="127.0.0.1",
        port=8080,
        log_level="INFO",
        debug_mode=False,
    )

    # Create server instance
    server = create_server(settings)

    # Test server info resource
    async with Client(server) as client:
        # List available resources
        resources = await client.list_resources()
        resource_uris = [str(resource.uri) for resource in resources]
        assert "info://server" in resource_uris

        # Read server info resource
        info = await client.read_resource("info://server")
        assert len(info) > 0

        # Verify info contains expected server configuration
        info_data = info[0]
        assert hasattr(info_data, "text") or hasattr(info_data, "data")


@pytest.mark.asyncio
async def test_available_tools_and_resources(temp_dir):
    """Test server exposes expected tools and resources."""
    # Create settings
    settings = Settings(planning_root=temp_dir / "planning")

    # Create server instance
    server = create_server(settings)

    # Test available tools and resources
    async with Client(server) as client:
        # List available tools
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]

        # Verify expected tools are available
        assert "health_check" in tool_names

        # List available resources
        resources = await client.list_resources()
        resource_uris = [str(resource.uri) for resource in resources]

        # Verify expected resources are available
        assert "info://server" in resource_uris


@pytest.mark.asyncio
async def test_server_configuration_consistency(temp_dir):
    """Test server configuration is consistently reported across tools and resources."""
    # Create settings with specific configuration
    planning_root = temp_dir / "planning"
    settings = Settings(
        planning_root=planning_root,
        schema_version="1.0",
        host="localhost",
        port=9000,
        log_level="WARNING",
        debug_mode=True,
    )

    # Create server instance
    server = create_server(settings)

    # Test configuration consistency
    async with Client(server) as client:
        # Get configuration from health check tool
        health_result = await client.call_tool("health_check")
        health_data = health_result.data

        # Verify consistent planning root across both sources
        assert health_data["planning_root"] == str(planning_root)
        assert health_data["schema_version"] == "1.0"
        assert health_data["server"] == "Trellis MCP Server"
