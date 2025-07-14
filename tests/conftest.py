"""Pytest configuration and shared fixtures for trellis_mcp tests.

This module provides common fixtures and test utilities for the trellis_mcp
test suite, including temporary directories, configuration helpers, and
mock utilities.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test operations.

    Creates a temporary directory that is automatically cleaned up
    after the test completes. Useful for testing file operations
    and directory structures.

    Returns:
        Path: A Path object pointing to a temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def clean_working_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Provide a clean working directory and change to it during the test.

    Changes the current working directory to a temporary directory
    for the duration of the test, then restores the original
    working directory when done.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: The temporary directory that is now the current working directory
    """
    import os

    original_cwd = Path.cwd()
    os.chdir(temp_dir)
    try:
        yield temp_dir
    finally:
        os.chdir(original_cwd)


@pytest.fixture
def sample_planning_structure(temp_dir: Path) -> Path:
    """Create a sample planning directory structure for testing.

    Creates a basic planning directory structure with sample
    projects, epics, features, and tasks for testing hierarchy
    operations.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: The planning directory root containing sample structure
    """
    planning_dir = temp_dir / "planning"
    planning_dir.mkdir()

    # Create sample project structure
    project_dir = planning_dir / "projects" / "P-001-sample-project"
    project_dir.mkdir(parents=True)

    # Create sample epic
    epic_dir = project_dir / "epics" / "E-001-sample-epic"
    epic_dir.mkdir(parents=True)

    # Create sample feature
    feature_dir = epic_dir / "features" / "F-001-sample-feature"
    feature_dir.mkdir(parents=True)

    # Create task directories
    (feature_dir / "tasks-open").mkdir()
    (feature_dir / "tasks-done").mkdir()

    return planning_dir
