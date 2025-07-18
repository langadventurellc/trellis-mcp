"""Object loading utilities for validation operations.

This module provides functions to load and parse objects from the filesystem
for validation purposes.
"""

import logging
import os
from pathlib import Path
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)


def get_all_objects(project_root: str | Path, include_mtimes: bool = False):
    """Load all objects from the filesystem using glob patterns for resilient discovery.

    Args:
        project_root: The root directory of the project
        include_mtimes: If True, also return file modification times for caching

    Returns:
        Dictionary mapping object IDs to their parsed data, optionally with file mtimes

    Raises:
        FileNotFoundError: If the project root doesn't exist
        ValueError: If object parsing fails
    """
    from ..id_utils import clean_prerequisite_id
    from ..object_parser import parse_object

    project_root_path = Path(project_root)
    if not project_root_path.exists():
        raise FileNotFoundError(f"Project root not found: {project_root}")

    objects: dict[str, dict[str, Any]] = {}
    file_mtimes: dict[str, float] = {}

    # Use glob patterns to find all object files more efficiently
    patterns = [
        "projects/P-*/project.md",  # Projects
        "projects/P-*/epics/E-*/epic.md",  # Epics
        "projects/P-*/epics/E-*/features/F-*/feature.md",  # Features
        "projects/P-*/epics/E-*/features/F-*/tasks-open/T-*.md",  # Open tasks
        "projects/P-*/epics/E-*/features/F-*/tasks-done/*-T-*.md",  # Done tasks
        "tasks-open/T-*.md",  # Standalone open tasks
        "tasks-done/*-T-*.md",  # Standalone done tasks
    ]

    for pattern in patterns:
        for file_path in project_root_path.glob(pattern):
            try:
                obj = parse_object(file_path)
                # Store objects using clean IDs (without prefixes) for consistent lookup
                clean_id = clean_prerequisite_id(obj.id)
                objects[clean_id] = obj.model_dump()

                # Record file modification time for caching
                if include_mtimes and file_mtimes is not None:
                    file_mtimes[str(file_path)] = os.path.getmtime(file_path)

            except Exception as e:
                logger.warning(f"Skipping invalid file {file_path}: {e}")
                continue

    if include_mtimes:
        return objects, file_mtimes
    return objects
