"""Pytest configuration and shared fixtures for trellis_mcp tests.

This module provides common fixtures and test utilities for the trellis_mcp
test suite, including temporary directories, configuration helpers, mock
utilities, and enhanced fixtures for inference engine testing.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.trellis_mcp.inference.engine import KindInferenceEngine


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


@pytest.fixture
def inference_test_structure(temp_dir: Path) -> Path:
    """Create a comprehensive planning structure for inference testing.

    Creates a realistic planning structure with multiple projects,
    epics, features, and tasks for comprehensive inference engine testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: The planning directory root containing comprehensive structure
    """
    planning_dir = temp_dir / "planning"
    planning_dir.mkdir()

    # Create comprehensive hierarchical structure
    projects = [
        ("P-web-platform", "Web Platform"),
        ("P-mobile-app", "Mobile Application"),
        ("P-data-pipeline", "Data Pipeline"),
    ]

    for project_id, project_title in projects:
        project_dir = planning_dir / "projects" / project_id
        project_dir.mkdir(parents=True)
        _create_object_file(project_dir / "project.md", "project", project_id, project_title)

        # Create epics
        epics = [
            (f"E-{project_id.split('-')[1]}-frontend", "Frontend Development"),
            (f"E-{project_id.split('-')[1]}-backend", "Backend Services"),
            (f"E-{project_id.split('-')[1]}-integration", "System Integration"),
        ]

        for epic_id, epic_title in epics:
            epic_dir = project_dir / "epics" / epic_id
            epic_dir.mkdir(parents=True)
            _create_object_file(epic_dir / "epic.md", "epic", epic_id, epic_title)

            # Create features
            features = [
                (f"F-{epic_id.split('-')[1]}-auth", "Authentication"),
                (f"F-{epic_id.split('-')[1]}-ui", "User Interface"),
            ]

            for feature_id, feature_title in features:
                feature_dir = epic_dir / "features" / feature_id
                feature_dir.mkdir(parents=True)
                _create_object_file(
                    feature_dir / "feature.md", "feature", feature_id, feature_title
                )

                # Create tasks
                task_dir = feature_dir / "tasks-open"
                task_dir.mkdir()

                tasks = [
                    (f"T-{feature_id.split('-')[1]}-login", "Implement Login"),
                    (f"T-{feature_id.split('-')[1]}-logout", "Implement Logout"),
                ]

                for task_id, task_title in tasks:
                    _create_object_file(task_dir / f"{task_id}.md", "task", task_id, task_title)

    # Create standalone tasks
    standalone_dir = planning_dir / "tasks-open"
    standalone_dir.mkdir()

    standalone_tasks = [
        ("T-database-setup", "Database Setup"),
        ("T-monitoring-config", "Monitoring Configuration"),
        ("T-security-audit", "Security Audit"),
        ("T-performance-test", "Performance Testing"),
    ]

    for task_id, task_title in standalone_tasks:
        _create_object_file(standalone_dir / f"{task_id}.md", "task", task_id, task_title)

    return planning_dir


@pytest.fixture
def inference_engine(inference_test_structure: Path) -> KindInferenceEngine:
    """Create a KindInferenceEngine with comprehensive test structure.

    Args:
        inference_test_structure: Comprehensive planning structure fixture

    Returns:
        KindInferenceEngine: Engine initialized with test structure
    """
    return KindInferenceEngine(inference_test_structure)


@pytest.fixture
def mixed_project_structure(temp_dir: Path) -> Path:
    """Create a mixed project structure with both hierarchical and standalone objects.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: The planning directory root containing mixed structure
    """
    planning_dir = temp_dir / "planning"
    planning_dir.mkdir()

    # Hierarchical structure
    project_dir = planning_dir / "projects" / "P-mixed-project"
    project_dir.mkdir(parents=True)
    _create_object_file(project_dir / "project.md", "project", "P-mixed-project", "Mixed Project")

    epic_dir = project_dir / "epics" / "E-mixed-epic"
    epic_dir.mkdir(parents=True)
    _create_object_file(epic_dir / "epic.md", "epic", "E-mixed-epic", "Mixed Epic")

    feature_dir = epic_dir / "features" / "F-mixed-feature"
    feature_dir.mkdir(parents=True)
    _create_object_file(feature_dir / "feature.md", "feature", "F-mixed-feature", "Mixed Feature")

    task_dir = feature_dir / "tasks-open"
    task_dir.mkdir()
    _create_object_file(
        task_dir / "T-hierarchical-task.md", "task", "T-hierarchical-task", "Hierarchical Task"
    )

    # Standalone tasks
    standalone_dir = planning_dir / "tasks-open"
    standalone_dir.mkdir()
    _create_object_file(
        standalone_dir / "T-standalone-task.md", "task", "T-standalone-task", "Standalone Task"
    )

    return planning_dir


@pytest.fixture
def corrupted_test_structure(temp_dir: Path) -> Path:
    """Create a project structure with various corruption scenarios for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: The planning directory root containing corrupted test structure
    """
    planning_dir = temp_dir / "planning"
    planning_dir.mkdir()

    # Valid structure
    project_dir = planning_dir / "projects" / "P-valid-project"
    project_dir.mkdir(parents=True)
    _create_object_file(project_dir / "project.md", "project", "P-valid-project", "Valid Project")

    # Corrupted structures
    # Empty file
    empty_project_dir = planning_dir / "projects" / "P-empty-project"
    empty_project_dir.mkdir(parents=True)
    (empty_project_dir / "project.md").write_text("")

    # Malformed YAML
    malformed_project_dir = planning_dir / "projects" / "P-malformed-project"
    malformed_project_dir.mkdir(parents=True)
    (malformed_project_dir / "project.md").write_text(
        """---
invalid: yaml: content:
missing: proper: structure
---
# Malformed Project"""
    )

    # Missing front matter
    no_fm_project_dir = planning_dir / "projects" / "P-no-frontmatter"
    no_fm_project_dir.mkdir(parents=True)
    (no_fm_project_dir / "project.md").write_text("# Project without front matter")

    return planning_dir


def _create_object_file(file_path: Path, kind: str, obj_id: str, title: str):
    """Create a valid object file with proper YAML front matter.

    Args:
        file_path: Path where the file should be created
        kind: Object kind (project, epic, feature, task)
        obj_id: Object ID
        title: Object title
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Set appropriate status based on kind
    if kind == "project":
        status = "in-progress"
    elif kind in ["epic", "feature"]:
        status = "in-progress"
    else:  # task
        status = "open"

    content = f"""---
kind: {kind}
id: {obj_id}
title: {title}
status: {status}
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# {title}

This is a {kind} for testing the Kind Inference Engine.

## Description

Test content for {obj_id}.
"""
    file_path.write_text(content)
