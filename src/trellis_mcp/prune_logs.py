"""Log pruning utility for Trellis MCP.

Provides functionality to remove old log files based on retention policy.
Removes daily log files older than the configured retention window.
"""

import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final, Union

from .settings import Settings

# Pattern for daily log filenames (YYYY-MM-DD.log)
DAILY_LOG_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.log$")

# Global lock for thread-safe pruning operations
_prune_lock = threading.Lock()


def prune_logs(settings: Settings | None = None, dry_run: bool = False) -> Union[int, list[Path]]:
    """Remove log files older than the retention window.

    Scans the log directory for daily log files matching the pattern YYYY-MM-DD.log
    and removes those older than the configured retention period. This function is
    thread-safe and can be called concurrently from multiple threads.

    Args:
        settings: Optional Settings instance. If None, creates a new Settings instance.
        dry_run: If True, returns list of files that would be deleted without actually
                deleting them. If False, deletes files and returns count of removed files.

    Returns:
        If dry_run is True: List of Path objects that would be deleted.
        If dry_run is False: Number of log files that were successfully removed.

    Raises:
        OSError: If there are filesystem permission issues accessing or removing files
        ValueError: If retention_days is configured as 0 or negative (should be > 0)

    Example:
        >>> from trellis_mcp.settings import Settings
        >>> settings = Settings(log_retention_days=7)
        >>> removed_count = prune_logs(settings)
        >>> print(f"Removed {removed_count} old log files")

        >>> # Use default settings
        >>> removed_count = prune_logs()
        >>> print(f"Removed {removed_count} old log files")

        >>> # Dry run to see what would be deleted
        >>> files_to_delete = prune_logs(settings, dry_run=True)
        >>> print(f"Would delete {len(files_to_delete)} files")
        >>> for file_path in files_to_delete:
        ...     print(f"  - {file_path.name}")

    Note:
        - Only removes files matching the exact pattern YYYY-MM-DD.log
        - Retention window is calculated from current date minus retention_days
        - If retention_days is 0, raises ValueError as per settings validation
        - Thread-safe: uses global lock to prevent concurrent pruning operations
        - Gracefully handles missing log directory (returns 0)
    """
    # Load settings if not provided
    if settings is None:
        settings = Settings()

    # Validate retention setting
    if settings.log_retention_days <= 0:
        raise ValueError(f"Invalid retention period: {settings.log_retention_days}. Must be > 0.")

    # Calculate cutoff date (files older than this will be removed)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=settings.log_retention_days)

    # Get log directory path
    log_dir = settings.log_dir

    # Check if log directory exists
    if not log_dir.exists():
        # No log directory means no files to prune
        return [] if dry_run else 0

    if not log_dir.is_dir():
        raise OSError(f"Log path exists but is not a directory: {log_dir}")

    removed_count = 0
    files_to_remove = []

    # Thread-safe pruning operation
    with _prune_lock:
        try:
            # Scan log directory for daily log files
            for file_path in log_dir.iterdir():
                if not file_path.is_file():
                    continue

                # Check if filename matches daily log pattern
                match = DAILY_LOG_PATTERN.match(file_path.name)
                if not match:
                    continue

                # Parse date from filename
                year, month, day = match.groups()
                try:
                    file_date = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
                except ValueError:
                    # Invalid date in filename, skip this file
                    continue

                # Check if file is older than retention window
                if file_date < cutoff_date:
                    if dry_run:
                        # For dry run, just collect files that would be deleted
                        files_to_remove.append(file_path)
                    else:
                        # For actual pruning, delete the file
                        try:
                            file_path.unlink()
                            removed_count += 1
                        except OSError as e:
                            # Log the error but continue processing other files
                            # In a real implementation, we might want to log this error
                            # For now, just re-raise to let caller handle it
                            raise OSError(f"Failed to remove log file {file_path}: {e}") from e

        except OSError as e:
            # Re-raise filesystem errors for caller to handle
            raise OSError(f"Error accessing log directory {log_dir}: {e}") from e

    return files_to_remove if dry_run else removed_count
