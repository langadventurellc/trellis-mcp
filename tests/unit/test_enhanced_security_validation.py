"""Tests for enhanced security validation functions.

This module tests the enhanced security validation functions specifically
designed for path traversal prevention and comprehensive security validation.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from trellis_mcp.validation.security import (
    validate_path_boundaries,
    validate_path_construction_security,
    validate_standalone_task_path_security,
)


class TestValidatePathBoundaries:
    """Test path boundary validation functionality."""

    def test_validate_path_within_boundaries(self, tmp_path: Path):
        """Test that paths within boundaries are validated successfully."""
        # Create a test directory structure
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        # Create a file within the boundaries
        test_file = test_dir / "test_file.txt"
        test_file.write_text("test content")

        # Test validation
        errors = validate_path_boundaries(str(test_file), str(test_dir))
        assert errors == []

    def test_validate_path_outside_boundaries(self, tmp_path: Path):
        """Test that paths outside boundaries are rejected."""
        # Create test directories
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        forbidden_dir = tmp_path / "forbidden"
        forbidden_dir.mkdir()

        # Create a file outside the allowed boundary
        forbidden_file = forbidden_dir / "forbidden.txt"
        forbidden_file.write_text("forbidden content")

        # Test validation
        errors = validate_path_boundaries(str(forbidden_file), str(allowed_dir))
        assert len(errors) == 1
        assert "resolves outside allowed boundary" in errors[0]

    def test_validate_path_with_traversal_attack(self, tmp_path: Path):
        """Test that path traversal attacks are detected."""
        # Create test directory
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        # Create a path with traversal attempt
        traversal_path = str(test_dir / ".." / ".." / "etc" / "passwd")

        # Test validation
        errors = validate_path_boundaries(traversal_path, str(test_dir))
        assert len(errors) >= 1
        assert any("boundary" in error or "traversal" in error for error in errors)

    def test_validate_path_with_symlink_attack(self, tmp_path: Path):
        """Test that symbolic link attacks are detected."""
        # Create test directories
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        forbidden_dir = tmp_path / "forbidden"
        forbidden_dir.mkdir()

        # Create a target file outside the boundary
        target_file = forbidden_dir / "secret.txt"
        target_file.write_text("secret content")

        # Create a symlink inside the boundary pointing outside
        symlink_path = allowed_dir / "symlink.txt"

        try:
            # Create symlink (skip if not supported on this system)
            symlink_path.symlink_to(target_file)

            # Test validation
            errors = validate_path_boundaries(str(symlink_path), str(allowed_dir))
            assert len(errors) >= 1
            assert any("symbolic link" in error or "boundary" in error for error in errors)
        except (OSError, NotImplementedError):
            # Skip test if symlinks not supported
            pytest.skip("Symbolic links not supported on this system")

    def test_validate_path_with_absolute_symlink(self, tmp_path: Path):
        """Test that absolute symbolic links are detected."""
        # Create test directory
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        # Create a symlink pointing to absolute path
        symlink_path = test_dir / "abs_symlink.txt"

        try:
            # Create absolute symlink
            symlink_path.symlink_to("/etc/passwd")

            # Test validation - only run if symlink was created successfully
            if symlink_path.exists() or symlink_path.is_symlink():
                errors = validate_path_boundaries(str(symlink_path), str(test_dir))
                assert len(errors) >= 1
                assert any("absolute symbolic link" in error for error in errors)
            else:
                pytest.skip("Symbolic link creation failed")
        except (OSError, NotImplementedError):
            # Skip test if symlinks not supported
            pytest.skip("Symbolic links not supported on this system")

    def test_validate_path_with_invalid_path(self):
        """Test handling of invalid paths."""
        # Test with non-existent path
        errors = validate_path_boundaries("/non/existent/path", "/tmp")
        assert len(errors) >= 1
        assert "validation failed" in errors[0] or "boundary" in errors[0]


class TestValidatePathConstructionSecurity:
    """Test path construction security validation."""

    def test_validate_safe_path_components(self):
        """Test that safe path components pass validation."""
        components = ["project", "tasks-open", "T-valid-task.md"]
        errors = validate_path_construction_security(components)
        assert errors == []

    def test_validate_path_traversal_in_components(self):
        """Test detection of path traversal in components."""
        components = ["project", "..", "etc", "passwd"]
        errors = validate_path_construction_security(components)
        assert len(errors) >= 1
        assert any("directory traversal" in error for error in errors)

    def test_validate_absolute_path_injection(self):
        """Test detection of absolute path injection."""
        # Test Unix-style absolute path (not in first component)
        components = ["project", "/etc/passwd"]
        errors = validate_path_construction_security(components, allow_absolute_root=True)
        assert len(errors) >= 1
        assert any("absolute path injection" in error for error in errors)

        # Test Windows-style absolute path (not in first component)
        components = ["project", "C:\\Windows\\System32"]
        errors = validate_path_construction_security(components, allow_absolute_root=True)
        assert len(errors) >= 1
        assert any("absolute path injection" in error for error in errors)

        # Test that absolute path is allowed in first component
        components = ["/tmp/project", "tasks-open", "file.md"]
        errors = validate_path_construction_security(components, allow_absolute_root=True)
        assert not any("absolute path injection" in error for error in errors)

    def test_validate_null_byte_injection(self):
        """Test detection of null byte injection."""
        components = ["project", "file\x00.txt"]
        errors = validate_path_construction_security(components)
        assert len(errors) >= 1
        assert any("null byte injection" in error for error in errors)

    def test_validate_control_characters(self):
        """Test detection of control characters."""
        components = ["project", "file\x01.txt"]
        errors = validate_path_construction_security(components)
        assert len(errors) >= 1
        assert any("control characters" in error for error in errors)

    def test_validate_reserved_names(self):
        """Test detection of reserved system names."""
        reserved_names = ["con", "prn", "aux", "nul", "com1", "lpt1"]

        for name in reserved_names:
            components = ["project", name]
            errors = validate_path_construction_security(components)
            assert len(errors) >= 1
            assert any("reserved system name" in error for error in errors)

    def test_validate_empty_components(self):
        """Test handling of empty components."""
        components = ["project", "", "file.txt"]
        errors = validate_path_construction_security(components)
        # Empty components should be ignored, not flagged as errors
        assert errors == []

    def test_validate_multiple_security_issues(self):
        """Test detection of multiple security issues."""
        components = ["project", "..", "/etc/passwd", "file\x00.txt"]
        errors = validate_path_construction_security(components)
        assert len(errors) >= 3
        assert any("directory traversal" in error for error in errors)
        assert any("absolute path injection" in error for error in errors)
        assert any("null byte injection" in error for error in errors)


class TestValidateStandaloneTaskPathSecurity:
    """Test standalone task path security validation."""

    def test_validate_valid_task_id(self, tmp_path: Path):
        """Test validation of valid task IDs."""
        project_root = str(tmp_path / "project")
        errors = validate_standalone_task_path_security("valid-task-id", project_root)
        assert errors == []

    def test_validate_task_id_with_prefix(self, tmp_path: Path):
        """Test validation of task IDs with T- prefix."""
        project_root = str(tmp_path / "project")
        errors = validate_standalone_task_path_security("T-valid-task", project_root)
        assert errors == []

    def test_validate_empty_task_id(self, tmp_path: Path):
        """Test validation of empty task IDs."""
        project_root = str(tmp_path / "project")
        errors = validate_standalone_task_path_security("", project_root)
        assert len(errors) >= 1
        assert "Task ID cannot be empty" in errors[0]

    def test_validate_task_id_with_dot_prefix(self, tmp_path: Path):
        """Test validation of task IDs starting with dot."""
        project_root = str(tmp_path / "project")
        errors = validate_standalone_task_path_security(".hidden-task", project_root)
        assert len(errors) >= 1
        assert any("cannot start with dot" in error for error in errors)

    def test_validate_task_id_with_suspicious_extensions(self, tmp_path: Path):
        """Test validation of task IDs with suspicious file extensions."""
        project_root = str(tmp_path / "project")

        suspicious_extensions = [".exe", ".bat", ".sh", ".py", ".js"]
        for ext in suspicious_extensions:
            task_id = f"malicious-task{ext}"
            errors = validate_standalone_task_path_security(task_id, project_root)
            assert len(errors) >= 1
            assert any("suspicious file extension" in error for error in errors)

    def test_validate_task_id_with_url_encoding(self, tmp_path: Path):
        """Test validation of task IDs with URL encoding."""
        project_root = str(tmp_path / "project")
        errors = validate_standalone_task_path_security("task%20with%20encoding", project_root)
        assert len(errors) >= 1
        assert any("URL encoding sequences" in error for error in errors)

    def test_validate_path_boundaries_integration(self, tmp_path: Path):
        """Test integration with path boundary validation."""
        # Create project directory
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create a file within project boundaries
        tasks_dir = project_dir / "tasks-open"
        tasks_dir.mkdir()
        task_file = tasks_dir / "T-valid-task.md"
        task_file.write_text("task content")

        # Test validation with resolved path
        errors = validate_standalone_task_path_security(
            "valid-task", str(project_dir), str(task_file)
        )
        assert errors == []

    def test_validate_path_boundaries_violation(self, tmp_path: Path):
        """Test detection of path boundary violations."""
        # Create project directory
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create a file outside project boundaries
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "malicious.md"
        outside_file.write_text("malicious content")

        # Test validation with path outside boundaries
        errors = validate_standalone_task_path_security(
            "valid-task", str(project_dir), str(outside_file)
        )
        assert len(errors) >= 1
        assert any("boundary" in error for error in errors)

    def test_validate_multiple_security_violations(self, tmp_path: Path):
        """Test detection of multiple security violations."""
        project_root = str(tmp_path / "project")

        # Task ID with multiple security issues
        malicious_task_id = ".hidden%20task.exe"
        errors = validate_standalone_task_path_security(malicious_task_id, project_root)

        # Should detect multiple issues
        assert len(errors) >= 3
        assert any("dot" in error for error in errors)
        assert any("URL encoding" in error for error in errors)
        assert any("suspicious file extension" in error for error in errors)

    @patch("trellis_mcp.validation.security.audit_security_error")
    def test_security_auditing_integration(self, mock_audit, tmp_path: Path):
        """Test that security violations are properly audited."""
        project_root = str(tmp_path / "project")

        # Test with a task ID that triggers security auditing
        malicious_task_id = ".hidden-task"
        errors = validate_standalone_task_path_security(malicious_task_id, project_root)

        # Verify that auditing was called
        assert len(errors) >= 1
        mock_audit.assert_called()

    def test_validate_performance_with_large_inputs(self, tmp_path: Path):
        """Test performance with large inputs."""
        project_root = str(tmp_path / "project")

        # Test with very long task ID (but still valid)
        long_task_id = "a" * 100  # 100 characters, should be acceptable
        errors = validate_standalone_task_path_security(long_task_id, project_root)

        # Should not fail due to length (under 255 char limit)
        # but might fail due to charset validation in existing code
        # We're mainly testing that the function doesn't hang or crash
        assert isinstance(errors, list)

    def test_validate_edge_cases(self, tmp_path: Path):
        """Test edge cases and boundary conditions."""
        project_root = str(tmp_path / "project")

        # Test with whitespace-only task ID
        errors = validate_standalone_task_path_security("   ", project_root)
        assert len(errors) >= 1
        assert "empty" in errors[0]

        # Test with task ID containing only special characters
        errors = validate_standalone_task_path_security("...", project_root)
        assert len(errors) >= 1

        # Test with valid markdown extension
        errors = validate_standalone_task_path_security("task.md", project_root)
        # Should not flag .md extension as suspicious
        assert not any("suspicious file extension" in error for error in errors)

    def test_validate_with_unicode_characters(self, tmp_path: Path):
        """Test handling of Unicode characters."""
        project_root = str(tmp_path / "project")

        # Test with Unicode task ID
        unicode_task_id = "task-with-unicode-🔒"
        errors = validate_standalone_task_path_security(unicode_task_id, project_root)

        # Should handle Unicode gracefully (might fail charset validation)
        assert isinstance(errors, list)

        # Test with Unicode control characters
        control_char_task_id = "task\u0000with\u0001control"
        errors = validate_standalone_task_path_security(control_char_task_id, project_root)

        # Should detect control characters
        assert len(errors) >= 1
        assert any("control characters" in error for error in errors)


class TestSecurityValidationIntegration:
    """Test integration of security validation with other systems."""

    def test_security_validation_with_existing_validation(self, tmp_path: Path):
        """Test that security validation works with existing validation systems."""
        project_root = str(tmp_path / "project")

        # Test with task ID that would fail existing validation
        uppercase_task_id = "UPPERCASE-TASK"
        errors = validate_standalone_task_path_security(uppercase_task_id, project_root)

        # Should not interfere with existing validation
        assert isinstance(errors, list)

    def test_security_validation_error_handling(self, tmp_path: Path):
        """Test error handling in security validation."""
        project_root = str(tmp_path / "project")

        # Test with None task ID
        errors = validate_standalone_task_path_security(None, project_root)
        assert len(errors) >= 1
        assert "cannot be None" in errors[0]

        # Test with None project root
        errors = validate_standalone_task_path_security("valid-task", None)
        assert len(errors) >= 1
        assert "cannot be None" in errors[0]

        # Test with invalid project root
        errors = validate_standalone_task_path_security("valid-task", "/invalid/path")

        # Should handle invalid paths gracefully
        assert isinstance(errors, list)

    def test_security_validation_logging(self, tmp_path: Path):
        """Test that security validation produces appropriate logging."""
        project_root = str(tmp_path / "project")

        with patch("trellis_mcp.validation.security.audit_security_error") as mock_audit:
            # Test with malicious task ID
            errors = validate_standalone_task_path_security(".malicious", project_root)

            # Should log security violations
            assert len(errors) >= 1
            mock_audit.assert_called()

            # Check that logging includes appropriate context
            call_args = mock_audit.call_args
            assert call_args is not None
            assert len(call_args[0]) > 0  # Message should be provided
            assert isinstance(call_args[1], dict)  # Context should be provided

    def test_security_validation_consistency(self, tmp_path: Path):
        """Test that security validation is consistent across multiple calls."""
        project_root = str(tmp_path / "project")

        # Test same input multiple times
        task_id = "test-task"

        errors1 = validate_standalone_task_path_security(task_id, project_root)
        errors2 = validate_standalone_task_path_security(task_id, project_root)
        errors3 = validate_standalone_task_path_security(task_id, project_root)

        # Results should be consistent
        assert errors1 == errors2 == errors3

        # Test with malicious input
        malicious_id = ".malicious%20task.exe"

        errors1 = validate_standalone_task_path_security(malicious_id, project_root)
        errors2 = validate_standalone_task_path_security(malicious_id, project_root)

        # Should consistently detect all issues
        assert len(errors1) == len(errors2)
        assert set(errors1) == set(errors2)
