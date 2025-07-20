"""Centralized definition of valid object kinds for Trellis MCP.

This module provides the single source of truth for valid object kinds
used throughout the Trellis MCP system.
"""

from typing import Final

# Valid object kinds supported by Trellis MCP
VALID_KINDS: Final[set[str]] = {"project", "epic", "feature", "task"}
