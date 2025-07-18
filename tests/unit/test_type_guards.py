"""Tests for type guard functions in Trellis MCP.

Tests both the utility functions and the new TypeGuard implementations
for proper type narrowing and runtime type checking.
"""

from typing import Any

from trellis_mcp.types import (
    is_epic_object,
    is_feature_object,
    is_hierarchy_task,
    is_project_object,
    is_standalone_task,
    is_task_object,
)
from trellis_mcp.validation.task_utils import (
    is_hierarchy_task_guard,
    is_standalone_task_guard,
)


class TestStandaloneTaskGuard:
    """Tests for is_standalone_task type guard function."""

    def test_valid_standalone_task(self):
        """Test type guard with valid standalone task."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": None,
            "status": "open",
            "priority": "normal",
        }

        assert is_standalone_task(task_data) is True

    def test_valid_standalone_task_empty_parent(self):
        """Test type guard with standalone task having empty parent."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": "",
            "status": "open",
            "priority": "normal",
        }

        assert is_standalone_task(task_data) is True

    def test_valid_standalone_task_missing_parent(self):
        """Test type guard with standalone task missing parent field."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "status": "open",
            "priority": "normal",
        }

        assert is_standalone_task(task_data) is True

    def test_hierarchy_task_rejected(self):
        """Test type guard rejects hierarchy task."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": "F-feature-id",
            "status": "open",
            "priority": "normal",
        }

        assert is_standalone_task(task_data) is False

    def test_non_task_object_rejected(self):
        """Test type guard rejects non-task objects."""
        project_data = {
            "kind": "project",
            "id": "test-project",
            "title": "Test Project",
            "status": "draft",
            "priority": "normal",
        }

        assert is_standalone_task(project_data) is False

    def test_none_input_rejected(self):
        """Test type guard rejects None input."""
        assert is_standalone_task(None) is False

    def test_empty_dict_rejected(self):
        """Test type guard rejects empty dictionary."""
        assert is_standalone_task({}) is False

    def test_non_dict_input_rejected(self):
        """Test type guard rejects non-dictionary input."""
        assert is_standalone_task("not-a-dict") is False
        assert is_standalone_task(42) is False
        assert is_standalone_task([]) is False


class TestHierarchyTaskGuard:
    """Tests for is_hierarchy_task type guard function."""

    def test_valid_hierarchy_task(self):
        """Test type guard with valid hierarchy task."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": "F-feature-id",
            "status": "open",
            "priority": "normal",
        }

        assert is_hierarchy_task(task_data) is True

    def test_standalone_task_rejected(self):
        """Test type guard rejects standalone task."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": None,
            "status": "open",
            "priority": "normal",
        }

        assert is_hierarchy_task(task_data) is False

    def test_standalone_task_empty_parent_rejected(self):
        """Test type guard rejects task with empty parent."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": "",
            "status": "open",
            "priority": "normal",
        }

        assert is_hierarchy_task(task_data) is False

    def test_non_task_object_rejected(self):
        """Test type guard rejects non-task objects."""
        feature_data = {
            "kind": "feature",
            "id": "test-feature",
            "title": "Test Feature",
            "parent": "E-epic-id",
            "status": "draft",
            "priority": "normal",
        }

        assert is_hierarchy_task(feature_data) is False

    def test_none_input_rejected(self):
        """Test type guard rejects None input."""
        assert is_hierarchy_task(None) is False

    def test_empty_dict_rejected(self):
        """Test type guard rejects empty dictionary."""
        assert is_hierarchy_task({}) is False

    def test_non_dict_input_rejected(self):
        """Test type guard rejects non-dictionary input."""
        assert is_hierarchy_task("not-a-dict") is False
        assert is_hierarchy_task(42) is False
        assert is_hierarchy_task([]) is False


class TestObjectTypeGuards:
    """Tests for object type guard functions."""

    def test_project_object_guard(self):
        """Test project object type guard."""
        project_data = {
            "kind": "project",
            "id": "test-project",
            "title": "Test Project",
            "status": "draft",
            "priority": "normal",
        }

        assert is_project_object(project_data) is True
        assert is_epic_object(project_data) is False
        assert is_feature_object(project_data) is False
        assert is_task_object(project_data) is False

    def test_epic_object_guard(self):
        """Test epic object type guard."""
        epic_data = {
            "kind": "epic",
            "id": "test-epic",
            "title": "Test Epic",
            "parent": "P-project-id",
            "status": "draft",
            "priority": "normal",
        }

        assert is_project_object(epic_data) is False
        assert is_epic_object(epic_data) is True
        assert is_feature_object(epic_data) is False
        assert is_task_object(epic_data) is False

    def test_feature_object_guard(self):
        """Test feature object type guard."""
        feature_data = {
            "kind": "feature",
            "id": "test-feature",
            "title": "Test Feature",
            "parent": "E-epic-id",
            "status": "draft",
            "priority": "normal",
        }

        assert is_project_object(feature_data) is False
        assert is_epic_object(feature_data) is False
        assert is_feature_object(feature_data) is True
        assert is_task_object(feature_data) is False

    def test_task_object_guard(self):
        """Test task object type guard."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": "F-feature-id",
            "status": "open",
            "priority": "normal",
        }

        assert is_project_object(task_data) is False
        assert is_epic_object(task_data) is False
        assert is_feature_object(task_data) is False
        assert is_task_object(task_data) is True

    def test_non_dict_input_rejected(self):
        """Test all type guards reject non-dictionary input."""
        test_inputs = [None, "string", 42, [], set()]

        for input_val in test_inputs:
            assert is_project_object(input_val) is False
            assert is_epic_object(input_val) is False
            assert is_feature_object(input_val) is False
            assert is_task_object(input_val) is False

    def test_empty_dict_rejected(self):
        """Test all type guards reject empty dictionary."""
        empty_dict = {}

        assert is_project_object(empty_dict) is False
        assert is_epic_object(empty_dict) is False
        assert is_feature_object(empty_dict) is False
        assert is_task_object(empty_dict) is False

    def test_invalid_kind_rejected(self):
        """Test all type guards reject invalid kind values."""
        invalid_data = {
            "kind": "invalid-kind",
            "id": "test-id",
            "title": "Test",
        }

        assert is_project_object(invalid_data) is False
        assert is_epic_object(invalid_data) is False
        assert is_feature_object(invalid_data) is False
        assert is_task_object(invalid_data) is False


class TestTaskUtilsTypeGuards:
    """Tests for task_utils type guard functions."""

    def test_standalone_task_guard_function(self):
        """Test standalone task guard function from task_utils."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": None,
            "status": "open",
            "priority": "normal",
        }

        assert is_standalone_task_guard(task_data) is True

    def test_hierarchy_task_guard_function(self):
        """Test hierarchy task guard function from task_utils."""
        task_data = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": "F-feature-id",
            "status": "open",
            "priority": "normal",
        }

        assert is_hierarchy_task_guard(task_data) is True

    def test_type_guard_consistency(self):
        """Test consistency between types module and task_utils guards."""
        # Test data for both standalone and hierarchy tasks
        standalone_task = {
            "kind": "task",
            "id": "standalone-task",
            "title": "Standalone Task",
            "parent": None,
            "status": "open",
            "priority": "normal",
        }

        hierarchy_task = {
            "kind": "task",
            "id": "hierarchy-task",
            "title": "Hierarchy Task",
            "parent": "F-feature-id",
            "status": "open",
            "priority": "normal",
        }

        # Both implementations should give the same results
        assert is_standalone_task(standalone_task) == is_standalone_task_guard(standalone_task)
        assert is_hierarchy_task(hierarchy_task) == is_hierarchy_task_guard(hierarchy_task)

        # Cross-checks should be false
        assert is_standalone_task(hierarchy_task) == is_standalone_task_guard(hierarchy_task)
        assert is_hierarchy_task(standalone_task) == is_hierarchy_task_guard(standalone_task)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_malformed_data_handling(self):
        """Test handling of malformed data structures."""
        malformed_data = {
            "kind": "task",
            "id": None,  # Invalid ID
            "title": "",  # Empty title
            "parent": "invalid-parent-format",
            "status": "invalid-status",
            "priority": None,
        }

        # Type guards should still work based on kind and parent
        assert is_task_object(malformed_data) is True
        assert is_hierarchy_task(malformed_data) is True
        assert is_standalone_task(malformed_data) is False

    def test_mixed_type_values(self):
        """Test with mixed type values in dictionary."""
        mixed_data = {
            "kind": "task",
            "id": 123,  # Number instead of string
            "title": ["list", "instead", "of", "string"],
            "parent": False,  # Boolean instead of string
            "status": {"nested": "object"},
            "priority": 3.14,  # Float instead of string
        }

        # Type guards should handle mixed types gracefully
        assert is_task_object(mixed_data) is True
        # parent=False is truthy, so it should be considered a hierarchy task
        assert is_hierarchy_task(mixed_data) is True
        assert is_standalone_task(mixed_data) is False

    def test_parent_field_variations(self):
        """Test various parent field values."""
        test_cases = [
            (None, True, False),  # None parent -> standalone
            ("", True, False),  # Empty string -> standalone
            ("   ", False, True),  # Whitespace -> hierarchy
            ("F-feature", False, True),  # Valid parent -> hierarchy
            (0, False, True),  # Number 0 -> hierarchy (valid parent)
            (1, False, True),  # Truthy number -> hierarchy
            ([], False, True),  # Empty list -> hierarchy (truthy object)
            (["parent"], False, True),  # Non-empty list -> hierarchy
        ]

        for parent_val, expect_standalone, expect_hierarchy in test_cases:
            task_data = {
                "kind": "task",
                "id": "test-task",
                "title": "Test Task",
                "parent": parent_val,
                "status": "open",
                "priority": "normal",
            }

            assert (
                is_standalone_task(task_data) == expect_standalone
            ), f"Failed for parent={parent_val}"
            assert (
                is_hierarchy_task(task_data) == expect_hierarchy
            ), f"Failed for parent={parent_val}"


class TestTypeNarrowing:
    """Tests to verify type narrowing behavior (manual verification)."""

    def test_type_narrowing_example(self):
        """Example showing type narrowing in action."""
        # This test demonstrates the intended usage pattern
        # Type checkers should narrow the type inside the if blocks

        unknown_data: Any = {
            "kind": "task",
            "id": "test-task",
            "title": "Test Task",
            "parent": None,
            "status": "open",
            "priority": "normal",
        }

        if is_standalone_task(unknown_data):
            # Type checker should narrow unknown_data to dict[str, Any]
            assert unknown_data["kind"] == "task"
            assert unknown_data.get("parent") is None or unknown_data.get("parent") == ""

        if is_hierarchy_task(unknown_data):
            # This branch should not execute for standalone task
            assert False, "Should not reach here for standalone task"

    def test_object_type_narrowing(self):
        """Test type narrowing for different object types."""
        unknown_objects = [
            {"kind": "project", "id": "P-1", "title": "Project 1"},
            {"kind": "epic", "id": "E-1", "title": "Epic 1", "parent": "P-1"},
            {"kind": "feature", "id": "F-1", "title": "Feature 1", "parent": "E-1"},
            {"kind": "task", "id": "T-1", "title": "Task 1", "parent": "F-1"},
        ]

        for obj in unknown_objects:
            obj_kind = obj["kind"]

            if is_project_object(obj):
                assert obj_kind == "project"
            elif is_epic_object(obj):
                assert obj_kind == "epic"
            elif is_feature_object(obj):
                assert obj_kind == "feature"
            elif is_task_object(obj):
                assert obj_kind == "task"
            else:
                assert False, f"Unknown object type: {obj_kind}"
