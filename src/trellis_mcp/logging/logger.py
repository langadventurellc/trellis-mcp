"""Thread-safe event logging for Trellis MCP.

Provides thread-safe logging functionality for system events in JSONL format.
Each log entry contains timestamp, level, message, and additional fields.
"""

import json
import threading
from typing import Any

from ..settings import Settings
from .log_filename import daily_log_filename
from .rfc3339_timestamp import rfc3339_timestamp

# Global lock for thread-safe file operations
_log_lock = threading.Lock()


def write_event(level: str, msg: str, settings: Settings | None = None, **fields: Any) -> None:
    """Write a log event to the daily log file in JSONL format.

    Creates a thread-safe log entry with timestamp, level, message, and
    additional fields. Log entries are written to daily log files in the
    configured log directory using JSONL format (one JSON object per line).

    The log entry schema follows: {ts, level, msg, ...fields}

    Args:
        level: Log level (e.g., 'INFO', 'ERROR', 'DEBUG')
        msg: Log message describing the event
        settings: Optional Settings instance. If None, creates a new Settings instance.
        **fields: Additional fields to include in the log entry

    Raises:
        OSError: If there are issues creating directories or writing files
        IOError: If there are filesystem permission issues
        ValueError: If the log entry cannot be serialized to JSON

    Example:
        >>> write_event('INFO', 'JSON-RPC call completed',
        ...             method='getTask', duration_ms=15, status='success')
        >>> # Creates log entry:
        >>> # {"ts": "2025-07-15T19:12:00Z", "level": "INFO",
        >>> #  "msg": "JSON-RPC call completed", "method": "getTask",
        >>> #  "duration_ms": 15, "status": "success"}
    """
    # Load settings if not provided
    if settings is None:
        settings = Settings()

    # Create log entry with required fields
    log_entry = {"ts": rfc3339_timestamp(), "level": level, "msg": msg, **fields}

    # Serialize to JSON string
    try:
        json_line = json.dumps(log_entry, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot serialize log entry to JSON: {e}") from e

    # Get log file path
    log_filename = daily_log_filename()
    log_file_path = settings.log_dir / log_filename

    # Thread-safe file operation
    with _log_lock:
        try:
            # Ensure log directory exists
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Append log entry to file
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(json_line + "\n")
                f.flush()

        except OSError as e:
            raise OSError(f"Cannot write to log file {log_file_path}: {e}") from e
