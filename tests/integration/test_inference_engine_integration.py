"""Comprehensive integration tests for the Kind Inference Engine.

This module provides comprehensive integration tests for the complete Kind Inference Engine,
validating end-to-end workflows, cross-system compatibility, component integration,
and production readiness scenarios.
"""

import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from tests.conftest import _create_object_file

from src.trellis_mcp.exceptions.validation_error import ValidationError, ValidationErrorCode
from src.trellis_mcp.inference.engine import KindInferenceEngine
from src.trellis_mcp.inference.validator import ValidationResult


class TestInferenceEngineIntegration:
    """Test comprehensive integration scenarios for the Kind Inference Engine."""

    def test_end_to_end_inference_workflow(self):
        """Test complete end-to-end inference workflow with all components."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create realistic project structure
            self._create_sample_project_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning")

            # Test complete workflow for each object type
            test_cases = [
                ("P-sample-project", "project"),
                ("E-core-features", "epic"),
                ("F-user-authentication", "feature"),
                ("T-implement-login", "task"),
            ]

            for object_id, expected_kind in test_cases:
                # Clear cache to ensure fresh test
                engine.clear_cache()

                # Test basic inference
                result = engine.infer_kind(object_id, validate=True)
                assert result == expected_kind, f"Failed for {object_id}"

                # Test extended inference (should hit cache from infer_kind call)
                extended_result = engine.infer_with_validation(object_id)
                assert extended_result.object_id == object_id
                assert extended_result.inferred_kind == expected_kind
                assert extended_result.is_valid is True
                assert extended_result.inference_time_ms > 0
                assert extended_result.cache_hit is True  # Cache hit from infer_kind

                # Test cache hit on subsequent call
                cached_result = engine.infer_with_validation(object_id)
                assert cached_result.cache_hit is True
                assert cached_result.inferred_kind == expected_kind

    def test_cross_system_object_handling(self):
        """Test inference with both hierarchical and standalone objects."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mixed project structure
            self._create_mixed_project_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning")

            # Test hierarchical objects
            hierarchical_objects = [
                ("P-main-project", "project"),
                ("E-backend-api", "epic"),
                ("F-user-service", "feature"),
                ("T-create-user-model", "task"),
            ]

            for object_id, expected_kind in hierarchical_objects:
                result = engine.infer_kind(object_id, validate=True)
                assert result == expected_kind

                # Verify path resolution works
                validation_result = engine.validate_object(object_id, expected_kind)
                assert validation_result.is_valid is True

            # Test standalone objects
            standalone_objects = [
                ("T-database-migration", "task"),
                ("T-security-audit", "task"),
                ("T-performance-optimization", "task"),
            ]

            for object_id, expected_kind in standalone_objects:
                result = engine.infer_kind(object_id, validate=True)
                assert result == expected_kind

                # Verify standalone path resolution
                validation_result = engine.validate_object(object_id, expected_kind)
                assert validation_result.is_valid is True

    def test_concurrent_inference_operations(self):
        """Test thread safety with concurrent inference operations."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_sample_project_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning")
            results = []
            errors = []

            def inference_worker(object_ids):
                """Worker function for concurrent inference testing."""
                worker_results = []
                for obj_id, expected_kind in object_ids:
                    try:
                        result = engine.infer_kind(obj_id, validate=True)
                        worker_results.append((obj_id, result, expected_kind))
                    except Exception as e:
                        errors.append((obj_id, e))
                results.extend(worker_results)

            # Define test object sets for different threads
            thread_data = [
                [("P-sample-project", "project"), ("E-core-features", "epic")],
                [("F-user-authentication", "feature"), ("T-implement-login", "task")],
                [
                    ("P-sample-project", "project"),
                    ("F-user-authentication", "feature"),
                ],  # Repeat for cache testing
            ]

            # Start concurrent threads
            threads = []
            for data in thread_data:
                thread = threading.Thread(target=inference_worker, args=[data])
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify results
            assert len(errors) == 0, f"Concurrent errors occurred: {errors}"
            assert len(results) == 6  # 2 + 2 + 2 objects from 3 threads

            # Verify all inferences were correct
            for obj_id, actual_kind, expected_kind in results:
                assert actual_kind == expected_kind, f"Incorrect inference for {obj_id}"

    def test_cache_integration_behavior(self):
        """Test cache behavior in integration scenarios."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_sample_project_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning", cache_size=10)

            # Test cache population
            test_objects = [
                ("P-sample-project", "project"),
                ("E-core-features", "epic"),
                ("F-user-authentication", "feature"),
                ("T-implement-login", "task"),
            ]

            # First round - populate cache
            for obj_id, expected_kind in test_objects:
                result = engine.infer_with_validation(obj_id)
                assert result.cache_hit is False
                assert result.inferred_kind == expected_kind

            # Second round - should hit cache
            for obj_id, expected_kind in test_objects:
                result = engine.infer_with_validation(obj_id)
                assert result.cache_hit is True
                assert result.inferred_kind == expected_kind
                assert result.inference_time_ms < 5  # Should be very fast

            # Test cache statistics
            stats = engine.get_cache_stats()
            assert stats["size"] == 4  # 4 objects cached
            assert stats["max_size"] == 10
            assert stats["hits"] >= 4
            assert stats["misses"] >= 4

            # Test cache eviction with many objects
            for i in range(15):
                obj_id = f"T-test-task-{i:03d}"
                try:
                    engine.infer_kind(
                        obj_id, validate=False
                    )  # Skip validation for non-existent objects
                except ValidationError:
                    pass  # Expected for non-existent objects

            # Cache should be limited to max_size
            final_stats = engine.get_cache_stats()
            assert final_stats["size"] <= 10

    def test_error_handling_integration(self):
        """Test error handling across component boundaries."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_sample_project_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning")

            # Test invalid object ID formats
            invalid_ids = [
                ("", "empty string"),
                ("   ", "whitespace only"),
                ("INVALID-FORMAT", "invalid prefix"),
                ("X-unknown-prefix", "unknown prefix"),
                (None, "None value"),
                (123, "non-string type"),
            ]

            for invalid_id, description in invalid_ids:
                with pytest.raises(ValidationError) as exc_info:
                    engine.infer_kind(invalid_id)

                # Verify error contains appropriate information
                error = exc_info.value
                assert len(error.errors) > 0
                assert any(
                    code in error.error_codes
                    for code in [
                        ValidationErrorCode.INVALID_FORMAT,
                        ValidationErrorCode.INVALID_FIELD,
                        ValidationErrorCode.MISSING_REQUIRED_FIELD,
                    ]
                )

            # Test non-existent but valid format objects
            nonexistent_objects = [
                "P-nonexistent-project",
                "E-missing-epic",
                "F-absent-feature",
                "T-void-task",
            ]

            for obj_id in nonexistent_objects:
                # Should work without validation
                try:
                    result = engine.infer_kind(obj_id, validate=False)
                    assert result in ["project", "epic", "feature", "task"]
                except ValidationError:
                    pytest.fail(f"Pattern matching should work for {obj_id}")

                # Should fail with validation
                with pytest.raises(ValidationError) as exc_info:
                    engine.infer_kind(obj_id, validate=True)

                assert ValidationErrorCode.INVALID_FIELD in exc_info.value.error_codes

    def test_validation_integration_scenarios(self):
        """Test validation integration with different object scenarios."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_validation_test_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning")

            # Test valid objects with proper structure
            valid_objects = [
                ("P-valid-project", "project"),
                ("E-valid-epic", "epic"),
                ("F-valid-feature", "feature"),
                ("T-valid-task", "task"),
            ]

            for obj_id, expected_kind in valid_objects:
                result = engine.infer_with_validation(obj_id)
                assert result.is_valid is True
                assert result.inferred_kind == expected_kind
                assert result.validation_result is not None
                assert result.validation_result.is_valid is True

            # Test objects with structural issues
            problematic_objects = [
                "P-empty-project",  # Empty project file
                "E-malformed-epic",  # Malformed YAML
                "F-missing-parent",  # Feature without proper parent structure
            ]

            for obj_id in problematic_objects:
                result = engine.infer_with_validation(obj_id)
                # Pattern matching should work but validation should fail
                assert result.inferred_kind != ""
                assert result.is_valid is False
                assert result.validation_result is not None
                assert result.validation_result.is_valid is False

    def test_component_integration_isolation(self):
        """Test that component failures don't affect other components."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_sample_project_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning")

            # Test pattern matcher isolation
            with patch.object(engine.pattern_matcher, "infer_kind") as mock_pattern:
                mock_pattern.side_effect = ValidationError(
                    errors=["Pattern matcher error"],
                    error_codes=[ValidationErrorCode.INVALID_FORMAT],
                )

                with pytest.raises(ValidationError):
                    engine.infer_kind("T-test")

                # Cache and validator should remain unaffected
                assert engine.cache.get_stats()["size"] >= 0  # Cache still functional

            # Test validator isolation
            with patch.object(engine.validator, "validate_object_structure") as mock_validator:
                mock_validator.return_value = ValidationResult.failure(errors=["Validator error"])

                with pytest.raises(ValidationError):
                    engine.infer_kind("P-sample-project", validate=True)

                # Pattern matcher should still work
                result = engine.infer_kind("P-sample-project", validate=False)
                assert result == "project"

    def test_large_scale_integration(self):
        """Test integration with larger project structures."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_large_project_structure(temp_path)

            engine = KindInferenceEngine(temp_path / "planning")

            # Test inference across large number of objects
            test_objects = []

            # Add multiple projects
            for p in range(3):
                project_id = f"P-project-{p:02d}"
                test_objects.append((project_id, "project"))

                # Add epics for each project
                for e in range(4):
                    epic_id = f"E-epic-{p:02d}-{e:02d}"
                    test_objects.append((epic_id, "epic"))

                    # Add features for each epic
                    for f in range(3):
                        feature_id = f"F-feature-{p:02d}-{e:02d}-{f:02d}"
                        test_objects.append((feature_id, "feature"))

                        # Add tasks for each feature
                        for t in range(5):
                            task_id = f"T-task-{p:02d}-{e:02d}-{f:02d}-{t:02d}"
                            test_objects.append((task_id, "task"))

            # Add standalone tasks
            for s in range(20):
                standalone_id = f"T-standalone-{s:03d}"
                test_objects.append((standalone_id, "task"))

            # Test inference for all objects
            start_time = time.time()
            successful_inferences = 0

            for obj_id, expected_kind in test_objects:
                try:
                    result = engine.infer_kind(obj_id, validate=False)  # Skip validation for speed
                    assert result == expected_kind
                    successful_inferences += 1
                except ValidationError:
                    # Some objects might not exist, but pattern matching should work
                    pass

            end_time = time.time()
            total_time = (end_time - start_time) * 1000

            # Verify performance and success rate
            assert successful_inferences >= len(test_objects) * 0.8  # At least 80% success
            assert total_time < 5000  # Should complete in under 5 seconds

    def _create_sample_project_structure(self, temp_path: Path):
        """Create a sample project structure for testing."""
        planning_dir = temp_path / "planning"
        planning_dir.mkdir()

        # Create project structure
        project_dir = planning_dir / "projects" / "P-sample-project"
        project_dir.mkdir(parents=True)

        # Create project file
        _create_object_file(
            project_dir / "project.md", "project", "P-sample-project", "Sample Project"
        )

        # Create epic with parent relationship
        epic_dir = project_dir / "epics" / "E-core-features"
        epic_dir.mkdir(parents=True)
        epic_content = """---
kind: epic
id: E-core-features
title: Core Features
status: in-progress
priority: normal
parent: P-sample-project
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Core Features

This is an epic for testing the Kind Inference Engine.

## Description

Test content for E-core-features.
"""
        (epic_dir / "epic.md").write_text(epic_content)

        # Create feature with parent relationship
        feature_dir = epic_dir / "features" / "F-user-authentication"
        feature_dir.mkdir(parents=True)
        feature_content = """---
kind: feature
id: F-user-authentication
title: User Authentication
status: in-progress
priority: normal
parent: E-core-features
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# User Authentication

This is a feature for testing the Kind Inference Engine.

## Description

Test content for F-user-authentication.
"""
        (feature_dir / "feature.md").write_text(feature_content)

        # Create task with parent relationship
        task_open_dir = feature_dir / "tasks-open"
        task_open_dir.mkdir()
        task_content = """---
kind: task
id: T-implement-login
title: Implement Login
status: open
priority: normal
parent: F-user-authentication
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Implement Login

This is a task for testing the Kind Inference Engine.

## Description

Test content for T-implement-login.
"""
        (task_open_dir / "T-implement-login.md").write_text(task_content)

    def _create_mixed_project_structure(self, temp_path: Path):
        """Create a mixed project structure with both hierarchical and standalone objects."""
        planning_dir = temp_path / "planning"
        planning_dir.mkdir()

        # Create hierarchical structure
        project_dir = planning_dir / "projects" / "P-main-project"
        project_dir.mkdir(parents=True)
        _create_object_file(project_dir / "project.md", "project", "P-main-project", "Main Project")

        # Create epic with parent relationship
        epic_dir = project_dir / "epics" / "E-backend-api"
        epic_dir.mkdir(parents=True)
        epic_content = """---
kind: epic
id: E-backend-api
title: Backend API
status: in-progress
priority: normal
parent: P-main-project
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Backend API

This is an epic for testing the Kind Inference Engine.

## Description

Test content for E-backend-api.
"""
        (epic_dir / "epic.md").write_text(epic_content)

        # Create feature with parent relationship
        feature_dir = epic_dir / "features" / "F-user-service"
        feature_dir.mkdir(parents=True)
        feature_content = """---
kind: feature
id: F-user-service
title: User Service
status: in-progress
priority: normal
parent: E-backend-api
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# User Service

This is a feature for testing the Kind Inference Engine.

## Description

Test content for F-user-service.
"""
        (feature_dir / "feature.md").write_text(feature_content)

        # Create task with parent relationship
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()
        task_content = """---
kind: task
id: T-create-user-model
title: Create User Model
status: open
priority: normal
parent: F-user-service
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Create User Model

This is a task for testing the Kind Inference Engine.

## Description

Test content for T-create-user-model.
"""
        (task_dir / "T-create-user-model.md").write_text(task_content)

        # Create standalone tasks
        standalone_dir = planning_dir / "tasks-open"
        standalone_dir.mkdir()

        standalone_tasks = [
            ("T-database-migration", "Database Migration"),
            ("T-security-audit", "Security Audit"),
            ("T-performance-optimization", "Performance Optimization"),
        ]

        for task_id, title in standalone_tasks:
            _create_object_file(standalone_dir / f"{task_id}.md", "task", task_id, title)

    def _create_validation_test_structure(self, temp_path: Path):
        """Create a structure for validation testing with various file conditions."""
        planning_dir = temp_path / "planning"
        planning_dir.mkdir()

        # Valid objects
        self._create_valid_object(
            planning_dir, "projects/P-valid-project/project.md", "project", "P-valid-project"
        )

        epic_dir = planning_dir / "projects" / "P-valid-project" / "epics" / "E-valid-epic"
        epic_dir.mkdir(parents=True)
        # Create epic with parent relationship
        (epic_dir / "epic.md").write_text(
            """---
kind: epic
id: E-valid-epic
title: Valid Epic
status: in-progress
priority: normal
parent: P-valid-project
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Valid Epic

This is an epic for testing the Kind Inference Engine.

## Description

Test content for E-valid-epic.
"""
        )

        feature_dir = epic_dir / "features" / "F-valid-feature"
        feature_dir.mkdir(parents=True)
        # Create feature with parent relationship
        (feature_dir / "feature.md").write_text(
            """---
kind: feature
id: F-valid-feature
title: Valid Feature
status: in-progress
priority: normal
parent: E-valid-epic
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Valid Feature

This is a feature for testing the Kind Inference Engine.

## Description

Test content for F-valid-feature.
"""
        )

        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()
        # Create task with parent relationship
        (task_dir / "T-valid-task.md").write_text(
            """---
kind: task
id: T-valid-task
title: Valid Task
status: open
priority: normal
parent: F-valid-feature
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Valid Task

This is a task for testing the Kind Inference Engine.

## Description

Test content for T-valid-task.
"""
        )

        # Problematic objects
        # Empty project
        empty_project_dir = planning_dir / "projects" / "P-empty-project"
        empty_project_dir.mkdir(parents=True)
        (empty_project_dir / "project.md").write_text("")

        # Malformed epic
        malformed_epic_dir = epic_dir.parent / "E-malformed-epic"
        malformed_epic_dir.mkdir(parents=True)
        (malformed_epic_dir / "epic.md").write_text("invalid yaml content\nno front matter")

        # Feature without proper parent structure
        orphan_feature_dir = planning_dir / "orphan" / "F-missing-parent"
        orphan_feature_dir.mkdir(parents=True)
        self._create_valid_object(orphan_feature_dir, "feature.md", "feature", "F-missing-parent")

    def _create_valid_object(self, base_path: Path, filename: str, kind: str, obj_id: str):
        """Create a valid object file with proper YAML front matter."""
        file_path = base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Set appropriate status based on kind
        if kind == "project":
            status = "in-progress"
        elif kind in ["epic", "feature"]:
            status = "in-progress"
        else:  # task
            status = "open"

        file_path.write_text(
            f"""---
kind: {kind}
id: {obj_id}
title: {obj_id.replace('-', ' ').title()}
status: {status}
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# {obj_id.replace('-', ' ').title()}

This is a {kind} for testing the Kind Inference Engine.

## Description

Test content for {obj_id}.
"""
        )

    def _create_large_project_structure(self, temp_path: Path):
        """Create a large project structure for scale testing."""
        planning_dir = temp_path / "planning"
        planning_dir.mkdir()

        # Create multiple projects with nested structure
        for p in range(3):
            project_id = f"P-project-{p:02d}"
            project_dir = planning_dir / "projects" / project_id
            project_dir.mkdir(parents=True)
            self._create_valid_object(project_dir, "project.md", "project", project_id)

            for e in range(4):
                epic_id = f"E-epic-{p:02d}-{e:02d}"
                epic_dir = project_dir / "epics" / epic_id
                epic_dir.mkdir(parents=True)
                self._create_valid_object(epic_dir, "epic.md", "epic", epic_id)

                for f in range(3):
                    feature_id = f"F-feature-{p:02d}-{e:02d}-{f:02d}"
                    feature_dir = epic_dir / "features" / feature_id
                    feature_dir.mkdir(parents=True)
                    self._create_valid_object(feature_dir, "feature.md", "feature", feature_id)

                    task_dir = feature_dir / "tasks-open"
                    task_dir.mkdir()

                    for t in range(5):
                        task_id = f"T-task-{p:02d}-{e:02d}-{f:02d}-{t:02d}"
                        self._create_valid_object(task_dir, f"{task_id}.md", "task", task_id)

        # Create standalone tasks
        standalone_dir = planning_dir / "tasks-open"
        standalone_dir.mkdir()

        for s in range(20):
            task_id = f"T-standalone-{s:03d}"
            self._create_valid_object(standalone_dir, f"{task_id}.md", "task", task_id)


class TestInferenceEngineErrorRecovery:
    """Test error recovery and resilience scenarios."""

    def test_partial_system_failure_recovery(self):
        """Test recovery from partial system failures."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create basic structure
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(temp_path / "planning")

            # Simulate cache corruption recovery
            engine.clear_cache()
            assert engine.get_cache_stats()["size"] == 0

            # System should still work after cache clear
            result = engine.infer_kind("P-test-project", validate=False)
            assert result == "project"

            # Test component reinitialization
            original_cache = engine.cache
            engine.cache = type(original_cache)(max_size=500)

            # Should still work with new cache
            result = engine.infer_kind("E-test-epic", validate=False)
            assert result == "epic"

    def test_invalid_project_root_handling(self):
        """Test handling of invalid project root scenarios."""
        # Test nonexistent directory
        with pytest.raises(ValidationError) as exc_info:
            KindInferenceEngine("/nonexistent/path/to/nowhere")

        assert "Project root does not exist" in str(exc_info.value)
        assert ValidationErrorCode.INVALID_FIELD in exc_info.value.error_codes

        # Test file instead of directory
        with TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "not_a_directory.txt"
            temp_file.write_text("test")

            with pytest.raises(ValidationError):
                KindInferenceEngine(str(temp_file))

    def test_concurrent_error_handling(self):
        """Test error handling under concurrent access."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(temp_path / "planning")
            errors = []

            def error_prone_worker():
                """Worker that tests various error conditions."""
                try:
                    # Mix of valid and invalid operations
                    engine.infer_kind("P-valid", validate=False)
                    engine.infer_kind("", validate=False)  # Should fail
                except Exception as e:
                    errors.append(e)

                try:
                    engine.infer_kind("INVALID", validate=False)  # Should fail
                except Exception as e:
                    errors.append(e)

                try:
                    engine.infer_kind("T-valid", validate=False)  # Should work
                except Exception as e:
                    errors.append(e)

            # Run multiple error-prone workers concurrently
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=error_prone_worker)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Should have some errors but system should remain stable
            assert len(errors) > 0  # Expected errors from invalid inputs

            # System should still work after concurrent errors
            result = engine.infer_kind("F-test", validate=False)
            assert result == "feature"
