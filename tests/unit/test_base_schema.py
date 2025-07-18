"""Tests for BaseSchemaModel class focusing on optional parent field functionality.

This module provides comprehensive tests for the BaseSchemaModel class,
with particular emphasis on the optional parent field behavior introduced
to support standalone tasks while maintaining hierarchy validation.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from trellis_mcp.models.common import Priority
from trellis_mcp.schema.base_schema import BaseSchemaModel
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum


class TestBaseSchemaModelParentValidation:
    """Test parent field validation logic in BaseSchemaModel."""

    def test_parent_validation_project_must_have_none_parent(self) -> None:
        """Test that projects cannot have a parent."""
        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel(
                kind=KindEnum.PROJECT,
                id="test-project",
                parent="some-parent",  # Invalid for project
                status=StatusEnum.DRAFT,
                title="Test Project",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

        assert "Projects cannot have a parent" in str(exc_info.value)

    def test_parent_validation_project_with_none_parent_valid(self) -> None:
        """Test that projects with None parent are valid."""
        project = BaseSchemaModel(
            kind=KindEnum.PROJECT,
            id="test-project",
            parent=None,  # Valid for project
            status=StatusEnum.DRAFT,
            title="Test Project",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert project.parent is None

    def test_parent_validation_epic_must_have_parent(self) -> None:
        """Test that epics must have a parent."""
        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel(
                kind=KindEnum.EPIC,
                id="test-epic",
                parent=None,  # Invalid for epic
                status=StatusEnum.DRAFT,
                title="Test Epic",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

        assert "Epics must have a parent project ID" in str(exc_info.value)

    def test_parent_validation_epic_with_valid_parent(self) -> None:
        """Test that epics with valid parent are valid."""
        epic = BaseSchemaModel(
            kind=KindEnum.EPIC,
            id="test-epic",
            parent="test-project",  # Valid for epic
            status=StatusEnum.DRAFT,
            title="Test Epic",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert epic.parent == "test-project"

    def test_parent_validation_feature_must_have_parent(self) -> None:
        """Test that features must have a parent."""
        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel(
                kind=KindEnum.FEATURE,
                id="test-feature",
                parent=None,  # Invalid for feature
                status=StatusEnum.DRAFT,
                title="Test Feature",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

        assert "Features must have a parent epic ID" in str(exc_info.value)

    def test_parent_validation_feature_with_valid_parent(self) -> None:
        """Test that features with valid parent are valid."""
        feature = BaseSchemaModel(
            kind=KindEnum.FEATURE,
            id="test-feature",
            parent="test-epic",  # Valid for feature
            status=StatusEnum.DRAFT,
            title="Test Feature",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert feature.parent == "test-epic"

    def test_parent_validation_task_can_have_none_parent(self) -> None:
        """Test that tasks can have None parent (standalone tasks)."""
        task = BaseSchemaModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent=None,  # Valid for standalone task
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert task.parent is None

    def test_parent_validation_task_can_have_valid_parent(self) -> None:
        """Test that tasks can have valid parent (hierarchy tasks)."""
        task = BaseSchemaModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent="test-feature",  # Valid for hierarchy task
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert task.parent == "test-feature"

    def test_parent_validation_empty_string_converted_to_none(self) -> None:
        """Test that empty string parent is converted to None."""
        task = BaseSchemaModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent="",  # Empty string should be converted to None
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert task.parent is None

    def test_parent_validation_empty_string_for_project_still_invalid(self) -> None:
        """Test that empty string parent for project is still invalid after conversion."""
        # Should succeed because empty string is converted to None, and projects can have None parent  # noqa: E501
        project = BaseSchemaModel(
            kind=KindEnum.PROJECT,
            id="test-project",
            parent="",  # Empty string converted to None, valid for project
            status=StatusEnum.DRAFT,
            title="Test Project",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert project.parent is None

    def test_parent_validation_empty_string_for_epic_invalid(self) -> None:
        """Test that empty string parent for epic is invalid after conversion."""
        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel(
                kind=KindEnum.EPIC,
                id="test-epic",
                parent="",  # Empty string converted to None, invalid for epic
                status=StatusEnum.DRAFT,
                title="Test Epic",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

        assert "Epics must have a parent project ID" in str(exc_info.value)


class TestBaseSchemaModelOptionalParentSerialization:
    """Test serialization/deserialization with optional parent fields."""

    def test_serialization_with_none_parent(self) -> None:
        """Test serialization of model with None parent."""
        task = BaseSchemaModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        # Serialize to dict
        task_dict = task.model_dump()

        # Verify parent is None in serialized form
        assert task_dict["parent"] is None

    def test_serialization_with_valid_parent(self) -> None:
        """Test serialization of model with valid parent."""
        task = BaseSchemaModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        # Serialize to dict
        task_dict = task.model_dump()

        # Verify parent is preserved in serialized form
        assert task_dict["parent"] == "test-feature"

    def test_deserialization_with_none_parent(self) -> None:
        """Test deserialization of data with None parent."""
        data = {
            "kind": "task",
            "id": "test-task",
            "parent": None,
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        task = BaseSchemaModel.model_validate(data)
        assert task.parent is None

    def test_deserialization_with_missing_parent_field(self) -> None:
        """Test deserialization of data without parent field."""
        data = {
            "kind": "task",
            "id": "test-task",
            # parent field is missing
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        task = BaseSchemaModel.model_validate(data)
        assert task.parent is None

    def test_deserialization_with_empty_string_parent(self) -> None:
        """Test deserialization of data with empty string parent."""
        data = {
            "kind": "task",
            "id": "test-task",
            "parent": "",  # Empty string should be converted to None
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        task = BaseSchemaModel.model_validate(data)
        assert task.parent is None

    def test_roundtrip_serialization_with_none_parent(self) -> None:
        """Test that None parent survives round-trip serialization."""
        original_task = BaseSchemaModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        # Serialize to dict
        task_dict = original_task.model_dump()

        # Deserialize back to model
        restored_task = BaseSchemaModel.model_validate(task_dict)

        # Verify parent is still None
        assert restored_task.parent is None
        assert restored_task.id == original_task.id
        assert restored_task.kind == original_task.kind


class TestBaseSchemaModelEdgeCases:
    """Test edge cases and error conditions for BaseSchemaModel."""

    def test_validation_with_invalid_kind_ignores_parent_validation(self) -> None:
        """Test that invalid kind bypasses parent validation."""
        # This should raise ValidationError due to invalid kind, not parent validation
        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel(
                kind="invalid-kind",  # type: ignore  # Invalid kind
                id="test-object",
                parent="some-parent",
                status=StatusEnum.DRAFT,
                title="Test Object",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

        # Should get kind validation error, not parent validation error
        error_message = str(exc_info.value)
        assert "invalid-kind" in error_message or "Invalid kind" in error_message

    def test_validation_without_kind_field(self) -> None:
        """Test validation when kind field is missing."""
        data = {
            # kind field is missing
            "id": "test-object",
            "parent": "some-parent",
            "status": "draft",
            "title": "Test Object",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel.model_validate(data)

        error_message = str(exc_info.value)
        assert "kind" in error_message.lower()

    def test_status_validation_with_valid_statuses(self) -> None:
        """Test that valid statuses for each kind pass validation."""
        # Valid project status
        project = BaseSchemaModel(
            kind=KindEnum.PROJECT,
            id="test-project",
            parent=None,
            status=StatusEnum.DRAFT,  # Valid for project
            title="Test Project",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert project.status == StatusEnum.DRAFT

        # Valid task status
        task = BaseSchemaModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent=None,
            status=StatusEnum.OPEN,  # Valid for task
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )
        assert task.status == StatusEnum.OPEN

    def test_status_validation_with_invalid_statuses(self) -> None:
        """Test that invalid statuses for each kind fail validation."""
        # Invalid project status
        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel(
                kind=KindEnum.PROJECT,
                id="test-project",
                parent=None,
                status=StatusEnum.OPEN,  # Invalid for project
                title="Test Project",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

        assert "Invalid status" in str(exc_info.value) and "project" in str(exc_info.value)

        # Invalid task status
        with pytest.raises(ValidationError) as exc_info:
            BaseSchemaModel(
                kind=KindEnum.TASK,
                id="test-task",
                parent=None,
                status=StatusEnum.DRAFT,  # Invalid for task
                title="Test Task",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

        assert "Invalid status" in str(exc_info.value) and "task" in str(exc_info.value)

    def test_comprehensive_validation_success(self) -> None:
        """Test comprehensive validation with all valid fields."""
        # Test all object kinds with valid configurations
        objects = [
            {
                "kind": KindEnum.PROJECT,
                "id": "test-project",
                "parent": None,
                "status": StatusEnum.DRAFT,
                "title": "Test Project",
            },
            {
                "kind": KindEnum.EPIC,
                "id": "test-epic",
                "parent": "test-project",
                "status": StatusEnum.DRAFT,
                "title": "Test Epic",
            },
            {
                "kind": KindEnum.FEATURE,
                "id": "test-feature",
                "parent": "test-epic",
                "status": StatusEnum.DRAFT,
                "title": "Test Feature",
            },
            {
                "kind": KindEnum.TASK,
                "id": "test-task",
                "parent": None,  # Standalone task
                "status": StatusEnum.OPEN,
                "title": "Test Task",
            },
        ]

        for obj_data in objects:
            obj = BaseSchemaModel(
                kind=obj_data["kind"],
                id=obj_data["id"],
                parent=obj_data["parent"],
                status=obj_data["status"],
                title=obj_data["title"],
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

            assert obj.kind == obj_data["kind"]
            assert obj.id == obj_data["id"]
            assert obj.parent == obj_data["parent"]
            assert obj.status == obj_data["status"]
            assert obj.title == obj_data["title"]


class TestBaseSchemaModelStatusTransitions:
    """Test status transition validation in BaseSchemaModel."""

    def test_status_transition_validation_same_status(self) -> None:
        """Test that same status transitions are always valid."""
        # Test for different kinds
        statuses = [
            StatusEnum.DRAFT,
            StatusEnum.IN_PROGRESS,
            StatusEnum.DONE,
            StatusEnum.OPEN,
        ]

        for status in statuses:
            # Same status should always be valid
            result = BaseSchemaModel.validate_status_transition(status, status)
            assert result is True

    def test_status_transition_validation_empty_matrix(self) -> None:
        """Test that BaseSchemaModel with empty transition matrix fails for different statuses."""
        # BaseSchemaModel has an empty transition matrix
        with pytest.raises(ValueError) as exc_info:
            BaseSchemaModel.validate_status_transition(StatusEnum.OPEN, StatusEnum.IN_PROGRESS)

        error_message = str(exc_info.value)
        assert "Invalid status transition for baseschema" in error_message
        assert "is a terminal status with no valid transitions" in error_message

    def test_status_transition_validation_same_status_no_matrix(self) -> None:
        """Test that same status transitions work even without matrix."""
        # Same status should always be valid, even without transition matrix
        result = BaseSchemaModel.validate_status_transition(StatusEnum.OPEN, StatusEnum.OPEN)
        assert result is True

        result = BaseSchemaModel.validate_status_transition(StatusEnum.DRAFT, StatusEnum.DRAFT)
        assert result is True
