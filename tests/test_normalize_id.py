"""Tests for ID normalization utilities.

Comprehensive test suite for the normalize_id module covering generalized
ID normalization for all object types (Project, Epic, Feature, Task).
"""

import pytest

from trellis_mcp.utils.normalize_id import normalize_id


class TestNormalizeId:
    """Test cases for the generalized normalize_id function."""

    def test_task_id_normalization(self):
        """Test task ID normalization."""
        test_cases = [
            ("T-implement-auth", "task", "implement-auth"),
            ("implement-auth", "task", "implement-auth"),
            ("  T-task-name  ", "task", "task-name"),
            ("T-UPPERCASE-TASK", "task", "uppercase-task"),
            ("task_with_underscores", "task", "task-with-underscores"),
            ("Task With Spaces", "task", "task-with-spaces"),
        ]

        for input_id, kind, expected in test_cases:
            result = normalize_id(input_id, kind)
            assert (
                result == expected
            ), f"normalize_id('{input_id}', '{kind}') should return '{expected}', got '{result}'"

    def test_project_id_normalization(self):
        """Test project ID normalization."""
        test_cases = [
            ("P-web-platform", "project", "web-platform"),
            ("web-platform", "project", "web-platform"),
            ("  P-project-name  ", "project", "project-name"),
            ("P-UPPERCASE-PROJECT", "project", "uppercase-project"),
            ("project_with_underscores", "project", "project-with-underscores"),
            ("Project With Spaces", "project", "project-with-spaces"),
        ]

        for input_id, kind, expected in test_cases:
            result = normalize_id(input_id, kind)
            assert (
                result == expected
            ), f"normalize_id('{input_id}', '{kind}') should return '{expected}', got '{result}'"

    def test_epic_id_normalization(self):
        """Test epic ID normalization."""
        test_cases = [
            ("E-user-management", "epic", "user-management"),
            ("user-management", "epic", "user-management"),
            ("  E-epic-name  ", "epic", "epic-name"),
            ("E-UPPERCASE-EPIC", "epic", "uppercase-epic"),
            ("epic_with_underscores", "epic", "epic-with-underscores"),
            ("Epic With Spaces", "epic", "epic-with-spaces"),
        ]

        for input_id, kind, expected in test_cases:
            result = normalize_id(input_id, kind)
            assert (
                result == expected
            ), f"normalize_id('{input_id}', '{kind}') should return '{expected}', got '{result}'"

    def test_feature_id_normalization(self):
        """Test feature ID normalization."""
        test_cases = [
            ("F-login-system", "feature", "login-system"),
            ("login-system", "feature", "login-system"),
            ("  F-feature-name  ", "feature", "feature-name"),
            ("F-UPPERCASE-FEATURE", "feature", "uppercase-feature"),
            ("feature_with_underscores", "feature", "feature-with-underscores"),
            ("Feature With Spaces", "feature", "feature-with-spaces"),
        ]

        for input_id, kind, expected in test_cases:
            result = normalize_id(input_id, kind)
            assert (
                result == expected
            ), f"normalize_id('{input_id}', '{kind}') should return '{expected}', got '{result}'"

    def test_special_character_normalization(self):
        """Test normalization of special characters across all object types."""
        test_cases = [
            ("T-task@with-special", "task", "taskwith-special"),
            ("P-project#with%symbols", "project", "projectwithsymbols"),
            ("E-epic.with.dots", "epic", "epicwithdots"),
            ("F-feature/with\\slashes", "feature", "featurewithslashes"),
            ("T-multiple   spaces", "task", "multiple-spaces"),
            ("P-tabs\t\tand\nnewlines", "project", "tabs-and-newlines"),
        ]

        for input_id, kind, expected in test_cases:
            result = normalize_id(input_id, kind)
            assert (
                result == expected
            ), f"normalize_id('{input_id}', '{kind}') should return '{expected}', got '{result}'"

    def test_hyphen_cleanup(self):
        """Test cleanup of multiple hyphens across all object types."""
        test_cases = [
            ("T-double--hyphens", "task", "double-hyphens"),
            ("P-triple---hyphens", "project", "triple-hyphens"),
            ("E---leading-hyphens", "epic", "leading-hyphens"),
            ("F-trailing-hyphens--", "feature", "trailing-hyphens"),
            ("T---surrounded--", "task", "surrounded"),
            ("P-multiple--hyphens--everywhere", "project", "multiple-hyphens-everywhere"),
        ]

        for input_id, kind, expected in test_cases:
            result = normalize_id(input_id, kind)
            assert (
                result == expected
            ), f"normalize_id('{input_id}', '{kind}') should return '{expected}', got '{result}'"

    def test_empty_and_edge_cases(self):
        """Test empty strings and edge cases for all object types."""
        kinds = ["project", "epic", "feature", "task"]

        for kind in kinds:
            assert normalize_id("", kind) == ""
            assert normalize_id("   ", kind) == ""
            assert normalize_id("---", kind) == ""

            # Test with single character after prefix removal
            prefix = {"project": "P-", "epic": "E-", "feature": "F-", "task": "T-"}[kind]
            assert normalize_id(f"{prefix}a", kind) == "a"
            assert normalize_id("a", kind) == "a"

    def test_prefix_removal_variations(self):
        """Test prefix removal for all object types."""
        test_cases = [
            ("T-simple-task", "task", "simple-task"),
            ("P-simple-project", "project", "simple-project"),
            ("E-simple-epic", "epic", "simple-epic"),
            ("F-simple-feature", "feature", "simple-feature"),
            # Test lowercase prefixes
            ("t-lowercase-prefix", "task", "lowercase-prefix"),
            ("p-lowercase-prefix", "project", "lowercase-prefix"),
            ("e-lowercase-prefix", "epic", "lowercase-prefix"),
            ("f-lowercase-prefix", "feature", "lowercase-prefix"),
            # Test double prefixes (should handle nested prefixes)
            ("T-T-double-prefix", "task", "double-prefix"),
            ("P-P-double-prefix", "project", "double-prefix"),
        ]

        for input_id, kind, expected in test_cases:
            result = normalize_id(input_id, kind)
            assert (
                result == expected
            ), f"normalize_id('{input_id}', '{kind}') should return '{expected}', got '{result}'"

    def test_invalid_kind_raises_error(self):
        """Test that invalid kinds raise ValueError."""
        invalid_kinds = [
            "invalid",
            "tasks",  # plural
            "projects",  # plural
            "",
            "Task",  # wrong case
            "PROJECT",  # wrong case
        ]

        for invalid_kind in invalid_kinds:
            with pytest.raises(ValueError, match="Invalid kind"):
                normalize_id("test-id", invalid_kind)

    def test_cross_kind_prefix_handling(self):
        """Test that prefixes from other kinds are handled correctly."""
        # Task ID with project prefix should still be normalized correctly
        assert normalize_id("P-task-with-project-prefix", "task") == "task-with-project-prefix"

        # Project ID with task prefix should still be normalized correctly
        assert normalize_id("T-project-with-task-prefix", "project") == "project-with-task-prefix"

        # Epic ID with feature prefix should still be normalized correctly
        assert normalize_id("F-epic-with-feature-prefix", "epic") == "epic-with-feature-prefix"


class TestIntegrationWithExistingCode:
    """Integration tests to ensure the new functions work with existing code patterns."""

    def test_clean_prerequisite_id_integration(self):
        """Test that normalize_id integrates properly with clean_prerequisite_id."""
        from trellis_mcp.utils.id_utils import clean_prerequisite_id

        # Test that our function handles the same cases as clean_prerequisite_id
        test_cases = [
            ("T-task-name", "task"),
            ("P-project-name", "project"),
            ("E-epic-name", "epic"),
            ("F-feature-name", "feature"),
        ]

        for input_id, kind in test_cases:
            # Both should remove the prefix
            normalize_result = normalize_id(input_id, kind)
            clean_result = clean_prerequisite_id(input_id)

            # Results should be the same for simple prefix removal
            assert normalize_result == clean_result, f"Results should match for {input_id}"

    def test_id_utils_consistency(self):
        """Test consistency with existing id_utils validation functions."""
        from trellis_mcp.utils.id_utils import validate_id_charset, validate_id_length

        # Generate some IDs using normalize_id and verify they pass validation
        test_inputs = [
            ("T-valid-task-name", "task"),
            ("P-valid-project-name", "project"),
            ("E-valid-epic-name", "epic"),
            ("F-valid-feature-name", "feature"),
        ]

        for input_id, kind in test_inputs:
            normalized = normalize_id(input_id, kind)

            # Normalized IDs should pass charset validation
            assert validate_id_charset(
                normalized
            ), f"Normalized ID '{normalized}' should pass charset validation"

            # Normalized IDs should pass length validation
            assert validate_id_length(
                normalized
            ), f"Normalized ID '{normalized}' should pass length validation"
