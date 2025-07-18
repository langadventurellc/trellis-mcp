"""Tests for security validation of standalone tasks.

This module tests the security validation functions to ensure standalone tasks
don't introduce privilege escalation opportunities or allow validation bypass
through parent field manipulation.
"""

from pathlib import Path

import pytest

from trellis_mcp.validation import (
    TrellisValidationError,
    validate_object_data,
    validate_standalone_task_security,
)


class TestValidateStandaloneTaskSecurity:
    """Test security validation for standalone tasks."""

    def test_validate_standalone_task_security_valid_standalone(self):
        """Test security validation passes for valid standalone task."""
        data = {
            "kind": "task",
            "id": "T-valid-standalone",
            "parent": None,
            "status": "open",
            "title": "Valid Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        errors = validate_standalone_task_security(data)
        assert errors == []

    def test_validate_standalone_task_security_valid_standalone_empty_parent(self):
        """Test security validation passes for standalone task with empty parent."""
        data = {
            "kind": "task",
            "id": "T-valid-standalone",
            "parent": "",
            "status": "open",
            "title": "Valid Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        errors = validate_standalone_task_security(data)
        assert errors == []

    def test_validate_standalone_task_security_valid_hierarchy_task(self):
        """Test security validation passes for valid hierarchy task."""
        data = {
            "kind": "task",
            "id": "T-valid-hierarchy",
            "parent": "F-valid-feature",
            "status": "open",
            "title": "Valid Hierarchy Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        errors = validate_standalone_task_security(data)
        assert errors == []

    def test_validate_standalone_task_security_non_task_object(self):
        """Test security validation skips non-task objects."""
        data = {
            "kind": "project",
            "id": "P-test-project",
            "parent": None,
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        errors = validate_standalone_task_security(data)
        assert errors == []

    def test_validate_standalone_task_security_path_traversal_attack(self):
        """Test security validation detects path traversal attacks."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "../../../etc/passwd",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern '..'" in errors[0]
        )

    def test_validate_standalone_task_security_absolute_path_attack(self):
        """Test security validation detects absolute path attacks."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "/etc/passwd",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern '/'" in errors[0]
        )

    def test_validate_standalone_task_security_windows_path_attack(self):
        """Test security validation detects Windows path attacks."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "C:\\Windows\\System32",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern '\\'" in errors[0]
        )

    def test_validate_standalone_task_security_null_bypass_attempt(self):
        """Test security validation detects null bypass attempts."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "null",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern 'null'"
            in errors[0]
        )

    def test_validate_standalone_task_security_none_bypass_attempt(self):
        """Test security validation detects none bypass attempts."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "none",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern 'none'"
            in errors[0]
        )

    def test_validate_standalone_task_security_undefined_bypass_attempt(self):
        """Test security validation detects undefined bypass attempts."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "undefined",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern 'undefined'"
            in errors[0]
        )

    def test_validate_standalone_task_security_object_notation_bypass(self):
        """Test security validation detects object notation bypass attempts."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "{}",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern '{}'" in errors[0]
        )

    def test_validate_standalone_task_security_array_notation_bypass(self):
        """Test security validation detects array notation bypass attempts."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "[]",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern '[]'" in errors[0]
        )

    def test_validate_standalone_task_security_boolean_bypass_attempts(self):
        """Test security validation detects boolean bypass attempts."""
        # Test "false" string
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "false",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern 'false'"
            in errors[0]
        )

        # Test "true" string
        data["parent"] = "true"
        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern 'true'"
            in errors[0]
        )

    def test_validate_standalone_task_security_numeric_bypass_attempts(self):
        """Test security validation detects numeric bypass attempts."""
        # Test "0" string
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "0",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern '0'" in errors[0]
        )

        # Test "1" string
        data["parent"] = "1"
        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern '1'" in errors[0]
        )

    def test_validate_standalone_task_security_whitespace_bypass_attempts(self):
        """Test security validation detects whitespace bypass attempts."""
        # Test space character
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": " ",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern" in errors[0]
            or "Security validation failed: parent field contains only whitespace" in errors[0]
        )

        # Test tab character
        data["parent"] = "\t"
        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert "Security validation failed: parent field contains suspicious pattern" in errors[0]

        # Test newline character
        data["parent"] = "\n"
        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert "Security validation failed: parent field contains suspicious pattern" in errors[0]

        # Test whitespace-only string
        data["parent"] = "   "
        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert "Security validation failed: parent field contains only whitespace" in errors[0]

    def test_validate_standalone_task_security_case_insensitive_detection(self):
        """Test security validation is case insensitive."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "NULL",
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field contains suspicious pattern 'null'"
            in errors[0]
        )

    def test_validate_standalone_task_security_excessive_length_attack(self):
        """Test security validation detects excessively long parent values."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "A" * 256,  # 256 characters, exceeds 255 limit
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert (
            "Security validation failed: parent field exceeds maximum length (255 characters)"
            in errors[0]
        )

    def test_validate_standalone_task_security_control_character_injection(self):
        """Test security validation detects control character injection attempts."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "valid-parent\x00",  # null byte injection
            "status": "open",
            "title": "Malicious Task",
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 1
        assert "Security validation failed: parent field contains control characters" in errors[0]

    def test_validate_standalone_task_security_privileged_fields_detection(self):
        """Test security validation detects privileged fields."""
        privileged_fields = [
            "system_admin",
            "root_access",
            "privileged",
            "admin",
            "superuser",
            "elevated",
            "bypass_validation",
            "skip_checks",
            "ignore_constraints",
        ]

        for field in privileged_fields:
            data = {
                "kind": "task",
                "id": "T-malicious",
                "parent": "F-valid-feature",
                "status": "open",
                "title": "Malicious Task",
                field: True,  # Add privileged field
            }

            errors = validate_standalone_task_security(data)
            assert len(errors) == 1
            assert (
                f"Security validation failed: privileged field '{field}' is not allowed"
                in errors[0]
            )

    def test_validate_standalone_task_security_multiple_violations(self):
        """Test security validation detects multiple security violations."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "../../../etc/passwd",
            "status": "open",
            "title": "Malicious Task",
            "admin": True,
            "bypass_validation": True,
        }

        errors = validate_standalone_task_security(data)
        assert len(errors) == 3
        assert any("suspicious pattern" in error for error in errors)
        assert any("privileged field 'admin'" in error for error in errors)
        assert any("privileged field 'bypass_validation'" in error for error in errors)

    def test_validate_standalone_task_security_valid_parent_edge_cases(self):
        """Test security validation allows valid parent values with edge cases."""
        valid_parents = [
            "F-valid-feature",
            "F-feature-123",
            "F-my-feature-name",
            "F-test_feature",
            "F-feature-with-dashes",
            "F-feature.with.dots",
            "feature-without-prefix",
            "abc-numeric-feature",
        ]

        for parent in valid_parents:
            data = {
                "kind": "task",
                "id": "T-valid",
                "parent": parent,
                "status": "open",
                "title": "Valid Task",
            }

            errors = validate_standalone_task_security(data)
            assert errors == [], f"Valid parent '{parent}' should not trigger security errors"

    def test_validate_standalone_task_security_numeric_only_parent_detection(self):
        """Test security validation detects numeric-only parent values."""
        # Test standalone numeric values that might indicate bypass attempts
        for numeric_parent in ["0", "1", " 0 ", " 1 "]:
            data = {
                "kind": "task",
                "id": "T-malicious",
                "parent": numeric_parent,
                "status": "open",
                "title": "Malicious Task",
            }

            errors = validate_standalone_task_security(data)
            assert len(errors) == 1
            assert (
                "Security validation failed: parent field contains suspicious pattern" in errors[0]
            )

        # Test that numeric components within valid parent IDs are allowed
        valid_numeric_parents = [
            "F-feature-123",
            "F-123-feature",
            "feature-10-test",
            "F-test-1-feature",
        ]

        for parent in valid_numeric_parents:
            data = {
                "kind": "task",
                "id": "T-valid",
                "parent": parent,
                "status": "open",
                "title": "Valid Task",
            }

            errors = validate_standalone_task_security(data)
            assert errors == [], f"Valid parent '{parent}' should not trigger security errors"

    def test_validate_standalone_task_security_performance_with_large_data(self):
        """Test security validation performs well with large data structures."""
        # Create a task with many fields (but no privileged ones)
        data = {
            "kind": "task",
            "id": "T-large-task",
            "parent": "F-valid-feature",
            "status": "open",
            "title": "Large Task",
            "priority": "normal",
            "prerequisites": [f"T-prereq-{i}" for i in range(100)],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        # Add many non-privileged fields
        for i in range(100):
            data[f"custom_field_{i}"] = f"value_{i}"

        errors = validate_standalone_task_security(data)
        assert errors == []


class TestValidateObjectDataSecurityIntegration:
    """Test security validation integration with validate_object_data."""

    def test_validate_object_data_security_integration_valid_standalone(self, tmp_path: Path):
        """Test that validate_object_data includes security validation for standalone tasks."""
        data = {
            "kind": "task",
            "id": "T-valid-standalone",
            "parent": None,
            "status": "open",
            "title": "Valid Standalone Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        planning_root = tmp_path / "planning"
        planning_root.mkdir()

        # Should not raise any exception
        validate_object_data(data, planning_root)

    def test_validate_object_data_security_integration_malicious_task(self, tmp_path: Path):
        """Test that validate_object_data catches security violations in tasks."""
        data = {
            "kind": "task",
            "id": "T-malicious",
            "parent": "../../../etc/passwd",
            "status": "open",
            "title": "Malicious Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
            "admin": True,
        }

        planning_root = tmp_path / "planning"
        planning_root.mkdir()

        with pytest.raises(TrellisValidationError) as exc_info:
            validate_object_data(data, planning_root)

        error = exc_info.value
        # Should have 3 errors: security pattern, privileged field, and parent doesn't exist
        assert len(error.errors) == 3
        assert any("suspicious pattern" in err for err in error.errors)
        assert any("privileged field 'admin'" in err for err in error.errors)
        assert any("does not exist" in err for err in error.errors)

    def test_validate_object_data_security_integration_non_task_objects(self, tmp_path: Path):
        """Test that security validation doesn't interfere with non-task objects."""
        data = {
            "kind": "project",
            "id": "P-test-project",
            "status": "draft",
            "title": "Test Project",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        planning_root = tmp_path / "planning"
        planning_root.mkdir()

        # Should not raise any exception
        validate_object_data(data, planning_root)

    def test_validate_object_data_security_integration_hierarchy_task(self, tmp_path: Path):
        """Test that security validation works correctly with hierarchy tasks."""
        # Create a valid feature for the hierarchy task
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
            "id": "T-hierarchy",
            "parent": "F-test-feature",
            "status": "open",
            "title": "Hierarchy Task",
            "priority": "normal",
            "prerequisites": [],
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "schema_version": "1.1",
        }

        # Should not raise any exception
        validate_object_data(data, tmp_path / "planning")

    def test_validate_object_data_security_integration_performance(self, tmp_path: Path):
        """Test that security validation doesn't significantly impact performance."""
        # Create 100 tasks with various configurations
        planning_root = tmp_path / "planning"
        planning_root.mkdir()

        for i in range(100):
            data = {
                "kind": "task",
                "id": f"T-task-{i}",
                "parent": None if i % 2 == 0 else f"F-feature-{i}",
                "status": "open",
                "title": f"Task {i}",
                "priority": "normal",
                "prerequisites": [],
                "created": "2023-01-01T00:00:00Z",
                "updated": "2023-01-01T00:00:00Z",
                "schema_version": "1.1",
            }

            # For hierarchy tasks, we expect parent validation to fail
            # but security validation should still run
            if data["parent"] is not None:
                with pytest.raises(TrellisValidationError):
                    validate_object_data(data, planning_root)
            else:
                # Standalone tasks should pass
                validate_object_data(data, planning_root)
