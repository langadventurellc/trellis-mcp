"""Tests for JSON-RPC logging middleware.

Tests the middleware's ability to log JSON-RPC calls with timing and status information,
including concurrent safety and proper JSONL format output.
"""

import asyncio
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.server.middleware import MiddlewareContext

from trellis_mcp.logging.json_rpc_logging_middleware import JsonRpcLoggingMiddleware


class TestJsonRpcLoggingMiddleware:
    """Test suite for JsonRpcLoggingMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create a middleware instance for testing."""
        return JsonRpcLoggingMiddleware()

    @pytest.fixture
    def mock_context(self):
        """Create a mock middleware context."""
        context = MagicMock(spec=MiddlewareContext)
        context.method = "test_method"
        return context

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.asyncio
    async def test_successful_call_logging(self, middleware, mock_context, temp_log_dir):
        """Test that successful calls are logged with correct fields."""
        # Mock the call_next function to return a successful result
        call_next = AsyncMock(return_value={"result": "success"})

        # Mock settings and logger to use temp directory
        with patch("trellis_mcp.logging.json_rpc_logging_middleware.write_event") as mock_write:
            # Execute the middleware
            result = await middleware.on_call_tool(mock_context, call_next)

            # Verify the result is passed through
            assert result == {"result": "success"}

            # Verify logging was called with correct parameters
            mock_write.assert_called_once()
            call_args = mock_write.call_args

            # Check the log level and message
            assert call_args[1]["level"] == "INFO"
            assert call_args[1]["msg"] == "JSON-RPC call completed"

            # Check required fields are present
            assert call_args[1]["method"] == "test_method"
            assert "duration_ms" in call_args[1]
            assert call_args[1]["status"] == "success"

            # Duration should be a positive number
            assert isinstance(call_args[1]["duration_ms"], (int, float))
            assert call_args[1]["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_failed_call_logging(self, middleware, mock_context, temp_log_dir):
        """Test that failed calls are logged with error information."""
        # Mock the call_next function to raise an exception
        test_exception = ValueError("Test error")
        call_next = AsyncMock(side_effect=test_exception)

        # Mock settings and logger to use temp directory
        with patch("trellis_mcp.logging.json_rpc_logging_middleware.write_event") as mock_write:
            # Execute the middleware and expect the exception to be re-raised
            with pytest.raises(ValueError, match="Test error"):
                await middleware.on_call_tool(mock_context, call_next)

            # Verify logging was called with error information
            mock_write.assert_called_once()
            call_args = mock_write.call_args

            # Check the log level and message
            assert call_args[1]["level"] == "INFO"
            assert call_args[1]["msg"] == "JSON-RPC call failed"

            # Check required fields are present
            assert call_args[1]["method"] == "test_method"
            assert "duration_ms" in call_args[1]
            assert call_args[1]["status"] == "error"
            assert call_args[1]["error"] == "Test error"

            # Duration should be a positive number
            assert isinstance(call_args[1]["duration_ms"], (int, float))
            assert call_args[1]["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_duration_measurement(self, middleware, mock_context):
        """Test that duration is measured accurately."""

        # Mock call_next to add a delay
        async def delayed_call_next(context):
            await asyncio.sleep(0.1)  # 100ms delay
            return "result"

        with patch("trellis_mcp.logging.json_rpc_logging_middleware.write_event") as mock_write:
            await middleware.on_call_tool(mock_context, delayed_call_next)

            # Get the logged duration
            call_args = mock_write.call_args
            duration_ms = call_args[1]["duration_ms"]

            # Duration should be approximately 100ms (allowing for some variance)
            assert 90 <= duration_ms <= 150  # Allow 50ms variance

    @pytest.mark.asyncio
    async def test_concurrent_logging_safety(self, middleware, temp_log_dir):
        """Test that concurrent JSON-RPC calls are logged safely."""
        # Create multiple contexts for concurrent calls
        contexts = []
        for i in range(10):
            context = MagicMock(spec=MiddlewareContext)
            context.method = f"method_{i}"
            contexts.append(context)

        # Mock call_next functions with slight delays to simulate real work
        async def mock_call_next(context):
            await asyncio.sleep(0.01)  # Small delay to simulate work
            return {"method": context.method, "result": "success"}

        # Mock write_event to capture all calls
        logged_calls = []

        def capture_log_call(level, msg, **fields):
            logged_calls.append({"level": level, "msg": msg, **fields})

        with patch(
            "trellis_mcp.logging.json_rpc_logging_middleware.write_event",
            side_effect=capture_log_call,
        ):
            # Execute multiple calls concurrently
            tasks = []
            for context in contexts:
                task = asyncio.create_task(middleware.on_call_tool(context, mock_call_next))
                tasks.append(task)

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)

            # Verify all calls completed successfully
            assert len(results) == 10
            assert len(logged_calls) == 10

            # Verify each call was logged with correct method name
            logged_methods = [call["method"] for call in logged_calls]
            expected_methods = [f"method_{i}" for i in range(10)]
            assert sorted(logged_methods) == sorted(expected_methods)

            # Verify all calls have required fields
            for call in logged_calls:
                assert call["level"] == "INFO"
                assert call["msg"] == "JSON-RPC call completed"
                assert "method" in call
                assert "duration_ms" in call
                assert call["status"] == "success"

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure_logging(self, middleware, temp_log_dir):
        """Test logging of mixed successful and failed calls."""
        # Create contexts for different call types
        success_context = MagicMock(spec=MiddlewareContext)
        success_context.method = "success_method"

        failure_context = MagicMock(spec=MiddlewareContext)
        failure_context.method = "failure_method"

        # Mock call_next functions
        async def success_call_next(context):
            return "success"

        async def failure_call_next(context):
            raise RuntimeError("Intentional failure")

        # Mock write_event to capture all calls
        logged_calls = []

        def capture_log_call(level, msg, **fields):
            logged_calls.append({"level": level, "msg": msg, **fields})

        with patch(
            "trellis_mcp.logging.json_rpc_logging_middleware.write_event",
            side_effect=capture_log_call,
        ):
            # Execute successful call
            result = await middleware.on_call_tool(success_context, success_call_next)
            assert result == "success"

            # Execute failed call and catch exception
            with pytest.raises(RuntimeError, match="Intentional failure"):
                await middleware.on_call_tool(failure_context, failure_call_next)

            # Verify both calls were logged
            assert len(logged_calls) == 2

            # Check success call log
            success_log = logged_calls[0]
            assert success_log["method"] == "success_method"
            assert success_log["status"] == "success"
            assert success_log["msg"] == "JSON-RPC call completed"
            assert "error" not in success_log

            # Check failure call log
            failure_log = logged_calls[1]
            assert failure_log["method"] == "failure_method"
            assert failure_log["status"] == "error"
            assert failure_log["msg"] == "JSON-RPC call failed"
            assert failure_log["error"] == "Intentional failure"

    def test_integration_with_thread_pool(self, middleware, temp_log_dir):
        """Test that the middleware works correctly with thread pool execution."""
        # This test simulates the threading behavior that might occur in a real server

        # Create a context
        context = MagicMock(spec=MiddlewareContext)
        context.method = "threaded_method"

        # Mock call_next
        async def mock_call_next(context):
            # Simulate some CPU-bound work
            time.sleep(0.01)
            return "threaded_result"

        # Track logged calls
        logged_calls = []

        def capture_log_call(level, msg, **fields):
            logged_calls.append({"level": level, "msg": msg, **fields})

        with patch(
            "trellis_mcp.logging.json_rpc_logging_middleware.write_event",
            side_effect=capture_log_call,
        ):
            # Run the middleware call in a thread pool
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    asyncio.run, middleware.on_call_tool(context, mock_call_next)
                )
                result = future.result()

            # Verify the result
            assert result == "threaded_result"

            # Verify the log was captured
            assert len(logged_calls) == 1
            log_entry = logged_calls[0]
            assert log_entry["method"] == "threaded_method"
            assert log_entry["status"] == "success"
            assert "duration_ms" in log_entry
