"""Tests for field validation utilities.

This module tests field validation functions including required field validation,
enum membership validation, and status validation for different object kinds.
"""

import pytest

from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.validation import (
    validate_enum_membership,
    validate_required_fields_per_kind,
    validate_status_for_kind,
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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
            "schema_version": "1.1",
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


class TestPriorityMediumSupport:
    """Test medium priority support in Priority enum and validation."""

    def test_priority_enum_medium_alias(self):
        """Test Priority enum accepts 'medium' and returns NORMAL."""
        # Test case-insensitive medium support
        medium_variations = ["medium", "Medium", "MEDIUM", "MeDiUm"]

        for variation in medium_variations:
            priority = Priority(variation)
            assert priority == Priority.NORMAL
            assert str(priority) == "normal"  # String representation should be "normal"

    def test_priority_enum_standard_values_unchanged(self):
        """Test existing priority values still work correctly."""
        test_cases = [
            ("high", Priority.HIGH),
            ("normal", Priority.NORMAL),
            ("low", Priority.LOW),
            ("High", Priority.HIGH),
            ("Normal", Priority.NORMAL),
            ("Low", Priority.LOW),
        ]

        for input_value, expected in test_cases:
            priority = Priority(input_value)
            assert priority == expected

    def test_validate_enum_membership_medium_priority(self):
        """Test enum validation accepts 'medium' priority."""
        data = {"kind": "project", "status": "draft", "priority": "medium"}

        errors = validate_enum_membership(data)
        assert errors == []  # Should have no validation errors

    def test_validate_enum_membership_invalid_priority_includes_medium(self):
        """Test error message for invalid priority includes 'medium' option."""
        data = {"kind": "project", "status": "draft", "priority": "invalid_priority"}

        errors = validate_enum_membership(data)
        assert len(errors) == 1
        assert "Invalid priority" in errors[0]
        assert "medium" in errors[0]  # Should include medium in valid options
        assert "['high', 'normal', 'low', 'medium']" in errors[0]

    def test_priority_enum_invalid_values_still_fail(self):
        """Test Priority enum still rejects invalid values."""
        invalid_values = ["extra", "urgent", "critical", "", None, 123]

        for invalid_value in invalid_values:
            with pytest.raises((ValueError, TypeError)):
                Priority(invalid_value)
