"""Integration tests for prerequisite validation in the full validation pipeline.

Tests that prerequisite existence validation is properly integrated with the
existing validation system and works with real filesystem structures.
"""

import tempfile
from pathlib import Path

import pytest

from trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from trellis_mcp.io_utils import write_markdown
from trellis_mcp.validation.enhanced_validation import (
    validate_object_data_enhanced,
    validate_object_data_with_collector,
)


class TestPrerequisiteValidationIntegration:
    """Integration tests for prerequisite validation in validation pipeline."""

    def setup_method(self):
        """Set up test environment with temporary project structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create basic project structure
        planning_dir = self.project_root / "planning"
        planning_dir.mkdir(parents=True)

        # Create projects directory
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir()

        # Create project
        project_dir = projects_dir / "P-test-project"
        project_dir.mkdir()

        # Create project file
        project_data = {
            "kind": "project",
            "id": "test-project",
            "title": "Test Project",
            "status": "draft",
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }
        write_markdown(project_dir / "project.md", project_data, "")

        # Create epic
        epics_dir = project_dir / "epics"
        epic_dir = epics_dir / "E-test-epic"
        epic_dir.mkdir(parents=True)

        epic_data = {
            "kind": "epic",
            "id": "test-epic",
            "parent": "test-project",
            "title": "Test Epic",
            "status": "draft",
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }
        write_markdown(epic_dir / "epic.md", epic_data, "")

        # Create feature
        features_dir = epic_dir / "features"
        feature_dir = features_dir / "F-test-feature"
        feature_dir.mkdir(parents=True)

        feature_data = {
            "kind": "feature",
            "id": "test-feature",
            "parent": "test-epic",
            "title": "Test Feature",
            "status": "draft",
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }
        write_markdown(feature_dir / "feature.md", feature_data, "")

        # Create hierarchical tasks
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_open_dir.mkdir()

        # Task 1 (no prerequisites)
        task1_data = {
            "kind": "task",
            "id": "hierarchy-task-1",
            "parent": "test-feature",
            "title": "Hierarchy Task 1",
            "status": "open",
            "prerequisites": [],
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }
        write_markdown(tasks_open_dir / "T-hierarchy-task-1.md", task1_data, "")

        # Task 2 (with valid prerequisite)
        task2_data = {
            "kind": "task",
            "id": "hierarchy-task-2",
            "parent": "test-feature",
            "title": "Hierarchy Task 2",
            "status": "open",
            "prerequisites": ["hierarchy-task-1"],
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }
        write_markdown(tasks_open_dir / "T-hierarchy-task-2.md", task2_data, "")

        # Create standalone tasks
        standalone_tasks_dir = planning_dir / "tasks-open"
        standalone_tasks_dir.mkdir()

        # Standalone task 1 (no prerequisites)
        standalone1_data = {
            "kind": "task",
            "id": "standalone-task-1",
            "title": "Standalone Task 1",
            "status": "open",
            "prerequisites": [],
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }
        write_markdown(standalone_tasks_dir / "T-standalone-task-1.md", standalone1_data, "")

        # Standalone task 2 (with cross-system prerequisite)
        standalone2_data = {
            "kind": "task",
            "id": "standalone-task-2",
            "title": "Standalone Task 2",
            "status": "open",
            "prerequisites": ["hierarchy-task-1", "standalone-task-1"],
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }
        write_markdown(standalone_tasks_dir / "T-standalone-task-2.md", standalone2_data, "")

    def teardown_method(self):
        """Clean up temporary test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_valid_prerequisites_pass_validation(self):
        """Test that objects with valid prerequisites pass validation."""
        # Test hierarchical task with valid prerequisite
        task_data = {
            "kind": "task",
            "id": "new-hierarchy-task",
            "parent": "test-feature",
            "title": "New Hierarchy Task",
            "status": "open",
            "prerequisites": ["hierarchy-task-1"],  # Exists
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise exception
        validate_object_data_enhanced(task_data, self.project_root / "planning")

    def test_cross_system_prerequisites_validation(self):
        """Test that cross-system prerequisites are properly validated."""
        # Standalone task referencing hierarchical task
        standalone_data = {
            "kind": "task",
            "id": "new-standalone-task",
            "title": "New Standalone Task",
            "status": "open",
            "prerequisites": ["hierarchy-task-1", "standalone-task-1"],  # Both exist
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise exception
        validate_object_data_enhanced(standalone_data, self.project_root / "planning")

    def test_nonexistent_prerequisite_fails_validation(self):
        """Test that nonexistent prerequisites cause validation failure."""
        task_data = {
            "kind": "task",
            "id": "failing-task",
            "parent": "test-feature",
            "title": "Failing Task",
            "status": "open",
            "prerequisites": ["nonexistent-task"],  # Does not exist
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_object_data_enhanced(task_data, self.project_root / "planning")

        error = exc_info.value
        assert any("nonexistent-task" in err for err in error.errors)
        assert any("does not exist" in err for err in error.errors)
        assert error.has_error_code(ValidationErrorCode.PARENT_NOT_EXIST)

    def test_multiple_invalid_prerequisites(self):
        """Test validation with multiple invalid prerequisites."""
        task_data = {
            "kind": "task",
            "id": "failing-task",
            "title": "Failing Task",
            "status": "open",
            "prerequisites": [
                "missing-1",
                "missing-2",
                "hierarchy-task-1",
            ],  # Two missing, one valid
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_object_data_enhanced(task_data, self.project_root / "planning")

        error = exc_info.value
        # Should have errors for both missing prerequisites
        missing_errors = [err for err in error.errors if "does not exist" in err]
        assert len(missing_errors) == 2
        assert any("missing-1" in err for err in missing_errors)
        assert any("missing-2" in err for err in missing_errors)

    def test_empty_prerequisite_list_passes(self):
        """Test that empty prerequisite list passes validation."""
        task_data = {
            "kind": "task",
            "id": "no-prereq-task",
            "parent": "test-feature",
            "title": "No Prerequisite Task",
            "status": "open",
            "prerequisites": [],  # Empty list
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise exception
        validate_object_data_enhanced(task_data, self.project_root / "planning")

    def test_missing_prerequisites_field_passes(self):
        """Test that missing prerequisites field passes validation."""
        task_data = {
            "kind": "task",
            "id": "no-prereq-field-task",
            "parent": "test-feature",
            "title": "No Prerequisite Field Task",
            "status": "open",
            # No prerequisites field at all
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise exception
        validate_object_data_enhanced(task_data, self.project_root / "planning")

    def test_prerequisite_id_prefixes_handled(self):
        """Test that prerequisite IDs with prefixes are properly handled."""
        task_data = {
            "kind": "task",
            "id": "prefix-test-task",
            "title": "Prefix Test Task",
            "status": "open",
            "prerequisites": ["T-hierarchy-task-1", "T-standalone-task-1"],  # With T- prefixes
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise exception - prefixes should be cleaned
        validate_object_data_enhanced(task_data, self.project_root / "planning")

    def test_malicious_prerequisite_ids_blocked(self):
        """Test that malicious prerequisite IDs are blocked by security validation."""
        task_data = {
            "kind": "task",
            "id": "malicious-test-task",
            "title": "Malicious Test Task",
            "status": "open",
            "prerequisites": ["../../../etc/passwd"],  # Path traversal attempt
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_object_data_enhanced(task_data, self.project_root / "planning")

        error = exc_info.value
        assert any("security validation failed" in err.lower() for err in error.errors)

    def test_collector_integration(self):
        """Test that prerequisite validation integrates properly with ValidationErrorCollector."""
        task_data = {
            "kind": "task",
            "id": "collector-test-task",
            "title": "Collector Test Task",
            "status": "open",
            "prerequisites": ["missing-1", "missing-2"],
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Use collector directly
        collector = validate_object_data_with_collector(task_data, self.project_root / "planning")

        assert collector.has_errors()
        assert collector.get_error_count() >= 2  # At least 2 prerequisite errors

        # Check error details
        errors = collector.get_prioritized_errors()
        prerequisite_errors = [
            (msg, code, ctx)
            for msg, code, ctx in errors
            if ctx.get("validation_type") == "prerequisite_existence"
        ]
        assert len(prerequisite_errors) == 2

        for msg, code, ctx in prerequisite_errors:
            assert code == ValidationErrorCode.PARENT_NOT_EXIST
            assert ctx["cross_system_check"] is True

    def test_non_task_objects_skip_prerequisite_validation(self):
        """Test that non-task objects don't trigger prerequisite validation."""
        # Feature with invalid prerequisites field (should be ignored)
        feature_data = {
            "kind": "feature",
            "id": "test-feature-2",
            "parent": "test-epic",
            "title": "Test Feature 2",
            "status": "draft",
            "prerequisites": ["nonexistent-prereq"],  # Invalid, but should be ignored for features
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        # Should not raise exception because prerequisite validation should only apply to tasks
        # or objects that actually support prerequisites in their schema
        try:
            validate_object_data_enhanced(feature_data, self.project_root / "planning")
        except ValidationError as e:
            # If it fails, it should not be due to prerequisite validation
            assert not any("prerequisite" in err.lower() for err in e.errors)

    def test_performance_with_real_filesystem(self):
        """Test that prerequisite validation meets performance requirements with real filesystem."""
        import time

        task_data = {
            "kind": "task",
            "id": "perf-test-task",
            "title": "Performance Test Task",
            "status": "open",
            "prerequisites": ["hierarchy-task-1", "standalone-task-1", "hierarchy-task-2"],
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "schema_version": "1.1",
        }

        start_time = time.perf_counter()
        validate_object_data_enhanced(task_data, self.project_root / "planning")
        end_time = time.perf_counter()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Should meet performance requirement even with filesystem I/O
        assert execution_time < 100, f"Validation took {execution_time:.2f}ms, should be <100ms"


if __name__ == "__main__":
    pytest.main([__file__])
