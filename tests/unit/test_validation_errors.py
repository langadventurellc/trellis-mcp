"""Tests for contextual validation error messages.

This module tests the enhanced error message system that provides contextual
clarity for standalone and hierarchy-based tasks.
"""

from pathlib import Path

import pytest

from trellis_mcp.validation import (
    TrellisValidationError,
    format_validation_error_with_context,
    generate_contextual_error_message,
    get_task_type_context,
    validate_object_data,
)


class TestTaskTypeContext:
    """Test task type context detection functions."""

    def test_get_task_type_context_standalone_task(self):
        """Test context detection for standalone tasks."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        assert get_task_type_context(data) == "standalone task"

    def test_get_task_type_context_hierarchy_task(self):
        """Test context detection for hierarchy tasks."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        assert get_task_type_context(data) == "hierarchy task"

    def test_get_task_type_context_non_task(self):
        """Test context detection for non-task objects."""
        data = {
            "kind": "project",
            "id": "P-test",
            "status": "draft",
            "title": "Test Project",
        }
        assert get_task_type_context(data) == ""

    def test_get_task_type_context_empty_data(self):
        """Test context detection with empty data."""
        assert get_task_type_context({}) == ""

    def test_get_task_type_context_no_kind(self):
        """Test context detection with no kind field."""
        data = {
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        assert get_task_type_context(data) == ""


class TestContextualErrorMessageGeneration:
    """Test contextual error message generation functions."""

    def test_generate_contextual_error_message_invalid_status_standalone(self):
        """Test invalid status error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "draft",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message("invalid_status", data, status="draft")
        assert msg == "Invalid status 'draft' for standalone task"

    def test_generate_contextual_error_message_invalid_status_hierarchy(self):
        """Test invalid status error for hierarchy task."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "status": "draft",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message("invalid_status", data, status="draft")
        assert msg == "Invalid status 'draft' for hierarchy task"

    def test_generate_contextual_error_message_invalid_status_non_task(self):
        """Test invalid status error for non-task object."""
        data = {
            "kind": "project",
            "id": "P-test",
            "status": "open",
            "title": "Test Project",
        }
        msg = generate_contextual_error_message("invalid_status", data, status="open")
        assert msg == "Invalid status 'open' for project"

    def test_generate_contextual_error_message_missing_parent_standalone(self):
        """Test missing parent error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message("missing_parent", data)
        expected_msg = (
            "Missing required fields for standalone task: parent "
            "(Note: standalone tasks don't require parent)"
        )
        assert msg == expected_msg

    def test_generate_contextual_error_message_missing_parent_hierarchy(self):
        """Test missing parent error for hierarchy task."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message("missing_parent", data)
        assert msg == "Missing required fields for hierarchy task: parent"

    def test_generate_contextual_error_message_parent_not_exist_standalone(self):
        """Test parent not exist error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message(
            "parent_not_exist", data, parent_kind="feature", parent_id="nonexistent"
        )
        assert (
            msg
            == "Parent feature with ID 'nonexistent' does not exist (standalone task validation)"
        )

    def test_generate_contextual_error_message_parent_not_exist_hierarchy(self):
        """Test parent not exist error for hierarchy task."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message(
            "parent_not_exist", data, parent_kind="feature", parent_id="nonexistent"
        )
        assert (
            msg == "Parent feature with ID 'nonexistent' does not exist (hierarchy task validation)"
        )

    def test_generate_contextual_error_message_missing_fields_standalone(self):
        """Test missing fields error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message(
            "missing_fields", data, fields=["status", "created"]
        )
        assert msg == "Missing required fields for standalone task: status, created"

    def test_generate_contextual_error_message_missing_fields_hierarchy(self):
        """Test missing fields error for hierarchy task."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message(
            "missing_fields", data, fields=["status", "created"]
        )
        assert msg == "Missing required fields for hierarchy task: status, created"

    def test_generate_contextual_error_message_invalid_enum_standalone(self):
        """Test invalid enum error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message(
            "invalid_enum",
            data,
            field="priority",
            value="invalid",
            valid_values=["high", "normal", "low"],
        )
        expected_msg = (
            "Invalid priority 'invalid' for standalone task. "
            "Must be one of: ['high', 'normal', 'low']"
        )
        assert msg == expected_msg

    def test_generate_contextual_error_message_invalid_enum_hierarchy(self):
        """Test invalid enum error for hierarchy task."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = generate_contextual_error_message(
            "invalid_enum",
            data,
            field="priority",
            value="invalid",
            valid_values=["high", "normal", "low"],
        )
        expected_msg = (
            "Invalid priority 'invalid' for hierarchy task. "
            "Must be one of: ['high', 'normal', 'low']"
        )
        assert msg == expected_msg


class TestFormatValidationErrorWithContext:
    """Test validation error formatting with context."""

    def test_format_validation_error_with_context_status_standalone(self):
        """Test formatting status error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "draft",
            "title": "Test Task",
        }
        msg = format_validation_error_with_context("Invalid status 'draft' for task", data)
        assert msg == "Invalid status 'draft' for standalone task"

    def test_format_validation_error_with_context_status_hierarchy(self):
        """Test formatting status error for hierarchy task."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "status": "draft",
            "title": "Test Task",
        }
        msg = format_validation_error_with_context("Invalid status 'draft' for task", data)
        assert msg == "Invalid status 'draft' for hierarchy task"

    def test_format_validation_error_with_context_parent_not_exist_standalone(self):
        """Test formatting parent not exist error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = format_validation_error_with_context(
            "Parent feature with ID 'nonexistent' does not exist", data
        )
        assert (
            msg
            == "Parent feature with ID 'nonexistent' does not exist (standalone task validation)"
        )

    def test_format_validation_error_with_context_parent_not_exist_hierarchy(self):
        """Test formatting parent not exist error for hierarchy task."""
        data = {
            "kind": "task",
            "parent": "F-test-feature",
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = format_validation_error_with_context(
            "Parent feature with ID 'nonexistent' does not exist", data
        )
        assert (
            msg == "Parent feature with ID 'nonexistent' does not exist (hierarchy task validation)"
        )

    def test_format_validation_error_with_context_must_have_parent_standalone(self):
        """Test formatting must have parent error for standalone task."""
        data = {
            "kind": "task",
            "parent": None,
            "id": "T-test",
            "status": "open",
            "title": "Test Task",
        }
        msg = format_validation_error_with_context("task objects must have a parent", data)
        assert (
            msg == "task objects must have a parent (Note: standalone tasks don't require parent)"
        )

    def test_format_validation_error_with_context_non_task(self):
        """Test formatting error for non-task object."""
        data = {
            "kind": "project",
            "id": "P-test",
            "status": "draft",
            "title": "Test Project",
        }
        msg = format_validation_error_with_context("Invalid status 'open' for project", data)
        assert msg == "Invalid status 'open' for project"


class TestContextualValidationErrors:
    """Test contextual validation errors in full validation pipeline."""

    def test_validate_object_data_invalid_status_standalone_task(self, tmp_path: Path):
        """Test validation error for invalid status in standalone task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": None,
            "status": "draft",  # Invalid for task
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Invalid status 'draft' for standalone task" in error.errors[0]

    def test_validate_object_data_invalid_status_hierarchy_task(self, tmp_path: Path):
        """Test validation error for invalid status in hierarchy task."""
        # Create project structure first
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
            "id": "T-test",
            "parent": "F-test-feature",
            "status": "draft",  # Invalid for task
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Invalid status 'draft' for hierarchy task" in error.errors[0]

    def test_validate_object_data_invalid_priority_standalone_task(self, tmp_path: Path):
        """Test validation error for invalid priority in standalone task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": None,
            "status": "open",
            "title": "Test Task",
            "priority": "invalid",  # Invalid priority
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Invalid priority 'invalid' for standalone task" in error.errors[0]

    def test_validate_object_data_invalid_priority_hierarchy_task(self, tmp_path: Path):
        """Test validation error for invalid priority in hierarchy task."""
        # Create project structure first
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
            "id": "T-test",
            "parent": "F-test-feature",
            "status": "open",
            "title": "Test Task",
            "priority": "invalid",  # Invalid priority
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Invalid priority 'invalid' for hierarchy task" in error.errors[0]

    def test_validate_object_data_missing_fields_standalone_task(self, tmp_path: Path):
        """Test validation error for missing fields in standalone task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": None,
            "title": "Test Task",
            # Missing: status, created, updated, schema_version
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Missing required fields for standalone task:" in error.errors[0]

    def test_validate_object_data_missing_fields_hierarchy_task(self, tmp_path: Path):
        """Test validation error for missing fields in hierarchy task."""
        # Create project structure first
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
            "id": "T-test",
            "parent": "F-test-feature",
            "title": "Test Task",
            # Missing: status, created, updated, schema_version
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert "Missing required fields for hierarchy task:" in error.errors[0]

    def test_validate_object_data_parent_not_exist_hierarchy_task(self, tmp_path: Path):
        """Test validation error for non-existent parent in hierarchy task."""
        data = {
            "kind": "task",
            "id": "T-test",
            "parent": "F-nonexistent",
            "status": "open",
            "title": "Test Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        assert (
            "Parent feature with ID 'F-nonexistent' does not exist (hierarchy task validation)"
            in error.errors[0]
        )

    def test_validate_object_data_non_task_unchanged(self, tmp_path: Path):
        """Test that non-task validation errors remain unchanged."""
        data = {
            "kind": "project",
            "id": "P-test",
            "parent": None,
            "status": "open",  # Invalid for project
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        # Non-task errors should remain unchanged
        assert "Invalid status 'open' for project" in error.errors[0]
        assert "standalone" not in error.errors[0]
        assert "hierarchy" not in error.errors[0]


class TestBackwardCompatibility:
    """Test that existing error patterns are maintained for backward compatibility."""

    def test_non_task_error_messages_unchanged(self, tmp_path: Path):
        """Test that non-task error messages remain unchanged."""
        data = {
            "kind": "project",
            "id": "P-test",
            "parent": None,
            "status": "invalid",  # Invalid status
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, tmp_path / "planning")

        error = exc_info.value
        assert len(error.errors) == 1
        # Should not have task-specific context for non-task objects
        assert "standalone" not in error.errors[0]
        assert "hierarchy" not in error.errors[0]

    def test_missing_kind_error_unchanged(self, tmp_path: Path):
        """Test that missing kind error remains unchanged."""
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

    def test_invalid_kind_error_unchanged(self, tmp_path: Path):
        """Test that invalid kind error remains unchanged."""
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
