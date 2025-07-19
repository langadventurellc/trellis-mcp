"""Tests for ID pattern matching system.

Comprehensive test suite for the PatternMatcher class including pattern
recognition, error handling, performance validation, and edge cases.
"""

import time

import pytest

from trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from trellis_mcp.inference.pattern_matcher import PatternMatcher
from trellis_mcp.schema.kind_enum import KindEnum


class TestPatternMatcher:
    """Test cases for the PatternMatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = PatternMatcher()

    def test_initialization(self):
        """Test PatternMatcher initialization."""
        matcher = PatternMatcher()
        assert isinstance(matcher, PatternMatcher)
        # Verify patterns are accessible (they're class constants)
        assert len(PatternMatcher._PATTERNS) == 4
        assert KindEnum.PROJECT in PatternMatcher._PATTERNS
        assert KindEnum.EPIC in PatternMatcher._PATTERNS
        assert KindEnum.FEATURE in PatternMatcher._PATTERNS
        assert KindEnum.TASK in PatternMatcher._PATTERNS


class TestHierarchicalPatternRecognition:
    """Test hierarchical object pattern recognition."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = PatternMatcher()

    def test_project_pattern_recognition(self):
        """Test project prefix pattern recognition."""
        test_cases = [
            "P-user-auth-system",
            "P-ecommerce-platform",
            "P-api-gateway",
            "P-data-pipeline",
            "P-123",
            "P-a",
            "P-project-with-many-hyphens-and-numbers-123",
        ]

        for project_id in test_cases:
            result = self.matcher.infer_kind(project_id)
            assert result == KindEnum.PROJECT.value, f"Failed for {project_id}"

    def test_epic_pattern_recognition(self):
        """Test epic prefix pattern recognition."""
        test_cases = [
            "E-user-management",
            "E-payment-processing",
            "E-security-features",
            "E-api-endpoints",
            "E-456",
            "E-b",
            "E-epic-with-multiple-segments-789",
        ]

        for epic_id in test_cases:
            result = self.matcher.infer_kind(epic_id)
            assert result == KindEnum.EPIC.value, f"Failed for {epic_id}"

    def test_feature_pattern_recognition(self):
        """Test feature prefix pattern recognition."""
        test_cases = [
            "F-login-form",
            "F-registration-workflow",
            "F-password-reset",
            "F-two-factor-auth",
            "F-789",
            "F-c",
            "F-feature-with-complex-naming-convention-456",
        ]

        for feature_id in test_cases:
            result = self.matcher.infer_kind(feature_id)
            assert result == KindEnum.FEATURE.value, f"Failed for {feature_id}"

    def test_task_pattern_recognition(self):
        """Test task prefix pattern recognition."""
        test_cases = [
            "T-implement-login",
            "T-create-user-model",
            "T-add-validation",
            "T-write-tests",
            "T-012",
            "T-d",
            "T-task-with-extremely-detailed-description-123",
        ]

        for task_id in test_cases:
            result = self.matcher.infer_kind(task_id)
            assert result == KindEnum.TASK.value, f"Failed for {task_id}"


class TestValidationMethods:
    """Test ID format validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = PatternMatcher()

    def test_validate_id_format_valid_ids(self):
        """Test validate_id_format with valid IDs."""
        valid_ids = [
            "P-project-name",
            "E-epic-name",
            "F-feature-name",
            "T-task-name",
            "P-123",
            "E-a-b-c",
            "F-test123",
            "T-complex-name-with-numbers-456",
        ]

        for valid_id in valid_ids:
            assert self.matcher.validate_id_format(valid_id), f"Should be valid: {valid_id}"

    def test_validate_id_format_invalid_ids(self):
        """Test validate_id_format with invalid IDs."""
        invalid_ids = [
            "",
            "invalid-no-prefix",
            "X-invalid-prefix",
            "p-lowercase-prefix",
            "P-Invalid_Underscore",
            "P-Invalid Space",
            "P-Invalid@Symbol",
            "P",
            "P-",
            "-missing-prefix",
            "P--double-hyphen",
            None,
            123,
            [],
        ]

        for invalid_id in invalid_ids:
            assert not self.matcher.validate_id_format(
                invalid_id  # type: ignore
            ), f"Should be invalid: {invalid_id}"


class TestErrorHandling:
    """Test error handling and ValidationError integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = PatternMatcher()

    def test_empty_string_error(self):
        """Test error handling for empty string input."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind("")

        error = exc_info.value
        assert ValidationErrorCode.MISSING_REQUIRED_FIELD in error.error_codes
        assert "Object ID cannot be empty" in error.errors
        assert error.context["object_id"] == ""

    def test_none_input_error(self):
        """Test error handling for None input."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind(None)  # type: ignore

        error = exc_info.value
        assert ValidationErrorCode.MISSING_REQUIRED_FIELD in error.error_codes
        assert "Object ID cannot be empty" in error.errors

    def test_non_string_input_error(self):
        """Test error handling for non-string input types."""
        invalid_inputs = [123, [], {}, True, 45.67]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError) as exc_info:
                self.matcher.infer_kind(invalid_input)  # type: ignore

            error = exc_info.value
            assert ValidationErrorCode.INVALID_FIELD in error.error_codes
            assert "Object ID must be a string" in error.errors
            assert error.context["object_id"] == invalid_input
            assert error.context["type"] == type(invalid_input).__name__

    def test_invalid_prefix_error_lowercase(self):
        """Test error handling for lowercase prefix."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind("p-project-name")

        error = exc_info.value
        assert ValidationErrorCode.INVALID_FORMAT in error.error_codes
        assert "Prefix must be uppercase" in error.errors[0]
        assert "Did you mean 'P-'?" in error.errors[0]
        assert error.context["extracted_prefix"] == "p-"

    def test_invalid_prefix_error_unknown(self):
        """Test error handling for unknown prefix."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind("X-unknown-prefix")

        error = exc_info.value
        assert ValidationErrorCode.INVALID_FORMAT in error.error_codes
        assert "Unrecognized prefix 'X-'" in error.errors[0]
        assert (
            "Valid prefixes are: P- (project), E- (epic), F- (feature), T- (task)"
            in error.errors[0]
        )
        assert error.context["extracted_prefix"] == "X-"

    def test_invalid_suffix_format_error(self):
        """Test error handling for invalid suffix format."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind("P-Invalid_Underscore")

        error = exc_info.value
        assert ValidationErrorCode.INVALID_FORMAT in error.error_codes
        assert "Invalid suffix 'Invalid_Underscore'" in error.errors[0]
        assert "must contain only lowercase letters, numbers, and hyphens" in error.errors[0]

    def test_no_hyphen_error(self):
        """Test error handling for IDs without hyphens."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind("invalidformat")

        error = exc_info.value
        assert ValidationErrorCode.INVALID_FORMAT in error.error_codes
        assert "Expected format: [PREFIX]-[name]" in error.errors[0]
        assert error.context["extracted_prefix"] is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = PatternMatcher()

    def test_minimal_valid_ids(self):
        """Test minimal valid ID formats."""
        minimal_ids = [
            ("P-a", KindEnum.PROJECT.value),
            ("E-1", KindEnum.EPIC.value),
            ("F-x", KindEnum.FEATURE.value),
            ("T-0", KindEnum.TASK.value),
        ]

        for object_id, expected_kind in minimal_ids:
            result = self.matcher.infer_kind(object_id)
            assert result == expected_kind

    def test_complex_valid_ids(self):
        """Test complex but valid ID formats."""
        complex_ids = [
            ("P-very-long-project-name-with-many-segments", KindEnum.PROJECT.value),
            ("E-123-456-789", KindEnum.EPIC.value),
            ("F-feature-v2-update-123", KindEnum.FEATURE.value),
            ("T-implement-oauth2-authentication-flow", KindEnum.TASK.value),
        ]

        for object_id, expected_kind in complex_ids:
            result = self.matcher.infer_kind(object_id)
            assert result == expected_kind

    def test_whitespace_handling(self):
        """Test handling of IDs with whitespace."""
        whitespace_ids = [
            " P-project-name",
            "P-project-name ",
            " P-project-name ",
            "P-project name",  # Space in suffix
            "P project-name",  # Space in prefix
        ]

        for whitespace_id in whitespace_ids:
            with pytest.raises(ValidationError):
                self.matcher.infer_kind(whitespace_id)

    def test_special_characters(self):
        """Test handling of IDs with special characters."""
        special_char_ids = [
            "P-project@name",
            "P-project.name",
            "P-project_name",
            "P-project/name",
            "P-project\\name",
            "P-project+name",
            "P-project=name",
        ]

        for special_id in special_char_ids:
            with pytest.raises(ValidationError):
                self.matcher.infer_kind(special_id)


class TestPerformance:
    """Test performance requirements and optimization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = PatternMatcher()

    def test_pattern_matching_performance(self):
        """Test that pattern matching meets < 1ms requirement."""
        test_id = "P-performance-test-project"
        iterations = 1000

        start_time = time.perf_counter()
        for _ in range(iterations):
            result = self.matcher.infer_kind(test_id)
            assert result == KindEnum.PROJECT.value
        end_time = time.perf_counter()

        avg_time_ms = ((end_time - start_time) / iterations) * 1000
        assert avg_time_ms < 1.0, f"Average time {avg_time_ms:.3f}ms exceeds 1ms requirement"

    def test_validation_performance(self):
        """Test that ID validation meets performance requirements."""
        test_ids = [
            "P-project-name",
            "E-epic-name",
            "F-feature-name",
            "T-task-name",
            "invalid-id",
        ]
        iterations = 200

        start_time = time.perf_counter()
        for _ in range(iterations):
            for test_id in test_ids:
                self.matcher.validate_id_format(test_id)
        end_time = time.perf_counter()

        avg_time_ms = ((end_time - start_time) / (iterations * len(test_ids))) * 1000
        assert avg_time_ms < 1.0, f"Average time {avg_time_ms:.3f}ms exceeds 1ms requirement"

    def test_concurrent_access_safety(self):
        """Test thread safety for concurrent access."""
        import threading

        results = []
        errors = []

        def worker():
            try:
                for i in range(100):
                    result = self.matcher.infer_kind(f"P-project-{i}")
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 1000
        assert all(result == KindEnum.PROJECT.value for result in results)


class TestIntegrationWithExistingSystems:
    """Test integration with existing Trellis components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = PatternMatcher()

    def test_kindenum_integration(self):
        """Test proper integration with KindEnum values."""
        test_cases = [
            ("P-project", KindEnum.PROJECT),
            ("E-epic", KindEnum.EPIC),
            ("F-feature", KindEnum.FEATURE),
            ("T-task", KindEnum.TASK),
        ]

        for object_id, expected_enum in test_cases:
            result = self.matcher.infer_kind(object_id)
            assert result == expected_enum.value
            # Verify we can create KindEnum from result
            assert KindEnum(result) == expected_enum

    def test_validation_error_integration(self):
        """Test proper integration with ValidationError system."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind("invalid-id")

        error = exc_info.value
        # Test ValidationError interface
        assert hasattr(error, "errors")
        assert hasattr(error, "error_codes")
        assert hasattr(error, "context")
        assert hasattr(error, "to_dict")
        assert hasattr(error, "has_error_code")

        # Test error structure
        error_dict = error.to_dict()
        assert "error_type" in error_dict
        assert "message" in error_dict
        assert "errors" in error_dict
        assert "error_codes" in error_dict
        assert "context" in error_dict

    def test_error_context_information(self):
        """Test that error context provides useful debugging information."""
        with pytest.raises(ValidationError) as exc_info:
            self.matcher.infer_kind("X-invalid-prefix")

        error = exc_info.value
        context = error.context

        assert "object_id" in context
        assert "extracted_prefix" in context
        assert "valid_prefixes" in context
        assert context["object_id"] == "X-invalid-prefix"
        assert context["extracted_prefix"] == "X-"
        assert "P-" in context["valid_prefixes"]
        assert "E-" in context["valid_prefixes"]
        assert "F-" in context["valid_prefixes"]
        assert "T-" in context["valid_prefixes"]
