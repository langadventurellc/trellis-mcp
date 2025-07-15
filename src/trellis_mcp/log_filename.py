"""Daily log filename pattern generator for Trellis MCP.

Generates log filenames in YYYY-MM-DD format for daily log rotation.
"""

from datetime import datetime, timezone


def daily_log_filename(date: datetime | None = None) -> str:
    """Generate daily log filename in YYYY-MM-DD format.

    Creates a filename pattern for daily log rotation using ISO date format.
    This ensures lexicographic sorting matches chronological order.

    Args:
        date: Optional datetime to use for filename. If None, uses current date.

    Returns:
        Filename string in format 'YYYY-MM-DD.log' (e.g., '2025-07-15.log')

    Example:
        >>> from datetime import datetime
        >>> daily_log_filename(datetime(2025, 7, 15))
        '2025-07-15.log'
        >>> daily_log_filename()  # Uses current date
        '2025-07-15.log'
    """
    if date is None:
        date = datetime.now(timezone.utc)

    return f"{date.strftime('%Y-%m-%d')}.log"
