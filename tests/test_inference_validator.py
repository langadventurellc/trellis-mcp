"""Tests for FileSystemValidator in the Kind Inference Engine.

This module provides comprehensive tests for file system validation that verifies
inferred object types match actual objects on disk, including YAML metadata
consistency checking and cross-system validation support.
"""

import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationErrorCode
from src.trellis_mcp.inference.path_builder import PathBuilder
from src.trellis_mcp.inference.validator import FileSystemValidator, ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_success_result_creation(self):
        """Test creation of successful validation result."""
        result = ValidationResult.success()

        assert result.is_valid is True
        assert result.object_exists is True
        assert result.type_matches is True
        assert result.metadata_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_failure_result_creation(self):
        """Test creation of failed validation result."""
        errors = ["File not found", "Type mismatch"]
        warnings = ["Performance warning"]

        result = ValidationResult.failure(
            object_exists=False,
            type_matches=False,
            metadata_valid=True,
            errors=errors,
            warnings=warnings,
        )

        assert result.is_valid is False
        assert result.object_exists is False
        assert result.type_matches is False
        assert result.metadata_valid is True
        assert result.errors == errors
        assert result.warnings == warnings

    def test_failure_result_default_values(self):
        """Test failure result with default values."""
        result = ValidationResult.failure()

        assert result.is_valid is False
        assert result.object_exists is False
        assert result.type_matches is False
        assert result.metadata_valid is False
        assert result.errors == []
        assert result.warnings == []


class TestFileSystemValidatorInit:
    """Test FileSystemValidator initialization."""

    def test_init_with_valid_path_builder(self):
        """Test successful initialization with valid PathBuilder."""
        with TemporaryDirectory() as tmp_dir:
            path_builder = PathBuilder(tmp_dir)
            validator = FileSystemValidator(path_builder)

            assert validator.path_builder is path_builder

    def test_init_with_none_path_builder(self):
        """Test initialization fails with None PathBuilder."""
        with pytest.raises(ValueError, match="PathBuilder cannot be None"):
            FileSystemValidator(None)  # type: ignore


class TestValidateObjectExists:
    """Test validate_object_exists method."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        # Create minimal project structure FIRST
        self.planning_dir = self.tmp_path / "planning"
        self.planning_dir.mkdir(exist_ok=True)

        # Create PathBuilder AFTER planning directory exists
        self.path_builder = PathBuilder(self.tmp_path)
        self.validator = FileSystemValidator(self.path_builder)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.tmp_dir.cleanup()

    def test_object_exists_true(self):
        """Test object exists validation when file is present."""
        # Create a task file
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_file.write_text("# Test Task\n---\nkind: task\nid: T-test-task\n---\nTest content")

        # Set status to 'open' for standalone task path building
        result = self.validator.validate_object_exists("task", "T-test-task")
        assert result is True

    def test_object_exists_false_missing_file(self):
        """Test object exists validation when file is missing."""
        result = self.validator.validate_object_exists("task", "T-nonexistent-task")
        assert result is False

    def test_object_exists_false_invalid_kind(self):
        """Test object exists validation with invalid kind."""
        result = self.validator.validate_object_exists("invalid-kind", "T-test-task")
        assert result is False

    def test_object_exists_false_empty_object_id(self):
        """Test object exists validation with empty object ID."""
        result = self.validator.validate_object_exists("task", "")
        assert result is False

    def test_object_exists_directory_not_file(self):
        """Test object exists validation when path is directory."""
        # Create directory at expected file path
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        fake_file_dir = task_dir / "T-test-task.md"
        fake_file_dir.mkdir()

        result = self.validator.validate_object_exists("task", "T-test-task")
        assert result is False


class TestValidateTypeConsistency:
    """Test validate_type_consistency method."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        # Create minimal project structure FIRST
        self.planning_dir = self.tmp_path / "planning"
        self.planning_dir.mkdir(exist_ok=True)

        # Create PathBuilder AFTER planning directory exists
        self.path_builder = PathBuilder(self.tmp_path)
        self.validator = FileSystemValidator(self.path_builder)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.tmp_dir.cleanup()

    def test_type_consistency_true(self):
        """Test type consistency when inferred and actual types match."""
        # Create task file with correct kind
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_content = """---
kind: task
id: T-test-task
title: Test Task
status: open
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Test Task
Test content"""
        task_file.write_text(task_content)

        result = self.validator.validate_type_consistency("task", "T-test-task")
        assert result is True

    def test_type_consistency_false_mismatch(self):
        """Test type consistency when types don't match."""
        # Create task file with wrong kind
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_content = """---
kind: project
id: T-test-task
title: Test Task
status: open
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Test Task
Test content"""
        task_file.write_text(task_content)

        result = self.validator.validate_type_consistency("task", "T-test-task")
        assert result is False

    def test_type_consistency_false_object_not_exists(self):
        """Test type consistency when object doesn't exist."""
        result = self.validator.validate_type_consistency("task", "T-nonexistent")
        assert result is False

    def test_type_consistency_false_parse_error(self):
        """Test type consistency when object parsing fails."""
        # Create file with invalid YAML
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_file.write_text("Invalid YAML content without front-matter")

        result = self.validator.validate_type_consistency("task", "T-test-task")
        assert result is False


class TestValidateObjectStructure:
    """Test validate_object_structure method."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        # Create minimal project structure FIRST
        self.planning_dir = self.tmp_path / "planning"
        self.planning_dir.mkdir(exist_ok=True)

        # Create PathBuilder AFTER planning directory exists
        self.path_builder = PathBuilder(self.tmp_path)
        self.validator = FileSystemValidator(self.path_builder)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.tmp_dir.cleanup()

    def test_validate_object_structure_success(self):
        """Test complete successful validation."""
        # Create valid task file
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_content = """---
kind: task
id: T-test-task
title: Test Task
status: open
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Test Task
Test content"""
        task_file.write_text(task_content)

        result = self.validator.validate_object_structure("task", "T-test-task", "open")

        assert result.is_valid is True
        assert result.object_exists is True
        assert result.type_matches is True
        assert result.metadata_valid is True
        assert len(result.errors) == 0

    def test_validate_object_structure_file_not_found(self):
        """Test validation when object file doesn't exist."""
        result = self.validator.validate_object_structure("task", "T-nonexistent", "open")

        assert result.is_valid is False
        assert result.object_exists is False
        assert len(result.errors) > 0
        assert "Object file not found" in result.errors[0]

    def test_validate_object_structure_parse_error(self):
        """Test validation when object parsing fails."""
        # Create file with invalid YAML
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_file.write_text("Invalid content without proper YAML front-matter")

        result = self.validator.validate_object_structure("task", "T-test-task", "open")

        assert result.is_valid is False
        assert result.object_exists is True
        assert result.metadata_valid is False
        assert len(result.errors) > 0
        assert "Failed to parse object metadata" in result.errors[0]

    def test_validate_object_structure_type_mismatch(self):
        """Test validation when inferred and actual types don't match."""
        # Create task file with wrong kind
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_content = """---
kind: project
id: T-test-task
title: Test Task
status: in-progress
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Test Task
Test content"""
        task_file.write_text(task_content)

        result = self.validator.validate_object_structure("task", "T-test-task", "open")

        assert result.is_valid is False
        assert result.object_exists is True
        assert result.metadata_valid is True
        assert result.type_matches is False
        assert len(result.errors) > 0
        assert "Type mismatch" in result.errors[0]

    @patch("src.trellis_mcp.validation.enhanced_validation.validate_object_data_with_collector")
    def test_validate_object_structure_schema_validation_error(self, mock_validate):
        """Test validation when schema validation fails."""
        # Setup mock to return validation errors
        mock_collector = Mock()
        mock_collector.has_errors.return_value = True
        mock_collector.get_prioritized_errors.return_value = [
            ("Missing required field", ValidationErrorCode.MISSING_REQUIRED_FIELD, {})
        ]
        mock_validate.return_value = mock_collector

        # Create task file
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-test-task.md"
        task_content = """---
kind: task
id: T-test-task
title: Test Task
status: open
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Test Task
Test content"""
        task_file.write_text(task_content)

        result = self.validator.validate_object_structure("task", "T-test-task", "open")

        assert result.is_valid is False
        assert result.object_exists is True
        assert result.metadata_valid is True
        assert result.type_matches is True
        assert len(result.errors) > 0
        assert "Schema validation failed" in result.errors[0]

    def test_validate_object_structure_unexpected_error(self):
        """Test validation handles unexpected errors gracefully."""
        # Mock path_builder to raise an exception
        self.validator.path_builder = Mock()
        self.validator.path_builder.for_object.side_effect = Exception("Unexpected error")

        result = self.validator.validate_object_structure("task", "T-test-task", "open")

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "Unexpected validation error" in result.errors[0]


class TestCrossSystemValidation:
    """Test cross-system validation support."""

    def setup_method(self):
        """Set up test environment with both hierarchical and standalone structures."""
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        # Create minimal project structure FIRST
        self.planning_dir = self.tmp_path / "planning"
        self.planning_dir.mkdir(exist_ok=True)

        # Create PathBuilder AFTER planning directory exists
        self.path_builder = PathBuilder(self.tmp_path)
        self.validator = FileSystemValidator(self.path_builder)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.tmp_dir.cleanup()

    def test_standalone_task_validation(self):
        """Test validation of standalone tasks."""
        # Create standalone task
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-standalone-task.md"
        task_content = """---
kind: task
id: T-standalone-task
title: Standalone Task
status: open
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Standalone Task
Test content"""
        task_file.write_text(task_content)

        result = self.validator.validate_object_structure("task", "T-standalone-task", "open")
        assert result.is_valid is True

    def test_hierarchical_task_validation(self):
        """Test validation shows proper error for tasks in hierarchical locations."""
        # Create full project structure
        project_dir = self.planning_dir / "projects" / "P-test-project"
        epic_dir = project_dir / "epics" / "E-test-epic"
        feature_dir = epic_dir / "features" / "F-test-feature"
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create hierarchical task
        task_file = task_dir / "T-hierarchical-task.md"
        task_content = """---
kind: task
id: T-hierarchical-task
parent: F-test-feature
title: Hierarchical Task
status: open
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Hierarchical Task
Test content"""
        task_file.write_text(task_content)

        # The validator by default looks for standalone tasks
        # A hierarchical task stored in hierarchical location won't be found
        # This demonstrates the need for kind inference to detect task type
        result = self.validator.validate_object_structure("task", "T-hierarchical-task", "open")
        assert result.is_valid is False
        assert result.object_exists is False
        assert "Object file not found" in result.errors[0]


class TestValidationPerformance:
    """Test validation performance requirements."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        # Create minimal project structure FIRST
        self.planning_dir = self.tmp_path / "planning"
        self.planning_dir.mkdir(exist_ok=True)

        # Create PathBuilder AFTER planning directory exists
        self.path_builder = PathBuilder(self.tmp_path)
        self.validator = FileSystemValidator(self.path_builder)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.tmp_dir.cleanup()

    def test_validation_performance_under_20ms(self):
        """Test that validation completes in < 20ms."""
        # Create valid task file
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-perf-test.md"
        task_content = """---
kind: task
id: T-perf-test
title: Performance Test Task
status: open
priority: normal
created: "2025-07-19T14:00:00.000000"
updated: "2025-07-19T14:00:00.000000"
schema_version: "1.1"
---

# Performance Test
Test content"""
        task_file.write_text(task_content)

        # Measure validation time
        start_time = time.perf_counter()
        result = self.validator.validate_object_structure("task", "T-perf-test", "open")
        end_time = time.perf_counter()

        validation_time_ms = (end_time - start_time) * 1000

        assert result.is_valid is True
        assert (
            validation_time_ms < 20.0
        ), f"Validation took {validation_time_ms:.2f}ms, expected < 20ms"

    def test_object_exists_performance(self):
        """Test that object existence check is fast."""
        # Create valid task file
        task_dir = self.planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-exists-perf.md"
        task_file.write_text("# Test")

        # Measure multiple existence checks
        start_time = time.perf_counter()
        for _ in range(100):
            result = self.validator.validate_object_exists("task", "T-exists-perf")
            assert result is True
        end_time = time.perf_counter()

        avg_time_ms = ((end_time - start_time) / 100) * 1000
        assert avg_time_ms < 1.0, f"Average existence check took {avg_time_ms:.2f}ms"


class TestSecurityValidation:
    """Test security aspects of file system validation."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.path_builder = PathBuilder(self.tmp_path)
        self.validator = FileSystemValidator(self.path_builder)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.tmp_dir.cleanup()

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        # Attempt path traversal
        result = self.validator.validate_object_exists("task", "../../../etc/passwd")
        assert result is False

    def test_invalid_characters_handling(self):
        """Test handling of invalid characters in object IDs."""
        result = self.validator.validate_object_exists("task", "T-task\x00with\x00nulls")
        assert result is False

    def test_security_error_handling(self):
        """Test that security errors are handled gracefully."""
        # Test with various potentially problematic IDs
        problematic_ids = [
            "T-../../../sensitive",
            "T-task\x00null",
            "T-task\n\r\twhitespace",
            "T-task|pipe",
            "T-task;semicolon",
        ]

        for object_id in problematic_ids:
            result = self.validator.validate_object_exists("task", object_id)
            # Should either return False or handle gracefully without crashing
            assert isinstance(result, bool)


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.tmp_dir = TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.path_builder = PathBuilder(self.tmp_path)
        self.validator = FileSystemValidator(self.path_builder)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.tmp_dir.cleanup()

    def test_file_permission_errors(self):
        """Test handling of file permission errors."""
        # Create file and remove read permissions
        planning_dir = self.tmp_path / "planning"
        planning_dir.mkdir(exist_ok=True)
        task_dir = planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "T-no-perm.md"
        task_file.write_text("# Test")

        # Remove read permissions (Unix-like systems)
        if hasattr(os, "chmod"):
            try:
                task_file.chmod(0o000)
                result = self.validator.validate_type_consistency("task", "T-no-perm")
                assert result is False
            finally:
                # Restore permissions for cleanup
                task_file.chmod(0o644)

    def test_corrupted_file_handling(self):
        """Test handling of corrupted or malformed files."""
        planning_dir = self.tmp_path / "planning"
        planning_dir.mkdir(exist_ok=True)
        task_dir = planning_dir / "tasks-open"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create file with various corruption types
        corrupted_files = [
            ("T-binary.md", b"\x89PNG\r\n\x1a\n"),  # Binary content
            ("T-invalid-yaml.md", "---\ninvalid: [yaml: structure\n---\n"),  # Invalid YAML
            ("T-no-frontmatter.md", "Just plain text without frontmatter"),  # No frontmatter
        ]

        for filename, content in corrupted_files:
            task_file = task_dir / filename
            if isinstance(content, bytes):
                task_file.write_bytes(content)
            else:
                task_file.write_text(content)

            # Should handle gracefully without crashing
            object_id = filename.replace(".md", "")
            result = self.validator.validate_type_consistency("task", object_id)
            assert result is False
