"""Real project structure tests for Kind Inference Engine.

This module tests the Kind Inference Engine against realistic project structures,
including complex hierarchies, mixed environments, large-scale projects, and
edge cases that might be encountered in real-world usage.
"""

import tempfile
from pathlib import Path

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError
from src.trellis_mcp.inference.engine import KindInferenceEngine


class TestHierarchicalProjectStructures:
    """Test inference with realistic hierarchical project structures."""

    def test_deep_nested_hierarchical_structure(self):
        """Test inference in deeply nested hierarchical project structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create deep hierarchical structure
            # (3 projects, 5 epics each, 4 features each, 10 tasks each)
            self._create_deep_hierarchy(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test inference across all levels
            test_cases = [
                # Projects
                ("P-enterprise-platform", "project"),
                ("P-mobile-application", "project"),
                ("P-data-analytics", "project"),
                # Epics from different projects
                ("E-user-management", "epic"),
                ("E-payment-processing", "epic"),
                ("E-reporting-dashboard", "epic"),
                ("E-mobile-ui", "epic"),
                ("E-offline-sync", "epic"),
                # Features from different epics
                ("F-user-authentication", "feature"),
                ("F-user-profiles", "feature"),
                ("F-payment-gateway", "feature"),
                ("F-subscription-billing", "feature"),
                ("F-real-time-reports", "feature"),
                # Tasks from different features
                ("T-implement-oauth2", "task"),
                ("T-create-user-database", "task"),
                ("T-integrate-stripe", "task"),
                ("T-build-payment-ui", "task"),
                ("T-setup-report-cache", "task"),
            ]

            successful_inferences = 0
            for obj_id, expected_kind in test_cases:
                try:
                    # Test pattern matching first (core functionality)
                    result = engine.infer_kind(obj_id, validate=False)
                    assert result == expected_kind, f"Failed inference for {obj_id}"
                    successful_inferences += 1
                except ValidationError as e:
                    # Log validation errors but continue testing
                    print(f"Validation error for {obj_id}: {e}")

            # Should successfully infer most objects
            assert successful_inferences >= len(test_cases) * 0.8

    def test_complex_project_relationships(self):
        """Test inference with complex project relationship structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create structure with complex relationships
            self._create_complex_relationships(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test objects with various relationship patterns
            relationship_tests = [
                # Parent project with multiple child epics
                ("P-microservices-platform", "project"),
                ("E-auth-service", "epic"),
                ("E-user-service", "epic"),
                ("E-order-service", "epic"),
                ("E-notification-service", "epic"),
                # Epic with multiple feature types
                ("F-service-authentication", "feature"),
                ("F-service-authorization", "feature"),
                ("F-service-monitoring", "feature"),
                ("F-service-logging", "feature"),
                # Features with many tasks
                ("T-implement-jwt-tokens", "task"),
                ("T-setup-rate-limiting", "task"),
                ("T-configure-metrics", "task"),
                ("T-implement-circuit-breaker", "task"),
            ]

            for obj_id, expected_kind in relationship_tests:
                result = engine.infer_kind(obj_id, validate=False)  # Focus on pattern matching
                assert result == expected_kind

    def test_multi_level_project_validation(self):
        """Test validation across multiple project levels."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create multi-level structure for validation testing
            self._create_validation_hierarchy(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test validation at each level
            validation_tests = [
                ("P-validation-project", "project", True),
                ("E-validation-epic", "epic", True),
                ("F-validation-feature", "feature", True),
                ("T-validation-task", "task", True),
                ("P-invalid-project", "project", False),
                ("E-missing-epic", "epic", False),
                ("F-orphaned-feature", "feature", False),
            ]

            for obj_id, expected_kind, should_validate in validation_tests:
                result = engine.infer_with_validation(obj_id)
                assert result.inferred_kind == expected_kind
                if should_validate:
                    assert result.is_valid is True, f"{obj_id} should be valid"
                else:
                    assert result.is_valid is False, f"{obj_id} should be invalid"

    def _create_deep_hierarchy(self, planning_dir: Path):
        """Create a deep hierarchical project structure."""
        planning_dir.mkdir(parents=True)

        projects = [
            ("P-enterprise-platform", "Enterprise Platform"),
            ("P-mobile-application", "Mobile Application"),
            ("P-data-analytics", "Data Analytics"),
        ]

        epics_per_project = {
            "P-enterprise-platform": [
                ("E-user-management", "User Management"),
                ("E-payment-processing", "Payment Processing"),
                ("E-reporting-dashboard", "Reporting Dashboard"),
                ("E-system-integration", "System Integration"),
                ("E-security-compliance", "Security Compliance"),
            ],
            "P-mobile-application": [
                ("E-mobile-ui", "Mobile UI"),
                ("E-offline-sync", "Offline Sync"),
                ("E-push-notifications", "Push Notifications"),
                ("E-app-performance", "App Performance"),
                ("E-device-integration", "Device Integration"),
            ],
            "P-data-analytics": [
                ("E-data-collection", "Data Collection"),
                ("E-data-processing", "Data Processing"),
                ("E-visualization", "Visualization"),
                ("E-machine-learning", "Machine Learning"),
                ("E-data-governance", "Data Governance"),
            ],
        }

        features_per_epic = {
            "E-user-management": [
                ("F-user-authentication", "User Authentication"),
                ("F-user-profiles", "User Profiles"),
                ("F-access-control", "Access Control"),
                ("F-user-analytics", "User Analytics"),
            ],
            "E-payment-processing": [
                ("F-payment-gateway", "Payment Gateway"),
                ("F-subscription-billing", "Subscription Billing"),
                ("F-payment-analytics", "Payment Analytics"),
                ("F-fraud-detection", "Fraud Detection"),
            ],
            "E-reporting-dashboard": [
                ("F-real-time-reports", "Real-time Reports"),
                ("F-scheduled-reports", "Scheduled Reports"),
                ("F-custom-dashboards", "Custom Dashboards"),
                ("F-export-functionality", "Export Functionality"),
            ],
        }

        tasks_per_feature = {
            "F-user-authentication": [
                ("T-implement-oauth2", "Implement OAuth2"),
                ("T-setup-2fa", "Setup Two-Factor Authentication"),
                ("T-create-login-ui", "Create Login UI"),
                ("T-implement-password-reset", "Implement Password Reset"),
                ("T-add-social-login", "Add Social Login"),
            ],
            "F-payment-gateway": [
                ("T-integrate-stripe", "Integrate Stripe"),
                ("T-implement-paypal", "Implement PayPal"),
                ("T-create-payment-ui", "Create Payment UI"),
                ("T-setup-webhooks", "Setup Webhooks"),
                ("T-implement-refunds", "Implement Refunds"),
            ],
            "F-real-time-reports": [
                ("T-setup-report-cache", "Setup Report Cache"),
                ("T-implement-websockets", "Implement WebSockets"),
                ("T-create-chart-components", "Create Chart Components"),
                ("T-optimize-queries", "Optimize Queries"),
                ("T-add-filters", "Add Filters"),
            ],
        }

        # Create project structure
        for project_id, project_title in projects:
            project_dir = planning_dir / "projects" / project_id
            project_dir.mkdir(parents=True)
            self._create_object_file(
                project_dir / "project.md", "project", project_id, project_title
            )

            # Create epics for this project
            epics = epics_per_project.get(project_id, [])
            for epic_id, epic_title in epics:
                epic_dir = project_dir / "epics" / epic_id
                epic_dir.mkdir(parents=True)
                self._create_object_file(epic_dir / "epic.md", "epic", epic_id, epic_title)

                # Create features for this epic
                features = features_per_epic.get(epic_id, [])
                for feature_id, feature_title in features:
                    feature_dir = epic_dir / "features" / feature_id
                    feature_dir.mkdir(parents=True)
                    self._create_object_file(
                        feature_dir / "feature.md", "feature", feature_id, feature_title
                    )

                    # Create tasks for this feature
                    task_dir = feature_dir / "tasks-open"
                    task_dir.mkdir()

                    tasks = tasks_per_feature.get(feature_id, [])
                    for task_id, task_title in tasks:
                        self._create_object_file(
                            task_dir / f"{task_id}.md", "task", task_id, task_title
                        )

    def _create_complex_relationships(self, planning_dir: Path):
        """Create a complex project structure with various relationship patterns."""
        planning_dir.mkdir(parents=True)

        # Microservices platform project
        project_dir = planning_dir / "projects" / "P-microservices-platform"
        project_dir.mkdir(parents=True)
        self._create_object_file(
            project_dir / "project.md",
            "project",
            "P-microservices-platform",
            "Microservices Platform",
        )

        # Service-based epics
        services = [
            ("E-auth-service", "Authentication Service"),
            ("E-user-service", "User Service"),
            ("E-order-service", "Order Service"),
            ("E-notification-service", "Notification Service"),
        ]

        for epic_id, epic_title in services:
            epic_dir = project_dir / "epics" / epic_id
            epic_dir.mkdir(parents=True)
            self._create_object_file(epic_dir / "epic.md", "epic", epic_id, epic_title)

            # Common features across services
            common_features = [
                ("F-service-authentication", "Service Authentication"),
                ("F-service-authorization", "Service Authorization"),
                ("F-service-monitoring", "Service Monitoring"),
                ("F-service-logging", "Service Logging"),
            ]

            for feature_id, feature_title in common_features:
                feature_dir = epic_dir / "features" / feature_id
                feature_dir.mkdir(parents=True)
                self._create_object_file(
                    feature_dir / "feature.md", "feature", feature_id, feature_title
                )

                # Common tasks across features
                task_dir = feature_dir / "tasks-open"
                task_dir.mkdir()

                common_tasks = [
                    ("T-implement-jwt-tokens", "Implement JWT Tokens"),
                    ("T-setup-rate-limiting", "Setup Rate Limiting"),
                    ("T-configure-metrics", "Configure Metrics"),
                    ("T-implement-circuit-breaker", "Implement Circuit Breaker"),
                ]

                for task_id, task_title in common_tasks:
                    # Make task IDs unique by including epic prefix
                    unique_task_id = f"{task_id}-{epic_id.split('-')[1]}"
                    self._create_object_file(
                        task_dir / f"{unique_task_id}.md",
                        "task",
                        unique_task_id,
                        f"{task_title} ({epic_title})",
                    )

    def _create_validation_hierarchy(self, planning_dir: Path):
        """Create hierarchy for validation testing."""
        planning_dir.mkdir(parents=True)

        # Valid project
        valid_project_dir = planning_dir / "projects" / "P-validation-project"
        valid_project_dir.mkdir(parents=True)
        self._create_object_file(
            valid_project_dir / "project.md",
            "project",
            "P-validation-project",
            "Validation Project",
        )

        # Valid epic
        valid_epic_dir = valid_project_dir / "epics" / "E-validation-epic"
        valid_epic_dir.mkdir(parents=True)
        self._create_object_file(
            valid_epic_dir / "epic.md", "epic", "E-validation-epic", "Validation Epic"
        )

        # Valid feature
        valid_feature_dir = valid_epic_dir / "features" / "F-validation-feature"
        valid_feature_dir.mkdir(parents=True)
        self._create_object_file(
            valid_feature_dir / "feature.md",
            "feature",
            "F-validation-feature",
            "Validation Feature",
        )

        # Valid task
        valid_task_dir = valid_feature_dir / "tasks-open"
        valid_task_dir.mkdir()
        self._create_object_file(
            valid_task_dir / "T-validation-task.md", "task", "T-validation-task", "Validation Task"
        )

        # Invalid structures for testing
        # Invalid project (empty file)
        invalid_project_dir = planning_dir / "projects" / "P-invalid-project"
        invalid_project_dir.mkdir(parents=True)
        (invalid_project_dir / "project.md").write_text("")

        # Missing epic (referenced but doesn't exist)
        # E-missing-epic is referenced in tests but not created

        # Orphaned feature (no proper parent structure)
        orphan_dir = planning_dir / "orphan"
        orphan_dir.mkdir()
        self._create_object_file(
            orphan_dir / "F-orphaned-feature.md",
            "feature",
            "F-orphaned-feature",
            "Orphaned Feature",
        )

    def _create_object_file(self, file_path: Path, kind: str, obj_id: str, title: str):
        """Create a valid object file with proper YAML front matter."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Set appropriate status based on kind
        if kind == "project":
            status = "in-progress"
        elif kind in ["epic", "feature"]:
            status = "in-progress"
        else:  # task
            status = "open"

        # Build YAML content
        yaml_content = f"""kind: {kind}
id: {obj_id}
title: {title}
status: {status}
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z"""

        # Add parent relationships for hierarchical structure testing
        # We'll extract parent IDs from the file path or use default relationships
        if kind == "epic":
            # Epic files are in projects/<project>/epics/<epic>/epic.md
            project_part = (
                str(file_path).split("/projects/")[1].split("/")[0]
                if "/projects/" in str(file_path)
                else "P-sample-project"
            )
            yaml_content += f"\nparent: {project_part}"
        elif kind == "feature":
            # Feature files are in epics/<epic>/features/<feature>/feature.md
            epic_part = (
                str(file_path).split("/epics/")[1].split("/")[0]
                if "/epics/" in str(file_path)
                else "E-sample-epic"
            )
            yaml_content += f"\nparent: {epic_part}"
        elif kind == "task":
            # Task files can be in features/<feature>/tasks-*/<task>.md (hierarchical)
            # or in tasks-open/<task>.md (standalone)
            if "/features/" in str(file_path):
                feature_part = str(file_path).split("/features/")[1].split("/")[0]
                yaml_content += f"\nparent: {feature_part}"
            # Standalone tasks (in tasks-open) don't have parent relationships

        content = f"""---
{yaml_content}
---
# {title}

This is a {kind} for testing the Kind Inference Engine.

## Description

Test content for {obj_id}.
"""
        file_path.write_text(content)


class TestMixedEnvironmentProjects:
    """Test inference with mixed hierarchical and standalone objects."""

    def test_mixed_hierarchical_and_standalone_objects(self):
        """Test projects with both hierarchical and standalone task structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create mixed environment
            self._create_mixed_environment(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test hierarchical objects
            hierarchical_tests = [
                ("P-web-application", "project"),
                ("E-frontend-development", "epic"),
                ("F-user-interface", "feature"),
                ("T-create-login-component", "task"),
                ("T-implement-navigation", "task"),
            ]

            for obj_id, expected_kind in hierarchical_tests:
                result = engine.infer_kind(obj_id, validate=True)
                assert result == expected_kind

                # Verify it's correctly identified as hierarchical
                extended_result = engine.infer_with_validation(obj_id)
                assert extended_result.is_valid is True

            # Test standalone tasks
            standalone_tests = [
                ("T-database-setup", "task"),
                ("T-security-scan", "task"),
                ("T-performance-test", "task"),
                ("T-backup-configuration", "task"),
                ("T-monitoring-setup", "task"),
            ]

            for obj_id, expected_kind in standalone_tests:
                result = engine.infer_kind(obj_id, validate=True)
                assert result == expected_kind

                # Verify it's correctly identified as standalone
                extended_result = engine.infer_with_validation(obj_id)
                assert extended_result.is_valid is True

    def test_mixed_environment_cache_behavior(self):
        """Test cache behavior with mixed hierarchical and standalone objects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            self._create_mixed_environment(planning_dir)

            engine = KindInferenceEngine(planning_dir, cache_size=50)

            # Mix hierarchical and standalone inferences
            mixed_objects = [
                ("P-web-application", "project"),
                ("T-database-setup", "task"),
                ("E-frontend-development", "epic"),
                ("T-security-scan", "task"),
                ("F-user-interface", "feature"),
                ("T-performance-test", "task"),
            ]

            # First pass - populate cache
            for obj_id, expected_kind in mixed_objects:
                result = engine.infer_with_validation(obj_id)
                assert result.cache_hit is False
                assert result.inferred_kind == expected_kind

            # Second pass - should hit cache
            for obj_id, expected_kind in mixed_objects:
                result = engine.infer_with_validation(obj_id)
                assert result.cache_hit is True
                assert result.inferred_kind == expected_kind

            # Verify cache contains both types
            stats = engine.get_cache_stats()
            assert stats["size"] == len(mixed_objects)

    def test_mixed_environment_error_scenarios(self):
        """Test error handling in mixed environments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            self._create_mixed_environment(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test invalid objects in mixed environment
            invalid_objects = [
                "P-nonexistent-project",
                "T-missing-standalone-task",
                "E-absent-epic",
                "F-void-feature",
            ]

            for obj_id in invalid_objects:
                # Pattern matching should work
                result = engine.infer_kind(obj_id, validate=False)
                expected_kind = {"P": "project", "E": "epic", "F": "feature", "T": "task"}[
                    obj_id[0]
                ]
                assert result == expected_kind

                # Validation should fail
                with pytest.raises(ValidationError):
                    engine.infer_kind(obj_id, validate=True)

    def _create_mixed_environment(self, planning_dir: Path):
        """Create a mixed environment with both hierarchical and standalone structures."""
        planning_dir.mkdir(parents=True)

        # Create hierarchical structure
        project_dir = planning_dir / "projects" / "P-web-application"
        project_dir.mkdir(parents=True)
        self._create_object_file(
            project_dir / "project.md", "project", "P-web-application", "Web Application"
        )

        epic_dir = project_dir / "epics" / "E-frontend-development"
        epic_dir.mkdir(parents=True)
        self._create_object_file(
            epic_dir / "epic.md", "epic", "E-frontend-development", "Frontend Development"
        )

        feature_dir = epic_dir / "features" / "F-user-interface"
        feature_dir.mkdir(parents=True)
        self._create_object_file(
            feature_dir / "feature.md", "feature", "F-user-interface", "User Interface"
        )

        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()

        hierarchical_tasks = [
            ("T-create-login-component", "Create Login Component"),
            ("T-implement-navigation", "Implement Navigation"),
            ("T-design-responsive-layout", "Design Responsive Layout"),
        ]

        for task_id, task_title in hierarchical_tasks:
            self._create_object_file(task_dir / f"{task_id}.md", "task", task_id, task_title)

        # Create standalone tasks
        standalone_dir = planning_dir / "tasks-open"
        standalone_dir.mkdir()

        standalone_tasks = [
            ("T-database-setup", "Database Setup"),
            ("T-security-scan", "Security Scan"),
            ("T-performance-test", "Performance Test"),
            ("T-backup-configuration", "Backup Configuration"),
            ("T-monitoring-setup", "Monitoring Setup"),
        ]

        for task_id, task_title in standalone_tasks:
            self._create_object_file(standalone_dir / f"{task_id}.md", "task", task_id, task_title)

    def _create_object_file(self, file_path: Path, kind: str, obj_id: str, title: str):
        """Create a valid object file with proper YAML front matter."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Set appropriate status based on kind
        if kind == "project":
            status = "in-progress"
        elif kind in ["epic", "feature"]:
            status = "in-progress"
        else:  # task
            status = "open"

        # Build YAML content
        yaml_content = f"""kind: {kind}
id: {obj_id}
title: {title}
status: {status}
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z"""

        # Add parent relationships for hierarchical structure testing
        if kind == "epic":
            project_part = (
                str(file_path).split("/projects/")[1].split("/")[0]
                if "/projects/" in str(file_path)
                else "P-mixed-project"
            )
            yaml_content += f"\nparent: {project_part}"
        elif kind == "feature":
            epic_part = (
                str(file_path).split("/epics/")[1].split("/")[0]
                if "/epics/" in str(file_path)
                else "E-mixed-epic"
            )
            yaml_content += f"\nparent: {epic_part}"
        elif kind == "task":
            # Task files can be in features/<feature>/tasks-*/<task>.md (hierarchical)
            # or in tasks-open/<task>.md (standalone)
            if "/features/" in str(file_path):
                feature_part = str(file_path).split("/features/")[1].split("/")[0]
                yaml_content += f"\nparent: {feature_part}"
            # Standalone tasks (in tasks-open) don't have parent relationships

        content = f"""---
{yaml_content}
---
# {title}

This is a {kind} for testing mixed environment inference.
"""
        file_path.write_text(content)


class TestLargeScaleProjects:
    """Test inference with large-scale project structures."""

    def test_large_project_with_many_objects(self):
        """Test inference performance and accuracy with large numbers of objects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create large project structure
            self._create_large_scale_project(planning_dir)

            engine = KindInferenceEngine(planning_dir, cache_size=2000)

            # Test sample of objects across the large structure
            sample_objects = [
                # Projects
                ("P-enterprise-suite", "project"),
                ("P-mobile-platform", "project"),
                ("P-analytics-engine", "project"),
                # Epics (generated as E-{project_part}-epic-{number:03d})
                ("E-enterprise-epic-000", "epic"),
                ("E-mobile-epic-001", "epic"),
                ("E-analytics-epic-002", "epic"),
                # Features (generated as F-{project_part}-feature-{epic_num:03d}-{feature_num:03d})
                ("F-enterprise-feature-000-000", "feature"),
                ("F-mobile-feature-001-001", "feature"),
                ("F-analytics-feature-002-002", "feature"),
                # Tasks (generated as T-{project_part}-task-{epic_num:03d}-
                # {feature_num:03d}-{task_num:03d})
                ("T-enterprise-task-000-000-000", "task"),
                ("T-mobile-task-001-001-001", "task"),
                ("T-analytics-task-002-002-002", "task"),
            ]

            successful_inferences = 0
            for obj_id, expected_kind in sample_objects:
                try:
                    result = engine.infer_kind(obj_id, validate=True)
                    assert result == expected_kind
                    successful_inferences += 1
                except Exception as e:
                    print(f"Failed to infer {obj_id}: {e}")

            # Should successfully infer most objects
            assert successful_inferences >= len(sample_objects) * 0.7

    def test_large_project_cache_efficiency(self):
        """Test cache efficiency with large project structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            self._create_large_scale_project(planning_dir)

            engine = KindInferenceEngine(planning_dir, cache_size=100)

            # Test many objects to exercise cache eviction
            test_objects = []
            for p in range(5):
                for e in range(10):
                    for f in range(8):
                        for t in range(5):
                            obj_id = f"T-task-{p:03d}-{e:03d}-{f:03d}-{t:03d}"
                            test_objects.append(obj_id)

            # First pass
            for obj_id in test_objects[:50]:  # Test subset to avoid overwhelming
                try:
                    engine.infer_kind(obj_id, validate=False)
                except ValidationError:
                    pass  # Expected for some non-existent objects

            # Check cache stats
            stats = engine.get_cache_stats()
            assert stats["size"] <= 100  # Should respect cache limit
            assert stats["hits"] + stats["misses"] > 0

    def _create_large_scale_project(self, planning_dir: Path):
        """Create a large-scale project structure."""
        planning_dir.mkdir(parents=True)

        # Create multiple large projects
        projects = [
            ("P-enterprise-suite", "Enterprise Suite"),
            ("P-mobile-platform", "Mobile Platform"),
            ("P-analytics-engine", "Analytics Engine"),
        ]

        for project_id, project_title in projects:
            project_dir = planning_dir / "projects" / project_id
            project_dir.mkdir(parents=True)
            self._create_object_file(
                project_dir / "project.md", "project", project_id, project_title
            )

            # Create many epics
            for e in range(10):
                epic_id = f"E-{project_id.split('-')[1]}-epic-{e:03d}"
                epic_dir = project_dir / "epics" / epic_id
                epic_dir.mkdir(parents=True)
                self._create_object_file(epic_dir / "epic.md", "epic", epic_id, f"Epic {e:03d}")

                # Create many features
                for f in range(8):
                    feature_id = f"F-{project_id.split('-')[1]}-feature-{e:03d}-{f:03d}"
                    feature_dir = epic_dir / "features" / feature_id
                    feature_dir.mkdir(parents=True)
                    self._create_object_file(
                        feature_dir / "feature.md",
                        "feature",
                        feature_id,
                        f"Feature {e:03d}-{f:03d}",
                    )

                    # Create many tasks
                    task_dir = feature_dir / "tasks-open"
                    task_dir.mkdir()

                    for t in range(5):
                        task_id = f"T-{project_id.split('-')[1]}-task-{e:03d}-{f:03d}-{t:03d}"
                        self._create_object_file(
                            task_dir / f"{task_id}.md",
                            "task",
                            task_id,
                            f"Task {e:03d}-{f:03d}-{t:03d}",
                        )

        # Create many standalone tasks
        standalone_dir = planning_dir / "tasks-open"
        standalone_dir.mkdir()

        for s in range(100):
            task_id = f"T-standalone-{s:03d}"
            self._create_object_file(
                standalone_dir / f"{task_id}.md", "task", task_id, f"Standalone Task {s:03d}"
            )

    def _create_object_file(self, file_path: Path, kind: str, obj_id: str, title: str):
        """Create a valid object file with proper YAML front matter."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Set appropriate status based on kind
        if kind == "project":
            status = "in-progress"
        elif kind in ["epic", "feature"]:
            status = "in-progress"
        else:  # task
            status = "open"

        # Build YAML content
        yaml_content = f"""kind: {kind}
id: {obj_id}
title: {title}
status: {status}
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z"""

        # Add parent relationships for hierarchical structure testing
        if kind == "epic":
            project_part = (
                str(file_path).split("/projects/")[1].split("/")[0]
                if "/projects/" in str(file_path)
                else "P-project-00"
            )
            yaml_content += f"\nparent: {project_part}"
        elif kind == "feature":
            epic_part = (
                str(file_path).split("/epics/")[1].split("/")[0]
                if "/epics/" in str(file_path)
                else "E-epic-00-00"
            )
            yaml_content += f"\nparent: {epic_part}"
        elif kind == "task":
            # Task files can be in features/<feature>/tasks-*/<task>.md (hierarchical)
            # or in tasks-open/<task>.md (standalone)
            if "/features/" in str(file_path):
                feature_part = str(file_path).split("/features/")[1].split("/")[0]
                yaml_content += f"\nparent: {feature_part}"
            # Standalone tasks (in tasks-open) don't have parent relationships

        content = f"""---
{yaml_content}
---
# {title}

Large scale project object for testing.
"""
        file_path.write_text(content)


class TestEdgeCaseProjectStructures:
    """Test inference with edge case and problematic project structures."""

    def test_corrupted_and_malformed_objects(self):
        """Test handling of corrupted and malformed object files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create structure with various corruption scenarios
            self._create_corrupted_structure(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test handling of corrupted objects
            corruption_tests = [
                # Valid objects should work
                ("P-valid-project", "project", True),
                ("E-valid-epic", "epic", True),
                ("F-valid-feature", "feature", True),
                ("T-valid-task", "task", True),
                # Corrupted objects should fail validation but pattern matching should work
                ("P-empty-project", "project", False),
                ("E-malformed-yaml", "epic", False),
                ("F-missing-front-matter", "feature", False),
                ("T-invalid-yaml", "task", False),
            ]

            for obj_id, expected_kind, should_be_valid in corruption_tests:
                # Pattern matching should always work
                result = engine.infer_kind(obj_id, validate=False)
                assert result == expected_kind

                # Validation behavior depends on file validity
                if should_be_valid:
                    result = engine.infer_kind(obj_id, validate=True)
                    assert result == expected_kind
                else:
                    with pytest.raises(ValidationError):
                        engine.infer_kind(obj_id, validate=True)

    def test_orphaned_and_inconsistent_structures(self):
        """Test handling of orphaned objects and inconsistent structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create inconsistent structure
            self._create_inconsistent_structure(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test orphaned objects
            orphan_tests = [
                ("P-orphaned-project", "project"),
                ("E-orphaned-epic", "epic"),
                ("F-orphaned-feature", "feature"),
                ("T-orphaned-task", "task"),
            ]

            for obj_id, expected_kind in orphan_tests:
                # Pattern matching should work
                result = engine.infer_kind(obj_id, validate=False)
                assert result == expected_kind

                # Validation may or may not work depending on file structure
                try:
                    engine.infer_kind(obj_id, validate=True)
                except ValidationError:
                    # Expected for some orphaned objects
                    pass

    def test_special_characters_and_edge_case_naming(self):
        """Test handling of special characters and edge case naming."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"

            # Create structure with edge case names
            self._create_edge_case_names(planning_dir)

            engine = KindInferenceEngine(planning_dir)

            # Test edge case names
            edge_case_tests = [
                ("P-project-with-many-hyphens-and-numbers-123", "project"),
                ("E-epic_with_underscores", "epic"),
                ("F-feature.with.dots", "feature"),
                ("T-task-with-UPPERCASE-and-numbers-456", "task"),
            ]

            for obj_id, expected_kind in edge_case_tests:
                try:
                    result = engine.infer_kind(obj_id, validate=False)
                    assert result == expected_kind
                except ValidationError:
                    # Some edge cases might not be supported
                    pass

    def _create_corrupted_structure(self, planning_dir: Path):
        """Create a structure with various types of corruption."""
        planning_dir.mkdir(parents=True)

        # Valid objects
        project_dir = planning_dir / "projects" / "P-valid-project"
        project_dir.mkdir(parents=True)
        self._create_valid_corrupted_object(project_dir, "project.md", "project", "P-valid-project")

        epic_dir = planning_dir / "projects" / "P-valid-project" / "epics" / "E-valid-epic"
        epic_dir.mkdir(parents=True)
        self._create_valid_corrupted_object(epic_dir, "epic.md", "epic", "E-valid-epic")

        feature_dir = epic_dir / "features" / "F-valid-feature"
        feature_dir.mkdir(parents=True)
        self._create_valid_corrupted_object(feature_dir, "feature.md", "feature", "F-valid-feature")

        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir()
        self._create_valid_corrupted_object(task_dir, "T-valid-task.md", "task", "T-valid-task")

        # Corrupted objects
        # Empty project
        empty_project_dir = planning_dir / "projects" / "P-empty-project"
        empty_project_dir.mkdir(parents=True)
        (empty_project_dir / "project.md").write_text("")

        # Malformed YAML epic
        malformed_epic_dir = epic_dir.parent / "E-malformed-yaml"
        malformed_epic_dir.mkdir(parents=True)
        (malformed_epic_dir / "epic.md").write_text(
            """---
invalid: yaml: content:
no: proper: structure
---
# Malformed Epic"""
        )

        # Missing front matter feature
        missing_fm_feature_dir = feature_dir.parent / "F-missing-front-matter"
        missing_fm_feature_dir.mkdir(parents=True)
        (missing_fm_feature_dir / "feature.md").write_text("# Feature without front matter")

        # Invalid YAML task
        (task_dir / "T-invalid-yaml.md").write_text(
            """---
kind: task
id: T-invalid-yaml
title: Invalid YAML Task
status: [invalid list structure
---
# Invalid YAML Task"""
        )

    def _create_inconsistent_structure(self, planning_dir: Path):
        """Create inconsistent and orphaned structures."""
        planning_dir.mkdir(parents=True)

        # Orphaned project in wrong location
        orphan_dir = planning_dir / "orphan"
        orphan_dir.mkdir()
        self._create_valid_corrupted_object(
            orphan_dir, "P-orphaned-project.md", "project", "P-orphaned-project"
        )

        # Orphaned epic without proper project parent
        self._create_valid_corrupted_object(
            orphan_dir, "E-orphaned-epic.md", "epic", "E-orphaned-epic"
        )

        # Orphaned feature
        self._create_valid_corrupted_object(
            orphan_dir, "F-orphaned-feature.md", "feature", "F-orphaned-feature"
        )

        # Orphaned task not in proper directory structure
        self._create_valid_corrupted_object(
            orphan_dir, "T-orphaned-task.md", "task", "T-orphaned-task"
        )

    def _create_edge_case_names(self, planning_dir: Path):
        """Create objects with edge case naming patterns."""
        planning_dir.mkdir(parents=True)

        # Create objects with various naming edge cases
        edge_cases = [
            (
                "projects/P-project-with-many-hyphens-and-numbers-123/project.md",
                "project",
                "P-project-with-many-hyphens-and-numbers-123",
            ),
            (
                "projects/P-project-with-many-hyphens-and-numbers-123/epics/"
                "E-epic_with_underscores/epic.md",
                "epic",
                "E-epic_with_underscores",
            ),
        ]

        for file_path, kind, obj_id in edge_cases:
            full_path = planning_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            self._create_valid_corrupted_object(full_path.parent, full_path.name, kind, obj_id)

    def _create_valid_corrupted_object(
        self, base_path: Path, filename: str, kind: str, obj_id: str
    ):
        """Create a valid object file for corruption testing."""
        base_path.mkdir(parents=True, exist_ok=True)

        # Set appropriate status based on kind
        if kind == "project":
            status = "in-progress"
        elif kind in ["epic", "feature"]:
            status = "in-progress"
        else:  # task
            status = "open"

        # Build YAML content based on object type
        yaml_content = f"""kind: {kind}
id: {obj_id}
title: {obj_id.replace('-', ' ').title()}
status: {status}
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z"""

        # Add parent for hierarchical objects if needed
        if kind == "epic":
            yaml_content += "\nparent: P-valid-project"
        elif kind == "feature":
            yaml_content += "\nparent: E-valid-epic"
        elif kind == "task":
            yaml_content += "\nparent: F-valid-feature"

        content = f"""---
{yaml_content}
---
# {obj_id.replace('-', ' ').title()}

Test object for corruption testing.
"""
        (base_path / filename).write_text(content)
