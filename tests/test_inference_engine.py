"""Tests for the Kind Inference Engine API.

This module provides comprehensive tests for the main KindInferenceEngine
including component integration, error handling, cache behavior, and
API functionality validation.
"""

import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.inference import infer_kind, infer_with_validation
from src.trellis_mcp.inference.cache import InferenceResult
from src.trellis_mcp.inference.engine import ExtendedInferenceResult, KindInferenceEngine
from src.trellis_mcp.inference.validator import ValidationResult


class TestKindInferenceEngine:
    """Test KindInferenceEngine class functionality."""

    def test_engine_initialization_success(self):
        """Test successful engine initialization with valid project root."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            assert engine.project_root == Path(temp_dir)
            assert engine.pattern_matcher is not None
            assert engine.path_builder is not None
            assert engine.validator is not None
            assert engine.cache is not None

    def test_engine_initialization_invalid_root(self):
        """Test engine initialization fails with invalid project root."""
        with pytest.raises(ValidationError) as exc_info:
            KindInferenceEngine("/nonexistent/path")

        assert "Project root does not exist" in str(exc_info.value)
        assert ValidationErrorCode.INVALID_FIELD in exc_info.value.error_codes

    def test_engine_initialization_invalid_cache_size(self):
        """Test engine initialization fails with invalid cache size."""
        with TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError) as exc_info:
                KindInferenceEngine(temp_dir, cache_size=0)

            assert "Cache size must be positive" in str(exc_info.value)


class TestInferKindMethod:
    """Test infer_kind() method functionality."""

    def test_infer_kind_basic_patterns(self):
        """Test basic kind inference for all object types."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Mock pattern matcher to avoid file system dependencies
            with (
                patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern,
                patch.object(engine.validator, "validate_object_structure") as mock_validator,
            ):

                mock_pattern.return_value = "project"
                mock_validator.return_value = ValidationResult.success()

                result = engine.infer_kind("P-test-project")
                assert result == "project"

                mock_pattern.assert_called_once_with("P-test-project")
                mock_validator.assert_called_once_with("project", "P-test-project")

    def test_infer_kind_cache_hit(self):
        """Test cache hit behavior in infer_kind."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Pre-populate cache and mock cache validation
            cached_result = InferenceResult.create("T-test", "task", True)

            with (
                patch.object(engine.cache, "get") as mock_cache_get,
                patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern,
            ):

                mock_cache_get.return_value = cached_result

                result = engine.infer_kind("T-test")
                assert result == "task"

                # Pattern matcher should not be called on cache hit
                mock_pattern.assert_not_called()

    def test_infer_kind_without_validation(self):
        """Test infer_kind with validation disabled."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with (
                patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern,
                patch.object(engine.validator, "validate_object_structure") as mock_validator,
            ):

                mock_pattern.return_value = "epic"

                result = engine.infer_kind("E-test-epic", validate=False)
                assert result == "epic"

                # Validator should not be called when validation disabled
                mock_validator.assert_not_called()

    def test_infer_kind_validation_failure(self):
        """Test infer_kind handles validation failures."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with (
                patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern,
                patch.object(engine.validator, "validate_object_structure") as mock_validator,
            ):

                mock_pattern.return_value = "feature"
                mock_validator.return_value = ValidationResult.failure(errors=["File not found"])

                with pytest.raises(ValidationError) as exc_info:
                    engine.infer_kind("F-nonexistent")

                assert "File not found" in str(exc_info.value)
                assert ValidationErrorCode.INVALID_FIELD in exc_info.value.error_codes

    def test_infer_kind_invalid_input(self):
        """Test infer_kind input validation."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Test None input
            with pytest.raises(ValidationError) as exc_info:
                engine.infer_kind(None)  # type: ignore
            assert "Object ID cannot be empty" in str(exc_info.value)

            # Test empty string
            with pytest.raises(ValidationError) as exc_info:
                engine.infer_kind("")
            assert "Object ID cannot be empty" in str(exc_info.value)

            # Test non-string input
            with pytest.raises(ValidationError) as exc_info:
                engine.infer_kind(123)  # type: ignore
            assert "Object ID must be a string" in str(exc_info.value)


class TestInferWithValidationMethod:
    """Test infer_with_validation() method functionality."""

    def test_infer_with_validation_success(self):
        """Test successful inference with validation."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with (
                patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern,
                patch.object(engine.validator, "validate_object_structure") as mock_validator,
            ):

                mock_pattern.return_value = "task"
                validation_result = ValidationResult.success()
                mock_validator.return_value = validation_result

                result = engine.infer_with_validation("T-test-task")

                assert isinstance(result, ExtendedInferenceResult)
                assert result.object_id == "T-test-task"
                assert result.inferred_kind == "task"
                assert result.is_valid is True
                assert result.validation_result == validation_result
                assert result.inference_time_ms > 0
                assert result.cache_hit is False

    def test_infer_with_validation_cache_hit(self):
        """Test cache hit in infer_with_validation."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Pre-populate cache and mock cache validation
            validation_result = ValidationResult.success()
            cached_result = InferenceResult.create("P-test", "project", True, validation_result)

            with patch.object(engine.cache, "get") as mock_cache_get:
                mock_cache_get.return_value = cached_result

                result = engine.infer_with_validation("P-test")

                assert result.cache_hit is True
                assert result.inferred_kind == "project"
                assert result.is_valid is True

    def test_infer_with_validation_pattern_error(self):
        """Test pattern matching error handling in infer_with_validation."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern:
                mock_pattern.side_effect = ValidationError(
                    errors=["Invalid pattern"], error_codes=[ValidationErrorCode.INVALID_FORMAT]
                )

                result = engine.infer_with_validation("INVALID-ID")

                assert result.is_valid is False
                assert result.inferred_kind == ""
                assert result.validation_result is not None
                assert len(result.validation_result.errors) > 0

    def test_infer_with_validation_invalid_input(self):
        """Test input validation in infer_with_validation."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with pytest.raises(ValidationError) as exc_info:
                engine.infer_with_validation("")
            assert "Object ID must be a non-empty string" in str(exc_info.value)


class TestValidateObjectMethod:
    """Test validate_object() method functionality."""

    def test_validate_object_with_expected_kind(self):
        """Test validation with explicitly provided expected kind."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with patch.object(engine.validator, "validate_object_structure") as mock_validator:
                validation_result = ValidationResult.success()
                mock_validator.return_value = validation_result

                result = engine.validate_object("T-test", expected_kind="task")

                assert result == validation_result
                mock_validator.assert_called_once_with("task", "T-test")

    def test_validate_object_inferred_kind(self):
        """Test validation with inferred kind."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with (
                patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern,
                patch.object(engine.validator, "validate_object_structure") as mock_validator,
            ):

                mock_pattern.return_value = "epic"
                validation_result = ValidationResult.success()
                mock_validator.return_value = validation_result

                result = engine.validate_object("E-test")

                assert result == validation_result
                mock_pattern.assert_called_once_with("E-test")
                mock_validator.assert_called_once_with("epic", "E-test")

    def test_validate_object_inference_failure(self):
        """Test validation when kind inference fails."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            with patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern:
                mock_pattern.side_effect = ValidationError(
                    errors=["Pattern error"], error_codes=[ValidationErrorCode.INVALID_FORMAT]
                )

                result = engine.validate_object("INVALID")

                assert result.is_valid is False
                assert "Pattern inference failed" in result.errors[0]


class TestCacheIntegration:
    """Test cache integration and performance."""

    def test_cache_statistics(self):
        """Test cache statistics retrieval."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir, cache_size=100)

            stats = engine.get_cache_stats()

            assert isinstance(stats, dict)
            assert "size" in stats
            assert "max_size" in stats
            assert stats["max_size"] == 100
            assert "hits" in stats
            assert "misses" in stats

    def test_cache_clear(self):
        """Test cache clearing functionality."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Add something to cache
            result = InferenceResult.create("T-test", "task", True)
            engine.cache.put("T-test", result)

            stats_before = engine.get_cache_stats()
            assert stats_before["size"] > 0

            engine.clear_cache()

            stats_after = engine.get_cache_stats()
            assert stats_after["size"] == 0


class TestConcurrentAccess:
    """Test thread safety and concurrent access."""

    def test_concurrent_inference(self):
        """Test concurrent inference operations."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)
            results = []
            errors = []

            def worker(object_id: str):
                try:
                    with (
                        patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern,
                        patch.object(
                            engine.validator, "validate_object_structure"
                        ) as mock_validator,
                    ):

                        mock_pattern.return_value = "task"
                        mock_validator.return_value = ValidationResult.success()

                        result = engine.infer_kind(object_id)
                        results.append(result)
                except Exception as e:
                    errors.append(e)

            # Start multiple threads
            threads = []
            for i in range(10):
                thread = threading.Thread(target=worker, args=[f"T-test-{i}"])
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            # Check results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 10
            assert all(result == "task" for result in results)


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_component_integration_errors(self):
        """Test error handling across component integration."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Test pattern matcher error propagation
            with patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern:
                mock_pattern.side_effect = ValidationError(
                    errors=["Custom pattern error"],
                    error_codes=[ValidationErrorCode.INVALID_FORMAT],
                    context={"test": "context"},
                )

                with pytest.raises(ValidationError) as exc_info:
                    engine.infer_kind("TEST-ID")

                # Error should be propagated with original context
                assert "Custom pattern error" in str(exc_info.value)
                assert exc_info.value.context["test"] == "context"


class TestConvenienceFunctions:
    """Test package-level convenience functions."""

    def test_convenience_infer_kind(self):
        """Test convenience infer_kind function."""
        with TemporaryDirectory() as temp_dir:
            with patch("src.trellis_mcp.inference.KindInferenceEngine") as mock_engine_class:
                mock_engine = Mock()
                mock_engine.infer_kind.return_value = "project"
                mock_engine_class.return_value = mock_engine

                result = infer_kind("P-test", temp_dir, validate=False)

                assert result == "project"
                mock_engine_class.assert_called_once_with(temp_dir)
                mock_engine.infer_kind.assert_called_once_with("P-test", False)

    def test_convenience_infer_with_validation(self):
        """Test convenience infer_with_validation function."""
        with TemporaryDirectory() as temp_dir:
            with patch("src.trellis_mcp.inference.KindInferenceEngine") as mock_engine_class:
                mock_engine = Mock()
                expected_result = ExtendedInferenceResult(
                    object_id="T-test", inferred_kind="task", is_valid=True
                )
                mock_engine.infer_with_validation.return_value = expected_result
                mock_engine_class.return_value = mock_engine

                result = infer_with_validation("T-test", temp_dir)

                assert result == expected_result
                mock_engine_class.assert_called_once_with(temp_dir)
                mock_engine.infer_with_validation.assert_called_once_with("T-test")


class TestIntegrationWithExistingComponents:
    """Test integration with existing Trellis MCP components."""

    def test_integration_with_real_pattern_matcher(self):
        """Test integration with actual PatternMatcher component."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Test with actual pattern matcher (no validation to avoid file dependencies)
            result = engine.infer_kind("P-test-project", validate=False)
            assert result == "project"

            result = engine.infer_kind("E-test-epic", validate=False)
            assert result == "epic"

            result = engine.infer_kind("F-test-feature", validate=False)
            assert result == "feature"

            result = engine.infer_kind("T-test-task", validate=False)
            assert result == "task"

    def test_integration_error_code_consistency(self):
        """Test that error codes are consistent with existing validation system."""
        with TemporaryDirectory() as temp_dir:
            engine = KindInferenceEngine(temp_dir)

            # Test invalid ID format
            with pytest.raises(ValidationError) as exc_info:
                engine.infer_kind("INVALID-FORMAT", validate=False)

            # Should use existing ValidationErrorCode values
            assert ValidationErrorCode.INVALID_FORMAT in exc_info.value.error_codes
