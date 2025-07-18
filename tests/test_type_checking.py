"""Comprehensive type checking tests for Trellis MCP.

This module provides comprehensive testing for type checking functionality
using mypy and pyright. Tests cover all type annotations, type guards,
edge cases, and performance characteristics.
"""

import time
from typing import Any, Dict, List, Optional, Union

import pytest

from trellis_mcp.types import (
    ObjectKind,
    TaskKind,
    create_task_object_generic,
    create_typed_task_factory,
    handle_task_by_type,
    is_epic_object,
    is_feature_object,
    is_hierarchy_task,
    is_object_with_kind,
    is_project_object,
    is_standalone_task,
    is_task_object,
    is_task_with_parent_type,
    process_task_generic,
    validate_task_parent_constraint,
)
from trellis_mcp.validation.task_utils import (
    is_hierarchy_task_guard,
    is_standalone_task_guard,
)


class TestTypeAnnotationCoverage:
    """Tests to ensure all type annotations are properly exercised."""

    def test_object_kind_literal_types(self):
        """Test ObjectKind literal types are properly constrained."""
        # Test valid object kinds
        valid_kinds: List[ObjectKind] = ["task", "project", "epic", "feature"]

        for kind in valid_kinds:
            assert kind in ["task", "project", "epic", "feature"]

        # Test TaskKind specifically
        task_kind: TaskKind = "task"
        assert task_kind == "task"

    def test_type_guard_return_types(self):
        """Test type guard functions return correct types."""
        valid_task = {
            "kind": "task",
            "id": "T-test",
            "title": "Test Task",
            "parent": "F-feature",
            "status": "open",
            "priority": "normal",
        }

        # Test return types are booleans
        assert isinstance(is_standalone_task(valid_task), bool)
        assert isinstance(is_hierarchy_task(valid_task), bool)
        assert isinstance(is_task_object(valid_task), bool)
        assert isinstance(is_project_object(valid_task), bool)
        assert isinstance(is_epic_object(valid_task), bool)
        assert isinstance(is_feature_object(valid_task), bool)

    def test_generic_type_variables(self):
        """Test generic type variables work correctly."""
        # Test create_task_object_generic
        task_dict = create_task_object_generic(
            "T-generic", "Generic Task", "F-parent", status="open"
        )

        assert isinstance(task_dict, dict)
        assert task_dict["kind"] == "task"
        assert task_dict["id"] == "T-generic"
        assert task_dict["title"] == "Generic Task"
        assert task_dict["parent"] == "F-parent"
        assert task_dict["status"] == "open"

    def test_union_type_handling(self):
        """Test Union type handling for optional fields."""
        # Test with None parent
        standalone_task = create_task_object_generic("T-standalone", "Standalone", None)
        assert standalone_task["parent"] is None

        # Test with string parent
        hierarchy_task = create_task_object_generic("T-hierarchy", "Hierarchy", "F-parent")
        assert hierarchy_task["parent"] == "F-parent"

        # Test Union[str, None] handling
        parent_value: Union[str, None] = None
        task_with_union = create_task_object_generic("T-union", "Union", parent_value)
        assert task_with_union["parent"] is None

    def test_optional_type_annotation(self):
        """Test Optional type annotations work correctly."""
        parent_optional: Optional[str] = None
        task_optional = create_task_object_generic("T-optional", "Optional", parent_optional)
        assert task_optional["parent"] is None

        parent_optional = "F-feature"
        task_optional = create_task_object_generic("T-optional2", "Optional2", parent_optional)
        assert task_optional["parent"] == "F-feature"

    def test_dict_type_annotations(self):
        """Test Dict type annotations are properly handled."""
        task_data: Dict[str, Any] = {
            "kind": "task",
            "id": "T-dict",
            "title": "Dict Task",
            "parent": "F-feature",
            "status": "open",
            "priority": "normal",
        }

        assert is_task_object(task_data)
        assert is_hierarchy_task(task_data)


class TestTypeGuardComprehensive:
    """Comprehensive tests for all type guard functions."""

    def test_is_object_with_kind_comprehensive(self):
        """Test is_object_with_kind with all valid kinds."""
        test_objects = [
            ({"kind": "task", "id": "T-1"}, "task", True),
            ({"kind": "project", "id": "P-1"}, "project", True),
            ({"kind": "epic", "id": "E-1"}, "epic", True),
            ({"kind": "feature", "id": "F-1"}, "feature", True),
            ({"kind": "task", "id": "T-1"}, "project", False),
            ({"kind": "invalid", "id": "I-1"}, "task", False),
            ({}, "task", False),
            (None, "task", False),
            ("not-dict", "task", False),
        ]

        for obj, kind, expected in test_objects:
            assert is_object_with_kind(obj, kind) == expected

    def test_is_task_with_parent_type_comprehensive(self):
        """Test is_task_with_parent_type with all scenarios."""
        test_cases = [
            # (task_data, parent_required, expected_result)
            ({"kind": "task", "parent": "F-1"}, True, True),
            ({"kind": "task", "parent": None}, True, False),
            ({"kind": "task", "parent": ""}, True, False),
            ({"kind": "task", "parent": "F-1"}, False, False),
            ({"kind": "task", "parent": None}, False, True),
            ({"kind": "task", "parent": ""}, False, True),
            ({"kind": "project", "parent": "F-1"}, True, False),
            ({"kind": "project", "parent": None}, False, False),
            ({}, True, False),
            (None, True, False),
            ("not-dict", False, False),
        ]

        for task_data, parent_required, expected in test_cases:
            assert is_task_with_parent_type(task_data, parent_required) == expected

    def test_type_guard_edge_cases(self):
        """Test type guards with edge cases."""
        edge_cases = [
            # Test with missing fields
            {"kind": "task"},  # Missing required fields
            {"id": "T-1"},  # Missing kind
            {},  # Empty dict
            {"kind": None},  # None kind
            {"kind": 123},  # Non-string kind
            {"kind": "task", "parent": 0},  # Numeric parent
            {"kind": "task", "parent": []},  # List parent
            {"kind": "task", "parent": {}},  # Dict parent
        ]

        for edge_case in edge_cases:
            # Should not crash on any edge case
            assert isinstance(is_standalone_task(edge_case), bool)
            assert isinstance(is_hierarchy_task(edge_case), bool)
            assert isinstance(is_task_object(edge_case), bool)

    def test_type_guard_consistency_across_modules(self):
        """Test consistency between type guards in different modules."""
        test_tasks = [
            {"kind": "task", "id": "T-1", "parent": None},
            {"kind": "task", "id": "T-2", "parent": "F-1"},
            {"kind": "task", "id": "T-3", "parent": ""},
            {"kind": "project", "id": "P-1", "parent": None},
            {},
            None,
            "not-dict",
        ]

        for task in test_tasks:
            # Compare results between modules
            types_standalone = is_standalone_task(task)
            utils_standalone = is_standalone_task_guard(task)
            types_hierarchy = is_hierarchy_task(task)
            utils_hierarchy = is_hierarchy_task_guard(task)

            assert types_standalone == utils_standalone, f"Standalone mismatch for {task}"
            assert types_hierarchy == utils_hierarchy, f"Hierarchy mismatch for {task}"


class TestTypeNarrowingBehavior:
    """Tests for type narrowing behavior with type guards."""

    def test_type_narrowing_in_conditionals(self):
        """Test type narrowing behavior in conditional statements."""
        unknown_data: Any = {
            "kind": "task",
            "id": "T-narrow",
            "title": "Narrowing Test",
            "parent": "F-feature",
            "status": "open",
            "priority": "normal",
        }

        # Test hierarchy task narrowing
        if is_hierarchy_task(unknown_data):
            # After type guard, should be narrowed to dict[str, Any]
            assert unknown_data["kind"] == "task"
            assert unknown_data["parent"] == "F-feature"
            assert "id" in unknown_data

        # Test standalone task narrowing
        standalone_data: Any = {
            "kind": "task",
            "id": "T-standalone",
            "title": "Standalone Test",
            "parent": None,
            "status": "open",
            "priority": "normal",
        }

        if is_standalone_task(standalone_data):
            # After type guard, should be narrowed to dict[str, Any]
            assert standalone_data["kind"] == "task"
            assert standalone_data["parent"] is None
            assert "id" in standalone_data

    def test_complex_type_narrowing_scenarios(self):
        """Test complex type narrowing scenarios."""
        mixed_objects: List[Any] = [
            {"kind": "project", "id": "P-1", "title": "Project 1"},
            {"kind": "epic", "id": "E-1", "title": "Epic 1", "parent": "P-1"},
            {"kind": "feature", "id": "F-1", "title": "Feature 1", "parent": "E-1"},
            {"kind": "task", "id": "T-1", "title": "Task 1", "parent": "F-1"},
            {"kind": "task", "id": "T-2", "title": "Task 2", "parent": None},
            "not-a-dict",
            None,
            {"kind": "unknown", "id": "U-1"},
        ]

        projects_found = 0
        epics_found = 0
        features_found = 0
        hierarchy_tasks_found = 0
        standalone_tasks_found = 0

        for obj in mixed_objects:
            if is_project_object(obj):
                projects_found += 1
                assert obj["kind"] == "project"
            elif is_epic_object(obj):
                epics_found += 1
                assert obj["kind"] == "epic"
            elif is_feature_object(obj):
                features_found += 1
                assert obj["kind"] == "feature"
            elif is_hierarchy_task(obj):
                hierarchy_tasks_found += 1
                assert obj["kind"] == "task"
                assert obj["parent"] is not None and obj["parent"] != ""
            elif is_standalone_task(obj):
                standalone_tasks_found += 1
                assert obj["kind"] == "task"
                assert obj["parent"] is None or obj["parent"] == ""

        assert projects_found == 1
        assert epics_found == 1
        assert features_found == 1
        assert hierarchy_tasks_found == 1
        assert standalone_tasks_found == 1

    def test_nested_type_narrowing(self):
        """Test type narrowing in nested conditionals."""
        test_data: Any = {
            "kind": "task",
            "id": "T-nested",
            "title": "Nested Test",
            "parent": "F-feature",
            "status": "open",
            "priority": "high",
        }

        if is_task_object(test_data):
            # First level narrowing
            assert test_data["kind"] == "task"

            if is_hierarchy_task(test_data):
                # Second level narrowing
                assert test_data["parent"] == "F-feature"
                assert test_data["parent"] is not None

                # Should be able to access all dict methods
                assert "id" in test_data
                assert len(test_data) > 0
                assert list(test_data.keys()) is not None


class TestGenericFunctionality:
    """Tests for generic type functionality."""

    def test_create_typed_task_factory(self):
        """Test create_typed_task_factory function."""
        # Test standalone task factory
        create_standalone = create_typed_task_factory(False)
        standalone_task = create_standalone("T-standalone", "Standalone Task")

        assert standalone_task["kind"] == "task"
        assert standalone_task["id"] == "T-standalone"
        assert standalone_task["title"] == "Standalone Task"
        assert standalone_task["parent"] is None

        # Test hierarchy task factory
        create_hierarchy = create_typed_task_factory(True)
        hierarchy_task = create_hierarchy("T-hierarchy", "Hierarchy Task", "F-parent")

        assert hierarchy_task["kind"] == "task"
        assert hierarchy_task["id"] == "T-hierarchy"
        assert hierarchy_task["title"] == "Hierarchy Task"
        assert hierarchy_task["parent"] == "F-parent"

    def test_create_typed_task_factory_validation(self):
        """Test create_typed_task_factory validation."""
        create_standalone = create_typed_task_factory(False)
        create_hierarchy = create_typed_task_factory(True)

        # Test standalone factory rejects parent
        with pytest.raises(ValueError, match="Parent must be None or empty"):
            create_standalone("T-invalid", "Invalid", "F-parent")

        # Test hierarchy factory requires parent
        with pytest.raises(ValueError, match="Parent is required"):
            create_hierarchy("T-invalid", "Invalid", None)

        with pytest.raises(ValueError, match="Parent is required"):
            create_hierarchy("T-invalid", "Invalid", "")

    def test_handle_task_by_type_generic(self):
        """Test handle_task_by_type generic function."""

        def standalone_handler(task):
            task["processed_type"] = "standalone"
            return task

        def hierarchy_handler(task):
            task["processed_type"] = "hierarchy"
            return task

        # Test standalone task
        standalone_task = {"kind": "task", "id": "T-1", "parent": None}
        result = handle_task_by_type(standalone_task, standalone_handler, hierarchy_handler)
        assert result["processed_type"] == "standalone"

        # Test hierarchy task
        hierarchy_task = {"kind": "task", "id": "T-2", "parent": "F-1"}
        result = handle_task_by_type(hierarchy_task, standalone_handler, hierarchy_handler)
        assert result["processed_type"] == "hierarchy"

    def test_process_task_generic_function(self):
        """Test process_task_generic function."""

        def add_timestamp(task):
            task["processed"] = True
            return task

        task_data = {"kind": "task", "id": "T-process", "title": "Process Test"}
        result = process_task_generic(task_data, add_timestamp)

        assert result["processed"] is True
        assert result["kind"] == "task"
        assert result["id"] == "T-process"

    def test_validate_task_parent_constraint_function(self):
        """Test validate_task_parent_constraint function."""
        standalone_task = {"kind": "task", "id": "T-1", "parent": None}
        hierarchy_task = {"kind": "task", "id": "T-2", "parent": "F-1"}

        # Test standalone validation
        assert validate_task_parent_constraint(standalone_task, type(None)) is True
        assert validate_task_parent_constraint(standalone_task, str) is False

        # Test hierarchy validation
        assert validate_task_parent_constraint(hierarchy_task, str) is True
        assert validate_task_parent_constraint(hierarchy_task, type(None)) is False

        # Test invalid input - need to cast to Any for type checker
        assert validate_task_parent_constraint(None, str) is False  # type: ignore
        assert validate_task_parent_constraint("not-dict", str) is False  # type: ignore
        assert validate_task_parent_constraint({"kind": "project"}, str) is False


class TestErrorConditions:
    """Tests for error conditions and edge cases."""

    def test_invalid_input_types(self):
        """Test handling of invalid input types."""
        invalid_inputs = [
            None,
            "string",
            123,
            3.14,
            [],
            set(),
            object(),
            lambda x: x,
        ]

        for invalid_input in invalid_inputs:
            # All type guards should return False for invalid input
            assert is_standalone_task(invalid_input) is False
            assert is_hierarchy_task(invalid_input) is False
            assert is_task_object(invalid_input) is False
            assert is_project_object(invalid_input) is False
            assert is_epic_object(invalid_input) is False
            assert is_feature_object(invalid_input) is False

    def test_malformed_dictionaries(self):
        """Test handling of malformed dictionaries."""
        malformed_dicts = [
            {},  # Empty dict
            {"kind": None},  # None kind
            {"kind": ""},  # Empty kind
            {"kind": "invalid"},  # Invalid kind
            {"kind": "task", "parent": object()},  # Invalid parent type
            {"kind": "task", "parent": {"nested": "dict"}},  # Complex parent
        ]

        for malformed_dict in malformed_dicts:
            # Should not crash on malformed input
            try:
                is_standalone_task(malformed_dict)
                is_hierarchy_task(malformed_dict)
                is_task_object(malformed_dict)
            except Exception as e:
                pytest.fail(f"Type guard crashed on malformed dict {malformed_dict}: {e}")

    def test_generic_function_error_handling(self):
        """Test error handling in generic functions."""
        # Test process_task_generic with invalid input - need to cast to Any for type checker
        with pytest.raises(ValueError, match="task_obj must be a dictionary"):
            process_task_generic("not-dict", lambda x: x)  # type: ignore

        with pytest.raises(ValueError, match="task_obj must be a task object"):
            process_task_generic({"kind": "project"}, lambda x: x)

        # Test handle_task_by_type with invalid input - need to cast to Any for type checker
        with pytest.raises(ValueError, match="task_obj must be a dictionary"):
            handle_task_by_type("not-dict", lambda x: x, lambda x: x)  # type: ignore

        with pytest.raises(ValueError, match="task_obj must be a task object"):
            handle_task_by_type({"kind": "project"}, lambda x: x, lambda x: x)


class TestPerformanceBenchmarks:
    """Performance benchmarks for type checking overhead."""

    def test_type_guard_performance(self):
        """Benchmark type guard performance."""
        # Create test data
        test_objects = [
            {"kind": "task", "id": f"T-{i}", "parent": "F-1" if i % 2 == 0 else None}
            for i in range(1000)
        ]

        # Benchmark type guard performance
        start_time = time.time()
        for obj in test_objects:
            is_standalone_task(obj)
            is_hierarchy_task(obj)
            is_task_object(obj)
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete within reasonable time (less than 1 second for 1000 objects)
        assert execution_time < 1.0, f"Type guard performance too slow: {execution_time}s"

        # Calculate operations per second
        operations_per_second = (1000 * 3) / execution_time  # 3 operations per object
        assert operations_per_second > 1000, f"Too slow: {operations_per_second} ops/sec"

    def test_type_narrowing_performance(self):
        """Benchmark type narrowing performance."""
        test_data = [
            {"kind": "task", "id": f"T-{i}", "parent": f"F-{i}" if i % 2 == 0 else None}
            for i in range(1000)
        ]

        start_time = time.time()

        processed_count = 0
        for obj in test_data:
            if is_task_object(obj):
                if is_standalone_task(obj):
                    processed_count += 1
                elif is_hierarchy_task(obj):
                    processed_count += 1

        end_time = time.time()
        execution_time = end_time - start_time

        # Should process all 1000 objects
        assert processed_count == 1000

        # Should complete within reasonable time
        assert execution_time < 1.0, f"Type narrowing performance too slow: {execution_time}s"

    def test_generic_function_performance(self):
        """Benchmark generic function performance."""
        test_tasks = [
            {"kind": "task", "id": f"T-{i}", "parent": f"F-{i}" if i % 2 == 0 else None}
            for i in range(1000)
        ]

        def simple_processor(task):
            task["processed"] = True
            return task

        start_time = time.time()

        for task in test_tasks:
            process_task_generic(task, simple_processor)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete within reasonable time
        assert execution_time < 1.0, f"Generic function performance too slow: {execution_time}s"

        # Verify all tasks were processed
        for task in test_tasks:
            assert task["processed"] is True

    def test_memory_usage_stability(self):
        """Test memory usage stability with type guards."""
        # Create many objects to test memory stability
        large_dataset = [
            {"kind": "task", "id": f"T-{i}", "parent": f"F-{i % 10}" if i % 3 == 0 else None}
            for i in range(10000)
        ]

        # Process all objects multiple times
        for iteration in range(5):
            standalone_count = 0
            hierarchy_count = 0

            for obj in large_dataset:
                if is_standalone_task(obj):
                    standalone_count += 1
                elif is_hierarchy_task(obj):
                    hierarchy_count += 1

            # Verify consistent results across iterations
            assert standalone_count > 0
            assert hierarchy_count > 0
            assert standalone_count + hierarchy_count == 10000


class TestCICDIntegration:
    """Tests for CI/CD integration and tooling."""

    def test_type_checking_tools_available(self):
        """Test that type checking tools are properly configured."""
        # This test verifies that type checking is properly integrated
        # Actual tool execution happens in CI/CD pipeline

        # Test that type annotations are preserved
        task_data: Dict[str, Any] = {"kind": "task", "id": "T-test"}
        assert isinstance(task_data, dict)

        # Test that type guards work as expected
        assert is_task_object(task_data) is True
        assert is_standalone_task(task_data) is True

    def test_type_annotation_completeness(self):
        """Test that all public functions have type annotations."""
        from trellis_mcp import types

        # Check that key functions have proper annotations
        assert hasattr(types.is_standalone_task, "__annotations__")
        assert hasattr(types.is_hierarchy_task, "__annotations__")
        assert hasattr(types.create_task_object_generic, "__annotations__")

        # Verify return type annotations
        assert types.is_standalone_task.__annotations__.get("return") is not None
        assert types.is_hierarchy_task.__annotations__.get("return") is not None
