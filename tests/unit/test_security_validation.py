"""Tests for security validation of standalone tasks.

This module tests the security validation functions to ensure standalone tasks
don't introduce privilege escalation opportunities or allow validation bypass
through parent field manipulation.
"""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from trellis_mcp.exceptions.validation_error import ValidationErrorCode
from trellis_mcp.validation import (
    TrellisValidationError,
    validate_object_data,
    validate_standalone_task_security,
)
from trellis_mcp.validation.error_collector import (
    ErrorCategory,
    ErrorSeverity,
    ValidationErrorCollector,
)
from trellis_mcp.validation.security import (
    audit_security_error,
    create_consistent_error_response,
    filter_sensitive_information,
    sanitize_error_message,
    validate_error_message_safety,
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


class TestErrorMessageSanitization:
    """Test error message sanitization functionality."""

    def _sanitize_and_assert(
        self, message: str, expected_redacted: str, original_text: str
    ) -> None:
        """Helper to sanitize and assert results."""
        sanitized = sanitize_error_message(message)
        assert sanitized is not None
        assert expected_redacted in sanitized
        assert original_text not in sanitized

    def test_sanitize_basic_file_path(self):
        """Test sanitization of basic file paths."""
        message = "Error in file /home/user/secret/config.txt"
        self._sanitize_and_assert(message, "[REDACTED_PATH]", "/home/user/secret/config.txt")

    def test_sanitize_windows_path(self):
        """Test sanitization of Windows file paths."""
        message = "Error in file C:\\Users\\user\\secret\\config.txt"
        self._sanitize_and_assert(message, "[REDACTED_PATH]", "C:\\Users\\user\\secret\\config.txt")

    def test_sanitize_database_connection(self):
        """Test sanitization of database connection strings."""
        message = "Connection failed: postgresql://user:pass@localhost/db"
        self._sanitize_and_assert(
            message, "[REDACTED_CONNECTION]", "postgresql://user:pass@localhost/db"
        )

    def test_sanitize_ip_address(self):
        """Test sanitization of IP addresses."""
        message = "Connection failed to 192.168.1.100"
        self._sanitize_and_assert(message, "[REDACTED_IP]", "192.168.1.100")

    def test_sanitize_token(self):
        """Test sanitization of tokens."""
        message = "Token: abc123def456ghi789jkl"
        self._sanitize_and_assert(message, "[REDACTED_TOKEN]", "abc123def456ghi789jkl")

    def test_sanitize_api_key(self):
        """Test sanitization of API keys."""
        message = "Key: xyz987uvw654rst321pqr"  # 18 characters, >= 15
        self._sanitize_and_assert(message, "[REDACTED_KEY]", "xyz987uvw654rst321pqr")

    def test_sanitize_uuid(self):
        """Test sanitization of UUIDs."""
        message = "ID: 12345678-1234-5678-9012-123456789012"
        self._sanitize_and_assert(
            message, "[REDACTED_UUID]", "12345678-1234-5678-9012-123456789012"
        )

    def test_sanitize_environment_variable(self):
        """Test sanitization of environment variables."""
        message = "Environment: DATABASE_URL=postgresql://user:pass@host/db"
        self._sanitize_and_assert(
            message, "[REDACTED_ENV]", "DATABASE_URL=postgresql://user:pass@host/db"
        )

    def test_sanitize_stack_trace(self):
        """Test sanitization of stack traces."""
        message = 'File "/path/to/file.py", line 123, in function'
        sanitized = sanitize_error_message(message)
        assert sanitized is not None
        assert "[REDACTED]" in sanitized
        assert '"/path/to/file.py"' not in sanitized
        assert "line 123" not in sanitized

    def test_sanitize_empty_message(self):
        """Test sanitization of empty messages."""
        assert sanitize_error_message("") == ""
        assert sanitize_error_message(None) is None

    def test_sanitize_safe_message(self):
        """Test that safe messages are not modified."""
        message = "Invalid field value provided"
        sanitized = sanitize_error_message(message)
        assert sanitized == message


class TestErrorMessageSafety:
    """Test error message safety validation."""

    def test_detect_password_information(self):
        """Test detection of password-related information."""
        message = "Password validation failed"
        issues = validate_error_message_safety(message)
        assert len(issues) == 1
        assert "password-related information" in issues[0]

    def test_detect_secret_information(self):
        """Test detection of secret information."""
        message = "Secret token is invalid"
        issues = validate_error_message_safety(message)
        assert len(issues) == 1
        assert "secret/token information" in issues[0]

    def test_detect_file_paths(self):
        """Test detection of detailed file paths."""
        message = "Error in /home/user/app/config/data.txt"
        issues = validate_error_message_safety(message)
        assert len(issues) == 1
        assert "detailed file paths" in issues[0]

    def test_detect_database_errors(self):
        """Test detection of database errors."""
        message = "SQL Error: Table not found"
        issues = validate_error_message_safety(message)
        assert len(issues) == 1
        assert "database error details" in issues[0]

    def test_detect_ip_addresses(self):
        """Test detection of IP addresses."""
        message = "Connection failed to 10.0.0.1"
        issues = validate_error_message_safety(message)
        assert len(issues) == 1
        assert "IP addresses" in issues[0]

    def test_detect_port_numbers(self):
        """Test detection of port numbers."""
        message = "Connection failed on port :8080"
        issues = validate_error_message_safety(message)
        assert len(issues) == 1
        assert "port numbers" in issues[0]

    def test_safe_message_no_issues(self):
        """Test that safe messages have no issues."""
        message = "Invalid field value"
        issues = validate_error_message_safety(message)
        assert len(issues) == 0

    def test_empty_message_no_issues(self):
        """Test that empty messages have no issues."""
        assert validate_error_message_safety("") == []
        assert validate_error_message_safety(None) == []

    def test_multiple_issues(self):
        """Test detection of multiple security issues."""
        message = "Password failed for user at 192.168.1.1:3306"
        issues = validate_error_message_safety(message)
        assert len(issues) >= 2  # Should detect password and IP/port


class TestSensitiveInformationFiltering:
    """Test filtering of sensitive information from context data."""

    def test_filter_password_fields(self):
        """Test filtering of password fields."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com",
        }
        filtered = filter_sensitive_information(data)
        assert filtered is not None
        assert "password" not in filtered
        assert "username" in filtered
        assert "email" in filtered

    def test_filter_api_keys(self):
        """Test filtering of API keys."""
        data = {
            "api_key": "secret123",
            "token": "abc123def456",
            "user_id": "12345",
        }
        filtered = filter_sensitive_information(data)
        assert filtered is not None
        assert "api_key" not in filtered
        assert "token" not in filtered
        assert "user_id" in filtered

    def test_obfuscate_identifiers(self):
        """Test obfuscation of identifier fields."""
        data = {
            "user_id": "12345678",
            "email": "test@example.com",
            "title": "Test Title",
        }
        filtered = filter_sensitive_information(data)
        assert filtered is not None
        assert filtered["user_id"] == "12***78"
        assert filtered["email"] == "te***om"
        assert filtered["title"] == "Test Title"

    def test_obfuscate_short_values(self):
        """Test obfuscation of short values."""
        data = {
            "id": "123",
            "path": "/a",
        }
        filtered = filter_sensitive_information(data)
        assert filtered is not None
        assert filtered["id"] == "***"
        assert filtered["path"] == "***"

    def test_sanitize_string_values(self):
        """Test sanitization of string values."""
        data = {
            "message": "Error in /home/user/file.txt",
            "count": 42,
        }
        filtered = filter_sensitive_information(data)
        assert filtered is not None
        assert "[REDACTED_PATH]" in filtered["message"]
        assert filtered["count"] == 42

    def test_filter_empty_data(self):
        """Test filtering of empty data."""
        assert filter_sensitive_information(None) is None
        assert filter_sensitive_information({}) == {}

    def test_filter_connection_strings(self):
        """Test filtering of connection strings."""
        data = {
            "connection_string": "postgresql://user:pass@host/db",
            "database_url": "mysql://user:pass@host/db",
            "normal_field": "value",
        }
        filtered = filter_sensitive_information(data)
        assert filtered is not None
        assert "connection_string" not in filtered
        assert "database_url" not in filtered
        assert filtered["normal_field"] == "value"


class TestConsistentErrorResponse:
    """Test consistent error response functionality."""

    def test_create_consistent_response_structure(self):
        """Test that consistent error responses have proper structure."""
        response = create_consistent_error_response("Test error", "validation")

        assert response["error"] is True
        assert response["message"] == "Test error"
        assert response["type"] == "validation"
        assert "timestamp" in response
        assert isinstance(response["timestamp"], float)

    def test_create_consistent_response_timing(self):
        """Test that consistent error responses have timing delays."""
        start_time = time.time()
        create_consistent_error_response("Test error")
        end_time = time.time()

        # Should have at least 1ms delay
        assert end_time - start_time >= 0.001

    def test_create_consistent_response_sanitization(self):
        """Test that error responses are sanitized."""
        response = create_consistent_error_response("Error in /home/user/file.txt")
        assert "[REDACTED_PATH]" in response["message"]
        assert "/home/user/file.txt" not in response["message"]

    def test_create_consistent_response_default_type(self):
        """Test default error type."""
        response = create_consistent_error_response("Test error")
        assert response["type"] == "validation"


class TestSecurityAuditing:
    """Test security auditing functionality."""

    @patch("logging.getLogger")
    def test_audit_security_error_basic(self, mock_get_logger):
        """Test basic security error auditing."""
        mock_logger = mock_get_logger.return_value

        audit_security_error("Test security error")

        mock_get_logger.assert_called_once_with("trellis_mcp.security")
        mock_logger.warning.assert_called_once()

    @patch("logging.getLogger")
    def test_audit_security_error_with_context(self, mock_get_logger):
        """Test security error auditing with context."""
        mock_logger = mock_get_logger.return_value

        context = {
            "user_id": "12345",
            "password": "secret",  # Should be filtered
            "action": "login",
        }

        audit_security_error("Login failed", context)

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args

        # Check that context was sanitized
        extra_context = call_args[1]["extra"]["security_context"]
        assert "password" not in extra_context
        assert "user_id" in extra_context
        assert "action" in extra_context

    @patch("logging.getLogger")
    def test_audit_security_error_message_sanitization(self, mock_get_logger):
        """Test that audited messages are sanitized."""
        mock_logger = mock_get_logger.return_value

        audit_security_error("Error in /home/user/secret.txt")

        call_args = mock_logger.warning.call_args
        message = call_args[0][1]  # Second argument (first is format string)
        assert "[REDACTED_PATH]" in message
        assert "/home/user/secret.txt" not in message


class TestValidationErrorCollectorSecurity:
    """Test security integration in ValidationErrorCollector."""

    def test_add_error_with_security_validation(self):
        """Test adding errors with security validation enabled."""
        collector = ValidationErrorCollector()

        # Add error with sensitive information
        collector.add_error(
            "Error in /home/user/secret.txt",
            ValidationErrorCode.INVALID_FIELD,
            context={"password": "secret123", "user_id": "12345"},
            perform_security_validation=True,
        )

        errors = collector.get_prioritized_errors()
        assert len(errors) == 1

        message, _, context = errors[0]
        assert "[REDACTED_PATH]" in message
        assert "/home/user/secret.txt" not in message
        assert "password" not in context
        assert "user_id" in context

    def test_add_error_without_security_validation(self):
        """Test adding errors with security validation disabled."""
        collector = ValidationErrorCollector()

        # Add error without security validation
        collector.add_error(
            "Error in /home/user/secret.txt",
            ValidationErrorCode.INVALID_FIELD,
            context={"password": "secret123", "user_id": "12345"},
            perform_security_validation=False,
        )

        errors = collector.get_prioritized_errors()
        assert len(errors) == 1

        message, _, context = errors[0]
        assert "/home/user/secret.txt" in message  # Not sanitized
        assert "password" in context  # Not filtered

    def test_add_security_error(self):
        """Test adding security-specific errors."""
        collector = ValidationErrorCollector()

        collector.add_security_error(
            "Security violation detected",
            ValidationErrorCode.INVALID_FIELD,
            context={"attack_type": "injection"},
        )

        # Check that error was added with security category
        security_errors = collector.get_errors_by_category(ErrorCategory.SECURITY)
        assert len(security_errors) == 1

        message, code, context = security_errors[0]
        assert message == "Security violation detected"
        assert code == ValidationErrorCode.INVALID_FIELD
        assert context["attack_type"] == "injection"

    def test_add_security_error_default_severity(self):
        """Test that security errors default to HIGH severity."""
        collector = ValidationErrorCollector()

        collector.add_security_error(
            "Security violation",
            ValidationErrorCode.INVALID_FIELD,
        )

        # Check that error has HIGH severity
        high_errors = collector.get_errors_by_severity(ErrorSeverity.HIGH)
        assert len(high_errors) == 1

    @patch("trellis_mcp.validation.error_collector.audit_security_error")
    def test_add_security_error_auditing(self, mock_audit):
        """Test that security errors are audited."""
        collector = ValidationErrorCollector()

        collector.add_security_error(
            "Security violation",
            ValidationErrorCode.INVALID_FIELD,
            context={"user_id": "12345"},
        )

        mock_audit.assert_called_once()

    def test_unsafe_error_message_replacement(self):
        """Test that unsafe error messages are replaced with generic ones."""
        collector = ValidationErrorCollector()

        # Add error with unsafe message
        collector.add_error(
            "Password validation failed for user secret123",
            ValidationErrorCode.INVALID_FIELD,
            perform_security_validation=True,
        )

        errors = collector.get_prioritized_errors()
        assert len(errors) == 1

        message, _, _ = errors[0]
        # Should be replaced with generic message due to safety concerns
        assert message == "Validation error occurred"
