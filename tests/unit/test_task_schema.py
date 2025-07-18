"""Tests for TaskModel schema focusing on optional parent functionality.

This module provides comprehensive tests for the TaskModel class,
with emphasis on the new optional parent field that enables both
standalone tasks and hierarchy-based tasks.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from trellis_mcp.models.common import Priority
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


class TestTaskModelOptionalParent:
    """Test TaskModel with optional parent field functionality."""

    def test_standalone_task_creation_with_none_parent(self) -> None:
        """Test creation of standalone task with None parent."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="standalone-task",
            parent=None,  # Standalone task
            status=StatusEnum.OPEN,
            title="Standalone Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.parent is None
        assert task.kind == KindEnum.TASK
        assert task.id == "standalone-task"
        assert task.status == StatusEnum.OPEN

    def test_standalone_task_creation_with_missing_parent_field(self) -> None:
        """Test creation of standalone task without parent field."""
        data = {
            "kind": "task",
            "id": "standalone-task",
            # parent field is missing
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        task = TaskModel.model_validate(data)
        assert task.parent is None
        assert task.kind == KindEnum.TASK
        assert task.id == "standalone-task"

    def test_standalone_task_creation_with_empty_string_parent(self) -> None:
        """Test creation of standalone task with empty string parent."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="standalone-task",
            parent="",  # Empty string should be converted to None
            status=StatusEnum.OPEN,
            title="Standalone Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.parent is None
        assert task.kind == KindEnum.TASK
        assert task.id == "standalone-task"

    def test_hierarchy_task_creation_with_valid_parent(self) -> None:
        """Test creation of hierarchy task with valid parent."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="hierarchy-task",
            parent="test-feature",  # Hierarchy task
            status=StatusEnum.OPEN,
            title="Hierarchy Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.parent == "test-feature"
        assert task.kind == KindEnum.TASK
        assert task.id == "hierarchy-task"
        assert task.status == StatusEnum.OPEN

    def test_task_all_valid_statuses(self) -> None:
        """Test that all valid task statuses work correctly."""
        valid_statuses = [
            StatusEnum.OPEN,
            StatusEnum.IN_PROGRESS,
            StatusEnum.REVIEW,
            StatusEnum.DONE,
        ]

        for status in valid_statuses:
            task = TaskModel(
                kind=KindEnum.TASK,
                id=f"task-{status.value}",
                parent=None,  # Standalone task
                status=status,
                title=f"Task with {status.value} Status",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

            assert task.status == status

    def test_task_invalid_statuses(self) -> None:
        """Test that invalid statuses for tasks fail validation."""
        invalid_statuses = [
            StatusEnum.DRAFT,  # Invalid for task
        ]

        for status in invalid_statuses:
            with pytest.raises(ValidationError) as exc_info:
                TaskModel(
                    kind=KindEnum.TASK,
                    id="invalid-task",
                    parent=None,
                    status=status,
                    title="Invalid Task",
                    priority=Priority.NORMAL,
                    prerequisites=[],
                    worktree=None,
                    created=datetime.now(),
                    updated=datetime.now(),
                    schema_version="1.1",
                )

            assert "Invalid status" in str(exc_info.value) and "task" in str(exc_info.value)

    def test_task_with_prerequisites_standalone(self) -> None:
        """Test standalone task with prerequisites."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="standalone-task-with-prereqs",
            parent=None,  # Standalone task
            status=StatusEnum.OPEN,
            title="Standalone Task with Prerequisites",
            priority=Priority.HIGH,
            prerequisites=["prereq-1", "prereq-2", "prereq-3"],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.parent is None
        assert task.prerequisites == ["prereq-1", "prereq-2", "prereq-3"]
        assert task.priority == Priority.HIGH

    def test_task_with_prerequisites_hierarchy(self) -> None:
        """Test hierarchy task with prerequisites."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="hierarchy-task-with-prereqs",
            parent="test-feature",  # Hierarchy task
            status=StatusEnum.OPEN,
            title="Hierarchy Task with Prerequisites",
            priority=Priority.LOW,
            prerequisites=["other-task-1", "other-task-2"],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.parent == "test-feature"
        assert task.prerequisites == ["other-task-1", "other-task-2"]
        assert task.priority == Priority.LOW

    def test_task_with_worktree_standalone(self) -> None:
        """Test standalone task with worktree."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="standalone-task-with-worktree",
            parent=None,  # Standalone task
            status=StatusEnum.IN_PROGRESS,
            title="Standalone Task with Worktree",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree="/path/to/worktree",
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.parent is None
        assert task.worktree == "/path/to/worktree"
        assert task.status == StatusEnum.IN_PROGRESS

    def test_task_with_worktree_hierarchy(self) -> None:
        """Test hierarchy task with worktree."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="hierarchy-task-with-worktree",
            parent="test-feature",  # Hierarchy task
            status=StatusEnum.IN_PROGRESS,
            title="Hierarchy Task with Worktree",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree="/path/to/hierarchy/worktree",
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.parent == "test-feature"
        assert task.worktree == "/path/to/hierarchy/worktree"
        assert task.status == StatusEnum.IN_PROGRESS


class TestTaskModelStatusTransitions:
    """Test status transition validation specific to TaskModel."""

    def test_task_status_transition_matrix(self) -> None:
        """Test the complete task status transition matrix."""
        # Get transition matrix from TaskModel
        transitions = TaskModel._valid_transitions

        # Verify expected transitions exist
        assert StatusEnum.OPEN in transitions
        assert StatusEnum.IN_PROGRESS in transitions
        assert StatusEnum.REVIEW in transitions
        assert StatusEnum.DONE in transitions

        # Verify specific valid transitions
        assert StatusEnum.IN_PROGRESS in transitions[StatusEnum.OPEN]
        assert StatusEnum.DONE in transitions[StatusEnum.OPEN]
        assert StatusEnum.REVIEW in transitions[StatusEnum.IN_PROGRESS]
        assert StatusEnum.DONE in transitions[StatusEnum.IN_PROGRESS]
        assert StatusEnum.DONE in transitions[StatusEnum.REVIEW]

    def test_task_valid_status_transitions(self) -> None:
        """Test valid status transitions for tasks."""
        valid_transitions = [
            (StatusEnum.OPEN, StatusEnum.IN_PROGRESS),
            (StatusEnum.OPEN, StatusEnum.DONE),  # Shortcut
            (StatusEnum.IN_PROGRESS, StatusEnum.REVIEW),
            (StatusEnum.IN_PROGRESS, StatusEnum.DONE),  # Shortcut
            (StatusEnum.REVIEW, StatusEnum.DONE),
        ]

        for old_status, new_status in valid_transitions:
            # Should not raise exception
            result = TaskModel.validate_status_transition(old_status, new_status)
            assert result is True

    def test_task_invalid_status_transitions(self) -> None:
        """Test invalid status transitions for tasks."""
        invalid_transitions = [
            (StatusEnum.OPEN, StatusEnum.REVIEW),  # Can't skip in-progress
            (StatusEnum.IN_PROGRESS, StatusEnum.OPEN),  # Can't go backward
            (StatusEnum.REVIEW, StatusEnum.OPEN),  # Can't go backward
            (StatusEnum.REVIEW, StatusEnum.IN_PROGRESS),  # Can't go backward
            (StatusEnum.DONE, StatusEnum.OPEN),  # Can't go backward
            (StatusEnum.DONE, StatusEnum.IN_PROGRESS),  # Can't go backward
            (StatusEnum.DONE, StatusEnum.REVIEW),  # Can't go backward
        ]

        for old_status, new_status in invalid_transitions:
            with pytest.raises(ValueError) as exc_info:
                TaskModel.validate_status_transition(old_status, new_status)

            error_message = str(exc_info.value)
            assert "Invalid status transition for task" in error_message
            assert old_status.value in error_message
            assert new_status.value in error_message

    def test_task_same_status_transitions(self) -> None:
        """Test that same status transitions are always valid."""
        task_statuses = [
            StatusEnum.OPEN,
            StatusEnum.IN_PROGRESS,
            StatusEnum.REVIEW,
            StatusEnum.DONE,
        ]

        for status in task_statuses:
            # Same status should always be valid
            result = TaskModel.validate_status_transition(status, status)
            assert result is True


class TestTaskModelSerialization:
    """Test serialization and deserialization of TaskModel."""

    def test_standalone_task_serialization(self) -> None:
        """Test serialization of standalone task."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="standalone-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="Standalone Task",
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
        assert task_dict["kind"] == "task"
        assert task_dict["id"] == "standalone-task"

    def test_hierarchy_task_serialization(self) -> None:
        """Test serialization of hierarchy task."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="hierarchy-task",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Hierarchy Task",
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
        assert task_dict["kind"] == "task"
        assert task_dict["id"] == "hierarchy-task"

    def test_standalone_task_deserialization(self) -> None:
        """Test deserialization of standalone task data."""
        data = {
            "kind": "task",
            "id": "standalone-task",
            "parent": None,
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        task = TaskModel.model_validate(data)
        assert task.parent is None
        assert task.kind == KindEnum.TASK
        assert task.id == "standalone-task"

    def test_hierarchy_task_deserialization(self) -> None:
        """Test deserialization of hierarchy task data."""
        data = {
            "kind": "task",
            "id": "hierarchy-task",
            "parent": "test-feature",
            "status": "open",
            "title": "Hierarchy Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        task = TaskModel.model_validate(data)
        assert task.parent == "test-feature"
        assert task.kind == KindEnum.TASK
        assert task.id == "hierarchy-task"

    def test_task_deserialization_missing_parent(self) -> None:
        """Test deserialization when parent field is missing."""
        data = {
            "kind": "task",
            "id": "task-missing-parent",
            # parent field is missing
            "status": "open",
            "title": "Task Missing Parent",
            "priority": "normal",
            "prerequisites": [],
            "created": "2025-01-01T00:00:00",
            "updated": "2025-01-01T00:00:00",
            "schema_version": "1.1",
        }

        task = TaskModel.model_validate(data)
        assert task.parent is None
        assert task.kind == KindEnum.TASK
        assert task.id == "task-missing-parent"

    def test_task_roundtrip_serialization_standalone(self) -> None:
        """Test round-trip serialization for standalone task."""
        original_task = TaskModel(
            kind=KindEnum.TASK,
            id="roundtrip-standalone",
            parent=None,
            status=StatusEnum.OPEN,
            title="Roundtrip Standalone Task",
            priority=Priority.HIGH,
            prerequisites=["prereq-1", "prereq-2"],
            worktree="/path/to/worktree",
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        # Serialize to dict
        task_dict = original_task.model_dump()

        # Deserialize back to model
        restored_task = TaskModel.model_validate(task_dict)

        # Verify integrity
        assert restored_task.parent is None
        assert restored_task.kind == original_task.kind
        assert restored_task.id == original_task.id
        assert restored_task.status == original_task.status
        assert restored_task.title == original_task.title
        assert restored_task.priority == original_task.priority
        assert restored_task.prerequisites == original_task.prerequisites
        assert restored_task.worktree == original_task.worktree

    def test_task_roundtrip_serialization_hierarchy(self) -> None:
        """Test round-trip serialization for hierarchy task."""
        original_task = TaskModel(
            kind=KindEnum.TASK,
            id="roundtrip-hierarchy",
            parent="test-feature",
            status=StatusEnum.IN_PROGRESS,
            title="Roundtrip Hierarchy Task",
            priority=Priority.LOW,
            prerequisites=["other-task"],
            worktree="/path/to/hierarchy/worktree",
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        # Serialize to dict
        task_dict = original_task.model_dump()

        # Deserialize back to model
        restored_task = TaskModel.model_validate(task_dict)

        # Verify integrity
        assert restored_task.parent == "test-feature"
        assert restored_task.kind == original_task.kind
        assert restored_task.id == original_task.id
        assert restored_task.status == original_task.status
        assert restored_task.title == original_task.title
        assert restored_task.priority == original_task.priority
        assert restored_task.prerequisites == original_task.prerequisites
        assert restored_task.worktree == original_task.worktree


class TestTaskModelEdgeCases:
    """Test edge cases and error conditions for TaskModel."""

    def test_task_with_all_priority_levels(self) -> None:
        """Test task creation with all priority levels."""
        priorities = [Priority.HIGH, Priority.NORMAL, Priority.LOW]

        for i, priority in enumerate(priorities):
            task = TaskModel(
                kind=KindEnum.TASK,
                id=f"task-priority-{i}",
                parent=None,
                status=StatusEnum.OPEN,
                title=f"Task with {priority.value} Priority",
                priority=priority,
                prerequisites=[],
                worktree=None,
                created=datetime.now(),
                updated=datetime.now(),
                schema_version="1.1",
            )

            assert task.priority == priority

    def test_task_with_empty_prerequisites(self) -> None:
        """Test task with empty prerequisites list."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="empty-prereqs-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="Task with Empty Prerequisites",
            priority=Priority.NORMAL,
            prerequisites=[],  # Explicitly empty
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.prerequisites == []

    def test_task_with_complex_prerequisites(self) -> None:
        """Test task with complex prerequisites."""
        complex_prereqs = [
            "T-task-1",
            "simple-task",
            "T-task-with-dashes",
            "task-with-many-words-and-dashes",
            "T-another-complex-task-name",
        ]

        task = TaskModel(
            kind=KindEnum.TASK,
            id="complex-prereqs-task",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Task with Complex Prerequisites",
            priority=Priority.NORMAL,
            prerequisites=complex_prereqs,
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.prerequisites == complex_prereqs

    def test_task_with_null_worktree(self) -> None:
        """Test task with null worktree."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="null-worktree-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="Task with Null Worktree",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,  # Explicitly null
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.worktree is None

    def test_task_kind_field_validation(self) -> None:
        """Test that kind field is properly validated."""
        # TaskModel should have kind fixed as TASK
        task = TaskModel(
            kind=KindEnum.TASK,
            id="kind-validation-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="Kind Validation Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.kind == KindEnum.TASK

    def test_task_datetime_precision(self) -> None:
        """Test that datetime fields preserve precision."""
        created_time = datetime(2025, 1, 15, 14, 30, 45, 123456)
        updated_time = datetime(2025, 1, 15, 15, 45, 30, 654321)

        task = TaskModel(
            kind=KindEnum.TASK,
            id="datetime-precision-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="DateTime Precision Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=created_time,
            updated=updated_time,
            schema_version="1.1",
        )

        assert task.created == created_time
        assert task.updated == updated_time

    def test_task_schema_version_validation(self) -> None:
        """Test that schema version is properly validated."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="schema-version-task",
            parent=None,
            status=StatusEnum.OPEN,
            title="Schema Version Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

        assert task.schema_version == "1.1"

    def test_task_comprehensive_validation(self) -> None:
        """Test comprehensive validation with maximum fields."""
        task = TaskModel(
            kind=KindEnum.TASK,
            id="comprehensive-task",
            parent="test-feature",
            status=StatusEnum.REVIEW,
            title="Comprehensive Validation Task",
            priority=Priority.HIGH,
            prerequisites=["prereq-1", "prereq-2", "prereq-3"],
            worktree="/path/to/comprehensive/worktree",
            created=datetime(2025, 1, 1, 10, 0, 0),
            updated=datetime(2025, 1, 1, 15, 30, 0),
            schema_version="1.1",
        )

        # Verify all fields
        assert task.kind == KindEnum.TASK
        assert task.id == "comprehensive-task"
        assert task.parent == "test-feature"
        assert task.status == StatusEnum.REVIEW
        assert task.title == "Comprehensive Validation Task"
        assert task.priority == Priority.HIGH
        assert task.prerequisites == ["prereq-1", "prereq-2", "prereq-3"]
        assert task.worktree == "/path/to/comprehensive/worktree"
        assert task.created == datetime(2025, 1, 1, 10, 0, 0)
        assert task.updated == datetime(2025, 1, 1, 15, 30, 0)
        assert task.schema_version == "1.1"
