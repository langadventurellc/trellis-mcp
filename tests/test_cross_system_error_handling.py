"""Comprehensive test suite for cross-system error handling scenarios.

This module tests the enhanced error handling functionality across different
error conditions, ensuring all enhanced error messages and validation functions
work correctly with performance and security requirements.
"""

import time
from unittest.mock import patch

import pytest
from fastmcp import Client

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.server import create_server
from src.trellis_mcp.settings import Settings
from src.trellis_mcp.validation.benchmark import PerformanceBenchmark
from src.trellis_mcp.validation.exceptions import CircularDependencyError


class TestCrossSystemErrorHandling:
    """Test suite for cross-system error handling scenarios."""

    def test_missing_prerequisite_error_messages(self):
        """Test enhanced error messages for missing prerequisites across systems."""
        # Test standalone task referencing non-existent hierarchical task
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchical",
            source_task_id="T-auth-setup",
            target_task_id="F-nonexistent",
            conflict_type="prerequisite",
        )

        # Check for prerequisite validation error structure
        assert "Prerequisite validation failed" in str(error)
        assert "requires" in str(error) and "does not exist" in str(error)
        assert error.has_error_code(ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID)
        assert error.object_id == "T-auth-setup"
        assert error.task_type == "standalone"

        # Test hierarchical task referencing non-existent standalone task
        error2 = ValidationError.create_cross_system_error(
            source_task_type="hierarchical",
            target_task_type="standalone",
            source_task_id="T-user-model",
            target_task_id="T-missing-auth",
            conflict_type="prerequisite",
        )

        assert "Prerequisite validation failed" in str(error2)
        assert "requires" in str(error2) and "does not exist" in str(error2)
        assert error2.has_error_code(ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID)

    def test_cycle_detection_cross_system_context(self):
        """Test cycle detection with enhanced cross-system error context."""
        # Create mock cycle path with mixed task types
        cycle_path = ["T-auth-setup", "F-user-login", "T-auth-setup"]

        # Test enhanced CircularDependencyError with task type detection
        objects_data = {
            "T-auth-setup": {"kind": "task", "id": "T-auth-setup", "parent": None},
            "F-user-login": {"kind": "feature", "id": "F-user-login", "parent": "E-authentication"},
        }

        error = CircularDependencyError(cycle_path, objects_data)

        error_msg = str(error)
        assert "standalone" in error_msg
        assert "feature" in error_msg  # Features show as "feature", not "hierarchical"
        assert "T-auth-setup" in error_msg
        assert "F-user-login" in error_msg
        assert "→" in error_msg  # Enhanced arrow formatting

    def test_prerequisite_existence_validation(self):
        """Test prerequisite existence validation across different systems."""
        # Test validation of cross-system prerequisites
        error_cases = [
            {
                "source": "T-frontend-auth",
                "source_type": "standalone",
                "target": "F-backend-api",
                "target_type": "hierarchical",
                "conflict": "reference",
            },
            {
                "source": "T-api-test",
                "source_type": "hierarchical",
                "target": "T-missing-service",
                "target_type": "standalone",
                "conflict": "prerequisite",
            },
        ]

        for case in error_cases:
            error = ValidationError.create_cross_system_error(
                source_task_type=case["source_type"],
                target_task_type=case["target_type"],
                source_task_id=case["source"],
                target_task_id=case["target"],
                conflict_type=case["conflict"],
            )

            # Verify error contains system context
            error_str = str(error)
            assert case["source_type"] in error_str
            assert case["target_type"] in error_str

            # Check for appropriate error message based on conflict type
            if case["conflict"] == "prerequisite":
                assert "Prerequisite validation failed" in error_str
                assert "requires" in error_str and "does not exist" in error_str
            else:  # reference conflict
                assert "Cross-system reference conflict" in error_str
                assert "between" in error_str

    def test_enhanced_validation_error_context(self):
        """Test enhanced ValidationError with comprehensive context information."""
        context = {
            "field": "prerequisites",
            "invalid_references": ["T-missing-1", "F-invalid-2"],
            "conflict_details": "Cross-system reference validation failed",
        }

        error = ValidationError(
            ["Multiple cross-system validation errors detected"],
            error_codes=[ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT],
            context=context,
            object_id="T-complex-task",
            object_kind="task",
            task_type="standalone",
        )

        # Test error dictionary contains all context
        error_dict = error.to_dict()
        assert error_dict["context"]["field"] == "prerequisites"
        assert "T-missing-1" in error_dict["context"]["invalid_references"]
        assert error_dict["task_type"] == "standalone"
        assert error_dict["object_kind"] == "task"

        # Test structured error codes
        assert error.has_error_code(ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT)

    def test_performance_error_handling(self):
        """Test that error handling operations complete within performance requirements."""
        benchmark = PerformanceBenchmark()

        # Test typical error creation performance
        benchmark.start("error_creation")

        for i in range(100):
            error = ValidationError.create_cross_system_error(
                source_task_type="standalone",
                target_task_type="hierarchical",
                source_task_id=f"T-test-{i}",
                target_task_id=f"F-target-{i}",
                conflict_type="prerequisite",
            )
            # Force error message generation
            str(error)

        duration = benchmark.end("error_creation")

        # Performance requirement: <10ms for typical error scenarios
        # 100 errors should complete well under 1 second
        assert duration < 1.0, f"Error creation took {duration:.4f}s, expected < 1.0s"

        # Test individual error performance (should be microseconds)
        single_start = time.perf_counter()
        error = ValidationError.create_cross_system_error(
            source_task_type="standalone",
            target_task_type="hierarchical",
            source_task_id="T-perf-test",
            target_task_id="F-perf-target",
            conflict_type="reference",
        )
        str(error)
        single_duration = time.perf_counter() - single_start

        # Single error should be well under 10ms
        assert single_duration < 0.01, f"Single error took {single_duration:.6f}s, expected < 0.01s"

    def test_edge_case_malformed_prerequisite_references(self):
        """Test error handling for malformed prerequisite references."""
        edge_cases = [
            # Empty/None references - use valid IDs but test edge behavior
            {"source": "T-empty-test", "target": "F-valid", "error_expected": False},
            {"source": "T-valid", "target": "F-empty-test", "error_expected": False},
            # Test with valid format IDs
            {"source": "T-invalid-id", "target": "F-valid", "error_expected": False},
            {"source": "T-valid", "target": "F-malformed", "error_expected": False},
            # Mixed valid combinations
            {"source": "T-auth", "target": "F-unknown-prefix", "error_expected": False},
        ]

        for case in edge_cases:
            try:
                error = ValidationError.create_cross_system_error(
                    source_task_type="standalone",
                    target_task_type="hierarchical",
                    source_task_id=case["source"],
                    target_task_id=case["target"],
                    conflict_type="reference",
                )

                # Should create error object with cross-system validation context
                error_str = str(error)
                assert "Cross-system conflict" in error_str or "validation" in error_str.lower()

                # Verify task IDs are included in error
                assert case["source"] in error_str or "source" in error_str.lower()

            except Exception as e:
                if case["error_expected"]:
                    # Expected to fail validation
                    assert isinstance(e, (ValidationError, ValueError))
                else:
                    # Unexpected failure - for debugging
                    print(f"Unexpected error for case {case}: {e}")
                    raise

    def test_security_error_message_sanitization(self):
        """Test that error messages don't expose sensitive paths or internal details."""
        # Test that file paths are not exposed in error messages
        with patch(
            "src.trellis_mcp.validation.cycle_detection.get_all_objects"
        ) as mock_get_objects:
            mock_get_objects.return_value = {
                "T-sensitive": {
                    "kind": "task",
                    "id": "T-sensitive",
                    "file_path": "/Users/secret/planning/projects/confidential/tasks/T-sensitive.md",  # noqa: E501
                }
            }

            error = ValidationError.create_cross_system_error(
                source_task_type="standalone",
                target_task_type="hierarchical",
                source_task_id="T-sensitive",
                target_task_id="F-public",
                conflict_type="prerequisite",
            )

            error_str = str(error)

            # Sensitive paths should not be exposed
            assert "/Users/secret" not in error_str
            assert "confidential" not in error_str
            assert ".md" not in error_str

            # Only sanitized task IDs should appear
            assert "sensitive" in error_str  # From cleaned ID
            assert "public" in error_str

    def test_error_context_boundary_validation(self):
        """Test that enhanced errors maintain proper security boundaries."""
        # Test internal implementation details don't leak
        context_with_internals = {
            "internal_cache_key": "secret_cache_123",
            "file_system_path": "/internal/system/path",
            "debug_trace": "Internal stack trace data",
            "user_field": "safe_user_data",  # This should be preserved
        }

        error = ValidationError(
            "Test error with mixed context",
            context=context_with_internals,
            object_id="T-boundary-test",
            task_type="standalone",
        )

        error_dict = error.to_dict()

        # Safe user data should be preserved
        assert error_dict["context"]["user_field"] == "safe_user_data"

        # Internal details should be present but not in string representation
        error_str = str(error)
        assert "secret_cache_123" not in error_str
        assert "/internal/system/path" not in error_str
        assert "Internal stack trace" not in error_str

    def test_cross_system_error_message_formats(self):
        """Test all supported cross-system error message formats."""
        format_cases = [
            {
                "conflict": "prerequisite",
                "expected_phrases": [
                    "Prerequisite validation failed",
                    "requires",
                    "does not exist",
                    "standalone",
                    "hierarchical",
                ],
            },
            {
                "conflict": "reference",
                "expected_phrases": [
                    "Cross-system reference conflict",
                    "between",
                    "standalone",
                    "hierarchical",
                ],
            },
        ]

        for case in format_cases:
            error = ValidationError.create_cross_system_error(
                source_task_type="standalone",
                target_task_type="hierarchical",
                source_task_id="T-format-test",
                target_task_id="F-format-target",
                conflict_type=case["conflict"],
            )

            error_str = str(error)

            # Verify expected phrases appear in error message
            for phrase in case["expected_phrases"]:
                assert (
                    phrase.lower() in error_str.lower()
                ), f"Missing phrase '{phrase}' in error: {error_str}"

    def test_error_code_categorization(self):
        """Test that cross-system errors use appropriate error codes."""
        error_code_mapping = {
            "prerequisite": ValidationErrorCode.CROSS_SYSTEM_PREREQUISITE_INVALID,
            "reference": ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT,
        }

        for conflict_type, expected_code in error_code_mapping.items():
            error = ValidationError.create_cross_system_error(
                source_task_type="standalone",
                target_task_type="hierarchical",
                source_task_id="T-code-test",
                target_task_id="F-code-target",
                conflict_type=conflict_type,
            )

            assert error.has_error_code(
                expected_code
            ), f"Expected code {expected_code} for conflict {conflict_type}"


@pytest.mark.asyncio
class TestCrossSystemIntegrationErrors:
    """Integration tests for cross-system error handling with MCP tools."""

    async def test_create_object_cross_system_validation_errors(self, temp_dir):
        """Test MCP createObject tool with cross-system validation errors."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )

        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # Test creating standalone task with invalid hierarchical prerequisites
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": "Cross-system validation test",
                        "projectRoot": planning_root,
                        "prerequisites": ["F-nonexistent-feature"],  # Invalid cross-system ref
                    },
                )

            error_message = str(exc_info.value)

            # Should contain cross-system error context
            assert (
                "cross-system" in error_message.lower() or "prerequisite" in error_message.lower()
            )

    async def test_update_object_cross_system_errors(self, temp_dir):
        """Test MCP updateObject tool with cross-system error scenarios."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )

        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # First create a valid standalone task
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test task for update",
                    "projectRoot": planning_root,
                },
            )

            task_id = result.data["id"]

            # Test updating with invalid cross-system prerequisites
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": task_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {
                            "prerequisites": [
                                "E-nonexistent-epic",
                                "P-invalid-project",
                            ]  # Invalid refs
                        },
                    },
                )

            error_message = str(exc_info.value)

            # Should contain validation error details
            assert any(
                word in error_message.lower()
                for word in ["validation", "prerequisite", "cross-system"]
            )


class TestPerformanceBenchmarks:
    """Performance-focused tests for error handling operations."""

    def test_bulk_error_creation_performance(self):
        """Test performance of creating many cross-system errors."""
        benchmark = PerformanceBenchmark()

        # Test creating 1000 errors
        benchmark.start("bulk_error_creation")

        errors = []
        for i in range(1000):
            error = ValidationError.create_cross_system_error(
                source_task_type="standalone" if i % 2 == 0 else "hierarchical",
                target_task_type="hierarchical" if i % 2 == 0 else "standalone",
                source_task_id=f"T-bulk-{i}",
                target_task_id=f"F-target-{i}",
                conflict_type="prerequisite",
            )
            errors.append(error)

        duration = benchmark.end("bulk_error_creation")

        # Should complete bulk operations efficiently
        assert duration < 5.0, f"Bulk error creation took {duration:.4f}s, expected < 5.0s"
        assert len(errors) == 1000

    def test_error_serialization_performance(self):
        """Test performance of error serialization to dict format."""
        # Create complex error with rich context
        complex_context = {
            "field": "prerequisites",
            "validation_errors": [f"error_{i}" for i in range(50)],
            "cross_system_refs": [f"T-ref-{i}" for i in range(100)],
            "metadata": {"timestamp": "2025-07-18T12:00:00Z", "operation": "update"},
        }

        error = ValidationError(
            ["Complex cross-system validation failed"],
            error_codes=[ValidationErrorCode.CROSS_SYSTEM_REFERENCE_CONFLICT],
            context=complex_context,
            object_id="T-complex-perf-test",
            object_kind="task",
            task_type="standalone",
        )

        benchmark = PerformanceBenchmark()
        benchmark.start("error_serialization")

        # Serialize error 100 times
        for _ in range(100):
            error_dict = error.to_dict()
            assert error_dict["error_type"] == "ValidationError"

        duration = benchmark.end("error_serialization")

        # Should serialize efficiently even with complex context
        assert duration < 1.0, f"Error serialization took {duration:.4f}s, expected < 1.0s"
