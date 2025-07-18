"""Tests for validation failure cases.

This module tests specific failure scenarios for validation functions,
Pydantic models, and object parsing to ensure proper error handling.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from trellis_mcp.models.common import Priority
from trellis_mcp.object_parser import parse_object
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.project import ProjectModel
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel
from trellis_mcp.validation import (
    CircularDependencyError,
    validate_acyclic_prerequisites,
    validate_enum_membership,
    validate_parent_exists_for_object,
    validate_required_fields_per_kind,
    validate_status_for_kind,
)


class TestMissingFieldFailures:
    """Test validation failures for missing required fields."""

    def test_project_missing_id(self):
        """Test project validation fails with missing ID."""
        data = {
            "kind": "project",
            "parent": None,
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        assert "id" in missing_fields

    def test_project_missing_status(self):
        """Test project validation fails with missing status."""
        data = {
            "kind": "project",
            "id": "P-test",
            "parent": None,
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        assert "status" in missing_fields

    def test_project_missing_title(self):
        """Test project validation fails with missing title."""
        data = {
            "kind": "project",
            "id": "P-test",
            "parent": None,
            "status": "draft",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        assert "title" in missing_fields

    def test_project_missing_created(self):
        """Test project validation fails with missing created timestamp."""
        data = {
            "kind": "project",
            "id": "P-test",
            "parent": None,
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        assert "created" in missing_fields

    def test_project_missing_updated(self):
        """Test project validation fails with missing updated timestamp."""
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
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        assert "updated" in missing_fields

    def test_project_missing_schema_version(self):
        """Test project validation fails with missing schema_version."""
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
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        assert "schema_version" in missing_fields

    def test_epic_missing_parent(self):
        """Test epic validation fails with missing parent."""
        data = {
            "kind": "epic",
            "id": "E-test",
            "status": "draft",
            "title": "Test Epic",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.EPIC)
        assert "parent" in missing_fields

    def test_feature_missing_parent(self):
        """Test feature validation fails with missing parent."""
        data = {
            "kind": "feature",
            "id": "F-test",
            "status": "draft",
            "title": "Test Feature",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.FEATURE)
        assert "parent" in missing_fields

    def test_task_missing_parent(self):
        """Test task validation passes with missing parent (standalone tasks allowed)."""
        data = {
            "kind": "task",
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "worktree": None,
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.0",
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.TASK)
        assert "parent" not in missing_fields  # Parent is now optional for tasks

    def test_missing_kind_field(self):
        """Test validation fails when kind field is missing."""
        data = {
            "id": "P-test",
            "status": "draft",
            "title": "Test Project",
        }

        errors = validate_enum_membership(data)
        # Should not crash, but kind validation should fail elsewhere
        assert len(errors) == 0  # No kind field to validate

    def test_project_multiple_missing_fields(self):
        """Test project validation fails with multiple missing fields."""
        data = {
            "kind": "project",
            "title": "Test Project",
            # Missing: id, status, created, updated, schema_version
        }

        missing_fields = validate_required_fields_per_kind(data, KindEnum.PROJECT)
        expected_missing = {"id", "status", "created", "updated", "schema_version"}
        assert set(missing_fields) == expected_missing


class TestBadEnumFailures:
    """Test validation failures for invalid enum values."""

    def test_invalid_kind_value(self):
        """Test validation fails with invalid kind enum value."""
        data = {
            "kind": "invalid_kind",
            "status": "draft",
            "priority": "normal",
        }

        errors = validate_enum_membership(data)
        assert len(errors) == 1
        assert "Invalid kind" in errors[0]
        assert "invalid_kind" in errors[0]

    def test_invalid_status_value(self):
        """Test validation fails with invalid status enum value."""
        data = {
            "kind": "project",
            "status": "invalid_status",
            "priority": "normal",
        }

        errors = validate_enum_membership(data)
        assert len(errors) == 1
        assert "Invalid status" in errors[0]
        assert "invalid_status" in errors[0]

    def test_invalid_priority_value(self):
        """Test validation fails with invalid priority enum value."""
        data = {
            "kind": "project",
            "status": "draft",
            "priority": "invalid_priority",
        }

        errors = validate_enum_membership(data)
        assert len(errors) == 1
        assert "Invalid priority" in errors[0]
        assert "invalid_priority" in errors[0]

    def test_project_with_task_status(self):
        """Test project validation fails with task-specific status."""
        with pytest.raises(ValueError, match="Invalid status 'open' for project"):
            validate_status_for_kind(StatusEnum.OPEN, KindEnum.PROJECT)

    def test_project_with_review_status(self):
        """Test project validation fails with review status."""
        with pytest.raises(ValueError, match="Invalid status 'review' for project"):
            validate_status_for_kind(StatusEnum.REVIEW, KindEnum.PROJECT)

    def test_task_with_draft_status(self):
        """Test task validation fails with draft status."""
        with pytest.raises(ValueError, match="Invalid status 'draft' for task"):
            validate_status_for_kind(StatusEnum.DRAFT, KindEnum.TASK)

    def test_epic_with_open_status(self):
        """Test epic validation fails with open status."""
        with pytest.raises(ValueError, match="Invalid status 'open' for epic"):
            validate_status_for_kind(StatusEnum.OPEN, KindEnum.EPIC)

    def test_epic_with_review_status(self):
        """Test epic validation fails with review status."""
        with pytest.raises(ValueError, match="Invalid status 'review' for epic"):
            validate_status_for_kind(StatusEnum.REVIEW, KindEnum.EPIC)

    def test_feature_with_open_status(self):
        """Test feature validation fails with open status."""
        with pytest.raises(ValueError, match="Invalid status 'open' for feature"):
            validate_status_for_kind(StatusEnum.OPEN, KindEnum.FEATURE)

    def test_feature_with_review_status(self):
        """Test feature validation fails with review status."""
        with pytest.raises(ValueError, match="Invalid status 'review' for feature"):
            validate_status_for_kind(StatusEnum.REVIEW, KindEnum.FEATURE)

    def test_multiple_invalid_enums(self):
        """Test validation fails with multiple invalid enum values."""
        data = {
            "kind": "invalid_kind",
            "status": "invalid_status",
            "priority": "invalid_priority",
        }

        errors = validate_enum_membership(data)
        assert len(errors) == 3

        error_text = " ".join(errors)
        assert "Invalid kind" in error_text
        assert "Invalid status" in error_text
        assert "Invalid priority" in error_text


class TestBadParentFailures:
    """Test validation failures for invalid parent relationships."""

    def test_project_with_parent(self, tmp_path: Path):
        """Test project validation fails when parent is not null."""
        with pytest.raises(ValueError, match="Projects cannot have parent objects"):
            validate_parent_exists_for_object("some-parent", KindEnum.PROJECT, tmp_path)

    def test_epic_without_parent(self, tmp_path: Path):
        """Test epic validation fails when parent is null."""
        with pytest.raises(ValueError, match="epic objects must have a parent"):
            validate_parent_exists_for_object(None, KindEnum.EPIC, tmp_path)

    def test_feature_without_parent(self, tmp_path: Path):
        """Test feature validation fails when parent is null."""
        with pytest.raises(ValueError, match="feature objects must have a parent"):
            validate_parent_exists_for_object(None, KindEnum.FEATURE, tmp_path)

    def test_task_without_parent(self, tmp_path: Path):
        """Test task validation fails when parent is null."""
        with pytest.raises(ValueError, match="task objects must have a parent"):
            validate_parent_exists_for_object(None, KindEnum.TASK, tmp_path)

    def test_epic_with_nonexistent_parent(self, tmp_path: Path):
        """Test epic validation fails with non-existent parent project."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        with pytest.raises(ValueError, match="Parent project with ID 'nonexistent' does not exist"):
            validate_parent_exists_for_object("nonexistent", KindEnum.EPIC, planning_dir)

    def test_feature_with_nonexistent_parent(self, tmp_path: Path):
        """Test feature validation fails with non-existent parent epic."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        with pytest.raises(ValueError, match="Parent epic with ID 'nonexistent' does not exist"):
            validate_parent_exists_for_object("nonexistent", KindEnum.FEATURE, planning_dir)

    def test_task_with_nonexistent_parent(self, tmp_path: Path):
        """Test task validation fails with non-existent parent feature."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        with pytest.raises(ValueError, match="Parent feature with ID 'nonexistent' does not exist"):
            validate_parent_exists_for_object("nonexistent", KindEnum.TASK, planning_dir)


class TestCircularPrerequisitesFailures:
    """Test validation failures for circular prerequisites."""

    def test_self_referencing_prerequisite(self, tmp_path: Path):
        """Test validation fails with self-referencing prerequisite."""
        # Create project structure
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
title: Self-referencing Task
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---

Task that depends on itself
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert error.cycle_path == ["task1", "task1"]
        assert "Circular dependency detected: task1 -> task1" in str(error)

    def test_simple_circular_dependency(self, tmp_path: Path):
        """Test validation fails with simple circular dependency (A -> B -> A)."""
        # Create project structure
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

        # Task 1 depends on task 2
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

Task 1 depends on task 2
"""
        )

        # Task 2 depends on task 1 (creates cycle)
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

Task 2 depends on task 1
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert len(error.cycle_path) >= 2
        assert "Circular dependency detected" in str(error)

    def test_complex_circular_dependency(self, tmp_path: Path):
        """Test validation fails with complex circular dependency (A -> B -> C -> A)."""
        # Create project structure
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature
        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)

        # Create tasks with complex circular dependencies
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)

        # Task 1 depends on task 2
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

Task 1 depends on task 2
"""
        )

        # Task 2 depends on task 3
        task2_file = task_dir / "T-task2.md"
        task2_file.write_text(
            """---
kind: task
id: task2
parent: test-feature
status: open
title: Task 2
priority: normal
prerequisites: ["task3"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---

Task 2 depends on task 3
"""
        )

        # Task 3 depends on task 1 (creates cycle)
        task3_file = task_dir / "T-task3.md"
        task3_file.write_text(
            """---
kind: task
id: task3
parent: test-feature
status: open
title: Task 3
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.0"
---

Task 3 depends on task 1
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert len(error.cycle_path) >= 3
        assert "Circular dependency detected" in str(error)


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
                schema_version="1.0",
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
                schema_version="1.0",
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
            schema_version="1.0",
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
                schema_version="1.0",
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
        assert "Input should be '1.0'" in str(error)

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
            "schema_version": "1.0",
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
schema_version: "1.0"
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
