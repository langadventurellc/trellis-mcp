"""Trellis MCP Kind Inference Engine.

This module provides pattern matching capabilities for automatically detecting
object types from ID prefixes, eliminating the need for explicit kind parameters
in tool calls, along with unified path construction for all object types.
"""

from pathlib import Path

from .cache import InferenceResult
from .engine import ExtendedInferenceResult, KindInferenceEngine
from .path_builder import PathBuilder
from .pattern_matcher import PatternMatcher

# Public API
__all__ = [
    "KindInferenceEngine",
    "InferenceResult",
    "ExtendedInferenceResult",
    "PatternMatcher",
    "PathBuilder",
    # Convenience functions
    "infer_kind",
    "infer_with_validation",
]


# Convenience functions for one-off inference operations
def infer_kind(object_id: str, project_root: str | Path, validate: bool = True) -> str:
    """Convenience function for one-off kind inference.

    Creates a temporary KindInferenceEngine instance and performs inference.
    For repeated operations, use KindInferenceEngine directly for better performance.

    Args:
        object_id: Object ID to analyze (e.g., "P-auth-system")
        project_root: Root directory for the planning structure
        validate: Whether to perform file system validation (default: True)

    Returns:
        The KindEnum value ("project", "epic", "feature", or "task")

    Raises:
        ValidationError: If object_id is invalid or validation fails

    Example:
        >>> kind = infer_kind("T-implement-auth", "./planning")
        >>> print(f"Detected: {kind}")  # "task"
    """
    engine = KindInferenceEngine(project_root)
    return engine.infer_kind(object_id, validate)


def infer_with_validation(object_id: str, project_root: str | Path) -> ExtendedInferenceResult:
    """Convenience function for one-off inference with validation.

    Creates a temporary KindInferenceEngine instance and performs extended inference
    with comprehensive validation results.

    Args:
        object_id: Object ID to analyze
        project_root: Root directory for the planning structure

    Returns:
        ExtendedInferenceResult with detailed validation information

    Raises:
        ValidationError: If object_id format is invalid

    Example:
        >>> result = infer_with_validation("P-user-system", "./planning")
        >>> if result.is_valid:
        ...     print(f"Valid {result.inferred_kind}")
    """
    engine = KindInferenceEngine(project_root)
    return engine.infer_with_validation(object_id)
