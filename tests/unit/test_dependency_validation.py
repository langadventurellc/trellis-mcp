"""Tests for dependency and prerequisite validation utilities.

This module tests prerequisite graph building, circular dependency detection,
and acyclic validation functions.
"""

from pathlib import Path

import pytest

from trellis_mcp.validation import (
    CircularDependencyError,
    build_prerequisites_graph,
    check_prereq_cycles,
    detect_cycle_dfs,
    validate_acyclic_prerequisites,
)


class TestBuildPrerequisitesGraph:
    """Test the build_prerequisites_graph function."""

    def test_build_prerequisites_graph_empty(self):
        """Test building graph with no objects."""
        objects = {}
        graph = build_prerequisites_graph(objects)
        assert graph == {}

    def test_build_prerequisites_graph_no_prerequisites(self):
        """Test building graph with objects but no prerequisites."""
        objects = {
            "task1": {"id": "task1", "prerequisites": []},
            "task2": {"id": "task2", "prerequisites": []},
        }
        graph = build_prerequisites_graph(objects)

        assert graph == {
            "task1": [],
            "task2": [],
        }

    def test_build_prerequisites_graph_with_prerequisites(self):
        """Test building graph with prerequisites."""
        objects = {
            "task1": {"id": "task1", "prerequisites": ["task2"]},
            "task2": {"id": "task2", "prerequisites": ["task3"]},
            "task3": {"id": "task3", "prerequisites": []},
        }
        graph = build_prerequisites_graph(objects)

        assert graph == {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": [],
        }

    def test_build_prerequisites_graph_with_prefixes(self):
        """Test building graph with prefixed IDs."""
        objects = {
            "T-task1": {"id": "T-task1", "prerequisites": ["T-task2"]},
            "T-task2": {"id": "T-task2", "prerequisites": ["T-task3"]},
            "T-task3": {"id": "T-task3", "prerequisites": []},
        }
        graph = build_prerequisites_graph(objects)

        assert graph == {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": [],
        }


class TestDetectCycleDFS:
    """Test the detect_cycle_dfs function."""

    def test_detect_cycle_dfs_no_cycle(self):
        """Test cycle detection with no cycles."""
        graph = {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": [],
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is None

    def test_detect_cycle_dfs_simple_cycle(self):
        """Test cycle detection with simple cycle."""
        graph = {
            "task1": ["task2"],
            "task2": ["task1"],
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert len(cycle) == 3  # A -> B -> A has 3 elements
        assert cycle[0] == cycle[-1]  # Cycle should end with the same node it starts

    def test_detect_cycle_dfs_self_cycle(self):
        """Test cycle detection with self-referencing cycle."""
        graph = {
            "task1": ["task1"],
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert cycle == ["task1", "task1"]

    def test_detect_cycle_dfs_complex_cycle(self):
        """Test cycle detection with complex cycle."""
        graph = {
            "task1": ["task2"],
            "task2": ["task3"],
            "task3": ["task4"],
            "task4": ["task2"],  # Cycle: task2 -> task3 -> task4 -> task2
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert len(cycle) >= 3  # At least 3 nodes in cycle
        assert cycle[0] == cycle[-1]  # Cycle should end with the same node it starts

    def test_detect_cycle_dfs_multiple_components(self):
        """Test cycle detection with multiple disconnected components."""
        graph = {
            "task1": ["task2"],
            "task2": [],
            "task3": ["task4"],
            "task4": ["task3"],  # Cycle in second component
        }

        cycle = detect_cycle_dfs(graph)
        assert cycle is not None
        assert len(cycle) == 3  # A -> B -> A has 3 elements
        assert cycle[0] == cycle[-1]  # Cycle should end with the same node it starts


class TestValidateAcyclicPrerequisites:
    """Test the validate_acyclic_prerequisites function."""

    def test_validate_acyclic_prerequisites_empty_project(self, tmp_path: Path):
        """Test validation with empty project."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        errors = validate_acyclic_prerequisites(planning_dir)
        assert errors == []

    def test_validate_acyclic_prerequisites_no_cycles(self, tmp_path: Path):
        """Test validation with no cycles."""
        # Create project structure with no cycles
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature
        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)

        # Create tasks with linear dependencies
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)

        # Task 1 (no prerequisites)
        task1_file = task_dir / "T-task1.md"
        task1_file.write_text(
            """---
kind: task
id: task1
parent: test-feature
status: open
title: Task 1
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.1"
---
Task 1 description
"""
        )

        # Task 2 (depends on task1)
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
schema_version: "1.1"
---
Task 2 description
"""
        )

        errors = validate_acyclic_prerequisites(tmp_path / "planning")
        assert errors == []

    def test_validate_acyclic_prerequisites_with_cycle(self, tmp_path: Path):
        """Test validation with cycle detection."""
        # Create project structure with cycle
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

        # Task 1 (depends on task2)
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
schema_version: "1.1"
---
Task 1 description
"""
        )

        # Task 2 (depends on task1 - creates cycle)
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
schema_version: "1.1"
---
Task 2 description
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert len(error.cycle_path) >= 2
        assert "Circular dependency detected" in str(error)

    def test_validate_acyclic_prerequisites_self_reference(self, tmp_path: Path):
        """Test validation with self-referencing cycle."""
        # Create project structure with self-referencing task
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
title: Task 1
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.1"
---
Task 1 description
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert error.cycle_path == ["task1", "task1"]
        # Enhanced error message should show task type (hierarchical since it has a parent)
        assert "Circular dependency detected: task1 (hierarchical) → task1 (hierarchical)" in str(
            error
        )

    def test_validate_acyclic_prerequisites_nonexistent_directory(self, tmp_path: Path):
        """Test validation with non-existent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        errors = validate_acyclic_prerequisites(nonexistent_dir)
        assert len(errors) == 1
        assert "Error validating prerequisites" in errors[0]


class TestCheckPrereqCycles:
    """Test the check_prereq_cycles function."""

    def test_check_prereq_cycles_empty_project(self, tmp_path: Path):
        """Test cycle check with empty project."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        result = check_prereq_cycles(planning_dir)
        assert result is True

    def test_check_prereq_cycles_no_cycles(self, tmp_path: Path):
        """Test cycle check with no cycles."""
        # Create project structure with no cycles
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature
        feature_dir = epic_dir / "features" / "F-test-feature"
        feature_dir.mkdir(parents=True)

        # Create tasks with linear dependencies
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)

        # Task 1 (no prerequisites)
        task1_file = task_dir / "T-task1.md"
        task1_file.write_text(
            """---
kind: task
id: task1
parent: test-feature
status: open
title: Task 1
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.1"
---
Task 1 description
"""
        )

        # Task 2 (depends on task1)
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
schema_version: "1.1"
---
Task 2 description
"""
        )

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is True

    def test_check_prereq_cycles_with_cycle(self, tmp_path: Path):
        """Test cycle check with cycle detection."""
        # Create project structure with cycle
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

        # Task 1 (depends on task2)
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
schema_version: "1.1"
---
Task 1 description
"""
        )

        # Task 2 (depends on task1 - creates cycle)
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
schema_version: "1.1"
---
Task 2 description
"""
        )

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is False

    def test_check_prereq_cycles_self_reference(self, tmp_path: Path):
        """Test cycle check with self-referencing cycle."""
        # Create project structure with self-referencing task
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
title: Task 1
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.1"
---
Task 1 description
"""
        )

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is False

    def test_check_prereq_cycles_nonexistent_directory(self, tmp_path: Path):
        """Test cycle check with non-existent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        result = check_prereq_cycles(nonexistent_dir)
        assert result is False

    def test_check_prereq_cycles_complex_valid_structure(self, tmp_path: Path):
        """Test cycle check with complex valid structure."""
        # Create project structure with multiple features and tasks
        project_dir = tmp_path / "planning" / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)

        # Create epic
        epic_dir = project_dir / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)

        # Create feature 1
        feature1_dir = epic_dir / "features" / "F-feature1"
        feature1_dir.mkdir(parents=True)
        task1_dir = feature1_dir / "tasks-open"
        task1_dir.mkdir(parents=True)

        # Create feature 2
        feature2_dir = epic_dir / "features" / "F-feature2"
        feature2_dir.mkdir(parents=True)
        task2_dir = feature2_dir / "tasks-open"
        task2_dir.mkdir(parents=True)

        # Task in feature 1
        task1_file = task1_dir / "T-task1.md"
        task1_file.write_text(
            """---
kind: task
id: task1
parent: feature1
status: open
title: Task 1
priority: normal
prerequisites: []
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.1"
---
Task 1 description
"""
        )

        # Task in feature 2 that depends on task1
        task2_file = task2_dir / "T-task2.md"
        task2_file.write_text(
            """---
kind: task
id: task2
parent: feature2
status: open
title: Task 2
priority: normal
prerequisites: ["task1"]
created: 2023-01-01T00:00:00Z
updated: 2023-01-01T00:00:00Z
schema_version: "1.1"
---
Task 2 description
"""
        )

        result = check_prereq_cycles(tmp_path / "planning")
        assert result is True

    def test_check_prereq_cycles_with_string_path(self, tmp_path: Path):
        """Test cycle check with string path parameter."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        # Test with string path
        result = check_prereq_cycles(str(planning_dir))
        assert result is True

    def test_check_prereq_cycles_with_path_object(self, tmp_path: Path):
        """Test cycle check with Path object parameter."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()

        # Test with Path object
        result = check_prereq_cycles(planning_dir)
        assert result is True


class TestCircularDependencyError:
    """Test the CircularDependencyError exception class."""

    def test_circular_dependency_error_creation(self):
        """Test creating a CircularDependencyError with cycle path."""
        cycle_path = ["task1", "task2", "task3", "task1"]
        error = CircularDependencyError(cycle_path)

        assert error.cycle_path == cycle_path
        assert "Circular dependency detected: task1 -> task2 -> task3 -> task1" in str(error)

    def test_circular_dependency_error_short_cycle(self):
        """Test creating a CircularDependencyError with short cycle."""
        cycle_path = ["task1", "task1"]
        error = CircularDependencyError(cycle_path)

        assert error.cycle_path == cycle_path
        assert "Circular dependency detected: task1 -> task1" in str(error)

    def test_circular_dependency_error_with_standalone_tasks(self):
        """Test CircularDependencyError with standalone task context."""
        cycle_path = ["auth-setup", "user-validation", "auth-setup"]
        objects_data = {
            "auth-setup": {
                "kind": "task",
                "id": "auth-setup",
                "parent": None,  # Standalone task
            },
            "user-validation": {
                "kind": "task",
                "id": "user-validation",
                "parent": "",  # Standalone task (empty string)
            },
        }

        error = CircularDependencyError(cycle_path, objects_data)

        assert error.cycle_path == cycle_path
        assert error.objects_data == objects_data
        error_str = str(error)
        assert "auth-setup (standalone)" in error_str
        assert "user-validation (standalone)" in error_str
        assert " → " in error_str  # Enhanced arrow format

    def test_circular_dependency_error_with_hierarchical_tasks(self):
        """Test CircularDependencyError with hierarchical task context."""
        cycle_path = ["task-a", "task-b", "task-a"]
        objects_data = {
            "task-a": {
                "kind": "task",
                "id": "task-a",
                "parent": "feature-auth",  # Hierarchical task
            },
            "task-b": {
                "kind": "task",
                "id": "task-b",
                "parent": "feature-user",  # Hierarchical task
            },
        }

        error = CircularDependencyError(cycle_path, objects_data)

        error_str = str(error)
        assert "task-a (hierarchical)" in error_str
        assert "task-b (hierarchical)" in error_str
        assert " → " in error_str

    def test_circular_dependency_error_with_mixed_task_types(self):
        """Test CircularDependencyError with mixed standalone and hierarchical tasks."""
        cycle_path = ["standalone-task", "hierarchical-task", "standalone-task"]
        objects_data = {
            "standalone-task": {
                "kind": "task",
                "id": "standalone-task",
                "parent": None,  # Standalone
            },
            "hierarchical-task": {
                "kind": "task",
                "id": "hierarchical-task",
                "parent": "feature-x",  # Hierarchical
            },
        }

        error = CircularDependencyError(cycle_path, objects_data)

        error_str = str(error)
        assert "standalone-task (standalone)" in error_str
        assert "hierarchical-task (hierarchical)" in error_str

    def test_circular_dependency_error_with_mixed_object_types(self):
        """Test CircularDependencyError with mixed object types (task, feature, etc.)."""
        cycle_path = ["task-1", "feature-auth", "task-2", "task-1"]
        objects_data = {
            "task-1": {
                "kind": "task",
                "id": "task-1",
                "parent": "feature-user",  # Hierarchical task
            },
            "feature-auth": {
                "kind": "feature",
                "id": "feature-auth",
                "parent": "epic-user-mgmt",
            },
            "task-2": {
                "kind": "task",
                "id": "task-2",
                "parent": None,  # Standalone task
            },
        }

        error = CircularDependencyError(cycle_path, objects_data)

        error_str = str(error)
        assert "task-1 (hierarchical)" in error_str
        assert "feature-auth (feature)" in error_str
        assert "task-2 (standalone)" in error_str

    def test_circular_dependency_error_missing_object_data(self):
        """Test CircularDependencyError when object data is missing for some objects."""
        cycle_path = ["task-1", "missing-task", "task-1"]
        objects_data = {
            "task-1": {
                "kind": "task",
                "id": "task-1",
                "parent": None,
            },
            # "missing-task" is not in objects_data
        }

        error = CircularDependencyError(cycle_path, objects_data)

        error_str = str(error)
        assert "task-1 (standalone)" in error_str
        assert "missing-task (unknown)" in error_str

    def test_circular_dependency_error_backward_compatibility(self):
        """Test that CircularDependencyError maintains backward compatibility."""
        cycle_path = ["task1", "task2", "task1"]

        # Test without objects_data (old behavior)
        error = CircularDependencyError(cycle_path)

        assert error.cycle_path == cycle_path
        assert error.objects_data is None
        error_str = str(error)
        # Should use old format with simple arrows
        assert "task1 -> task2 -> task1" in error_str
        assert " → " not in error_str  # Should not use enhanced arrows

    def test_circular_dependency_error_empty_objects_data(self):
        """Test CircularDependencyError with empty objects_data."""
        cycle_path = ["task1", "task2"]
        objects_data = {}

        error = CircularDependencyError(cycle_path, objects_data)

        error_str = str(error)
        assert "task1 (unknown)" in error_str
        assert "task2 (unknown)" in error_str


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
schema_version: "1.1"
---

Task that depends on itself
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert error.cycle_path == ["task1", "task1"]
        # Enhanced error message should show task type (hierarchical since it has a parent)
        assert "Circular dependency detected: task1 (hierarchical) → task1 (hierarchical)" in str(
            error
        )

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
schema_version: "1.1"
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
schema_version: "1.1"
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
schema_version: "1.1"
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
schema_version: "1.1"
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
schema_version: "1.1"
---

Task 3 depends on task 1
"""
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            validate_acyclic_prerequisites(tmp_path / "planning")

        error = exc_info.value
        assert len(error.cycle_path) >= 3
        assert "Circular dependency detected" in str(error)
