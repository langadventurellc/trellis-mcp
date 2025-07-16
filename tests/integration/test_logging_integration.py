"""Integration tests for logging and pruning functionality."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastmcp import Client

from trellis_mcp.prune_logs import prune_logs
from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_server_logging_and_pruning_integration():
    """Test complete logging and pruning workflow with server RPC calls."""

    # Create temporary directory for this test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        log_dir = temp_path / "logs"
        log_dir.mkdir()

        # Create server with logging enabled
        settings = Settings(
            planning_root=temp_path / "planning",
            log_dir=log_dir,
            log_retention_days=7,
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)

        # Test Phase 1: Start server and make RPC calls
        async with Client(server) as client:
            # Make first RPC call
            health_result = await client.call_tool("health_check")
            assert health_result.data["status"] == "healthy"

            # Make second RPC call
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Integration Test Project",
                    "description": "Test project for logging integration",
                    "projectRoot": str(temp_path / "planning"),
                },
            )
            assert project_result.data["kind"] == "project"

        # Test Phase 2: Verify log file content
        # Use UTC time to match the actual log filename generation in daily_log_filename()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = log_dir / f"{today}.log"

        assert log_file.exists(), f"Log file {log_file} should exist"

        # Read and verify log entries
        log_entries = []
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)  # Verify it's valid JSON
                    log_entries.append(entry)

        # Should have at least 2 entries (health_check and createObject)
        assert len(log_entries) >= 2, f"Expected at least 2 log entries, got {len(log_entries)}"

        # Find the health_check and createObject entries
        health_entry = None
        create_entry = None

        for entry in log_entries:
            if entry.get("method") == "health_check":
                health_entry = entry
            elif entry.get("method") == "createObject":
                create_entry = entry

        assert health_entry is not None, "Should have health_check log entry"
        assert create_entry is not None, "Should have createObject log entry"

        # Verify log entry schema
        for entry in [health_entry, create_entry]:
            assert "ts" in entry, "Log entry should have timestamp"
            assert "level" in entry, "Log entry should have level"
            assert "msg" in entry, "Log entry should have message"
            assert "method" in entry, "Log entry should have method"
            assert "duration_ms" in entry, "Log entry should have duration"
            assert "status" in entry, "Log entry should have status"

            # Verify data types
            assert isinstance(entry["duration_ms"], (int, float)), "Duration should be numeric"
            assert entry["status"] in ["success", "error"], "Status should be success or error"

        # Test Phase 3: Create dummy old log files for pruning test
        old_dates = [
            datetime.now() - timedelta(days=10),  # 10 days old (should be removed)
            datetime.now() - timedelta(days=15),  # 15 days old (should be removed)
            datetime.now() - timedelta(days=5),  # 5 days old (should be kept)
        ]

        old_log_files = []
        for old_date in old_dates:
            old_filename = old_date.strftime("%Y-%m-%d.log")
            old_log_file = log_dir / old_filename
            old_log_file.write_text(
                '{"ts": "2025-01-01T00:00:00Z", "level": "INFO", "msg": "old log entry"}\n'
            )
            old_log_files.append(old_log_file)

        # Verify old files exist before pruning
        for old_file in old_log_files:
            assert old_file.exists(), f"Old log file {old_file} should exist before pruning"

        # Test Phase 4: Run prune_logs and verify results
        removed_count = prune_logs(settings)

        # Should have removed 2 files (10 days old and 15 days old)
        assert removed_count == 2, f"Expected 2 files removed, got {removed_count}"

        # Verify which files were removed/kept
        assert not old_log_files[0].exists(), "10-day-old file should be removed"
        assert not old_log_files[1].exists(), "15-day-old file should be removed"
        assert old_log_files[2].exists(), "5-day-old file should be kept"

        # Today's log file should still exist
        assert log_file.exists(), "Today's log file should be kept"

        # Test Phase 5: Verify remaining log files are still valid
        remaining_files = list(log_dir.glob("*.log"))
        assert (
            len(remaining_files) == 2
        ), f"Expected 2 remaining log files, got {len(remaining_files)}"

        # Verify remaining files contain valid JSON
        for remaining_file in remaining_files:
            with open(remaining_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        json.loads(line)  # Should not raise exception
