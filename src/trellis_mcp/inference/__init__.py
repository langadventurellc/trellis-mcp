"""Trellis MCP Kind Inference Engine.

This module provides pattern matching capabilities for automatically detecting
object types from ID prefixes, eliminating the need for explicit kind parameters
in tool calls, along with unified path construction for all object types.
"""

from .path_builder import PathBuilder
from .pattern_matcher import PatternMatcher

__all__ = ["PatternMatcher", "PathBuilder"]
