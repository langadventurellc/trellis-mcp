"""Children discovery and caching system.

This module provides high-performance caching for children discovery operations
to optimize repeated children lookup operations in the Trellis MCP system.
"""

from .cache import ChildrenCache

__all__ = ["ChildrenCache"]
