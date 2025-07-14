"""Trellis MCP Schema Package.

This package contains Pydantic models for the Trellis MCP v1.0 specification.
It provides type-safe data structures for Projects, Epics, Features, and Tasks
with validation and serialization capabilities.
"""

from .base import TrellisBaseModel
from .base_schema import BaseSchemaModel
from .epic import EpicModel
from .feature import FeatureModel
from .kind_enum import KindEnum
from .priority_enum import PriorityEnum
from .project import ProjectModel
from .status_enum import StatusEnum
from .task import TaskModel

__all__ = [
    "TrellisBaseModel",
    "BaseSchemaModel",
    "EpicModel",
    "FeatureModel",
    "KindEnum",
    "PriorityEnum",
    "ProjectModel",
    "StatusEnum",
    "TaskModel",
]
