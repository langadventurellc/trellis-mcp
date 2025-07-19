"""Tests for Trellis MCP server core functionality.

Tests server creation, configuration, and basic server instantiation
to ensure proper FastMCP integration and server behavior.
"""

from pathlib import Path

from fastmcp import FastMCP

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


def test_create_server_with_default_settings():
    """Test server creation with default settings."""
    settings = Settings()
    server = create_server(settings)

    assert server is not None
    assert hasattr(server, "run")
    assert isinstance(server, FastMCP)


def test_create_server_with_custom_settings():
    """Test server creation with custom settings."""
    settings = Settings(
        schema_version="2.0",
        planning_root=Path("./custom_planning"),
        debug_mode=True,
        log_level="DEBUG",
    )
    server = create_server(settings)

    assert server is not None
    assert hasattr(server, "run")


def test_create_server_returns_fastmcp_instance():
    """Test that create_server returns a FastMCP instance."""
    settings = Settings()
    server = create_server(settings)

    # Check that it's a FastMCP instance
    assert isinstance(server, FastMCP)


def test_server_has_expected_name():
    """Test that server is created with expected name."""
    settings = Settings()
    server = create_server(settings)

    # FastMCP servers have a name attribute
    assert hasattr(server, "name")
    assert server.name == "Trellis MCP Server"


def test_server_with_different_settings():
    """Test server creation with various settings combinations."""
    test_cases = [
        {"host": "localhost", "port": 9000},
        {"debug_mode": True, "log_level": "DEBUG"},
        {"planning_root": "./test", "schema_version": "1.5"},
    ]

    for settings_kwargs in test_cases:
        settings = Settings(**settings_kwargs)
        server = create_server(settings)
        assert server is not None
        assert isinstance(server, FastMCP)
