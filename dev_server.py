#!/usr/bin/env python3
"""Development server wrapper for FastMCP inspector.

This file creates a server instance that can be used with fastmcp dev command.
"""

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings

# Create default settings for development
settings = Settings()

# Create the server instance that FastMCP dev can discover
mcp = create_server(settings)

if __name__ == "__main__":
    # Run with STDIO transport by default
    mcp.run()
