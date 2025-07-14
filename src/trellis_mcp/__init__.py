"""Trellis MCP Server - File-backed project management for development agents.

A lightweight MCP server implementing hierarchical project management:
Projects → Epics → Features → Tasks stored as Markdown files with
YAML front-matter.
"""

from .object_parser import parse_object
from .object_dumper import dump_object, write_object
from .id_utils import clean_prerequisite_id
from .validation import (
    validate_parent_exists,
    validate_parent_exists_for_object,
    validate_required_fields_per_kind,
    validate_enum_membership,
    validate_status_for_kind,
    validate_object_data,
    CircularDependencyError,
    TrellisValidationError,
    validate_acyclic_prerequisites,
    get_all_objects,
    build_prerequisites_graph,
    detect_cycle_dfs,
)

__version__ = "0.1.0"
__author__ = "Lang Adventure LLC"
__description__ = "File-backed MCP server for project management"

__all__ = [
    "parse_object",
    "dump_object",
    "write_object",
    "clean_prerequisite_id",
    "validate_parent_exists",
    "validate_parent_exists_for_object",
    "validate_required_fields_per_kind",
    "validate_enum_membership",
    "validate_status_for_kind",
    "validate_object_data",
    "CircularDependencyError",
    "TrellisValidationError",
    "validate_acyclic_prerequisites",
    "get_all_objects",
    "build_prerequisites_graph",
    "detect_cycle_dfs",
]
