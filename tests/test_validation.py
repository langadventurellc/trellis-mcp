"""Tests for validation utilities module.

This module tests the validation functions for checking object relationships
and constraints beyond basic field validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from trellis_mcp.validation import (
    validate_parent_exists,
    validate_parent_exists_for_object,
    validate_required_fields_per_kind,
    validate_enum_membership,
    validate_status_for_kind,
    validate_object_data,
    create_parent_validator,
    CircularDependencyError,
    validate_acyclic_prerequisites,
    get_all_objects,
    build_prerequisites_graph,
    detect_cycle_dfs,
)
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum


class TestValidateParentExists:
    """Test parent existence validation functions."""

    def test_validate_parent_exists_success(self, tmp_path: Path):
        """Test successful parent existence validation."""
        # Create a project structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("---\nkind: project\n---\n")

        # Test that the project exists
        assert validate_parent_exists("test-project", KindEnum.PROJECT, tmp_path / "planning")

    def test_validate_parent_exists_failure(self, tmp_path: Path):
        """Test parent existence validation when parent doesn't exist."""
        # Test non-existent parent
        assert not validate_parent_exists("nonexistent", KindEnum.PROJECT, tmp_path / "planning")

    def test_validate_parent_exists_task_parent_error(self, tmp_path: Path):
        """Test that tasks cannot be parents."""
        with pytest.raises(ValueError, match="Tasks cannot be parents"):
            validate_parent_exists("test-task", KindEnum.TASK, tmp_path / "planning")

    def test_validate_parent_exists_for_object_project_no_parent(self, tmp_path: Path):
        """Test that projects should not have parents."""
        # Valid case: project with no parent
        assert validate_parent_exists_for_object(None, KindEnum.PROJECT, tmp_path / "planning")

        # Invalid case: project with parent
        with pytest.raises(ValueError, match="Projects cannot have parent objects"):
            validate_parent_exists_for_object(
                "some-parent", KindEnum.PROJECT, tmp_path / "planning"
            )

    def test_validate_parent_exists_for_object_epic_requires_parent(self, tmp_path: Path):
        """Test that epics require parents."""
        # Invalid case: epic without parent
        with pytest.raises(ValueError, match="epic objects must have a parent"):
            validate_parent_exists_for_object(None, KindEnum.EPIC, tmp_path / "planning")

    def test_validate_parent_exists_for_object_epic_with_existing_parent(self, tmp_path: Path):
        """Test epic with existing parent project."""
        # Create a project structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("---\nkind: project\n---\n")

        # Valid case: epic with existing parent
        assert validate_parent_exists_for_object(
            "test-project", KindEnum.EPIC, tmp_path / "planning"
        )

        # Also test with P- prefix
        assert validate_parent_exists_for_object(
            "P-test-project", KindEnum.EPIC, tmp_path / "planning"
        )

    def test_validate_parent_exists_for_object_epic_with_nonexistent_parent(self, tmp_path: Path):
        """Test epic with non-existent parent project."""
        with pytest.raises(ValueError, match="Parent project with ID 'nonexistent' does not exist"):
            validate_parent_exists_for_object("nonexistent", KindEnum.EPIC, tmp_path / "planning")

    def test_validate_parent_exists_for_object_feature_with_existing_parent(self, tmp_path: Path):
        """Test feature with existing parent epic."""
        # Create a project and epic structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("---\nkind: project\n---\n")

        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("---\nkind: epic\n---\n")

        # Valid case: feature with existing parent
        assert validate_parent_exists_for_object(
            "test-epic", KindEnum.FEATURE, tmp_path / "planning"
        )

        # Also test with E- prefix
        assert validate_parent_exists_for_object(
            "E-test-epic", KindEnum.FEATURE, tmp_path / "planning"
        )

    def test_validate_parent_exists_for_object_task_with_existing_parent(self, tmp_path: Path):
        """Test task with existing parent feature."""
        # Create a project, epic, and feature structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("---\nkind: project\n---\n")

        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("---\nkind: epic\n---\n")

        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("---\nkind: feature\n---\n")

        # Valid case: task with existing parent
        assert validate_parent_exists_for_object(
            "test-feature", KindEnum.TASK, tmp_path / "planning"
        )

        # Also test with F- prefix
        assert validate_parent_exists_for_object(
            "F-test-feature", KindEnum.TASK, tmp_path / "planning"
        )


class TestValidateRequiredFields:
    """Test required fields validation."""

    def test_validate_required_fields_project_complete(self):
        """Test project with all required fields."""
        data = {
            "kind": "project",
            "id": "P-test",
            "status": "draft",
            "title": "Test Project",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        missing = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        assert missing == []

    def test_validate_required_fields_project_missing_fields(self):
        """Test project with missing required fields."""
        data = {
            "kind": "project",
            "title": "Test Project",
        }

        missing = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        expected_missing = {"id", "status", "created", "updated", "schema_version"}
        assert set(missing) == expected_missing

    def test_validate_required_fields_epic_complete(self):
        """Test epic with all required fields."""
        data = {
            "kind": "epic",
            "id": "E-test",
            "parent": "P-test-project",
            "status": "draft",
            "title": "Test Epic",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        missing = validate_required_fields_per_kind(data, KindEnum.EPIC)
        assert missing == []

    def test_validate_required_fields_epic_missing_parent(self):
        """Test epic with missing parent field."""
        data = {
            "kind": "epic",
            "id": "E-test",
            "status": "draft",
            "title": "Test Epic",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        missing = validate_required_fields_per_kind(data, KindEnum.EPIC)
        assert "parent" in missing

    def test_validate_required_fields_task_complete(self):
        """Test task with all required fields."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": "F-test-feature",
            "status": "open",
            "title": "Test Task",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        missing = validate_required_fields_per_kind(data, KindEnum.TASK)
        assert missing == []


class TestValidateEnumMembership:
    """Test enum membership validation."""

    def test_validate_enum_membership_valid(self):
        """Test data with valid enum values."""
        data = {"kind": "project", "status": "draft", "priority": "high"}

        errors = validate_enum_membership(data)
        assert errors == []

    def test_validate_enum_membership_invalid_kind(self):
        """Test data with invalid kind enum."""
        data = {"kind": "invalid_kind", "status": "draft", "priority": "high"}

        errors = validate_enum_membership(data)
        assert len(errors) == 1
        assert "Invalid kind" in errors[0]
        assert "invalid_kind" in errors[0]

    def test_validate_enum_membership_invalid_status(self):
        """Test data with invalid status enum."""
        data = {"kind": "project", "status": "invalid_status", "priority": "high"}

        errors = validate_enum_membership(data)
        assert len(errors) == 1
        assert "Invalid status" in errors[0]
        assert "invalid_status" in errors[0]

    def test_validate_enum_membership_invalid_priority(self):
        """Test data with invalid priority enum."""
        data = {"kind": "project", "status": "draft", "priority": "invalid_priority"}

        errors = validate_enum_membership(data)
        assert len(errors) == 1
        assert "Invalid priority" in errors[0]
        assert "invalid_priority" in errors[0]

    def test_validate_enum_membership_multiple_invalid(self):
        """Test data with multiple invalid enum values."""
        data = {"kind": "invalid_kind", "status": "invalid_status", "priority": "invalid_priority"}

        errors = validate_enum_membership(data)
        assert len(errors) == 3


class TestValidateStatusForKind:
    """Test status validation per object kind."""

    def test_validate_status_for_project_valid(self):
        """Test valid statuses for projects."""
        valid_statuses = [StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE]

        for status in valid_statuses:
            assert validate_status_for_kind(status, KindEnum.PROJECT)

    def test_validate_status_for_project_invalid(self):
        """Test invalid status for projects."""
        with pytest.raises(ValueError, match="Invalid status 'open' for project"):
            validate_status_for_kind(StatusEnum.OPEN, KindEnum.PROJECT)

    def test_validate_status_for_task_valid(self):
        """Test valid statuses for tasks."""
        valid_statuses = [
            StatusEnum.OPEN,
            StatusEnum.IN_PROGRESS,
            StatusEnum.REVIEW,
            StatusEnum.DONE,
        ]

        for status in valid_statuses:
            assert validate_status_for_kind(status, KindEnum.TASK)

    def test_validate_status_for_task_invalid(self):
        """Test invalid status for tasks."""
        with pytest.raises(ValueError, match="Invalid status 'draft' for task"):
            validate_status_for_kind(StatusEnum.DRAFT, KindEnum.TASK)

    def test_validate_status_for_epic_valid(self):
        """Test valid statuses for epics."""
        valid_statuses = [StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE]

        for status in valid_statuses:
            assert validate_status_for_kind(status, KindEnum.EPIC)

    def test_validate_status_for_feature_valid(self):
        """Test valid statuses for features."""
        valid_statuses = [StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE]

        for status in valid_statuses:
            assert validate_status_for_kind(status, KindEnum.FEATURE)


class TestValidateObjectData:
    """Test comprehensive object data validation."""

    def test_validate_object_data_project_valid(self, tmp_path: Path):
        """Test valid project data."""
        data = {
            "kind": "project",
            "id": "P-test",
            "status": "draft",
            "title": "Test Project",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert errors == []

    def test_validate_object_data_project_invalid_status(self, tmp_path: Path):
        """Test project with invalid status."""
        data = {
            "kind": "project",
            "id": "P-test",
            "status": "open",  # Invalid for project
            "title": "Test Project",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert len(errors) == 1
        assert "Invalid status" in errors[0]

    def test_validate_object_data_epic_with_existing_parent(self, tmp_path: Path):
        """Test epic with existing parent project."""
        # Create project structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("---\nkind: project\n---\n")

        data = {
            "kind": "epic",
            "id": "E-test",
            "parent": "P-test-project",
            "status": "draft",
            "title": "Test Epic",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert errors == []

    def test_validate_object_data_epic_with_nonexistent_parent(self, tmp_path: Path):
        """Test epic with non-existent parent project."""
        data = {
            "kind": "epic",
            "id": "E-test",
            "parent": "P-nonexistent",
            "status": "draft",
            "title": "Test Epic",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert len(errors) == 1
        assert "Parent project with ID" in errors[0]
        assert "does not exist" in errors[0]

    def test_validate_object_data_missing_kind(self, tmp_path: Path):
        """Test data without kind field."""
        data = {
            "id": "test",
            "status": "draft",
            "title": "Test",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert len(errors) == 1
        assert "Missing 'kind' field" in errors[0]

    def test_validate_object_data_invalid_kind(self, tmp_path: Path):
        """Test data with invalid kind field."""
        data = {
            "kind": "invalid_kind",
            "id": "test",
            "status": "draft",
            "title": "Test",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert len(errors) == 1
        assert "Invalid kind 'invalid_kind'" in errors[0]

    def test_validate_object_data_missing_required_fields(self, tmp_path: Path):
        """Test data with missing required fields."""
        data = {
            "kind": "project",
            "title": "Test Project",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]

    def test_validate_object_data_multiple_errors(self, tmp_path: Path):
        """Test data with multiple validation errors."""
        data = {
            "kind": "epic",
            "id": "E-test",
            "parent": "P-nonexistent",
            "status": "invalid_status",
            "title": "Test Epic",
            "priority": "invalid_priority",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.0",
        }

        errors = validate_object_data(data, tmp_path / "planning")
        assert len(errors) >= 3  # Should have multiple errors

        # Check that we have the expected error types
        error_text = " ".join(errors)
        assert "Invalid status" in error_text
        assert "Invalid priority" in error_text
        assert "does not exist" in error_text


class TestCreateParentValidator:
    """Test the Pydantic parent validator factory."""

    def test_create_parent_validator_returns_function(self, tmp_path: Path):
        """Test that create_parent_validator returns a function."""
        validator = create_parent_validator(tmp_path / "planning")
        assert callable(validator)

    def test_parent_validator_with_no_context(self, tmp_path: Path):
        """Test parent validator with no context information."""
        validator = create_parent_validator(tmp_path / "planning")

        # Mock ValidationInfo with no data
        class MockInfo:
            data = None

        # Should return parent_id unchanged when no context
        result = validator("test-parent", MockInfo())
        assert result == "test-parent"

    def test_parent_validator_with_project_kind(self, tmp_path: Path):
        """Test parent validator with project kind."""
        validator = create_parent_validator(tmp_path / "planning")

        # Mock ValidationInfo with project kind
        class MockInfo:
            data = {"kind": "project"}

        # Should pass for project with no parent
        result = validator(None, MockInfo())
        assert result is None

        # Should raise for project with parent
        with pytest.raises(ValueError, match="Projects cannot have parent objects"):
            validator("some-parent", MockInfo())

    def test_parent_validator_with_invalid_kind(self, tmp_path: Path):
        """Test parent validator with invalid kind."""
        validator = create_parent_validator(tmp_path / "planning")

        # Mock ValidationInfo with invalid kind
        class MockInfo:
            data = {"kind": "invalid_kind"}

        # Should return parent_id unchanged for invalid kind
        result = validator("test-parent", MockInfo())
        assert result == "test-parent"


class TestCircularDependencyError:
    """Test the CircularDependencyError exception class."""

    def test_circular_dependency_error_creation(self):
        """Test creating a CircularDependencyError with cycle path."""
        cycle_path = ["task1", "task2", "task3", "task1"]
        error = CircularDependencyError(cycle_path)

        assert error.cycle_path == cycle_path
        assert "Circular dependency detected: task1 -> task2 -> task3 -> task1" in str(error)

    def test_circular_dependency_error_short_cycle(self):
        """Test creating a CircularDependencyError with short cycle."""
        cycle_path = ["task1", "task1"]
        error = CircularDependencyError(cycle_path)

        assert error.cycle_path == cycle_path
        assert "Circular dependency detected: task1 -> task1" in str(error)


class TestGetAllObjects:
    """Test the get_all_objects function."""

    def test_get_all_objects_empty_directory(self, tmp_path: Path):
        """Test getting objects from empty directory."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        objects = get_all_objects(planning_dir)
        assert objects == {}

    def test_get_all_objects_nonexistent_directory(self, tmp_path: Path):
        """Test getting objects from non-existent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            get_all_objects(nonexistent_dir)

    def test_get_all_objects_with_project(self, tmp_path: Path):
        """Test getting objects with a single project."""
        # Create project structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        project_file = project_dir / "project.md"
        project_file.write_text(
            """---
kind: project
id: test-project
status: draft
title: Test Project
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Test project description
"""
        )

        objects = get_all_objects(tmp_path / "planning")
        assert len(objects) == 1
        assert "test-project" in objects
        assert objects["test-project"]["kind"] == "project"
        assert objects["test-project"]["title"] == "Test Project"

    def test_get_all_objects_with_hierarchy(self, tmp_path: Path):
        """Test getting objects with full hierarchy."""
        # Create project
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        project_file = project_dir / "project.md"
        project_file.write_text(
            """---
kind: project
id: test-project
status: draft
title: Test Project
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Test project description
"""
        )

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        epic_file = epic_dir / "epic.md"
        epic_file.write_text(
            """---
kind: epic
id: test-epic
parent: test-project
status: draft
title: Test Epic
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Test epic description
"""
        )

        # Create feature
        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)

        feature_file = feature_dir / "feature.md"
        feature_file.write_text(
            """---
kind: feature
id: test-feature
parent: test-epic
status: draft
title: Test Feature
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Test feature description
"""
        )

        # Create task
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)

        task_file = task_dir / "T-test-task.md"
        task_file.write_text(
            """---
kind: task
id: test-task
parent: test-feature
status: open
title: Test Task
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Test task description
"""
        )

        objects = get_all_objects(tmp_path / "planning")
        assert len(objects) == 4
        assert "test-project" in objects
        assert "test-epic" in objects
        assert "test-feature" in objects
        assert "test-task" in objects


class TestBuildPrerequisitesGraph:
    """Test the build_prerequisites_graph function."""

    def test_build_prerequisites_graph_empty(self):
        """Test building graph with no objects."""
        objects = {}
        graph = build_prerequisites_graph(objects)
        assert graph == {}

    def test_build_prerequisites_graph_no_prerequisites(self):
        """Test building graph with objects but no prerequisites."""
        objects = {
            "task1": {"id": "task1", "prerequisites": []},
            "task2": {"id": "task2", "prerequisites": []},
        }
        graph = build_prerequisites_graph(objects)

        assert graph == {
            "task1": [],
            "task2": [],
        }

    def test_build_prerequisites_graph_with_prerequisites(self):
        """Test building graph with prerequisites."""
        objects = {
            "task1": {"id": "task1", "prerequisites": ["task2"]},
            "task2": {"id": "task2", "prerequisites": ["task3"]},
            "task3": {"id": "task3", "prerequisites": []},
        }
        graph = build_prerequisites_graph(objects)

        assert graph == {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": [],
        }

    def test_build_prerequisites_graph_with_prefixes(self):
        """Test building graph with prefixed IDs."""
        objects = {
            "T-task1": {"id": "T-task1", "prerequisites": ["T-task2"]},
            "T-task2": {"id": "T-task2", "prerequisites": ["T-task3"]},
            "T-task3": {"id": "T-task3", "prerequisites": []},
        }
        graph = build_prerequisites_graph(objects)

        assert graph == {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": [],
        }


class TestDetectCycleDFS:
    """Test the detect_cycle_dfs function."""

    def test_detect_cycle_dfs_no_cycle(self):
        """Test cycle detection with no cycles."""
        graph = {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": [],
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is None

    def test_detect_cycle_dfs_simple_cycle(self):
        """Test cycle detection with simple cycle."""
        graph = {
            "task1": ["task2"],
            "task2": ["task1"],
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert len(cycle) == 3  # A -> B -> A has 3 elements
        assert cycle[0] == cycle[-1]  # Cycle should end with the same node it starts

    def test_detect_cycle_dfs_self_cycle(self):
        """Test cycle detection with self-referencing cycle."""
        graph = {
            "task1": ["task1"],
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert cycle == ["task1", "task1"]

    def test_detect_cycle_dfs_complex_cycle(self):
        """Test cycle detection with complex cycle."""
        graph = {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": ["task4"],
            "task4": ["task2"],  # Cycle: task2 -> task3 -> task4 -> task2
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert len(cycle) >= 3  # At least 3 nodes in cycle
        assert cycle[0] == cycle[-1]  # Cycle should end with the same node it starts

    def test_detect_cycle_dfs_multiple_components(self):
        """Test cycle detection with multiple disconnected components."""
        graph = {
            "task1": ["task2"],
            "task2": [],
            "task3": ["task4"],
            "task4": ["task3"],  # Cycle in second component
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert len(cycle) == 3  # A -> B -> A has 3 elements
        assert cycle[0] == cycle[-1]  # Cycle should end with the same node it starts


class TestValidateAcyclicPrerequisites:
    """Test the validate_acyclic_prerequisites function."""

    def test_validate_acyclic_prerequisites_empty_project(self, tmp_path: Path):
        """Test validation with empty project."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        errors = validate_acyclic_prerequisites(planning_dir)
        assert errors == []

    def test_validate_acyclic_prerequisites_no_cycles(self, tmp_path: Path):
        """Test validation with no cycles."""
        # Create project structure with no cycles
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature
        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)

        # Create tasks with linear dependencies
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)

        # Task 1 (no prerequisites)
        task1_file = task_dir / "T-task1.md"
        task1_file.write_text(
            """---
kind: task
id: task1
parent: test-feature
status: open
title: Task 1
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Task 1 description
"""
        )

        # Task 2 (depends on task1)
        task2_file = task_dir / "T-task2.md"
        task2_file.write_text(
            """---
kind: task
id: task2
parent: test-feature
status: open
title: Task 2
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Task 2 description
"""
        )

        errors = validate_acyclic_prerequisites(tmp_path / "planning")
        assert errors == []

    def test_validate_acyclic_prerequisites_with_cycle(self, tmp_path: Path):
        """Test validation with cycle detection."""
        # Create project structure with cycle
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature
        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)

        # Create tasks with circular dependencies
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)

        # Task 1 (depends on task2)
        task1_file = task_dir / "T-task1.md"
        task1_file.write_text(
            """---
kind: task
id: task1
parent: test-feature
status: open
title: Task 1
priority: normal
prerequisites: ["task2"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Task 1 description
"""
        )

        # Task 2 (depends on task1 - creates cycle)
        task2_file = task_dir / "T-task2.md"
        task2_file.write_text(
            """---
kind: task
id: task2
parent: test-feature
status: open
title: Task 2
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Task 2 description
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert len(error.cycle_path) >= 2
        assert "Circular dependency detected" in str(error)

    def test_validate_acyclic_prerequisites_self_reference(self, tmp_path: Path):
        """Test validation with self-referencing cycle."""
        # Create project structure with self-referencing task
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature
        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)

        # Create task that depends on itself
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)

        task_file = task_dir / "T-task1.md"
        task_file.write_text(
            """---
kind: task
id: task1
parent: test-feature
status: open
title: Task 1
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---
Task 1 description
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert error.cycle_path == ["task1", "task1"]
        assert "Circular dependency detected: task1 -> task1" in str(error)

    def test_validate_acyclic_prerequisites_nonexistent_directory(self, tmp_path: Path):
        """Test validation with non-existent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        errors = validate_acyclic_prerequisites(nonexistent_dir)
        assert len(errors) == 1
        assert "Error validating prerequisites" in errors[0]
