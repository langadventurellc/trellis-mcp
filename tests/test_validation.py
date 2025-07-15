"""Tests for validation utilities module.

This module tests the validation functions for checking object relationships
and constraints beyond basic field validation.
"""

from pathlib import Path

import pytest

from trellis_mcp.validation import (
    validate_parent_exists,
    validate_parent_exists_for_object,
    validate_required_fields_per_kind,
    validate_enum_membership,
    validate_status_for_kind,
    validate_object_data,
    validate_front_matter,
    enforce_status_transition,
    CircularDependencyError,
    TrellisValidationError,
    validate_acyclic_prerequisites,
    get_all_objects,
    build_prerequisites_graph,
    detect_cycle_dfs,
    check_prereq_cycles,
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
        project_file.write_text("---\nkind: project\npriority: normal\n---\n")

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
        project_file.write_text("---\nkind: project\npriority: normal\n---\n")

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
        project_file.write_text("---\nkind: project\npriority: normal\n---\n")

        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("---\nkind: epic\npriority: normal\n---\n")

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
        project_file.write_text("---\nkind: project\npriority: normal\n---\n")

        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("---\nkind: epic\npriority: normal\n---\n")

        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_file.write_text("---\nkind: feature\npriority: normal\n---\n")

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

        # Should not raise any exception
        validate_object_data(data, tmp_path / "planning")

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

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Invalid status" in error.errors[0]

    def test_validate_object_data_epic_with_existing_parent(self, tmp_path: Path):
        """Test epic with existing parent project."""
        # Create project structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("---\nkind: project\npriority: normal\n---\n")

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

        # Should not raise any exception
        validate_object_data(data, tmp_path / "planning")

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

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Parent project with ID" in error.errors[0]
        assert "does not exist" in error.errors[0]

    def test_validate_object_data_missing_kind(self, tmp_path: Path):
        """Test data without kind field."""
        data = {
            "id": "test",
            "status": "draft",
            "title": "Test",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Missing 'kind' field" in error.errors[0]

    def test_validate_object_data_invalid_kind(self, tmp_path: Path):
        """Test data with invalid kind field."""
        data = {
            "kind": "invalid_kind",
            "id": "test",
            "status": "draft",
            "title": "Test",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Invalid kind 'invalid_kind'" in error.errors[0]

    def test_validate_object_data_missing_required_fields(self, tmp_path: Path):
        """Test data with missing required fields."""
        data = {
            "kind": "project",
            "title": "Test Project",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Missing required fields" in error.errors[0]

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

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) >= 3  # Should have multiple errors

        # Check that we have the expected error types
        error_text = " ".join(error.errors)
        assert "Invalid status" in error_text
        assert "Invalid priority" in error_text
        assert "does not exist" in error_text


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


class TestCheckPrereqCycles:
    """Test the check_prereq_cycles function."""

    def test_check_prereq_cycles_empty_project(self, tmp_path: Path):
        """Test cycle check with empty project."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        result = check_prereq_cycles(planning_dir)
        assert result is True

    def test_check_prereq_cycles_no_cycles(self, tmp_path: Path):
        """Test cycle check with no cycles."""
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

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is True

    def test_check_prereq_cycles_with_cycle(self, tmp_path: Path):
        """Test cycle check with cycle detection."""
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

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is False

    def test_check_prereq_cycles_self_reference(self, tmp_path: Path):
        """Test cycle check with self-referencing cycle."""
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

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is False

    def test_check_prereq_cycles_nonexistent_directory(self, tmp_path: Path):
        """Test cycle check with non-existent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        result = check_prereq_cycles(nonexistent_dir)
        assert result is False

    def test_check_prereq_cycles_complex_valid_structure(self, tmp_path: Path):
        """Test cycle check with complex valid structure."""
        # Create project structure with multiple features and tasks
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature 1
        feature1_dir = epic_dir / "features" / "F-feature1"
        feature1_dir.mkdir(parents=True)
        task1_dir = feature1_dir / "tasks-open"
        task1_dir.mkdir(parents=True)

        # Create feature 2
        feature2_dir = epic_dir / "features" / "F-feature2"
        feature2_dir.mkdir(parents=True)
        task2_dir = feature2_dir / "tasks-open"
        task2_dir.mkdir(parents=True)

        # Task in feature 1
        task1_file = task1_dir / "T-task1.md"
        task1_file.write_text(
            """---
kind: task
id: task1
parent: feature1
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

        # Task in feature 2 that depends on task1
        task2_file = task2_dir / "T-task2.md"
        task2_file.write_text(
            """---
kind: task
id: task2
parent: feature2
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

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is True

    def test_check_prereq_cycles_with_string_path(self, tmp_path: Path):
        """Test cycle check with string path parameter."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        # Test with string path
        result = check_prereq_cycles(str(planning_dir))
        assert result is True

    def test_check_prereq_cycles_with_path_object(self, tmp_path: Path):
        """Test cycle check with Path object parameter."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        # Test with Path object
        result = check_prereq_cycles(planning_dir)
        assert result is True


class TestValidateFrontMatter:
    """Test the validate_front_matter function."""

    def test_validate_front_matter_valid_project(self):
        """Test valid project front matter."""
        yaml_dict = {
            "kind": "project",
            "id": "test-project",
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "project")
        assert errors == []

    def test_validate_front_matter_valid_project_with_enum(self):
        """Test valid project front matter with KindEnum."""
        yaml_dict = {
            "kind": "project",
            "id": "test-project",
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, KindEnum.PROJECT)
        assert errors == []

    def test_validate_front_matter_valid_task(self):
        """Test valid task front matter."""
        yaml_dict = {
            "kind": "task",
            "id": "test-task",
            "parent": "test-feature",
            "status": "open",
            "title": "Test Task",
            "priority": "high",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "task")
        assert errors == []

    def test_validate_front_matter_valid_epic(self):
        """Test valid epic front matter."""
        yaml_dict = {
            "kind": "epic",
            "id": "test-epic",
            "parent": "test-project",
            "status": "draft",
            "title": "Test Epic",
            "priority": "low",
            "prerequisites": ["other-epic"],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "epic")
        assert errors == []

    def test_validate_front_matter_valid_feature(self):
        """Test valid feature front matter."""
        yaml_dict = {
            "kind": "feature",
            "id": "test-feature",
            "parent": "test-epic",
            "status": "in-progress",
            "title": "Test Feature",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "feature")
        assert errors == []

    def test_validate_front_matter_invalid_kind(self):
        """Test invalid kind parameter."""
        yaml_dict = {
            "kind": "project",
            "id": "test-project",
            "status": "draft",
            "title": "Test Project",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "invalid-kind")
        assert len(errors) == 1
        assert "Invalid kind 'invalid-kind'" in errors[0]

    def test_validate_front_matter_missing_required_fields(self):
        """Test missing required fields."""
        yaml_dict = {
            "kind": "project",
            "title": "Test Project",
        }

        errors = validate_front_matter(yaml_dict, "project")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]
        assert "id" in errors[0]
        assert "status" in errors[0]

    def test_validate_front_matter_missing_parent_for_epic(self):
        """Test missing parent field for epic."""
        yaml_dict = {
            "kind": "epic",
            "id": "test-epic",
            "status": "draft",
            "title": "Test Epic",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "epic")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]
        assert "parent" in errors[0]

    def test_validate_front_matter_missing_parent_for_feature(self):
        """Test missing parent field for feature."""
        yaml_dict = {
            "kind": "feature",
            "id": "test-feature",
            "status": "draft",
            "title": "Test Feature",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "feature")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]
        assert "parent" in errors[0]

    def test_validate_front_matter_missing_parent_for_task(self):
        """Test missing parent field for task."""
        yaml_dict = {
            "kind": "task",
            "id": "test-task",
            "status": "open",
            "title": "Test Task",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "task")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]
        assert "parent" in errors[0]

    def test_validate_front_matter_invalid_enum_values(self):
        """Test invalid enum values."""
        yaml_dict = {
            "kind": "invalid-kind",
            "id": "test-project",
            "status": "invalid-status",
            "title": "Test Project",
            "priority": "invalid-priority",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "project")
        assert len(errors) == 3

        # Check that we have all expected errors
        error_text = " ".join(errors)
        assert "Invalid kind" in error_text
        assert "Invalid status" in error_text
        assert "Invalid priority" in error_text

    def test_validate_front_matter_invalid_status_for_kind(self):
        """Test invalid status for specific kind."""
        yaml_dict = {
            "kind": "project",
            "id": "test-project",
            "status": "open",  # Invalid for project
            "title": "Test Project",
            "priority": "normal",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "project")
        assert len(errors) == 1
        assert "Invalid status 'open' for project" in errors[0]

    def test_validate_front_matter_invalid_task_status(self):
        """Test invalid status for task."""
        yaml_dict = {
            "kind": "task",
            "id": "test-task",
            "parent": "test-feature",
            "status": "draft",  # Invalid for task
            "title": "Test Task",
            "priority": "normal",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "task")
        assert len(errors) == 1
        assert "Invalid status 'draft' for task" in errors[0]

    def test_validate_front_matter_valid_all_task_statuses(self):
        """Test all valid task statuses."""
        valid_statuses = ["open", "in-progress", "review", "done"]

        for status in valid_statuses:
            yaml_dict = {
                "kind": "task",
                "id": "test-task",
                "parent": "test-feature",
                "status": status,
                "title": "Test Task",
                "priority": "normal",
                "created": "2023-01-01T00:00:00Z",
                "updated": "2023-01-01T00:00:00Z",
                "schema_version": "1.0",
            }

            errors = validate_front_matter(yaml_dict, "task")
            assert errors == [], f"Expected no errors for status '{status}', got: {errors}"

    def test_validate_front_matter_valid_all_project_statuses(self):
        """Test all valid project statuses."""
        valid_statuses = ["draft", "in-progress", "done"]

        for status in valid_statuses:
            yaml_dict = {
                "kind": "project",
                "id": "test-project",
                "status": status,
                "title": "Test Project",
                "priority": "normal",
                "created": "2023-01-01T00:00:00Z",
                "updated": "2023-01-01T00:00:00Z",
                "schema_version": "1.0",
            }

            errors = validate_front_matter(yaml_dict, "project")
            assert errors == [], f"Expected no errors for status '{status}', got: {errors}"

    def test_validate_front_matter_missing_status(self):
        """Test missing status field."""
        yaml_dict = {
            "kind": "project",
            "id": "test-project",
            "title": "Test Project",
            "priority": "normal",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "project")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]
        assert "status" in errors[0]

    def test_validate_front_matter_null_status(self):
        """Test null status field."""
        yaml_dict = {
            "kind": "project",
            "id": "test-project",
            "status": None,
            "title": "Test Project",
            "priority": "normal",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "project")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]
        assert "status" in errors[0]

    def test_validate_front_matter_multiple_errors(self):
        """Test multiple validation errors."""
        yaml_dict = {
            "kind": "epic",
            "id": "test-epic",
            "status": "open",  # Invalid for epic
            "title": "Test Epic",
            "priority": "invalid-priority",  # Invalid priority
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        errors = validate_front_matter(yaml_dict, "epic")
        assert len(errors) == 3

        # Check that we have all expected errors
        error_text = " ".join(errors)
        assert "Missing required fields" in error_text
        assert "parent" in error_text
        assert "Invalid priority" in error_text
        assert "Invalid status" in error_text

    def test_validate_front_matter_empty_dict(self):
        """Test empty YAML dictionary."""
        yaml_dict = {}

        errors = validate_front_matter(yaml_dict, "project")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]

    def test_validate_front_matter_valid_priorities(self):
        """Test all valid priority values."""
        valid_priorities = ["high", "normal", "low"]

        for priority in valid_priorities:
            yaml_dict = {
                "kind": "project",
                "id": "test-project",
                "status": "draft",
                "title": "Test Project",
                "priority": priority,
                "created": "2023-01-01T00:00:00Z",
                "updated": "2023-01-01T00:00:00Z",
                "schema_version": "1.0",
            }

            errors = validate_front_matter(yaml_dict, "project")
            assert errors == [], f"Expected no errors for priority '{priority}', got: {errors}"


class TestEnforceStatusTransition:
    """Test status transition enforcement function."""

    def test_enforce_status_transition_same_status(self):
        """Test transition from status to itself is always valid."""
        # Same status should always be valid regardless of kind
        assert enforce_status_transition(StatusEnum.OPEN, StatusEnum.OPEN, KindEnum.TASK) is True
        assert enforce_status_transition("draft", "draft", "project") is True
        assert enforce_status_transition(StatusEnum.DONE, StatusEnum.DONE, KindEnum.FEATURE) is True

    def test_enforce_status_transition_task_valid_transitions(self):
        """Test valid task status transitions."""
        # open → in-progress
        assert (
            enforce_status_transition(StatusEnum.OPEN, StatusEnum.IN_PROGRESS, KindEnum.TASK)
            is True
        )
        assert enforce_status_transition("open", "in-progress", "task") is True

        # open → done
        assert enforce_status_transition(StatusEnum.OPEN, StatusEnum.DONE, KindEnum.TASK) is True
        assert enforce_status_transition("open", "done", "task") is True

        # in-progress → review
        assert (
            enforce_status_transition(StatusEnum.IN_PROGRESS, StatusEnum.REVIEW, KindEnum.TASK)
            is True
        )
        assert enforce_status_transition("in-progress", "review", "task") is True

        # in-progress → done
        assert (
            enforce_status_transition(StatusEnum.IN_PROGRESS, StatusEnum.DONE, KindEnum.TASK)
            is True
        )
        assert enforce_status_transition("in-progress", "done", "task") is True

        # review → done
        assert enforce_status_transition(StatusEnum.REVIEW, StatusEnum.DONE, KindEnum.TASK) is True
        assert enforce_status_transition("review", "done", "task") is True

    def test_enforce_status_transition_task_invalid_transitions(self):
        """Test invalid task status transitions."""
        # open → review (skipping in-progress)
        with pytest.raises(ValueError, match="Invalid status transition for task"):
            enforce_status_transition(StatusEnum.OPEN, StatusEnum.REVIEW, KindEnum.TASK)

        # in-progress → open (backwards)
        with pytest.raises(ValueError, match="Invalid status transition for task"):
            enforce_status_transition("in-progress", "open", "task")

        # review → open (backwards)
        with pytest.raises(ValueError, match="Invalid status transition for task"):
            enforce_status_transition("review", "open", "task")

        # review → in-progress (backwards)
        with pytest.raises(ValueError, match="Invalid status transition for task"):
            enforce_status_transition("review", "in-progress", "task")

        # done → any status (terminal)
        with pytest.raises(ValueError, match="terminal status"):
            enforce_status_transition(StatusEnum.DONE, StatusEnum.OPEN, KindEnum.TASK)

        # open → draft (invalid status for task)
        with pytest.raises(ValueError, match="Invalid status transition for task"):
            enforce_status_transition("open", "draft", "task")

        # draft → open (invalid status for task)
        with pytest.raises(ValueError, match="Invalid status transition for task"):
            enforce_status_transition("draft", "open", "task")

    def test_enforce_status_transition_project_valid_transitions(self):
        """Test valid project status transitions."""
        # draft → in-progress
        assert (
            enforce_status_transition(StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, KindEnum.PROJECT)
            is True
        )
        assert enforce_status_transition("draft", "in-progress", "project") is True

        # in-progress → done
        assert (
            enforce_status_transition(StatusEnum.IN_PROGRESS, StatusEnum.DONE, KindEnum.PROJECT)
            is True
        )
        assert enforce_status_transition("in-progress", "done", "project") is True

    def test_enforce_status_transition_project_invalid_transitions(self):
        """Test invalid project status transitions."""
        # draft → done (skipping in-progress)
        with pytest.raises(ValueError, match="Invalid status transition for project"):
            enforce_status_transition(StatusEnum.DRAFT, StatusEnum.DONE, KindEnum.PROJECT)

        # in-progress → draft (backwards)
        with pytest.raises(ValueError, match="Invalid status transition for project"):
            enforce_status_transition("in-progress", "draft", "project")

        # done → any status (terminal)
        with pytest.raises(ValueError, match="terminal status"):
            enforce_status_transition(StatusEnum.DONE, StatusEnum.DRAFT, KindEnum.PROJECT)

        # draft → open (invalid status for project)
        with pytest.raises(ValueError, match="Invalid status transition for project"):
            enforce_status_transition("draft", "open", "project")

    def test_enforce_status_transition_epic_valid_transitions(self):
        """Test valid epic status transitions."""
        # draft → in-progress
        assert (
            enforce_status_transition(StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, KindEnum.EPIC)
            is True
        )
        assert enforce_status_transition("draft", "in-progress", "epic") is True

        # in-progress → done
        assert (
            enforce_status_transition(StatusEnum.IN_PROGRESS, StatusEnum.DONE, KindEnum.EPIC)
            is True
        )
        assert enforce_status_transition("in-progress", "done", "epic") is True

    def test_enforce_status_transition_epic_invalid_transitions(self):
        """Test invalid epic status transitions."""
        # draft → done (skipping in-progress)
        with pytest.raises(ValueError, match="Invalid status transition for epic"):
            enforce_status_transition(StatusEnum.DRAFT, StatusEnum.DONE, KindEnum.EPIC)

        # in-progress → draft (backwards)
        with pytest.raises(ValueError, match="Invalid status transition for epic"):
            enforce_status_transition("in-progress", "draft", "epic")

        # done → any status (terminal)
        with pytest.raises(ValueError, match="terminal status"):
            enforce_status_transition(StatusEnum.DONE, StatusEnum.DRAFT, KindEnum.EPIC)

        # draft → review (invalid status for epic)
        with pytest.raises(ValueError, match="Invalid status transition for epic"):
            enforce_status_transition("draft", "review", "epic")

    def test_enforce_status_transition_feature_valid_transitions(self):
        """Test valid feature status transitions."""
        # draft → in-progress
        assert (
            enforce_status_transition(StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, KindEnum.FEATURE)
            is True
        )
        assert enforce_status_transition("draft", "in-progress", "feature") is True

        # in-progress → done
        assert (
            enforce_status_transition(StatusEnum.IN_PROGRESS, StatusEnum.DONE, KindEnum.FEATURE)
            is True
        )
        assert enforce_status_transition("in-progress", "done", "feature") is True

    def test_enforce_status_transition_feature_invalid_transitions(self):
        """Test invalid feature status transitions."""
        # draft → done (skipping in-progress)
        with pytest.raises(ValueError, match="Invalid status transition for feature"):
            enforce_status_transition(StatusEnum.DRAFT, StatusEnum.DONE, KindEnum.FEATURE)

        # in-progress → draft (backwards)
        with pytest.raises(ValueError, match="Invalid status transition for feature"):
            enforce_status_transition("in-progress", "draft", "feature")

        # done → any status (terminal)
        with pytest.raises(ValueError, match="terminal status"):
            enforce_status_transition(StatusEnum.DONE, StatusEnum.DRAFT, KindEnum.FEATURE)

        # draft → open (invalid status for feature)
        with pytest.raises(ValueError, match="Invalid status transition for feature"):
            enforce_status_transition("draft", "open", "feature")

    def test_enforce_status_transition_invalid_input_parameters(self):
        """Test error handling for invalid input parameters."""
        # Invalid old status
        with pytest.raises(ValueError, match="Invalid old status"):
            enforce_status_transition("invalid-status", "done", "task")

        # Invalid new status
        with pytest.raises(ValueError, match="Invalid new status"):
            enforce_status_transition("open", "invalid-status", "task")

        # Invalid kind
        with pytest.raises(ValueError, match="Invalid kind"):
            enforce_status_transition("open", "done", "invalid-kind")

    def test_enforce_status_transition_mixed_string_enum_parameters(self):
        """Test function works with mixed string and enum parameters."""
        # Mix of string and enum parameters
        assert enforce_status_transition(StatusEnum.OPEN, "in-progress", KindEnum.TASK) is True
        assert enforce_status_transition("open", StatusEnum.IN_PROGRESS, "task") is True
        assert enforce_status_transition(StatusEnum.OPEN, StatusEnum.IN_PROGRESS, "task") is True
        assert enforce_status_transition("open", "in-progress", KindEnum.TASK) is True

    def test_enforce_status_transition_error_messages(self):
        """Test that error messages are clear and helpful."""
        # Test error message format for invalid transitions
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("open", "review", "task")

        error_msg = str(exc_info.value)
        assert "Invalid status transition for task" in error_msg
        assert "'open' cannot transition to 'review'" in error_msg
        assert "Valid transitions: done, in-progress" in error_msg

        # Test error message for terminal status
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("done", "open", "task")

        error_msg = str(exc_info.value)
        assert "Invalid status transition for task" in error_msg
        assert "'done' is a terminal status" in error_msg

    def test_enforce_status_transition_comprehensive_task_transitions(self):
        """Test comprehensive task transition matrix."""
        # Valid transitions
        valid_transitions = [
            ("open", "in-progress"),
            ("open", "done"),
            ("in-progress", "review"),
            ("in-progress", "done"),
            ("review", "done"),
        ]

        for old, new in valid_transitions:
            assert enforce_status_transition(old, new, "task") is True

        # Invalid transitions (not exhaustive, but covers key cases)
        invalid_transitions = [
            ("open", "review"),
            ("in-progress", "open"),
            ("review", "open"),
            ("review", "in-progress"),
            ("done", "open"),
            ("done", "in-progress"),
            ("done", "review"),
        ]

        for old, new in invalid_transitions:
            with pytest.raises(ValueError):
                enforce_status_transition(old, new, "task")

    def test_enforce_status_transition_comprehensive_project_transitions(self):
        """Test comprehensive project transition matrix."""
        # Valid transitions
        valid_transitions = [
            ("draft", "in-progress"),
            ("in-progress", "done"),
        ]

        for old, new in valid_transitions:
            assert enforce_status_transition(old, new, "project") is True

        # Invalid transitions
        invalid_transitions = [
            ("draft", "done"),
            ("in-progress", "draft"),
            ("done", "draft"),
            ("done", "in-progress"),
        ]

        for old, new in invalid_transitions:
            with pytest.raises(ValueError):
                enforce_status_transition(old, new, "project")

    def test_enforce_status_transition_comprehensive_epic_transitions(self):
        """Test comprehensive epic transition matrix."""
        # Valid transitions
        valid_transitions = [
            ("draft", "in-progress"),
            ("in-progress", "done"),
        ]

        for old, new in valid_transitions:
            assert enforce_status_transition(old, new, "epic") is True

        # Invalid transitions
        invalid_transitions = [
            ("draft", "done"),
            ("in-progress", "draft"),
            ("done", "draft"),
            ("done", "in-progress"),
        ]

        for old, new in invalid_transitions:
            with pytest.raises(ValueError):
                enforce_status_transition(old, new, "epic")

    def test_enforce_status_transition_comprehensive_feature_transitions(self):
        """Test comprehensive feature transition matrix."""
        # Valid transitions
        valid_transitions = [
            ("draft", "in-progress"),
            ("in-progress", "done"),
        ]

        for old, new in valid_transitions:
            assert enforce_status_transition(old, new, "feature") is True

        # Invalid transitions
        invalid_transitions = [
            ("draft", "done"),
            ("in-progress", "draft"),
            ("done", "draft"),
            ("done", "in-progress"),
        ]

        for old, new in invalid_transitions:
            with pytest.raises(ValueError):
                enforce_status_transition(old, new, "feature")

    def test_enforce_status_transition_edge_cases(self):
        """Test edge cases for status transition enforcement."""
        # Empty string parameters should raise ValueError
        with pytest.raises(ValueError, match="Invalid old status"):
            enforce_status_transition("", "done", "task")

        with pytest.raises(ValueError, match="Invalid new status"):
            enforce_status_transition("open", "", "task")

        with pytest.raises(ValueError, match="Invalid kind"):
            enforce_status_transition("open", "done", "")

        # Whitespace-only strings should raise ValueError
        with pytest.raises(ValueError, match="Invalid old status"):
            enforce_status_transition("  ", "done", "task")

        with pytest.raises(ValueError, match="Invalid new status"):
            enforce_status_transition("open", "  ", "task")

        with pytest.raises(ValueError, match="Invalid kind"):
            enforce_status_transition("open", "done", "  ")

    def test_enforce_status_transition_terminal_status_comprehensive(self):
        """Test that 'done' is terminal for all object kinds."""
        # done should be terminal for all kinds except same status (done -> done)
        for kind in ["task", "project", "epic", "feature"]:
            for status in ["open", "in-progress", "review", "draft"]:
                with pytest.raises(ValueError, match="terminal status"):
                    enforce_status_transition("done", status, kind)

            # done -> done should be valid (same status)
            assert enforce_status_transition("done", "done", kind) is True

    def test_enforce_status_transition_cross_kind_invalid_statuses(self):
        """Test that invalid statuses for specific kinds are properly rejected."""
        # Task-specific statuses should not work with other kinds
        task_only_statuses = ["open", "review"]
        non_task_kinds = ["project", "epic", "feature"]

        for status in task_only_statuses:
            for kind in non_task_kinds:
                with pytest.raises(ValueError, match=f"Invalid status transition for {kind}"):
                    enforce_status_transition("draft", status, kind)

        # Draft should not work with tasks
        with pytest.raises(ValueError, match="Invalid status transition for task"):
            enforce_status_transition("draft", "done", "task")

    def test_enforce_status_transition_error_message_specificity(self):
        """Test that error messages are specific and helpful for different scenarios."""
        # Test invalid transition with available options
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("draft", "done", "project")

        error_msg = str(exc_info.value)
        assert "Invalid status transition for project" in error_msg
        assert "'draft' cannot transition to 'done'" in error_msg
        assert "Valid transitions: in-progress" in error_msg

        # Test terminal status error
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("done", "draft", "epic")

        error_msg = str(exc_info.value)
        assert "Invalid status transition for epic" in error_msg
        assert "'done' is a terminal status" in error_msg

        # Test invalid status error
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("invalid", "done", "task")

        error_msg = str(exc_info.value)
        assert "Invalid old status" in error_msg
        assert "invalid" in error_msg
