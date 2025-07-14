"""Integration test for YAML schema loading with sample repository tree.

This test validates that the complete YAML schema loading system works
correctly with a realistic repository structure containing ~6 objects
across the full project hierarchy.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from datetime import datetime

from trellis_mcp import (
    get_all_objects,
    validate_acyclic_prerequisites,
    validate_object_data,
)


@pytest.mark.asyncio
async def test_integration_load_sample_repo_tree(temp_dir: Path) -> None:
    """Test loading a sample repository tree with ~6 objects.

    Creates a complete sample repository structure with:
    - 1 Project (P-web-platform)
    - 1 Epic (E-user-authentication)
    - 1 Feature (F-login-system)
    - 3 Tasks (T-setup-database, T-implement-jwt, T-add-password-reset)

    Tests that all objects load correctly, pass validation,
    and have an acyclic prerequisites graph.
    """
    # Create sample repository structure
    planning_root = temp_dir / "planning"
    _create_sample_repo_tree(planning_root)

    # Load all objects from the sample tree
    loaded_objects = get_all_objects(planning_root)

    # Verify we loaded exactly 6 objects
    assert len(loaded_objects) == 6, f"Expected 6 objects, got {len(loaded_objects)}"

    # Validate each object's data
    parsed_objects = []
    for obj_id, obj_data in loaded_objects.items():
        # Validate object data (should not raise exception for valid data)
        try:
            validate_object_data(obj_data, planning_root)
        except Exception as e:
            assert False, f"Object {obj_id} failed validation: {e}"

        # Parse to model instance for type checking
        from trellis_mcp.schema.project import ProjectModel
        from trellis_mcp.schema.epic import EpicModel
        from trellis_mcp.schema.feature import FeatureModel
        from trellis_mcp.schema.task import TaskModel

        if obj_data["kind"] == "project":
            parsed_obj = ProjectModel.model_validate(obj_data)
        elif obj_data["kind"] == "epic":
            parsed_obj = EpicModel.model_validate(obj_data)
        elif obj_data["kind"] == "feature":
            parsed_obj = FeatureModel.model_validate(obj_data)
        elif obj_data["kind"] == "task":
            parsed_obj = TaskModel.model_validate(obj_data)
        else:
            raise ValueError(f"Unknown object kind: {obj_data['kind']}")

        parsed_objects.append(parsed_obj)

    # Verify we have the expected object types
    kinds = [obj.kind for obj in parsed_objects]
    assert "project" in kinds
    assert "epic" in kinds
    assert "feature" in kinds
    assert kinds.count("task") == 3

    # Verify parent-child relationships
    project_obj = next(obj for obj in parsed_objects if obj.kind == "project")
    epic_obj = next(obj for obj in parsed_objects if obj.kind == "epic")
    feature_obj = next(obj for obj in parsed_objects if obj.kind == "feature")
    task_objects = [obj for obj in parsed_objects if obj.kind == "task"]

    # Check hierarchy relationships
    assert project_obj.parent is None
    assert epic_obj.parent == project_obj.id
    assert feature_obj.parent == epic_obj.id
    for task in task_objects:
        assert task.parent == feature_obj.id

    # Verify prerequisites graph is acyclic
    # This should not raise CircularDependencyError
    validate_acyclic_prerequisites(planning_root)

    # Verify specific objects exist with expected properties
    assert project_obj.id == "web-platform"
    assert project_obj.title == "Web Platform"
    assert project_obj.status == "in-progress"

    assert epic_obj.id == "user-authentication"
    assert epic_obj.title == "User Authentication System"
    assert epic_obj.status == "in-progress"

    assert feature_obj.id == "login-system"
    assert feature_obj.title == "Login System Implementation"
    assert feature_obj.status == "in-progress"

    # Verify task prerequisites form a valid chain
    task_by_id = {task.id: task for task in task_objects}

    setup_task = task_by_id["setup-database"]
    assert setup_task.status == "done"
    assert setup_task.prerequisites == []

    reset_task = task_by_id["add-password-reset"]
    assert reset_task.status == "in-progress"
    assert reset_task.prerequisites == ["setup-database"]

    jwt_task = task_by_id["implement-jwt"]
    assert jwt_task.status == "open"
    assert jwt_task.prerequisites == ["add-password-reset"]


def _create_sample_repo_tree(planning_root: Path) -> dict[str, Path]:
    """Create a sample repository tree with ~6 objects for testing.

    Returns a dictionary mapping object names to their file paths.
    """
    current_time = datetime.now().isoformat()

    # Create project structure
    project_dir = planning_root / "projects" / "P-web-platform"
    project_dir.mkdir(parents=True)

    epic_dir = project_dir / "epics" / "E-user-authentication"
    epic_dir.mkdir(parents=True)

    feature_dir = epic_dir / "features" / "F-login-system"
    feature_dir.mkdir(parents=True)

    tasks_open_dir = feature_dir / "tasks-open"
    tasks_open_dir.mkdir(parents=True)

    tasks_done_dir = feature_dir / "tasks-done"
    tasks_done_dir.mkdir(parents=True)

    # Create object files
    files = {}

    # 1. Project object
    project_path = project_dir / "project.md"
    project_content = f"""---
schema_version: "1.0"
kind: project
id: web-platform
title: Web Platform
status: in-progress
priority: high
prerequisites: []
parent: null
created: {current_time}
updated: {current_time}
worktree: null
---
"""
    project_path.write_text(project_content)
    files["project"] = project_path

    # 2. Epic object
    epic_path = epic_dir / "epic.md"
    epic_content = f"""---
schema_version: "1.0"
kind: epic
id: user-authentication
title: User Authentication System
status: in-progress
priority: high
prerequisites: []
parent: web-platform
created: {current_time}
updated: {current_time}
worktree: null
---
"""
    epic_path.write_text(epic_content)
    files["epic"] = epic_path

    # 3. Feature object
    feature_path = feature_dir / "feature.md"
    feature_content = f"""---
schema_version: "1.0"
kind: feature
id: login-system
title: Login System Implementation
status: in-progress
priority: high
prerequisites: []
parent: user-authentication
created: {current_time}
updated: {current_time}
worktree: null
---
"""
    feature_path.write_text(feature_content)
    files["feature"] = feature_path

    # 4. Task (done) - setup-database
    task_done_path = tasks_done_dir / "2025-01-15T10:30:00-T-setup-database.md"
    task_done_content = f"""---
schema_version: "1.0"
kind: task
id: setup-database
title: Setup Database Schema
status: done
priority: high
prerequisites: []
parent: login-system
created: {current_time}
updated: {current_time}
worktree: null
---
"""
    task_done_path.write_text(task_done_content)
    files["task_done"] = task_done_path

    # 5. Task (in-progress) - add-password-reset
    task_in_progress_path = tasks_open_dir / "T-add-password-reset.md"
    task_in_progress_content = f"""---
schema_version: "1.0"
kind: task
id: add-password-reset
title: Add Password Reset Feature
status: in-progress
priority: normal
prerequisites: ["setup-database"]
parent: login-system
created: {current_time}
updated: {current_time}
worktree: null
---
"""
    task_in_progress_path.write_text(task_in_progress_content)
    files["task_in_progress"] = task_in_progress_path

    # 6. Task (open) - implement-jwt
    task_open_path = tasks_open_dir / "T-implement-jwt.md"
    task_open_content = f"""---
schema_version: "1.0"
kind: task
id: implement-jwt
title: Implement JWT Authentication
status: open
priority: normal
prerequisites: ["add-password-reset"]
parent: login-system
created: {current_time}
updated: {current_time}
worktree: null
---
"""
    task_open_path.write_text(task_open_content)
    files["task_open"] = task_open_path

    return files
