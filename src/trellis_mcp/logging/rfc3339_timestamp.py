"""RFC 3339 timestamp helper for Trellis MCP.

Generates RFC 3339 compliant timestamps for consistent log formatting.
"""

from datetime import datetime, timezone


def rfc3339_timestamp(dt: datetime | None = None) -> str:
    """Generate RFC 3339 compliant timestamp string.

    Creates a timestamp in RFC 3339 format (ISO 8601 profile) for consistent
    log formatting. This is the standard format used throughout the Trellis MCP
    system for all datetime representations.

    Args:
        dt: Optional datetime to format. If None, uses current UTC time.

    Returns:
        RFC 3339 formatted timestamp string (e.g., '2025-07-15T19:12:00Z')

    Example:
        >>> from datetime import datetime
        >>> rfc3339_timestamp(datetime(2025, 7, 15, 19, 12, 0))
        '2025-07-15T19:12:00Z'
        >>> rfc3339_timestamp()  # Uses current time
        '2025-07-15T19:12:00Z'
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    # For UTC timezone, always use Z suffix instead of +00:00
    iso_string = dt.isoformat()
    if iso_string.endswith("+00:00"):
        return iso_string.replace("+00:00", "Z")
    elif dt.tzinfo is None:
        return iso_string + "Z"
    else:
        return iso_string
