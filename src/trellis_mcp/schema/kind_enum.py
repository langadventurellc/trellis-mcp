"""Kind enumeration for Trellis MCP objects.

Defines the valid object types in the Trellis MCP hierarchy.
"""

from __future__ import annotations

from enum import Enum


class KindEnum(str, Enum):
    """Valid object kinds in the Trellis MCP hierarchy.

    Defines the four types of objects that can exist in the hierarchical
    structure: projects contain epics, epics contain features, features contain tasks.
    """

    PROJECT = "project"
    EPIC = "epic"
    FEATURE = "feature"
    TASK = "task"
