"""Unit tests for logger.py module focusing on JSONL format, field presence,
and concurrent safety.
"""

import json
import re
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from trellis_mcp.logger import write_event


class TestWriteEventJSONL:
    """Test JSONL format output from write_event function."""

    def test_single_entry_valid_json(self):
        """Test that a single log entry produces valid JSON parseable with json.loads()."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                # Write a single log entry
                write_event("INFO", "Test message", extra_field="test_value")

                # Read and verify the log file
                log_files = list(Path(temp_dir).glob("*.log"))
                assert len(log_files) == 1

                log_content = log_files[0].read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")
                assert len(lines) == 1

                # Parse the JSON line
                entry = json.loads(lines[0])
                assert isinstance(entry, dict)

    def test_multiple_entries_multiple_json_lines(self):
        """Test that multiple log entries create multiple JSON lines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                # Write multiple log entries
                write_event("INFO", "First message")
                write_event("ERROR", "Second message")
                write_event("DEBUG", "Third message")

                # Read and verify the log file
                log_files = list(Path(temp_dir).glob("*.log"))
                assert len(log_files) == 1

                log_content = log_files[0].read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")
                assert len(lines) == 3

                # Parse each JSON line
                for line in lines:
                    entry = json.loads(line)
                    assert isinstance(entry, dict)

    def test_json_loads_can_parse_each_entry(self):
        """Test that json.loads() can successfully parse each log entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                # Write entries with various data types
                write_event("INFO", "String message", count=42, active=True, data={"key": "value"})
                write_event("ERROR", "Error message", error_code=404, details=None)

                # Read and parse each entry
                log_files = list(Path(temp_dir).glob("*.log"))
                log_content = log_files[0].read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")

                # Verify each line parses successfully
                for line in lines:
                    entry = json.loads(line)  # Should not raise exception
                    assert isinstance(entry, dict)


class TestWriteEventFields:
    """Test field presence and correctness in log entries."""

    def test_required_fields_present(self):
        """Test that all required fields (ts, level, msg) are present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                write_event("INFO", "Test message")

                log_files = list(Path(temp_dir).glob("*.log"))
                log_content = log_files[0].read_text(encoding="utf-8")
                entry = json.loads(log_content.strip())

                # Check required fields
                assert "ts" in entry
                assert "level" in entry
                assert "msg" in entry
                assert entry["level"] == "INFO"
                assert entry["msg"] == "Test message"

    def test_additional_fields_included(self):
        """Test that additional fields (**fields) are included in log entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                write_event("INFO", "Test message", user_id=123, action="login", success=True)

                log_files = list(Path(temp_dir).glob("*.log"))
                log_content = log_files[0].read_text(encoding="utf-8")
                entry = json.loads(log_content.strip())

                # Check additional fields
                assert entry["user_id"] == 123
                assert entry["action"] == "login"
                assert entry["success"] is True

    def test_timestamp_format_rfc3339(self):
        """Test that timestamp field follows RFC 3339 format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                write_event("INFO", "Test message")

                log_files = list(Path(temp_dir).glob("*.log"))
                log_content = log_files[0].read_text(encoding="utf-8")
                entry = json.loads(log_content.strip())

                # Check timestamp format (RFC 3339)
                ts = entry["ts"]
                assert isinstance(ts, str)
                assert "T" in ts
                assert ts.endswith("Z")
                # Basic format check: YYYY-MM-DDTHH:MM:SS.ffffffZ (with microseconds)
                assert len(ts) >= 20  # At least YYYY-MM-DDTHH:MM:SSZ
                # More detailed format validation
                rfc3339_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
                assert re.match(
                    rfc3339_pattern, ts
                ), f"Timestamp {ts} doesn't match RFC 3339 format"


class TestWriteEventConcurrency:
    """Test concurrent write safety for write_event function."""

    def test_multiple_threads_writing_simultaneously(self):
        """Test multiple threads writing simultaneously without race conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                num_threads = 10
                entries_per_thread = 5

                def write_entries(thread_id):
                    """Write multiple entries from a single thread."""
                    for i in range(entries_per_thread):
                        write_event(
                            "INFO", f"Thread {thread_id} entry {i}", thread_id=thread_id, entry_id=i
                        )

                # Run multiple threads simultaneously
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(write_entries, i) for i in range(num_threads)]

                    # Wait for all threads to complete
                    for future in futures:
                        future.result()

                # Verify all entries were written correctly
                log_files = list(Path(temp_dir).glob("*.log"))
                assert len(log_files) == 1

                log_content = log_files[0].read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")

                # Should have all entries
                assert len(lines) == num_threads * entries_per_thread

                # Each line should be valid JSON
                entries = []
                for line in lines:
                    entry = json.loads(line)
                    entries.append(entry)

                # Verify we have entries from all threads
                thread_ids = {entry["thread_id"] for entry in entries}
                assert thread_ids == set(range(num_threads))

    def test_concurrent_writes_no_data_corruption(self):
        """Test that concurrent writes don't cause data corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                # Track which messages were written by each thread
                messages_written = {}
                lock = threading.Lock()

                def write_with_tracking(thread_id):
                    """Write entries while tracking what was written."""
                    thread_messages = []
                    for i in range(3):
                        message = f"Thread {thread_id} message {i}"
                        write_event("INFO", message, thread_id=thread_id, msg_id=i)
                        thread_messages.append(message)

                    with lock:
                        messages_written[thread_id] = thread_messages

                # Run concurrent writes
                num_threads = 5
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(write_with_tracking, i) for i in range(num_threads)]

                    for future in futures:
                        future.result()

                # Read and verify log file
                log_files = list(Path(temp_dir).glob("*.log"))
                log_content = log_files[0].read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")

                # Parse all entries
                logged_messages = []
                for line in lines:
                    entry = json.loads(line)
                    logged_messages.append(entry["msg"])

                # Verify all written messages are in the log
                all_expected_messages = []
                for thread_messages in messages_written.values():
                    all_expected_messages.extend(thread_messages)

                assert set(logged_messages) == set(all_expected_messages)
                assert len(logged_messages) == len(all_expected_messages)

    def test_threading_lock_effectiveness(self):
        """Test that the threading lock prevents race conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("trellis_mcp.logger.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)

                # Test with rapid concurrent writes
                num_threads = 20
                writes_per_thread = 10

                def rapid_writes(thread_id):
                    """Perform rapid writes to test thread safety."""
                    for i in range(writes_per_thread):
                        write_event(
                            "INFO", f"Rapid write {thread_id}-{i}", thread_id=thread_id, write_id=i
                        )
                        # Small delay to increase chance of race conditions
                        time.sleep(0.001)

                # Execute rapid concurrent writes
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(rapid_writes, i) for i in range(num_threads)]

                    for future in futures:
                        future.result()

                # Verify log integrity
                log_files = list(Path(temp_dir).glob("*.log"))
                assert len(log_files) == 1

                log_content = log_files[0].read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")

                # Should have exactly the expected number of entries
                expected_entries = num_threads * writes_per_thread
                assert len(lines) == expected_entries

                # Each line should be valid JSON (no corruption)
                for line in lines:
                    entry = json.loads(line)  # Should not raise exception
                    assert isinstance(entry, dict)
                    assert "ts" in entry
                    assert "level" in entry
                    assert "msg" in entry
