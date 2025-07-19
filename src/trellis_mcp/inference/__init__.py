"""Trellis MCP Kind Inference Engine.

This module provides pattern matching capabilities for automatically detecting
object types from ID prefixes, eliminating the need for explicit kind parameters
in tool calls.
"""

from .pattern_matcher import PatternMatcher

__all__ = ["PatternMatcher"]
