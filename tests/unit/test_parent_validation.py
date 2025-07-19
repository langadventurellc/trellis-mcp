"""Tests for parent relationship validation utilities.

This module tests parent existence validation, relationship constraints,
and task type detection functions.
"""

import time
from pathlib import Path

import pytest

from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.validation import (
    is_hierarchy_task,
    is_standalone_task,
    validate_parent_exists,
    validate_parent_exists_for_object,
)


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

    def test_validate_parent_exists_for_object_task_standalone(self, tmp_path: Path):
        """Test that standalone tasks (parent=None) are valid."""
        # Valid case: task with no parent (standalone task)
        assert validate_parent_exists_for_object(None, KindEnum.TASK, tmp_path / "planning")

    def test_validate_parent_exists_for_object_task_with_empty_string_parent(self, tmp_path: Path):
        """Test that tasks with empty string parent are valid (converted to None)."""
        # Valid case: task with empty string parent (converted to None for standalone task)
        assert validate_parent_exists_for_object("", KindEnum.TASK, tmp_path / "planning")


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
        """Test task validation succeeds when parent is null (standalone task)."""
        # Standalone tasks (parent=None) should now be allowed
        result = validate_parent_exists_for_object(None, KindEnum.TASK, tmp_path)
        assert result is True

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


class TestTaskTypeDetection:
    """Test task type detection utility functions."""

    def test_is_standalone_task_valid_standalone(self):
        """Test is_standalone_task with valid standalone task data."""
        # Valid standalone task (parent=None)
        task_data = {
            "kind": "task",
            "id": "T-standalone",
            "parent": None,
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_standalone_task(task_data) is True

    def test_is_standalone_task_missing_parent(self):
        """Test is_standalone_task with missing parent field."""
        # Task without parent field (missing key)
        task_data = {
            "kind": "task",
            "id": "T-standalone",
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_standalone_task(task_data) is True

    def test_is_standalone_task_empty_parent(self):
        """Test is_standalone_task with empty string parent."""
        # Task with empty string parent
        task_data = {
            "kind": "task",
            "id": "T-standalone",
            "parent": "",
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_standalone_task(task_data) is True

    def test_is_standalone_task_hierarchy_task(self):
        """Test is_standalone_task with hierarchy task data."""
        # Hierarchy task (has parent)
        task_data = {
            "kind": "task",
            "id": "T-hierarchy",
            "parent": "F-feature",
            "status": "open",
            "title": "Hierarchy Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_standalone_task(task_data) is False

    def test_is_standalone_task_non_task_object(self):
        """Test is_standalone_task with non-task object."""
        # Non-task object (project)
        project_data = {
            "kind": "project",
            "id": "P-project",
            "parent": None,
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_standalone_task(project_data) is False

    def test_is_standalone_task_edge_cases(self):
        """Test is_standalone_task with edge cases."""
        # None data
        assert is_standalone_task(None) is False

        # Empty dict
        assert is_standalone_task({}) is False

        # Dict with only kind field
        assert is_standalone_task({"kind": "task"}) is True

        # Dict with kind but wrong type
        assert is_standalone_task({"kind": "feature"}) is False

    def test_is_hierarchy_task_valid_hierarchy(self):
        """Test is_hierarchy_task with valid hierarchy task data."""
        # Valid hierarchy task (has parent)
        task_data = {
            "kind": "task",
            "id": "T-hierarchy",
            "parent": "F-feature",
            "status": "open",
            "title": "Hierarchy Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_hierarchy_task(task_data) is True

    def test_is_hierarchy_task_standalone_task(self):
        """Test is_hierarchy_task with standalone task data."""
        # Standalone task (parent=None)
        task_data = {
            "kind": "task",
            "id": "T-standalone",
            "parent": None,
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_hierarchy_task(task_data) is False

    def test_is_hierarchy_task_missing_parent(self):
        """Test is_hierarchy_task with missing parent field."""
        # Task without parent field (missing key)
        task_data = {
            "kind": "task",
            "id": "T-standalone",
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_hierarchy_task(task_data) is False

    def test_is_hierarchy_task_empty_parent(self):
        """Test is_hierarchy_task with empty string parent."""
        # Task with empty string parent
        task_data = {
            "kind": "task",
            "id": "T-standalone",
            "parent": "",
            "status": "open",
            "title": "Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_hierarchy_task(task_data) is False

    def test_is_hierarchy_task_non_task_object(self):
        """Test is_hierarchy_task with non-task object."""
        # Non-task object (epic with parent)
        epic_data = {
            "kind": "epic",
            "id": "E-epic",
            "parent": "P-project",
            "status": "draft",
            "title": "Test Epic",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        assert is_hierarchy_task(epic_data) is False

    def test_is_hierarchy_task_edge_cases(self):
        """Test is_hierarchy_task with edge cases."""
        # None data
        assert is_hierarchy_task(None) is False

        # Empty dict
        assert is_hierarchy_task({}) is False

        # Dict with only kind field
        assert is_hierarchy_task({"kind": "task"}) is False

        # Dict with kind but wrong type
        assert is_hierarchy_task({"kind": "feature", "parent": "P-project"}) is False

    def test_is_standalone_task_original_signature(self):
        """Test is_standalone_task with original signature for backward compatibility."""
        # Test original signature: is_standalone_task(object_kind, parent_id)
        assert is_standalone_task(KindEnum.TASK, None) is True
        assert is_standalone_task(KindEnum.TASK, "F-feature") is False
        assert is_standalone_task(KindEnum.PROJECT, None) is False
        assert is_standalone_task(KindEnum.EPIC, None) is False
        assert is_standalone_task(KindEnum.FEATURE, None) is False

    def test_function_type_detection_complementary(self):
        """Test that is_standalone_task and is_hierarchy_task are complementary for valid tasks."""
        # Standalone task
        standalone_task = {
            "kind": "task",
            "id": "T-standalone",
            "parent": None,
            "status": "open",
            "title": "Standalone Task",
        }

        # Hierarchy task
        hierarchy_task = {
            "kind": "task",
            "id": "T-hierarchy",
            "parent": "F-feature",
            "status": "open",
            "title": "Hierarchy Task",
        }

        # For standalone tasks: is_standalone_task=True, is_hierarchy_task=False
        assert is_standalone_task(standalone_task) is True
        assert is_hierarchy_task(standalone_task) is False

        # For hierarchy tasks: is_standalone_task=False, is_hierarchy_task=True
        assert is_standalone_task(hierarchy_task) is False
        assert is_hierarchy_task(hierarchy_task) is True

        # For non-task objects: both should return False
        non_task = {"kind": "project", "parent": None}
        assert is_standalone_task(non_task) is False
        assert is_hierarchy_task(non_task) is False

    def test_is_standalone_task_comprehensive_edge_cases(self):
        """Test is_standalone_task with comprehensive edge cases."""
        # Test with None input
        assert is_standalone_task(None) is False

        # Test with empty dictionary
        assert is_standalone_task({}) is False

        # Test with dictionary containing only kind field
        assert is_standalone_task({"kind": "task"}) is True

        # Test with dictionary containing kind and other fields but no parent
        minimal_task = {"kind": "task", "id": "T-minimal"}
        assert is_standalone_task(minimal_task) is True

        # Test with non-string kind field
        assert is_standalone_task({"kind": 123}) is False
        assert is_standalone_task({"kind": None}) is False
        assert is_standalone_task({"kind": []}) is False
        assert is_standalone_task({"kind": {}}) is False

        # Test with malformed data - missing kind field
        assert is_standalone_task({"id": "T-test", "parent": None}) is False

        # Test with whitespace-only parent (non-empty string so it's not standalone)
        assert is_standalone_task({"kind": "task", "parent": "   "}) is False

        # Test with numeric parent (edge case)
        assert is_standalone_task({"kind": "task", "parent": 0}) is False
        assert is_standalone_task({"kind": "task", "parent": 1}) is False

        # Test with boolean parent
        assert is_standalone_task({"kind": "task", "parent": False}) is False
        assert is_standalone_task({"kind": "task", "parent": True}) is False

        # Test with list/dict parent
        assert is_standalone_task({"kind": "task", "parent": []}) is False
        assert is_standalone_task({"kind": "task", "parent": {}}) is False

    def test_is_hierarchy_task_comprehensive_edge_cases(self):
        """Test is_hierarchy_task with comprehensive edge cases."""
        # Test with None input
        assert is_hierarchy_task(None) is False

        # Test with empty dictionary
        assert is_hierarchy_task({}) is False

        # Test with dictionary containing only kind field
        assert is_hierarchy_task({"kind": "task"}) is False

        # Test with dictionary containing kind and other fields but no parent
        minimal_task = {"kind": "task", "id": "T-minimal"}
        assert is_hierarchy_task(minimal_task) is False

        # Test with non-string kind field
        assert is_hierarchy_task({"kind": 123, "parent": "F-feature"}) is False
        assert is_hierarchy_task({"kind": None, "parent": "F-feature"}) is False
        assert is_hierarchy_task({"kind": [], "parent": "F-feature"}) is False
        assert is_hierarchy_task({"kind": {}, "parent": "F-feature"}) is False

        # Test with malformed data - missing kind field
        assert is_hierarchy_task({"id": "T-test", "parent": "F-feature"}) is False

        # Test with whitespace-only parent (non-empty string so it's a hierarchy task)
        assert is_hierarchy_task({"kind": "task", "parent": "   "}) is True

        # Test with numeric parent (edge case) - numeric values are truthy and not empty string
        assert is_hierarchy_task({"kind": "task", "parent": 0}) is True  # 0 is not None and not ""
        assert is_hierarchy_task({"kind": "task", "parent": 1}) is True

        # Test with boolean parent (not None and not empty string)
        assert is_hierarchy_task({"kind": "task", "parent": False}) is True
        assert is_hierarchy_task({"kind": "task", "parent": True}) is True

        # Test with list/dict parent (not None and not empty string)
        assert is_hierarchy_task({"kind": "task", "parent": []}) is True
        assert is_hierarchy_task({"kind": "task", "parent": {}}) is True

    def test_is_standalone_task_boundary_conditions(self):
        """Test is_standalone_task with boundary conditions."""
        # Test with very long parent string (should be hierarchy task)
        long_parent = "F-" + "x" * 1000
        assert is_standalone_task({"kind": "task", "parent": long_parent}) is False

        # Test with empty string parent (should be standalone)
        assert is_standalone_task({"kind": "task", "parent": ""}) is True

        # Test with string "null" as parent (should be hierarchy task)
        assert is_standalone_task({"kind": "task", "parent": "null"}) is False

        # Test with string "none" as parent (should be hierarchy task)
        assert is_standalone_task({"kind": "task", "parent": "none"}) is False

        # Test with string "None" as parent (should be hierarchy task)
        assert is_standalone_task({"kind": "task", "parent": "None"}) is False

        # Test with special characters in parent
        assert is_standalone_task({"kind": "task", "parent": "F-test@#$%"}) is False

        # Test with unicode characters in parent
        assert is_standalone_task({"kind": "task", "parent": "F-tëst"}) is False

        # Test with newlines/tabs in parent
        assert is_standalone_task({"kind": "task", "parent": "F-test\n"}) is False
        assert is_standalone_task({"kind": "task", "parent": "F-test\t"}) is False

    def test_is_hierarchy_task_boundary_conditions(self):
        """Test is_hierarchy_task with boundary conditions."""
        # Test with very long parent string (should be hierarchy task)
        long_parent = "F-" + "x" * 1000
        assert is_hierarchy_task({"kind": "task", "parent": long_parent}) is True

        # Test with empty string parent (should be standalone)
        assert is_hierarchy_task({"kind": "task", "parent": ""}) is False

        # Test with string "null" as parent (should be hierarchy task)
        assert is_hierarchy_task({"kind": "task", "parent": "null"}) is True

        # Test with string "none" as parent (should be hierarchy task)
        assert is_hierarchy_task({"kind": "task", "parent": "none"}) is True

        # Test with string "None" as parent (should be hierarchy task)
        assert is_hierarchy_task({"kind": "task", "parent": "None"}) is True

        # Test with special characters in parent
        assert is_hierarchy_task({"kind": "task", "parent": "F-test@#$%"}) is True

        # Test with unicode characters in parent
        assert is_hierarchy_task({"kind": "task", "parent": "F-tëst"}) is True

        # Test with newlines/tabs in parent
        assert is_hierarchy_task({"kind": "task", "parent": "F-test\n"}) is True
        assert is_hierarchy_task({"kind": "task", "parent": "F-test\t"}) is True

        # Test with minimum valid parent (single character)
        assert is_hierarchy_task({"kind": "task", "parent": "F"}) is True

    def test_is_standalone_task_malformed_data(self):
        """Test is_standalone_task with malformed data."""
        # Test with circular reference (dict containing itself)
        circular_dict = {"kind": "task"}
        circular_dict["parent"] = circular_dict  # type: ignore
        # This should not crash and should return False
        assert is_standalone_task(circular_dict) is False

        # Test with deeply nested structure
        nested_data = {"kind": "task", "parent": {"nested": {"deeply": {"parent": "F-feature"}}}}
        assert is_standalone_task(nested_data) is False

        # Test with list containing parent data
        list_parent = ["F-feature"]
        assert is_standalone_task({"kind": "task", "parent": list_parent}) is False

        # Test with function as parent (should not occur in practice)
        def func_parent(x):
            return x

        assert is_standalone_task({"kind": "task", "parent": func_parent}) is False

        # Test with very large dictionary
        large_dict = {"kind": "task", "parent": None}
        for i in range(1000):
            large_dict[f"field_{i}"] = f"value_{i}"
        assert is_standalone_task(large_dict) is True

    def test_is_hierarchy_task_malformed_data(self):
        """Test is_hierarchy_task with malformed data."""
        # Test with circular reference (dict containing itself)
        circular_dict = {"kind": "task"}
        circular_dict["parent"] = circular_dict  # type: ignore
        # This should not crash and should return True (parent is not None and not empty string)
        assert is_hierarchy_task(circular_dict) is True

        # Test with deeply nested structure
        nested_data = {"kind": "task", "parent": {"nested": {"deeply": {"parent": "F-feature"}}}}
        assert is_hierarchy_task(nested_data) is True  # parent is not None and not empty string

        # Test with list containing parent data
        list_parent = ["F-feature"]
        assert is_hierarchy_task({"kind": "task", "parent": list_parent}) is True

        # Test with function as parent (should not occur in practice)
        def func_parent(x):
            return x

        assert is_hierarchy_task({"kind": "task", "parent": func_parent}) is True

        # Test with very large dictionary
        large_dict = {"kind": "task", "parent": "F-feature"}
        for i in range(1000):
            large_dict[f"field_{i}"] = f"value_{i}"
        assert is_hierarchy_task(large_dict) is True

    def test_task_type_detection_performance(self):
        """Test performance of task type detection functions."""
        # Test with large number of tasks
        standalone_tasks = []
        hierarchy_tasks = []

        for i in range(1000):
            standalone_tasks.append(
                {
                    "kind": "task",
                    "id": f"T-standalone-{i}",
                    "parent": None,
                    "status": "open",
                    "title": f"Standalone Task {i}",
                }
            )
            hierarchy_tasks.append(
                {
                    "kind": "task",
                    "id": f"T-hierarchy-{i}",
                    "parent": f"F-feature-{i}",
                    "status": "open",
                    "title": f"Hierarchy Task {i}",
                }
            )

        # Test is_standalone_task performance
        start_time = time.time()
        for task in standalone_tasks:
            assert is_standalone_task(task) is True
        for task in hierarchy_tasks:
            assert is_standalone_task(task) is False
        standalone_time = time.time() - start_time

        # Test is_hierarchy_task performance
        start_time = time.time()
        for task in standalone_tasks:
            assert is_hierarchy_task(task) is False
        for task in hierarchy_tasks:
            assert is_hierarchy_task(task) is True
        hierarchy_time = time.time() - start_time

        # Performance should be reasonable (less than 1 second for 2000 calls)
        assert (
            standalone_time < 1.0
        ), f"is_standalone_task took {standalone_time:.3f}s for 2000 calls"
        assert hierarchy_time < 1.0, f"is_hierarchy_task took {hierarchy_time:.3f}s for 2000 calls"

    def test_task_type_detection_with_original_signature(self):
        """Test is_standalone_task with original signature comprehensively."""
        # Test all combinations of KindEnum and parent_id
        for kind in KindEnum:
            if kind == KindEnum.TASK:
                # Tasks can be standalone
                assert is_standalone_task(kind, None) is True
                assert is_standalone_task(kind, "") is False  # Empty string parent is not None
                assert is_standalone_task(kind, "F-feature") is False
            else:
                # Non-tasks are never standalone
                assert is_standalone_task(kind, None) is False
                assert is_standalone_task(kind, "") is False
                assert is_standalone_task(kind, "P-project") is False

        # Test with None kind
        assert is_standalone_task(None, None) is False
        assert is_standalone_task(None, "F-feature") is False

    def test_task_type_detection_comprehensive_scenarios(self):
        """Test comprehensive scenarios for both functions."""
        # Test various task configurations
        test_cases = [
            # (task_data, expected_standalone, expected_hierarchy, description)
            ({"kind": "task", "parent": None}, True, False, "explicit None parent"),
            ({"kind": "task"}, True, False, "missing parent field"),
            ({"kind": "task", "parent": ""}, True, False, "empty string parent"),
            ({"kind": "task", "parent": "F-feature"}, False, True, "valid parent"),
            ({"kind": "task", "parent": "E-epic"}, False, True, "parent is epic"),
            ({"kind": "task", "parent": "P-project"}, False, True, "parent is project"),
            ({"kind": "task", "parent": "T-other-task"}, False, True, "parent is another task"),
            ({"kind": "project", "parent": None}, False, False, "project with no parent"),
            ({"kind": "epic", "parent": "P-project"}, False, False, "epic with parent"),
            ({"kind": "feature", "parent": "E-epic"}, False, False, "feature with parent"),
            ({"kind": "other", "parent": None}, False, False, "unknown kind"),
            ({}, False, False, "empty dict"),
            (None, False, False, "None input"),
        ]

        for task_data, expected_standalone, expected_hierarchy, description in test_cases:
            standalone_result = is_standalone_task(task_data)
            hierarchy_result = is_hierarchy_task(task_data)

            assert standalone_result == expected_standalone, (
                f"is_standalone_task failed for {description}: "
                f"expected {expected_standalone}, got {standalone_result}"
            )
            assert hierarchy_result == expected_hierarchy, (
                f"is_hierarchy_task failed for {description}: "
                f"expected {expected_hierarchy}, got {hierarchy_result}"
            )

    def test_task_type_detection_error_handling(self):
        """Test error handling in task type detection functions."""

        # Test with unusual but valid Python objects
        class CustomObject:
            def __init__(self):
                self.kind = "task"
                self.parent = "F-feature"

        custom_obj = CustomObject()

        # Functions should handle non-dict inputs gracefully
        assert is_standalone_task(custom_obj) is False  # type: ignore
        # is_hierarchy_task will fail on non-dict inputs that don't have .get() method
        # This is expected behavior since the function expects a dict
        try:
            is_hierarchy_task(custom_obj)  # type: ignore
            assert False, "Should have raised AttributeError"
        except AttributeError:
            pass  # Expected behavior

        # Test with string input - is_standalone_task handles non-dict inputs differently
        assert (
            is_standalone_task("task") is True  # type: ignore
        )  # Non-dict inputs are handled by the original signature
        try:
            is_hierarchy_task("task")  # type: ignore
            assert False, "Should have raised AttributeError"
        except AttributeError:
            pass  # Expected behavior

        # Test with numeric input
        assert is_standalone_task(123) is False  # type: ignore
        try:
            is_hierarchy_task(123)  # type: ignore
            assert False, "Should have raised AttributeError"
        except AttributeError:
            pass  # Expected behavior

        # Test with list input
        assert is_standalone_task([]) is False  # type: ignore
        # Empty list is falsy, so is_hierarchy_task returns False immediately
        assert is_hierarchy_task([]) is False  # type: ignore

        # Test with tuple input
        assert is_standalone_task(()) is False  # type: ignore
        # Empty tuple is falsy, so is_hierarchy_task returns False immediately
        assert is_hierarchy_task(()) is False  # type: ignore

    def test_task_type_detection_integration(self):
        """Test integration scenarios with both functions."""
        # Test that exactly one function returns True for valid task objects
        valid_task_cases = [
            {"kind": "task", "parent": None},
            {"kind": "task"},
            {"kind": "task", "parent": ""},
            {"kind": "task", "parent": "F-feature"},
            {"kind": "task", "parent": "E-epic"},
        ]

        for task_data in valid_task_cases:
            standalone = is_standalone_task(task_data)
            hierarchy = is_hierarchy_task(task_data)

            # For valid tasks, exactly one should be True
            assert (
                standalone != hierarchy
            ), f"For task {task_data}, both functions returned {standalone}"

        # Test that both functions return False for invalid objects
        invalid_cases = [
            {"kind": "project", "parent": None},
            {"kind": "epic", "parent": "P-project"},
            {"kind": "feature", "parent": "E-epic"},
            {"kind": "invalid", "parent": "F-feature"},
            {},
            None,
        ]

        for invalid_data in invalid_cases:
            standalone = is_standalone_task(invalid_data)
            hierarchy = is_hierarchy_task(invalid_data)

            # For invalid objects, both should be False
            assert standalone is False and hierarchy is False, (
                f"For invalid object {invalid_data}, "
                f"got standalone={standalone}, hierarchy={hierarchy}"
            )
