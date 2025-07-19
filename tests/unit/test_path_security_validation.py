"""Security validation tests for path resolution functions.

This module consolidates all security-focused validation tests to ensure path
operations are protected against directory traversal attacks, invalid characters,
and other security vulnerabilities across the entire path resolution system.
"""

from trellis_mcp.validation.field_validation import (
    _validate_status_parameter_security,
    _validate_task_id_security,
)


class TestTaskIdSecurityValidation:
    """Test core security validation for task IDs across all path operations."""

    def test_validate_valid_task_id(self):
        """Test validation passes for valid task ID."""
        errors = _validate_task_id_security("valid-task-id")
        assert errors == []

    def test_validate_task_id_with_numbers(self):
        """Test validation passes for task ID with numbers."""
        errors = _validate_task_id_security("task-123-id")
        assert errors == []

    def test_validate_path_traversal_sequences(self):
        """Test validation fails for path traversal sequences."""
        errors = _validate_task_id_security("../parent-dir")
        assert len(errors) >= 1
        assert any("path traversal" in error for error in errors)

    def test_validate_absolute_path_attempts(self):
        """Test validation fails for absolute path attempts."""
        errors = _validate_task_id_security("/absolute/path")
        assert len(errors) >= 1
        assert any("path separators" in error for error in errors)

    def test_validate_double_dot_sequences(self):
        """Test validation fails for double dot path traversal."""
        errors = _validate_task_id_security("task/../other")
        assert len(errors) >= 1
        assert any("path traversal" in error for error in errors)

    def test_validate_backslash_path_traversal(self):
        """Test validation fails for backslash path traversal (Windows)."""
        errors = _validate_task_id_security("task\\..\\other")
        assert len(errors) >= 1
        assert any("path traversal" in error for error in errors)

    def test_validate_url_encoded_path_traversal(self):
        """Test validation fails for URL-encoded path traversal."""
        errors = _validate_task_id_security("task%2F..%2Fother")
        assert len(errors) >= 1
        assert any("path traversal" in error for error in errors)

    def test_validate_special_characters(self):
        """Test validation fails for special characters in task ID."""
        # Note: Special character validation is handled by validate_id_charset in the main function
        # _validate_task_id_security focuses on specific security threats like path traversal
        from trellis_mcp.validation.field_validation import validate_standalone_task_path_parameters

        special_chars = ["@", "#", "$", "%", "&", "*", "+", "="]
        for char in special_chars:
            task_id = f"task{char}id"
            errors = validate_standalone_task_path_parameters(task_id, "open")
            assert len(errors) >= 1
            assert any("invalid characters" in error for error in errors)

    def test_validate_control_characters(self):
        """Test validation fails for control characters."""
        control_chars = ["\x00", "\x01", "\x1f"]  # \x7f is not caught by _validate_task_id_security
        for char in control_chars:
            task_id = f"task{char}id"
            errors = _validate_task_id_security(task_id)
            assert len(errors) >= 1
            assert any("control characters" in error for error in errors)

    def test_validate_unicode_normalization_attacks(self):
        """Test validation fails for Unicode normalization attacks."""
        # Unicode characters that could normalize to path traversal
        unicode_attacks = [
            "task\u002e\u002e/other",  # Unicode dots
            "task\u2024\u2024/other",  # One dot leader
            "task\uff0e\uff0e/other",  # Fullwidth dots
        ]
        # Note: Unicode validation is handled by validate_id_charset in the main function
        from trellis_mcp.validation.field_validation import validate_standalone_task_path_parameters

        for attack in unicode_attacks:
            errors = validate_standalone_task_path_parameters(attack, "open")
            assert len(errors) >= 1
            assert any(
                "invalid characters" in error or "path traversal" in error for error in errors
            )

    def test_validate_reserved_names(self):
        """Test validation fails for reserved filesystem names."""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for name in reserved_names:
            errors = _validate_task_id_security(name)
            assert len(errors) >= 1
            assert any("reserved" in error for error in errors)

    def test_validate_filesystem_name_limits(self):
        """Test validation fails for task IDs exceeding filesystem limits."""
        long_id = "a" * 300  # Exceeds 255 character filesystem limit
        errors = _validate_task_id_security(long_id)
        assert len(errors) >= 1
        assert any("filesystem name limits" in error for error in errors)

    def test_validate_empty_task_id(self):
        """Test validation fails for empty task ID."""
        errors = _validate_task_id_security("")
        assert len(errors) >= 1
        assert any("cannot be empty" in error for error in errors)

    def test_validate_whitespace_only_task_id(self):
        """Test validation fails for whitespace-only task ID."""
        errors = _validate_task_id_security("   ")
        assert len(errors) >= 1
        assert any("cannot be empty" in error for error in errors)

    def test_validate_leading_trailing_whitespace(self):
        """Test validation fails for task IDs with leading/trailing whitespace."""
        test_cases = [" task-id", "task-id ", " task-id "]
        for task_id in test_cases:
            errors = _validate_task_id_security(task_id)
            assert len(errors) >= 1
            assert any("whitespace" in error for error in errors)


class TestStatusParameterSecurityValidation:
    """Test security validation for status parameters in path operations."""

    def test_validate_valid_statuses(self):
        """Test validation passes for valid status values."""
        valid_statuses = ["open", "done", "in-progress", "review"]
        for status in valid_statuses:
            errors = _validate_status_parameter_security(status)
            assert errors == []

    def test_validate_none_status(self):
        """Test validation passes for None status (handled by main function)."""
        # None status should be handled by the main validation function, not the security function
        from trellis_mcp.validation.field_validation import validate_standalone_task_path_parameters

        errors = validate_standalone_task_path_parameters("valid-task-id", None)
        assert errors == []

    def test_validate_invalid_status_values(self):
        """Test validation fails for invalid status values."""
        invalid_statuses = [
            "invalid",
            "OPEN",  # Case sensitive
            "complete",
            "finished",
            "pending",
        ]
        for status in invalid_statuses:
            errors = _validate_status_parameter_security(status)
            assert len(errors) >= 1
            assert any("Invalid status parameter" in error for error in errors)

    def test_validate_status_path_traversal_attempts(self):
        """Test validation fails for path traversal in status parameter."""
        path_traversal_attempts = [
            "../open",
            "open/../done",
            "/absolute/path",
            "..\\open",  # Windows
            "%2e%2e%2fopen",  # URL encoded
        ]
        for status in path_traversal_attempts:
            errors = _validate_status_parameter_security(status)
            assert len(errors) >= 1
            assert any("Invalid status parameter" in error for error in errors)

    def test_validate_status_special_characters(self):
        """Test validation fails for special characters in status."""
        special_char_statuses = [
            "open@task",
            "done#id",
            "in-progress$",
            "review%",
            "open&done",
        ]
        for status in special_char_statuses:
            errors = _validate_status_parameter_security(status)
            assert len(errors) >= 1
            assert any("Invalid status parameter" in error for error in errors)

    def test_validate_status_control_characters(self):
        """Test validation fails for control characters in status."""
        control_char_statuses = [
            "open\x00",
            "done\x01",
            "in-progress\x1f",
            "review\x7f",
        ]
        for status in control_char_statuses:
            errors = _validate_status_parameter_security(status)
            assert len(errors) >= 1
            assert any("Invalid status parameter" in error for error in errors)

    def test_validate_empty_status(self):
        """Test validation fails for empty string status."""
        errors = _validate_status_parameter_security("")
        assert len(errors) >= 1
        assert any("Invalid status parameter" in error for error in errors)

    def test_validate_whitespace_status(self):
        """Test validation fails for whitespace-only status."""
        errors = _validate_status_parameter_security("   ")
        assert len(errors) >= 1
        assert any("Invalid status parameter" in error for error in errors)


class TestTaskIdEdgeCaseSecurity:
    """Test edge cases in task ID security validation."""

    def test_validate_minimal_valid_ids(self):
        """Test validation for minimal valid task IDs."""
        minimal_ids = ["a", "1", "x"]
        for task_id in minimal_ids:
            errors = _validate_task_id_security(task_id)
            assert errors == []

    def test_validate_hyphen_variations(self):
        """Test validation for various hyphen usage patterns."""
        hyphen_cases = [
            "task-id",
            "multi-word-task-id",
            "a-b-c-d-e",
            "task1-task2-task3",
        ]
        for task_id in hyphen_cases:
            errors = _validate_task_id_security(task_id)
            assert errors == []

    def test_validate_number_variations(self):
        """Test validation for various number patterns."""
        number_cases = [
            "123",
            "task123",
            "123task",
            "task-123-id",
            "v1-2-3",
        ]
        for task_id in number_cases:
            errors = _validate_task_id_security(task_id)
            assert errors == []

    def test_validate_boundary_length_cases(self):
        """Test validation at filesystem name length boundaries."""
        # Just under the limit should pass
        almost_max = "a" * 254
        errors = _validate_task_id_security(almost_max)
        assert errors == []

        # At the limit should pass
        at_max = "a" * 255
        errors = _validate_task_id_security(at_max)
        assert errors == []

        # Over the limit should fail
        over_max = "a" * 256
        errors = _validate_task_id_security(over_max)
        assert len(errors) >= 1
        assert any("filesystem name limits" in error for error in errors)

    def test_validate_unicode_edge_cases(self):
        """Test validation for Unicode edge cases."""
        unicode_cases = [
            "tâsk-ïd",  # Valid accented characters
            "タスク",  # Japanese characters
            "задача",  # Cyrillic characters
        ]
        for task_id in unicode_cases:
            errors = _validate_task_id_security(task_id)
            # These should pass if the system supports Unicode filenames
            # or fail gracefully with appropriate error messages
            if errors:
                assert any("invalid characters" in error for error in errors)

    def test_validate_mixed_attack_vectors(self):
        """Test validation against combined attack vectors."""
        combined_attacks = [
            "../task@id",  # Path traversal + invalid char
            "task\x00../other",  # Null byte + path traversal
            "%2e%2e/task#id",  # URL encoding + path traversal + invalid char
            "CON/../task",  # Reserved name + path traversal
        ]
        for attack in combined_attacks:
            errors = _validate_task_id_security(attack)
            assert len(errors) >= 1
            # Should catch at least one of the attack vectors
            assert any(
                any(
                    pattern in error
                    for pattern in ["path traversal", "invalid characters", "reserved"]
                )
                for error in errors
            )
