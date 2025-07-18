"""Tests for generic type functionality in Trellis MCP.

Tests the generic type definitions, type discrimination, and generic functions
for handling optional parent relationships in task objects.
"""

import pytest

from trellis_mcp.types import (
    create_task_object_generic,
    create_typed_task_factory,
    handle_task_by_type,
    is_hierarchy_task,
    is_object_with_kind,
    is_standalone_task,
    is_task_object,
    is_task_with_parent_type,
    process_task_generic,
    validate_task_parent_constraint,
)


class TestGenericTypeDiscrimination:
    """Tests for generic type discrimination functions."""

    def test_is_object_with_kind_task(self):
        """Test generic type discrimination for task objects."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": "F-feature",
            "status": "open",
            "priority": "normal",
        }

        assert is_object_with_kind(task_data, "task") is True
        assert is_object_with_kind(task_data, "project") is False
        assert is_object_with_kind(task_data, "epic") is False
        assert is_object_with_kind(task_data, "feature") is False

    def test_is_object_with_kind_project(self):
        """Test generic type discrimination for project objects."""
        project_data = {
            "kind": "project",
            "id": "test-project",
            "title": "Test Project",
            "status": "draft",
            "priority": "high",
        }

        assert is_object_with_kind(project_data, "project") is True
        assert is_object_with_kind(project_data, "task") is False
        assert is_object_with_kind(project_data, "epic") is False
        assert is_object_with_kind(project_data, "feature") is False

    def test_is_object_with_kind_invalid_input(self):
        """Test generic type discrimination with invalid input."""
        assert is_object_with_kind(None, "task") is False
        assert is_object_with_kind("not-a-dict", "task") is False
        assert is_object_with_kind([], "task") is False
        assert is_object_with_kind({}, "task") is False

    def test_is_task_with_parent_type_hierarchy(self):
        """Test generic parent type validation for hierarchy tasks."""
        hierarchy_task = {
            "kind": "task",
            "id": "hierarchy-task",
            "title": "Hierarchy Task",
            "parent": "F-feature",
            "status": "open",
            "priority": "normal",
        }

        assert is_task_with_parent_type(hierarchy_task, True) is True
        assert is_task_with_parent_type(hierarchy_task, False) is False

    def test_is_task_with_parent_type_standalone(self):
        """Test generic parent type validation for standalone tasks."""
        standalone_task = {
            "kind": "task",
            "id": "standalone-task",
            "title": "Standalone Task",
            "parent": None,
            "status": "open",
            "priority": "normal",
        }

        assert is_task_with_parent_type(standalone_task, False) is True
        assert is_task_with_parent_type(standalone_task, True) is False

    def test_is_task_with_parent_type_empty_parent(self):
        """Test generic parent type validation with empty parent."""
        empty_parent_task = {
            "kind": "task",
            "id": "empty-parent-task",
            "title": "Empty Parent Task",
            "parent": "",
            "status": "open",
            "priority": "normal",
        }

        assert is_task_with_parent_type(empty_parent_task, False) is True
        assert is_task_with_parent_type(empty_parent_task, True) is False

    def test_is_task_with_parent_type_non_task(self):
        """Test generic parent type validation with non-task objects."""
        project_data = {
            "kind": "project",
            "id": "test-project",
            "title": "Test Project",
            "status": "draft",
            "priority": "high",
        }

        assert is_task_with_parent_type(project_data, True) is False
        assert is_task_with_parent_type(project_data, False) is False

    def test_is_task_with_parent_type_invalid_input(self):
        """Test generic parent type validation with invalid input."""
        assert is_task_with_parent_type(None, True) is False
        assert is_task_with_parent_type("not-a-dict", True) is False
        assert is_task_with_parent_type([], False) is False


class TestGenericFactoryFunctions:
    """Tests for generic factory functions."""

    def test_create_task_object_generic_standalone(self):
        """Test generic task creation for standalone tasks."""
        task = create_task_object_generic("T-1", "Test Task")

        assert task["kind"] == "task"
        assert task["id"] == "T-1"
        assert task["title"] == "Test Task"
        assert task["parent"] is None
        assert is_standalone_task(task) is True
        assert is_hierarchy_task(task) is False

    def test_create_task_object_generic_hierarchy(self):
        """Test generic task creation for hierarchy tasks."""
        task = create_task_object_generic("T-2", "Test Task", "F-feature")

        assert task["kind"] == "task"
        assert task["id"] == "T-2"
        assert task["title"] == "Test Task"
        assert task["parent"] == "F-feature"
        assert is_standalone_task(task) is False
        assert is_hierarchy_task(task) is True

    def test_create_task_object_generic_with_kwargs(self):
        """Test generic task creation with additional fields."""
        task = create_task_object_generic(
            "T-3", "Test Task", "F-feature", status="open", priority="high", custom_field="value"
        )

        assert task["kind"] == "task"
        assert task["id"] == "T-3"
        assert task["title"] == "Test Task"
        assert task["parent"] == "F-feature"
        assert task["status"] == "open"
        assert task["priority"] == "high"
        assert task["custom_field"] == "value"

    def test_process_task_generic_valid_task(self):
        """Test generic task processing with valid task."""
        task = create_task_object_generic("T-4", "Test Task")

        def add_timestamp(task_obj):
            task_obj["processed"] = True
            return task_obj

        processed_task = process_task_generic(task, add_timestamp)

        assert processed_task["kind"] == "task"
        assert processed_task["id"] == "T-4"
        assert processed_task["processed"] is True

    def test_process_task_generic_invalid_input(self):
        """Test generic task processing with invalid input."""

        def dummy_processor(task_obj):
            return task_obj

        with pytest.raises(ValueError, match="task_obj must be a dictionary"):
            process_task_generic("not-a-dict", dummy_processor)  # type: ignore

        with pytest.raises(ValueError, match="task_obj must be a task object"):
            process_task_generic({"kind": "project"}, dummy_processor)


class TestGenericTemplateFunction:
    """Tests for generic template functions."""

    def test_handle_task_by_type_standalone(self):
        """Test generic task handling for standalone tasks."""
        standalone_task = create_task_object_generic("T-5", "Standalone Task")

        def process_standalone(task):
            task["type"] = "standalone"
            return task

        def process_hierarchy(task):
            task["type"] = "hierarchy"
            return task

        result = handle_task_by_type(standalone_task, process_standalone, process_hierarchy)

        assert result["type"] == "standalone"
        assert result["id"] == "T-5"

    def test_handle_task_by_type_hierarchy(self):
        """Test generic task handling for hierarchy tasks."""
        hierarchy_task = create_task_object_generic("T-6", "Hierarchy Task", "F-feature")

        def process_standalone(task):
            task["type"] = "standalone"
            return task

        def process_hierarchy(task):
            task["type"] = "hierarchy"
            return task

        result = handle_task_by_type(hierarchy_task, process_standalone, process_hierarchy)

        assert result["type"] == "hierarchy"
        assert result["id"] == "T-6"

    def test_handle_task_by_type_invalid_input(self):
        """Test generic task handling with invalid input."""

        def dummy_handler(task):
            return task

        with pytest.raises(ValueError, match="task_obj must be a dictionary"):
            handle_task_by_type("not-a-dict", dummy_handler, dummy_handler)  # type: ignore

        with pytest.raises(ValueError, match="task_obj must be a task object"):
            handle_task_by_type({"kind": "project"}, dummy_handler, dummy_handler)


class TestGenericParentConstraintValidation:
    """Tests for generic parent constraint validation."""

    def test_validate_task_parent_constraint_none_type(self):
        """Test parent constraint validation for None type (standalone)."""
        standalone_task = create_task_object_generic("T-7", "Standalone Task")
        hierarchy_task = create_task_object_generic("T-8", "Hierarchy Task", "F-feature")

        assert validate_task_parent_constraint(standalone_task, type(None)) is True
        assert validate_task_parent_constraint(hierarchy_task, type(None)) is False

    def test_validate_task_parent_constraint_str_type(self):
        """Test parent constraint validation for str type (hierarchy)."""
        standalone_task = create_task_object_generic("T-9", "Standalone Task")
        hierarchy_task = create_task_object_generic("T-10", "Hierarchy Task", "F-feature")

        assert validate_task_parent_constraint(standalone_task, str) is False
        assert validate_task_parent_constraint(hierarchy_task, str) is True

    def test_validate_task_parent_constraint_empty_parent(self):
        """Test parent constraint validation with empty parent."""
        task_with_empty_parent = {
            "kind": "task",
            "id": "T-11",
            "title": "Empty Parent Task",
            "parent": "",
        }

        assert validate_task_parent_constraint(task_with_empty_parent, type(None)) is True
        assert validate_task_parent_constraint(task_with_empty_parent, str) is False

    def test_validate_task_parent_constraint_invalid_input(self):
        """Test parent constraint validation with invalid input."""
        assert validate_task_parent_constraint("not-a-dict", type(None)) is False  # type: ignore
        assert validate_task_parent_constraint({"kind": "project"}, str) is False
        assert validate_task_parent_constraint(None, type(None)) is False  # type: ignore

    def test_validate_task_parent_constraint_invalid_type(self):
        """Test parent constraint validation with invalid expected type."""
        task = create_task_object_generic("T-12", "Test Task")
        assert validate_task_parent_constraint(task, int) is False  # type: ignore
        assert validate_task_parent_constraint(task, list) is False  # type: ignore


class TestGenericTaskFactoryCreation:
    """Tests for generic task factory creation."""

    def test_create_typed_task_factory_standalone(self):
        """Test creating a factory for standalone tasks."""
        create_standalone_task = create_typed_task_factory(False)

        task = create_standalone_task("T-13", "Standalone Task")

        assert task["kind"] == "task"
        assert task["id"] == "T-13"
        assert task["title"] == "Standalone Task"
        assert task["parent"] is None
        assert is_standalone_task(task) is True

    def test_create_typed_task_factory_hierarchy(self):
        """Test creating a factory for hierarchy tasks."""
        create_hierarchy_task = create_typed_task_factory(True)

        task = create_hierarchy_task("T-14", "Hierarchy Task", "F-feature")

        assert task["kind"] == "task"
        assert task["id"] == "T-14"
        assert task["title"] == "Hierarchy Task"
        assert task["parent"] == "F-feature"
        assert is_hierarchy_task(task) is True

    def test_create_typed_task_factory_standalone_with_parent_error(self):
        """Test standalone factory rejects parent."""
        create_standalone_task = create_typed_task_factory(False)

        with pytest.raises(ValueError, match="Parent must be None or empty for this task type"):
            create_standalone_task("T-15", "Invalid Task", "F-feature")

    def test_create_typed_task_factory_hierarchy_without_parent_error(self):
        """Test hierarchy factory requires parent."""
        create_hierarchy_task = create_typed_task_factory(True)

        with pytest.raises(ValueError, match="Parent is required for this task type"):
            create_hierarchy_task("T-16", "Invalid Task")

        with pytest.raises(ValueError, match="Parent is required for this task type"):
            create_hierarchy_task("T-17", "Invalid Task", "")

    def test_create_typed_task_factory_with_kwargs(self):
        """Test typed factories work with additional fields."""
        create_standalone_task = create_typed_task_factory(False)
        create_hierarchy_task = create_typed_task_factory(True)

        standalone = create_standalone_task(
            "T-18", "Standalone Task", status="open", priority="high"
        )

        hierarchy = create_hierarchy_task(
            "T-19", "Hierarchy Task", "F-feature", status="in_progress", priority="low"
        )

        assert standalone["status"] == "open"
        assert standalone["priority"] == "high"
        assert hierarchy["status"] == "in_progress"
        assert hierarchy["priority"] == "low"


class TestGenericTypeConsistency:
    """Tests for consistency between generic types and existing functionality."""

    def test_generic_functions_consistent_with_type_guards(self):
        """Test that generic functions are consistent with existing type guards."""
        standalone_task = create_task_object_generic("T-20", "Standalone Task")
        hierarchy_task = create_task_object_generic("T-21", "Hierarchy Task", "F-feature")

        # Test consistency with existing type guards
        assert is_standalone_task(standalone_task) == is_task_with_parent_type(
            standalone_task, False
        )
        assert is_hierarchy_task(hierarchy_task) == is_task_with_parent_type(hierarchy_task, True)

        # Test consistency with generic discrimination
        assert is_task_object(standalone_task) == is_object_with_kind(standalone_task, "task")
        assert is_task_object(hierarchy_task) == is_object_with_kind(hierarchy_task, "task")

    def test_generic_parent_validation_consistent(self):
        """Test that generic parent validation is consistent with type guards."""
        standalone_task = create_task_object_generic("T-22", "Standalone Task")
        hierarchy_task = create_task_object_generic("T-23", "Hierarchy Task", "F-feature")

        # Validate consistency
        assert validate_task_parent_constraint(standalone_task, type(None)) == is_standalone_task(
            standalone_task
        )
        assert validate_task_parent_constraint(hierarchy_task, str) == is_hierarchy_task(
            hierarchy_task
        )

    def test_generic_factory_produces_valid_objects(self):
        """Test that generic factories produce objects that pass type guards."""
        standalone_task = create_task_object_generic("T-24", "Standalone Task")
        hierarchy_task = create_task_object_generic("T-25", "Hierarchy Task", "F-feature")

        # Test that created objects pass all relevant type guards
        assert is_task_object(standalone_task) is True
        assert is_standalone_task(standalone_task) is True
        assert is_hierarchy_task(standalone_task) is False

        assert is_task_object(hierarchy_task) is True
        assert is_hierarchy_task(hierarchy_task) is True
        assert is_standalone_task(hierarchy_task) is False


class TestGenericTypeEdgeCases:
    """Tests for edge cases and error conditions with generic types."""

    def test_generic_functions_with_mixed_data_types(self):
        """Test generic functions handle mixed data types properly."""
        # Task with non-string parent (should still work for type checking)
        task_with_number_parent = {
            "kind": "task",
            "id": "T-26",
            "title": "Mixed Type Task",
            "parent": 123,  # Non-string parent
            "status": "open",
        }

        # Should be considered hierarchy task since parent is truthy
        assert is_task_with_parent_type(task_with_number_parent, True) is True
        assert is_task_with_parent_type(task_with_number_parent, False) is False

    def test_generic_functions_with_missing_fields(self):
        """Test generic functions handle missing fields gracefully."""
        incomplete_task = {
            "kind": "task",
            "id": "T-27",
            # Missing title and parent
        }

        # Should still work for type discrimination
        assert is_object_with_kind(incomplete_task, "task") is True
        assert (
            is_task_with_parent_type(incomplete_task, False) is True
        )  # No parent field = standalone

    def test_generic_template_function_with_invalid_task_state(self):
        """Test generic template function with task in invalid state."""
        invalid_task = {
            "kind": "task",
            "id": "T-28",
            "title": "Invalid Task",
            "parent": "   ",  # Whitespace parent - ambiguous case
        }

        def dummy_handler(task):
            return task

        # This should be treated as hierarchy task (non-empty parent)
        assert is_task_with_parent_type(invalid_task, True) is True
        result = handle_task_by_type(invalid_task, dummy_handler, dummy_handler)
        assert result["id"] == "T-28"
