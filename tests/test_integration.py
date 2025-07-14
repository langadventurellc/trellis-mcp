"""Integration tests for Trellis MCP server.

Tests the complete server functionality by starting a FastMCP server
and hitting it with a FastMCP test client to verify end-to-end behavior.
"""

from __future__ import annotations

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


@pytest.mark.asyncio
async def test_concurrent_client_connections(temp_dir):
    """Test server handles multiple concurrent client connections."""
    import asyncio

    # Create settings
    settings = Settings(planning_root=temp_dir / "planning")

    # Create server instance
    server = create_server(settings)

    async def client_task():
        """Single client task for concurrent testing."""
        async with Client(server) as client:
            await client.ping()
            result = await client.call_tool("health_check")
            return result.data["status"]

    # Create multiple concurrent client connections
    tasks = [client_task() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # Verify all connections succeeded
    assert all(status == "healthy" for status in results)
    assert len(results) == 5


@pytest.mark.asyncio
async def test_create_duplicate_title_tasks_generates_unique_ids(temp_dir):
    """Test creating two tasks with identical titles generates unique IDs and correct paths."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)

    async with Client(server) as client:
        # First, create the project hierarchy: project → epic → feature

        # Create project
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Test Project",
                "projectRoot": str(temp_dir / "planning"),
            },
        )
        project_id = project_result.data["id"]

        # Create epic under project
        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Test Epic",
                "projectRoot": str(temp_dir / "planning"),
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        # Create feature under epic
        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Test Feature",
                "projectRoot": str(temp_dir / "planning"),
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Now create two tasks with identical titles under the same feature
        task_title = "Implement Authentication"

        # Create first task
        task1_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": task_title,
                "projectRoot": str(temp_dir / "planning"),
                "parent": feature_id,
            },
        )

        # Create second task with same title
        task2_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": task_title,
                "projectRoot": str(temp_dir / "planning"),
                "parent": feature_id,
            },
        )

        # Verify both tasks were created successfully
        assert task1_result.data is not None
        assert task2_result.data is not None

        # Verify both tasks have the same title
        assert task1_result.data["title"] == task_title
        assert task2_result.data["title"] == task_title

        # Verify tasks have unique IDs (collision detection working)
        task1_id = task1_result.data["id"]
        task2_id = task2_result.data["id"]
        assert task1_id != task2_id

        # Verify first task gets base slug, second gets suffix (with T- prefix)
        assert task1_id == "T-implement-authentication"
        assert task2_id == "T-implement-authentication-1"

        # Verify both tasks have correct file paths
        task1_path = task1_result.data["file_path"]
        task2_path = task2_result.data["file_path"]
        assert task1_path != task2_path

        # Verify paths follow expected structure
        # Extract raw IDs (without prefixes) for path construction
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        planning_root = temp_dir / "planning"
        expected_task1_path = (
            planning_root
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{task1_id}.md"
        )
        expected_task2_path = (
            planning_root
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{task2_id}.md"
        )

        assert task1_path == str(expected_task1_path)
        assert task2_path == str(expected_task2_path)

        # Verify both task files actually exist on filesystem
        assert expected_task1_path.exists()
        assert expected_task2_path.exists()

        # Verify files have correct content structure (basic YAML front-matter check)
        task1_content = expected_task1_path.read_text()
        task2_content = expected_task2_path.read_text()

        # Both should contain YAML front-matter with correct IDs and titles
        assert f"id: {task1_id}" in task1_content
        assert f"title: {task_title}" in task1_content
        assert f"id: {task2_id}" in task2_content
        assert f"title: {task_title}" in task2_content
