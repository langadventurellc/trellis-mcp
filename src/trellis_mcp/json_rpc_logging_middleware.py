"""JSON-RPC logging middleware for Trellis MCP server.

Provides middleware to log all JSON-RPC method calls with timing and status information.
Each call is logged with method name, duration in milliseconds, and success/error status.
"""

import time
from typing import Any

from fastmcp.server.middleware import Middleware, MiddlewareContext

from .logger import write_event
from .settings import Settings


class JsonRpcLoggingMiddleware(Middleware):
    """Middleware to log JSON-RPC method calls with timing and status.

    Intercepts all JSON-RPC tool calls and logs them with:
    - method: The name of the JSON-RPC method being called
    - duration_ms: Call duration in milliseconds
    - status: "success" or "error" based on whether an exception was raised

    All logs are written using the existing write_event function with INFO level.
    """

    def __init__(self, settings: Settings | None = None):
        """Initialize the middleware with optional settings.

        Args:
            settings: Optional Settings instance. If None, write_event will create its own.
        """
        super().__init__()
        self.settings = settings

    async def on_call_tool(self, context: MiddlewareContext, call_next) -> Any:
        """Intercept and log JSON-RPC tool calls.

        Measures the duration of each tool call and logs the method name,
        duration in milliseconds, and success/error status.

        Args:
            context: FastMCP middleware context containing method and message info
            call_next: Function to call the next middleware or the actual tool

        Returns:
            The result from the tool call

        Raises:
            Any exception raised by the tool call (after logging)
        """
        # Extract the actual tool name from the context
        # For MCP tool calls, the method is 'tools/call' and the tool name is in the message.name
        if (
            context.method == "tools/call"
            and hasattr(context, "message")
            and hasattr(context.message, "name")
        ):
            tool_name = context.message.name
        else:
            tool_name = context.method

        start_time = time.perf_counter()

        try:
            # Call the actual tool/next middleware
            result = await call_next(context)

            # Calculate duration and log success
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            write_event(
                level="INFO",
                msg="JSON-RPC call completed",
                settings=self.settings,
                method=tool_name,
                duration_ms=duration_ms,
                status="success",
            )

            return result

        except Exception as e:
            # Calculate duration and log error
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            write_event(
                level="INFO",
                msg="JSON-RPC call failed",
                settings=self.settings,
                method=tool_name,
                duration_ms=duration_ms,
                status="error",
                error=str(e),
            )

            # Re-raise the exception to maintain normal error handling
            raise
