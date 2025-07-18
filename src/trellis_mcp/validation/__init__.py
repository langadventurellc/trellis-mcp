"""Validation utilities for Trellis MCP objects.

This module provides validation functions for checking object relationships
and constraints beyond basic field validation.
"""

# Re-export all public APIs to maintain backward compatibility

from .benchmark import PerformanceBenchmark, benchmark_cycle_detection

# Cache and performance utilities
from .cache import DependencyGraphCache, clear_dependency_cache, get_cache_stats

# Context utilities
from .context_utils import (
    format_validation_error_with_context,
    generate_contextual_error_message,
    get_task_type_context,
)

# Core validation
from .core import validate_object_data

# Cycle detection
from .cycle_detection import (
    check_prereq_cycles,
    check_prereq_cycles_in_memory,
    validate_acyclic_prerequisites,
)

# Exception classes
from .exceptions import CircularDependencyError, TrellisValidationError

# Field validation
from .field_validation import (
    validate_enum_membership,
    validate_front_matter,
    validate_priority_field,
    validate_required_fields_per_kind,
    validate_status_for_kind,
)

# Graph operations
from .graph_operations import (
    build_dependency_graph_in_memory,
    build_prerequisites_graph,
    detect_cycle_dfs,
)

# Object loading
from .object_loader import get_all_objects

# Parent validation
from .parent_validation import validate_parent_exists, validate_parent_exists_for_object

# Security validation
from .security import validate_standalone_task_security

# Status transitions
from .status_transitions import enforce_status_transition

# Task utilities
from .task_utils import is_hierarchy_task, is_standalone_task

# Export all public APIs
__all__ = [
    # Exception classes
    "CircularDependencyError",
    "TrellisValidationError",
    # Cache and performance utilities
    "DependencyGraphCache",
    "PerformanceBenchmark",
    "benchmark_cycle_detection",
    "clear_dependency_cache",
    "get_cache_stats",
    # Object loading
    "get_all_objects",
    # Graph operations
    "build_dependency_graph_in_memory",
    "build_prerequisites_graph",
    "detect_cycle_dfs",
    # Cycle detection
    "check_prereq_cycles",
    "check_prereq_cycles_in_memory",
    "validate_acyclic_prerequisites",
    # Task utilities
    "is_hierarchy_task",
    "is_standalone_task",
    # Parent validation
    "validate_parent_exists",
    "validate_parent_exists_for_object",
    # Field validation
    "validate_enum_membership",
    "validate_front_matter",
    "validate_priority_field",
    "validate_required_fields_per_kind",
    "validate_status_for_kind",
    # Security validation
    "validate_standalone_task_security",
    # Context utilities
    "format_validation_error_with_context",
    "generate_contextual_error_message",
    "get_task_type_context",
    # Core validation
    "validate_object_data",
    # Status transitions
    "enforce_status_transition",
]
