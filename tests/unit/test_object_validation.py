"""Tests for comprehensive object validation and integration.

This module consolidates object validation tests from multiple source files,
focusing on complete object validation, integration scenarios, and validation
failures. It provides comprehensive coverage of object data validation,
front-matter validation, status transitions, Pydantic model validation,
object parsing, and schema version compatibility.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Enhanced validation imports
from src.trellis_mcp.exceptions.validation_error import ValidationError as TrellisValidationErrorNew
from src.trellis_mcp.exceptions.validation_error import (
    ValidationErrorCode,
)
from src.trellis_mcp.validation.enhanced_validation import (
    validate_object_data_enhanced,
    validate_object_data_with_collector,
    validate_task_with_enhanced_errors,
)
from src.trellis_mcp.validation.error_collector import ErrorCategory, ErrorSeverity
from trellis_mcp.models.common import Priority
from trellis_mcp.object_parser import parse_object
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.project import ProjectModel
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel
from trellis_mcp.validation import (
    TrellisValidationError,
    enforce_status_transition,
    get_all_objects,
    validate_front_matter,
    validate_object_data,
)


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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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

    def test_validate_object_data_standalone_task_valid(self, tmp_path: Path):
        """Test standalone task (no parent) validates successfully."""
        data = {
            "kind": "task",
            "id": "T-standalone",
            "status": "open",
            "title": "Standalone Task",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise any exception - standalone tasks don't need parent validation
        validate_object_data(data, tmp_path / "planning")

    def test_validate_object_data_standalone_task_with_parent_field_none(self, tmp_path: Path):
        """Test standalone task with parent field set to None validates successfully."""
        data = {
            "kind": "task",
            "id": "T-standalone",
            "parent": None,
            "status": "open",
            "title": "Standalone Task",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise any exception - standalone tasks don't need parent validation
        validate_object_data(data, tmp_path / "planning")

    def test_validate_object_data_standalone_task_with_parent_field_empty(self, tmp_path: Path):
        """Test standalone task with parent field set to empty string validates successfully."""
        data = {
            "kind": "task",
            "id": "T-standalone",
            "parent": "",
            "status": "open",
            "title": "Standalone Task",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise any exception - standalone tasks don't need parent validation
        validate_object_data(data, tmp_path / "planning")

    def test_validate_object_data_hierarchy_task_with_existing_parent(self, tmp_path: Path):
        """Test hierarchy task with existing parent validates successfully."""
        # Create full hierarchy structure
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

        data = {
            "kind": "task",
            "id": "T-hierarchy",
            "parent": "F-test-feature",
            "status": "open",
            "title": "Hierarchy Task",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise any exception - hierarchy tasks with valid parent should pass
        validate_object_data(data, tmp_path / "planning")

    def test_validate_object_data_hierarchy_task_with_nonexistent_parent(self, tmp_path: Path):
        """Test hierarchy task with non-existent parent fails validation."""
        data = {
            "kind": "task",
            "id": "T-hierarchy",
            "parent": "F-nonexistent-parent",  # Changed to avoid false positive
            "status": "open",
            "title": "Hierarchy Task",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Parent feature with ID" in error.errors[0]
        assert "does not exist" in error.errors[0]

    def test_validate_object_data_conditional_validation_preserves_other_objects(
        self, tmp_path: Path
    ):
        """Test conditional validation doesn't affect non-task objects."""
        # Test that epic still requires parent validation
        data = {
            "kind": "epic",
            "id": "E-test",
            "parent": "P-nonexistent",
            "status": "draft",
            "title": "Test Epic",
            "created": "2023-01-01T00:00:00",
            "updated": "2023-01-01T00:00:00",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Parent project with ID" in error.errors[0]
        assert "does not exist" in error.errors[0]


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
schema_version: "1.1"
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
schema_version: "1.1"
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
schema_version: "1.1"
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
schema_version: "1.1"
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
schema_version: "1.1"
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
        }

        errors = validate_front_matter(yaml_dict, "feature")
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]
        assert "parent" in errors[0]

    def test_validate_front_matter_missing_parent_for_task(self):
        """Test that tasks can now be created without a parent field (standalone tasks)."""
        yaml_dict = {
            "kind": "task",
            "id": "test-task",
            "status": "open",
            "title": "Test Task",
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        errors = validate_front_matter(yaml_dict, "task")
        assert len(errors) == 0  # Should pass validation for standalone tasks

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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
                "schema_version": "1.1",
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
                "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
                "schema_version": "1.1",
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

        # done → open (invalid - only deleted is allowed from done)
        with pytest.raises(ValueError, match="Invalid status transition for task"):
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

        # done → draft (invalid - only deleted is allowed from done)
        with pytest.raises(ValueError, match="Invalid status transition for project"):
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

        # done → draft (invalid - only deleted is allowed from done)
        with pytest.raises(ValueError, match="Invalid status transition for epic"):
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

        # done → draft (invalid - only deleted is allowed from done)
        with pytest.raises(ValueError, match="Invalid status transition for feature"):
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
        assert "Valid transitions: deleted, done, in-progress" in error_msg

        # Test error message for done → open (invalid transition)
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("done", "open", "task")

        error_msg = str(exc_info.value)
        assert "Invalid status transition for task" in error_msg
        assert "'done' cannot transition to 'open'" in error_msg
        assert "Valid transitions: deleted" in error_msg

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
        # done should only allow transitions to deleted (and same status)
        for kind in ["task", "project", "epic", "feature"]:
            for status in ["open", "in-progress", "review", "draft"]:
                with pytest.raises(ValueError, match="Invalid status transition"):
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
        assert "Valid transitions: deleted, in-progress" in error_msg

        # Test done → draft error (only deleted is allowed from done)
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("done", "draft", "epic")

        error_msg = str(exc_info.value)
        assert "Invalid status transition for epic" in error_msg
        assert "'done' cannot transition to 'draft'" in error_msg
        assert "Valid transitions: deleted" in error_msg

        # Test invalid status error
        with pytest.raises(ValueError) as exc_info:
            enforce_status_transition("invalid", "done", "task")

        error_msg = str(exc_info.value)
        assert "Invalid old status" in error_msg
        assert "invalid" in error_msg


class TestPydanticModelFailures:
    """Test validation failures at the Pydantic model level."""

    def test_project_model_with_parent(self):
        """Test ProjectModel validation fails with non-null parent."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectModel(
                kind=KindEnum.PROJECT,
                id="P-test",
                parent="some-parent",  # Should fail
                status=StatusEnum.DRAFT,
                title="Test Project",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime(2023, 1, 1),
                updated=datetime(2023, 1, 1),
                schema_version="1.1",
            )

        error = exc_info.value
        assert "Projects cannot have a parent" in str(error)

    def test_project_model_with_invalid_status(self):
        """Test ProjectModel validation fails with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectModel(
                kind=KindEnum.PROJECT,
                id="P-test",
                parent=None,
                status=StatusEnum.OPEN,  # Invalid for project
                title="Test Project",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime(2023, 1, 1),
                updated=datetime(2023, 1, 1),
                schema_version="1.1",
            )

        error = exc_info.value
        assert "Invalid status 'StatusEnum.OPEN' for project" in str(error)

    def test_task_model_without_parent(self):
        """Test TaskModel validation passes with null parent (standalone tasks allowed)."""
        # Should no longer raise ValidationError - standalone tasks are now allowed
        task = TaskModel(
            kind=KindEnum.TASK,
            id="T-test",
            parent=None,  # Now allowed for standalone tasks
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime(2023, 1, 1),
            updated=datetime(2023, 1, 1),
            schema_version="1.1",
        )

        # Verify the task was created successfully
        assert task.parent is None
        assert task.kind == KindEnum.TASK

    def test_task_model_with_invalid_status(self):
        """Test TaskModel validation fails with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            TaskModel(
                kind=KindEnum.TASK,
                id="T-test",
                parent="F-test",
                status=StatusEnum.DRAFT,  # Invalid for task
                title="Test Task",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime(2023, 1, 1),
                updated=datetime(2023, 1, 1),
                schema_version="1.1",
            )

        error = exc_info.value
        assert "Invalid status 'StatusEnum.DRAFT' for task" in str(error)

    def test_model_with_invalid_schema_version(self):
        """Test model validation fails with invalid schema version."""
        data = {
            "kind": "project",
            "id": "P-test",
            "parent": None,
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "2.0",  # Invalid version
        }

        with pytest.raises(ValidationError) as exc_info:
            ProjectModel.model_validate(data)

        error = exc_info.value
        assert "Input should be '1.0' or '1.1'" in str(error)

    def test_model_with_extra_fields(self):
        """Test model validation fails with extra fields (due to extra='forbid')."""
        data = {
            "kind": "project",
            "id": "P-test",
            "parent": None,
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
            "extra_field": "should not be allowed",  # Should fail
        }

        with pytest.raises(ValidationError) as exc_info:
            ProjectModel.model_validate(data)

        error = exc_info.value
        assert "Extra inputs are not permitted" in str(error)


class TestParseObjectFailures:
    """Test validation failures in parse_object function."""

    def test_parse_object_with_invalid_kind(self, tmp_path: Path):
        """Test parse_object fails with invalid kind value."""
        invalid_file = tmp_path / "invalid.md"
        invalid_file.write_text(
            """---
kind: invalid_kind
id: P-test
status: draft
title: Invalid Object
priority: normal
---

Invalid object
"""
        )

        with pytest.raises(ValueError, match="Invalid kind value 'invalid_kind'"):
            parse_object(invalid_file)

    def test_parse_object_with_missing_kind(self, tmp_path: Path):
        """Test parse_object fails with missing kind field."""
        invalid_file = tmp_path / "invalid.md"
        invalid_file.write_text(
            """---
id: P-test
status: draft
title: Invalid Object
---

Missing kind field
"""
        )

        with pytest.raises(ValueError, match="Missing 'kind' field"):
            parse_object(invalid_file)

    def test_parse_object_with_validation_error(self, tmp_path: Path):
        """Test parse_object fails with Pydantic validation error."""
        invalid_file = tmp_path / "invalid.md"
        invalid_file.write_text(
            """---
kind: project
id: P-test
parent: "some-parent"
status: draft
title: Invalid Project
priority: normal
prerequisites: []
worktree: null
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.1"
---

Project with invalid parent
"""
        )

        with pytest.raises(ValidationError):
            parse_object(invalid_file)

    def test_parse_object_with_invalid_yaml(self, tmp_path: Path):
        """Test parse_object fails with invalid YAML."""
        invalid_file = tmp_path / "invalid.md"
        invalid_file.write_text(
            """---
kind: project
id: P-test
priority: normal
invalid: yaml: syntax: [
---

Invalid YAML
"""
        )

        with pytest.raises(ValueError, match="Failed to load markdown"):
            parse_object(invalid_file)

    def test_parse_object_missing_file(self, tmp_path: Path):
        """Test parse_object fails with missing file."""
        missing_file = tmp_path / "missing.md"

        with pytest.raises(FileNotFoundError, match="File not found"):
            parse_object(missing_file)


class TestSchemaVersionCompatibility:
    """Test compatibility between schema versions 1.0 and 1.1."""

    def test_schema_10_task_with_parent_validates(self):
        """Test that schema 1.0 tasks with parent validate correctly."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": "F-parent",
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        # Should not raise ValidationError
        model = TaskModel.model_validate(data)
        assert model.schema_version == "1.0"
        assert model.parent == "F-parent"

    def test_schema_10_task_without_parent_fails(self):
        """Test that schema 1.0 tasks without parent fail validation."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": None,
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        with pytest.raises(ValidationError) as exc_info:
            TaskModel.model_validate(data)

        error = exc_info.value
        assert "Tasks must have a parent in schema version 1.0" in str(error)

    def test_schema_11_task_without_parent_validates(self):
        """Test that schema 1.1 tasks without parent validate correctly."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": None,
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        # Should not raise ValidationError
        model = TaskModel.model_validate(data)
        assert model.schema_version == "1.1"
        assert model.parent is None

    def test_schema_11_task_with_parent_validates(self):
        """Test that schema 1.1 tasks with parent validate correctly."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": "F-parent",
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        # Should not raise ValidationError
        model = TaskModel.model_validate(data)
        assert model.schema_version == "1.1"
        assert model.parent == "F-parent"


class TestEnhancedValidation:
    """Test cases for enhanced validation functions."""

    def test_validate_object_data_with_collector_success(self):
        """Test successful validation returns empty collector."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert not collector.has_errors()
        assert collector.get_error_count() == 0
        assert collector.object_id == "T-test"
        assert collector.object_kind == "task"

    def test_validate_object_data_with_collector_missing_kind(self):
        """Test validation with missing kind field."""
        data = {
            "id": "T-test",
            "title": "Test Task",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()
        assert collector.has_critical_errors()

        # Should have missing kind error
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) == 1
        assert "Missing 'kind' field" in critical_errors[0][0]
        assert critical_errors[0][1] == ValidationErrorCode.MISSING_REQUIRED_FIELD

    def test_validate_object_data_with_collector_invalid_kind(self):
        """Test validation with invalid kind field."""
        data = {
            "kind": "invalid_kind",
            "id": "T-test",
            "title": "Test Task",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()
        assert collector.has_critical_errors()

        # Should have invalid kind error
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) == 1
        assert "Invalid kind 'invalid_kind'" in critical_errors[0][0]
        assert critical_errors[0][1] == ValidationErrorCode.INVALID_ENUM_VALUE

    def test_validate_object_data_with_collector_multiple_errors(self):
        """Test validation with multiple errors shows prioritization."""
        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title (critical)
            "status": "invalid_status",  # Invalid enum (critical)
            "priority": "invalid_priority",  # Invalid enum (critical)
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()
        assert collector.has_critical_errors()

        # Should have multiple critical errors
        critical_errors = collector.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) >= 2  # At least missing title and invalid status

        # Check error categories
        field_errors = collector.get_errors_by_category(ErrorCategory.FIELD)
        assert len(field_errors) >= 2

    def test_validate_object_data_with_collector_security_errors(self):
        """Test that security errors are properly collected."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_standalone_task_security"
        ) as mock_security:
            mock_security.return_value = ["Security error 1", "Security error 2"]

            collector = validate_object_data_with_collector(data, Path("/test"))

            # Should have security errors
            assert collector.has_errors()
            assert collector.get_error_count() == 2

            # All errors should be categorized as field errors with security context
            all_errors = collector.get_prioritized_errors()
            for msg, code, context in all_errors:
                assert code == ValidationErrorCode.INVALID_FIELD
                assert context.get("security_check") is True

    def test_validate_object_data_with_collector_parent_validation(self):
        """Test parent validation error collection."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-nonexistent",
            "schema_version": "1.0",  # Hierarchy task
        }

        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_parent_exists_for_object"
        ) as mock_parent:
            mock_parent.side_effect = ValueError("Parent F-nonexistent does not exist")

            collector = validate_object_data_with_collector(data, Path("/test"))

            assert collector.has_errors()

            # Should have parent validation error
            relationship_errors = collector.get_errors_by_category(ErrorCategory.RELATIONSHIP)
            assert len(relationship_errors) == 1
            assert "Parent F-nonexistent does not exist" in relationship_errors[0][0]
            assert relationship_errors[0][1] == ValidationErrorCode.PARENT_NOT_EXIST

    def test_validate_object_data_enhanced_success(self):
        """Test enhanced validation function with successful validation."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Should not raise any exception
        validate_object_data_enhanced(data, Path("/test"))

    def test_validate_object_data_enhanced_raises_validation_error(self):
        """Test enhanced validation function raises ValidationError."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(TrellisValidationErrorNew) as exc_info:
            validate_object_data_enhanced(data, Path("/test"))

        exception = exc_info.value
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert exception.task_type == "standalone"
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0

    def test_validate_object_data_enhanced_creates_proper_validation_error(self):
        """Test enhanced validation creates proper ValidationError structure."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(TrellisValidationErrorNew) as exc_info:
            validate_object_data_enhanced(data, Path("/test"))

        exception = exc_info.value

        # Check that the ValidationError has proper structure
        assert isinstance(exception, TrellisValidationErrorNew)
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert exception.task_type == "standalone"

        # Check that context information is preserved
        assert "error_summary" in exception.context
        assert exception.context["error_summary"]["total_errors"] > 0

    def test_error_prioritization_in_enhanced_validation(self):
        """Test that errors are properly prioritized in enhanced validation."""
        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title (critical)
            "status": "invalid_status",  # Invalid enum (critical)
            "priority": "invalid_priority",  # Invalid enum (critical)
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(TrellisValidationErrorNew) as exc_info:
            validate_object_data_enhanced(data, Path("/test"))

        exception = exc_info.value

        # All errors should be critical level, but check they're prioritized
        assert len(exception.errors) >= 2
        assert len(exception.error_codes) >= 2

        # Should contain both missing field and invalid enum errors
        error_codes = [code.value for code in exception.error_codes]
        assert "missing_required_field" in error_codes or "invalid_enum_value" in error_codes

    def test_collector_context_preservation(self):
        """Test that context is preserved through the enhanced validation."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        assert collector.has_errors()

        # Get errors and check context preservation
        prioritized_errors = collector.get_prioritized_errors()

        # Find the invalid status error
        for msg, code, context in prioritized_errors:
            if code == ValidationErrorCode.INVALID_ENUM_VALUE and "status" in context.get(
                "field", ""
            ):
                assert "value" in context
                assert context["value"] == "invalid_status"
                assert "valid_values" in context
                break
        else:
            pytest.fail("Invalid status error not found with proper context")

    def test_standalone_vs_hierarchy_task_detection(self):
        """Test that task type is correctly detected for ValidationError."""
        # Standalone task
        standalone_data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "schema_version": "1.1",  # Standalone
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises((TrellisValidationErrorNew, TrellisValidationError)) as exc_info:
            validate_object_data_enhanced(standalone_data, Path("/test"))

        # Accept either ValidationError or TrellisValidationError (fallback case)
        if isinstance(exc_info.value, TrellisValidationErrorNew):
            assert exc_info.value.task_type == "standalone"

        # Hierarchy task
        hierarchy_data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",  # Hierarchy
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises((TrellisValidationErrorNew, TrellisValidationError)) as exc_info:
            validate_object_data_enhanced(hierarchy_data, Path("/test"))

        # Accept either ValidationError or TrellisValidationError (fallback case)
        if isinstance(exc_info.value, TrellisValidationErrorNew):
            assert exc_info.value.task_type == "hierarchy"

    def test_collector_summary_and_detailed_view(self):
        """Test that collector provides useful summary and detailed views."""
        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title (critical field error)
            "status": "invalid_status",  # Invalid enum (critical field error)
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        collector = validate_object_data_with_collector(data, Path("/test"))

        # Test summary
        summary = collector.get_summary()
        assert summary["total_errors"] >= 2
        assert summary["has_critical"] is True
        assert "CRITICAL" in summary["severity_breakdown"]
        assert "field" in summary["category_breakdown"]

        # Test detailed view
        detailed = collector.get_detailed_view()
        assert detailed["object_id"] == "T-test"
        assert detailed["object_kind"] == "task"
        assert "errors_by_category" in detailed
        assert "field" in detailed["errors_by_category"]

        # Check that field errors are properly categorized
        field_errors = detailed["errors_by_category"]["field"]
        assert len(field_errors) >= 2

        for error in field_errors:
            assert "message" in error
            assert "error_code" in error
            assert "severity" in error
            assert "context" in error


class TestTaskSpecificValidation:
    """Test cases for task-specific validation functions."""

    def test_validate_task_with_enhanced_errors_standalone_success(self):
        """Test successful validation of a standalone task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Should not raise any exception
        validate_task_with_enhanced_errors(data, Path("/test"))

    def test_validate_task_with_enhanced_errors_hierarchy_success(self):
        """Test successful validation of a hierarchy task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Should not raise any exception (with mocked parent validation)
        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_parent_exists_for_object"
        ):
            validate_task_with_enhanced_errors(data, Path("/test"))

    def test_validate_task_with_enhanced_errors_non_task_fails(self):
        """Test that non-task objects raise ValueError."""
        data = {
            "kind": "project",
            "id": "P-test",
            "title": "Test Project",
            "status": "open",
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(ValueError, match="can only be used with tasks"):
            validate_task_with_enhanced_errors(data, Path("/test"))

    def test_validate_task_with_enhanced_errors_delegates_to_standalone(self):
        """Test that standalone tasks are delegated to standalone validation."""
        from src.trellis_mcp.exceptions.standalone_task_validation_error import (
            StandaloneTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",  # This should cause validation error
            "priority": "normal",
            "schema_version": "1.1",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(StandaloneTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0

    def test_validate_task_with_enhanced_errors_delegates_to_hierarchy(self):
        """Test that hierarchy tasks are delegated to hierarchy validation."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",  # This should cause validation error
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value
        assert exception.object_id == "T-test"
        assert exception.object_kind == "task"
        assert exception.parent_id == "F-test"
        assert len(exception.errors) > 0
        assert len(exception.error_codes) > 0

    def test_hierarchy_task_validation_context_aware_errors(self):
        """Test that hierarchy task validation provides context-aware error messages."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value

        # Check that context contains hierarchy-specific information
        assert "task_type" in exception.context
        assert exception.context["task_type"] == "hierarchy"
        assert "validation_context" in exception.context
        assert exception.context["validation_context"] == "enhanced_hierarchy_task_validation"

    def test_hierarchy_task_validation_error_aggregation(self):
        """Test that hierarchy task validation properly aggregates multiple errors."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            # Missing title
            "status": "invalid_status",
            "priority": "invalid_priority",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value

        # Should have multiple errors aggregated
        assert len(exception.errors) >= 2
        assert len(exception.error_codes) >= 2

        # Check that errors are properly ordered/prioritized
        error_messages = exception.errors
        error_codes = [code.value for code in exception.error_codes]

        # Should contain both missing field and invalid enum errors
        assert any("missing" in msg.lower() for msg in error_messages) or any(
            "invalid" in msg.lower() for msg in error_messages
        )
        assert "missing_required_field" in error_codes or "invalid_enum_value" in error_codes

    def test_hierarchy_task_validation_with_parent_errors(self):
        """Test hierarchy task validation with parent validation errors."""
        from src.trellis_mcp.exceptions.hierarchy_task_validation_error import (
            HierarchyTaskValidationError,
        )

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-nonexistent",  # This parent doesn't exist
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        with pytest.raises(HierarchyTaskValidationError) as exc_info:
            validate_task_with_enhanced_errors(data, Path("/test"))

        exception = exc_info.value

        # Should have parent validation error
        assert len(exception.errors) >= 1
        assert any("does not exist" in msg for msg in exception.errors)

        # Should have proper parent_id in the exception
        assert exception.parent_id == "F-nonexistent"

    def test_hierarchy_task_validation_performance(self):
        """Test that hierarchy task validation doesn't significantly impact performance."""
        import time

        data = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
            "parent": "F-test",
            "schema_version": "1.0",
            "created": "2025-01-01T00:00:00.000000",
            "updated": "2025-01-01T00:00:00.000000",
        }

        # Mock parent validation to avoid filesystem calls
        with patch(
            "src.trellis_mcp.validation.enhanced_validation.validate_parent_exists_for_object"
        ):
            start_time = time.time()

            # Run validation multiple times
            for _ in range(10):
                try:
                    validate_task_with_enhanced_errors(data, Path("/test"))
                except Exception:
                    pass  # Ignore validation errors, we're testing performance

            end_time = time.time()
            elapsed = end_time - start_time

            # Should complete within reasonable time (adjust as needed)
            assert elapsed < 1.0, f"Validation took too long: {elapsed:.2f}s"
