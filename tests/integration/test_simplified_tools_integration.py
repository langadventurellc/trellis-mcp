"""Comprehensive integration tests for simplified tools.

Tests end-to-end functionality of simplified getObject and updateObject tools
with automatic kind inference, clean response formats, and cross-system compatibility.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestSimplifiedToolsIntegration:
    """Test comprehensive integration scenarios for simplified tools."""

    @pytest.mark.asyncio
    async def test_end_to_end_simplified_workflow(self, temp_dir):
        """Test complete end-to-end workflow with simplified tools."""
        # Create realistic project structure
        project_root = temp_dir / "planning"
        self._create_complete_project_structure(project_root)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test simplified getObject for all object types
            test_objects = [
                ("P-sample-project", "project", "sample-project"),
                ("E-core-features", "epic", "core-features"),
                ("F-user-authentication", "feature", "user-authentication"),
                ("T-implement-login", "task", "implement-login"),
            ]

            for object_id, expected_kind, expected_clean_id in test_objects:
                # Test getObject with simplified interface
                get_result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )

                # Verify simplified getObject response
                assert get_result.data["kind"] == expected_kind
                assert get_result.data["id"] == expected_clean_id
                assert "file_path" not in get_result.data
                assert "yaml" in get_result.data
                assert "body" in get_result.data
                assert "children" in get_result.data

                # Test updateObject with simplified interface
                update_result = await client.call_tool(
                    "updateObject",
                    {
                        "id": object_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "high"},
                    },
                )

                # Verify simplified updateObject response
                assert update_result.data["kind"] == expected_kind
                assert update_result.data["id"] == expected_clean_id
                assert "file_path" not in update_result.data
                assert "updated" in update_result.data
                assert "changes" in update_result.data

                # Verify changes were applied
                get_updated_result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )
                assert get_updated_result.data["yaml"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_cross_system_object_handling(self, temp_dir):
        """Test simplified tools with both hierarchical and standalone objects."""
        project_root = temp_dir / "planning"
        self._create_mixed_project_structure(project_root)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test hierarchical objects
            hierarchical_objects = [
                ("P-main-project", "project"),
                ("E-backend-api", "epic"),
                ("F-user-service", "feature"),
                ("T-create-user-model", "task"),
            ]

            for object_id, expected_kind in hierarchical_objects:
                # Get object
                result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )
                assert result.data["kind"] == expected_kind
                assert "file_path" not in result.data

                # Update object
                update_result = await client.call_tool(
                    "updateObject",
                    {
                        "id": object_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "high"},
                    },
                )
                assert update_result.data["kind"] == expected_kind
                assert "file_path" not in update_result.data

            # Test standalone objects
            standalone_objects = [
                ("T-database-migration", "task"),
                ("T-security-audit", "task"),
                ("T-performance-optimization", "task"),
            ]

            for object_id, expected_kind in standalone_objects:
                # Get standalone object
                result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )
                assert result.data["kind"] == expected_kind
                assert "file_path" not in result.data

                # Update standalone object
                update_result = await client.call_tool(
                    "updateObject",
                    {
                        "id": object_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "high"},
                    },
                )
                assert update_result.data["kind"] == expected_kind
                assert "file_path" not in update_result.data

    @pytest.mark.asyncio
    async def test_kind_inference_integration_workflow(self, temp_dir):
        """Test kind inference integration across complete workflows."""
        project_root = temp_dir / "planning"
        self._create_inference_test_structure(project_root)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test all valid ID prefix patterns
            prefix_tests = [
                ("P-inference-project", "project"),
                ("E-inference-epic", "epic"),
                ("F-inference-feature", "feature"),
                ("T-inference-task", "task"),
            ]

            for object_id, expected_kind in prefix_tests:
                # Test getObject kind inference
                get_result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )

                # Verify kind was inferred correctly
                assert get_result.data["kind"] == expected_kind

                # Test updateObject kind inference
                update_result = await client.call_tool(
                    "updateObject",
                    {
                        "id": object_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "high"},
                    },
                )

                # Verify kind was inferred correctly in update
                assert update_result.data["kind"] == expected_kind

            # Test with IDs that already have prefixes stripped
            stripped_tests = [
                ("inference-project", "project"),
                ("inference-epic", "epic"),
                ("inference-feature", "feature"),
                ("inference-task", "task"),
            ]

            for object_id, expected_kind in stripped_tests:
                # These should fail because they don't have proper prefixes
                with pytest.raises(Exception):
                    await client.call_tool(
                        "getObject",
                        {"id": object_id, "projectRoot": str(project_root)},
                    )

    @pytest.mark.asyncio
    async def test_response_format_consistency(self, temp_dir):
        """Test response format consistency across all simplified tools."""
        project_root = temp_dir / "planning"
        self._create_complete_project_structure(project_root)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            test_objects = [
                "P-sample-project",
                "E-core-features",
                "F-user-authentication",
                "T-implement-login",
            ]

            for object_id in test_objects:
                # Test getObject response format
                get_result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )

                # Verify clean response format
                assert "file_path" not in get_result.data
                required_fields = ["yaml", "body", "kind", "id", "children"]
                for field in required_fields:
                    assert field in get_result.data

                # Test updateObject response format
                update_result = await client.call_tool(
                    "updateObject",
                    {
                        "id": object_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "high"},
                    },
                )

                # Verify clean response format
                assert "file_path" not in update_result.data
                required_fields = ["id", "kind", "updated", "changes"]
                for field in required_fields:
                    assert field in update_result.data

    @pytest.mark.asyncio
    async def test_children_discovery_integration(self, temp_dir):
        """Test children discovery integration with simplified tools."""
        project_root = temp_dir / "planning"
        self._create_hierarchical_structure(project_root)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test project with epics
            project_result = await client.call_tool(
                "getObject",
                {"id": "P-hierarchy-test", "projectRoot": str(project_root)},
            )

            assert "children" in project_result.data
            children = project_result.data["children"]
            assert len(children) == 2  # Two epics

            # Verify children don't have file_path
            for child in children:
                assert "file_path" not in child
                assert "id" in child
                assert "title" in child
                assert "status" in child
                assert "kind" in child
                assert "created" in child

            # Test epic with features
            epic_result = await client.call_tool(
                "getObject",
                {"id": "E-backend-epic", "projectRoot": str(project_root)},
            )

            assert "children" in epic_result.data
            epic_children = epic_result.data["children"]
            assert len(epic_children) == 1  # One feature

            # Test feature with tasks
            feature_result = await client.call_tool(
                "getObject",
                {"id": "F-auth-feature", "projectRoot": str(project_root)},
            )

            assert "children" in feature_result.data
            feature_children = feature_result.data["children"]
            assert len(feature_children) == 2  # Open and done tasks

            # Test task with no children
            task_result = await client.call_tool(
                "getObject",
                {"id": "T-login-task", "projectRoot": str(project_root)},
            )

            assert "children" in task_result.data
            assert len(task_result.data["children"]) == 0  # Tasks have no children

    @pytest.mark.asyncio
    async def test_concurrent_simplified_operations(self, temp_dir):
        """Test thread safety with concurrent simplified tool operations."""
        project_root = temp_dir / "planning"
        self._create_complete_project_structure(project_root)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        results = []
        errors = []

        async def concurrent_worker(client, object_ids):
            """Worker function for concurrent tool testing."""
            worker_results = []
            for obj_id, expected_kind in object_ids:
                try:
                    # Test getObject
                    get_result = await client.call_tool(
                        "getObject",
                        {"id": obj_id, "projectRoot": str(project_root)},
                    )
                    assert get_result.data["kind"] == expected_kind
                    assert "file_path" not in get_result.data

                    # Test updateObject
                    update_result = await client.call_tool(
                        "updateObject",
                        {
                            "id": obj_id,
                            "projectRoot": str(project_root),
                            "yamlPatch": {"priority": "high"},
                        },
                    )
                    assert update_result.data["kind"] == expected_kind
                    assert "file_path" not in update_result.data

                    worker_results.append((obj_id, expected_kind, "success"))
                except Exception as e:
                    errors.append((obj_id, e))

            results.extend(worker_results)

        # Define test object sets for different concurrent operations
        thread_data = [
            [("P-sample-project", "project"), ("E-core-features", "epic")],
            [("F-user-authentication", "feature"), ("T-implement-login", "task")],
            [
                ("P-sample-project", "project"),
                ("F-user-authentication", "feature"),
            ],  # Repeat for cache testing
        ]

        # Run concurrent operations
        async with Client(server) as client:
            import asyncio

            tasks = []
            for data in thread_data:
                task = asyncio.create_task(concurrent_worker(client, data))
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Verify results
        assert len(errors) == 0, f"Concurrent errors occurred: {errors}"
        assert len(results) == 6  # 2 + 2 + 2 objects from 3 tasks

        # Verify all operations succeeded
        for obj_id, expected_kind, status in results:
            assert status == "success", f"Operation failed for {obj_id}"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, temp_dir):
        """Test error handling across simplified tool boundaries."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test invalid ID formats
            invalid_ids = [
                "",  # Empty string
                "INVALID-FORMAT",  # Invalid prefix
                "X-unknown-prefix",  # Unknown prefix
            ]

            for invalid_id in invalid_ids:
                # Test getObject error handling
                with pytest.raises(Exception):
                    await client.call_tool(
                        "getObject",
                        {"id": invalid_id, "projectRoot": str(project_root)},
                    )

                # Test updateObject error handling
                with pytest.raises(Exception):
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": invalid_id,
                            "projectRoot": str(project_root),
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )

            # Test non-existent but valid format objects
            nonexistent_objects = [
                "P-nonexistent-project",
                "E-missing-epic",
                "F-absent-feature",
                "T-void-task",
            ]

            for obj_id in nonexistent_objects:
                # Should fail for both tools
                with pytest.raises(Exception):
                    await client.call_tool(
                        "getObject",
                        {"id": obj_id, "projectRoot": str(project_root)},
                    )

                with pytest.raises(Exception):
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": obj_id,
                            "projectRoot": str(project_root),
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )

    @pytest.mark.asyncio
    async def test_complex_workflow_integration(self, temp_dir):
        """Test complex workflows with simplified tools."""
        project_root = temp_dir / "planning"
        self._create_complex_workflow_structure(project_root)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test cascade deletion workflow
            # First, get the feature to see its children
            feature_result = await client.call_tool(
                "getObject",
                {"id": "F-deletable-feature", "projectRoot": str(project_root)},
            )

            # Verify it has children
            assert len(feature_result.data["children"]) > 0

            # Test updating to deleted status (cascade deletion)
            delete_result = await client.call_tool(
                "updateObject",
                {
                    "id": "F-deletable-feature",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "deleted"},
                },
            )

            # Verify cascade deletion response
            assert delete_result.data["kind"] == "feature"
            assert delete_result.data["changes"]["status"] == "deleted"
            assert "cascade_deleted" in delete_result.data["changes"]
            assert "file_path" not in delete_result.data

            # Verify the feature is now gone
            with pytest.raises(Exception):
                await client.call_tool(
                    "getObject",
                    {"id": "F-deletable-feature", "projectRoot": str(project_root)},
                )

    def _create_complete_project_structure(self, project_root):
        """Create a complete project structure for testing."""
        project_root.mkdir(parents=True, exist_ok=True)

        # Create project
        project_dir = project_root / "projects" / "P-sample-project"
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            """---
kind: project
id: P-sample-project
title: Sample Project
status: in-progress
priority: normal
created: '2025-07-20T10:00:00Z'
updated: '2025-07-20T10:00:00Z'
schema_version: '1.1'
---
Sample project for testing."""
        )

        # Create epic
        epic_dir = project_dir / "epics" / "E-core-features"
        epic_dir.mkdir(parents=True)
        (epic_dir / "epic.md").write_text(
            """---
kind: epic
id: E-core-features
parent: P-sample-project
title: Core Features
status: in-progress
priority: normal
created: '2025-07-20T10:01:00Z'
updated: '2025-07-20T10:01:00Z'
schema_version: '1.1'
---
Core features epic."""
        )

        # Create feature
        feature_dir = epic_dir / "features" / "F-user-authentication"
        feature_dir.mkdir(parents=True)
        (feature_dir / "feature.md").write_text(
            """---
kind: feature
id: F-user-authentication
parent: E-core-features
title: User Authentication
status: in-progress
priority: high
created: '2025-07-20T10:02:00Z'
updated: '2025-07-20T10:02:00Z'
schema_version: '1.1'
---
User authentication feature."""
        )

        # Create task
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)
        (task_dir / "T-implement-login.md").write_text(
            """---
kind: task
id: T-implement-login
parent: F-user-authentication
title: Implement Login
status: open
priority: high
created: '2025-07-20T10:03:00Z'
updated: '2025-07-20T10:03:00Z'
schema_version: '1.1'
---
Implement login functionality."""
        )

    def _create_mixed_project_structure(self, project_root):
        """Create a mixed project structure with hierarchical and standalone objects."""
        project_root.mkdir(parents=True, exist_ok=True)

        # Create hierarchical structure
        self._create_complete_project_structure(project_root)

        # Rename for consistency
        (project_root / "projects" / "P-sample-project").rename(
            project_root / "projects" / "P-main-project"
        )

        # Update project file
        (project_root / "projects" / "P-main-project" / "project.md").write_text(
            """---
kind: project
id: P-main-project
title: Main Project
status: in-progress
priority: normal
created: '2025-07-20T09:00:00Z'
updated: '2025-07-20T09:00:00Z'
schema_version: '1.1'
---
Main project for mixed testing."""
        )

        # Rename epic and feature
        epic_dir = project_root / "projects" / "P-main-project" / "epics"
        (epic_dir / "E-core-features").rename(epic_dir / "E-backend-api")
        (epic_dir / "E-backend-api" / "epic.md").write_text(
            """---
kind: epic
id: E-backend-api
parent: P-main-project
title: Backend API
status: in-progress
priority: normal
created: '2025-07-20T09:01:00Z'
updated: '2025-07-20T09:01:00Z'
schema_version: '1.1'
---
Backend API epic."""
        )

        feature_dir = epic_dir / "E-backend-api" / "features"
        (feature_dir / "F-user-authentication").rename(feature_dir / "F-user-service")
        (feature_dir / "F-user-service" / "feature.md").write_text(
            """---
kind: feature
id: F-user-service
parent: E-backend-api
title: User Service
status: in-progress
priority: normal
created: '2025-07-20T09:02:00Z'
updated: '2025-07-20T09:02:00Z'
schema_version: '1.1'
---
User service feature."""
        )

        task_dir = feature_dir / "F-user-service" / "tasks-open"
        (task_dir / "T-implement-login.md").rename(task_dir / "T-create-user-model.md")
        (task_dir / "T-create-user-model.md").write_text(
            """---
kind: task
id: T-create-user-model
parent: F-user-service
title: Create User Model
status: open
priority: normal
created: '2025-07-20T09:03:00Z'
updated: '2025-07-20T09:03:00Z'
schema_version: '1.1'
---
Create user model."""
        )

        # Create standalone tasks
        standalone_dir = project_root / "tasks-open"
        standalone_dir.mkdir(parents=True)

        standalone_tasks = [
            ("T-database-migration", "Database Migration"),
            ("T-security-audit", "Security Audit"),
            ("T-performance-optimization", "Performance Optimization"),
        ]

        for task_id, title in standalone_tasks:
            (standalone_dir / f"{task_id}.md").write_text(
                f"""---
kind: task
id: {task_id}
title: {title}
status: open
priority: normal
created: '2025-07-20T09:10:00Z'
updated: '2025-07-20T09:10:00Z'
schema_version: '1.1'
---
{title} task."""
            )

    def _create_inference_test_structure(self, project_root):
        """Create structure for testing kind inference."""
        project_root.mkdir(parents=True, exist_ok=True)

        # Create objects with specific IDs for inference testing
        objects = [
            (
                "projects/P-inference-project/project.md",
                "project",
                "P-inference-project",
                "Inference Project",
            ),
            (
                "projects/P-inference-project/epics/E-inference-epic/epic.md",
                "epic",
                "E-inference-epic",
                "Inference Epic",
            ),
            (
                "projects/P-inference-project/epics/E-inference-epic/features/"
                "F-inference-feature/feature.md",
                "feature",
                "F-inference-feature",
                "Inference Feature",
            ),
            (
                "projects/P-inference-project/epics/E-inference-epic/features/"
                "F-inference-feature/tasks-open/T-inference-task.md",
                "task",
                "T-inference-task",
                "Inference Task",
            ),
        ]

        for file_path, kind, obj_id, title in objects:
            full_path = project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            status = (
                "draft"
                if kind in ["epic", "feature"]
                else ("in-progress" if kind == "project" else "open")
            )
            parent = ""
            if kind == "epic":
                parent = "P-inference-project"
            elif kind == "feature":
                parent = "E-inference-epic"
            elif kind == "task":
                parent = "F-inference-feature"

            parent_line = f"parent: {parent}\n" if parent else ""

            full_path.write_text(
                f"""---
kind: {kind}
id: {obj_id}
{parent_line}title: {title}
status: {status}
priority: normal
created: '2025-07-20T08:00:00Z'
updated: '2025-07-20T08:00:00Z'
schema_version: '1.1'
---
{title} for inference testing."""
            )

    def _create_hierarchical_structure(self, project_root):
        """Create hierarchical structure for children discovery testing."""
        project_root.mkdir(parents=True, exist_ok=True)

        # Create project
        project_dir = project_root / "projects" / "P-hierarchy-test"
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            """---
kind: project
id: P-hierarchy-test
title: Hierarchy Test Project
status: in-progress
priority: normal
created: '2025-07-20T07:00:00Z'
updated: '2025-07-20T07:00:00Z'
schema_version: '1.1'
---
Project for hierarchy testing."""
        )

        # Create first epic
        epic1_dir = project_dir / "epics" / "E-backend-epic"
        epic1_dir.mkdir(parents=True)
        (epic1_dir / "epic.md").write_text(
            """---
kind: epic
id: E-backend-epic
parent: P-hierarchy-test
title: Backend Epic
status: in-progress
priority: high
created: '2025-07-20T07:01:00Z'
updated: '2025-07-20T07:01:00Z'
schema_version: '1.1'
---
Backend epic."""
        )

        # Create second epic
        epic2_dir = project_dir / "epics" / "E-frontend-epic"
        epic2_dir.mkdir(parents=True)
        (epic2_dir / "epic.md").write_text(
            """---
kind: epic
id: E-frontend-epic
parent: P-hierarchy-test
title: Frontend Epic
status: draft
priority: normal
created: '2025-07-20T07:02:00Z'
updated: '2025-07-20T07:02:00Z'
schema_version: '1.1'
---
Frontend epic."""
        )

        # Create feature under first epic
        feature_dir = epic1_dir / "features" / "F-auth-feature"
        feature_dir.mkdir(parents=True)
        (feature_dir / "feature.md").write_text(
            """---
kind: feature
id: F-auth-feature
parent: E-backend-epic
title: Auth Feature
status: in-progress
priority: high
created: '2025-07-20T07:03:00Z'
updated: '2025-07-20T07:03:00Z'
schema_version: '1.1'
---
Authentication feature."""
        )

        # Create tasks under feature
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_open_dir.mkdir(parents=True)
        (tasks_open_dir / "T-login-task.md").write_text(
            """---
kind: task
id: T-login-task
parent: F-auth-feature
title: Login Task
status: open
priority: high
created: '2025-07-20T07:04:00Z'
updated: '2025-07-20T07:04:00Z'
schema_version: '1.1'
---
Login task."""
        )

        tasks_done_dir = feature_dir / "tasks-done"
        tasks_done_dir.mkdir(parents=True)
        (tasks_done_dir / "20250720_070500-T-register-task.md").write_text(
            """---
kind: task
id: T-register-task
parent: F-auth-feature
title: Register Task
status: done
priority: normal
created: '2025-07-20T07:05:00Z'
updated: '2025-07-20T07:05:00Z'
schema_version: '1.1'
---
Register task."""
        )

    def _create_complex_workflow_structure(self, project_root):
        """Create structure for complex workflow testing."""
        project_root.mkdir(parents=True, exist_ok=True)

        # Create project
        project_dir = project_root / "projects" / "P-workflow-test"
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            """---
kind: project
id: P-workflow-test
title: Workflow Test Project
status: in-progress
priority: normal
created: '2025-07-20T06:00:00Z'
updated: '2025-07-20T06:00:00Z'
schema_version: '1.1'
---
Project for workflow testing."""
        )

        # Create epic
        epic_dir = project_dir / "epics" / "E-workflow-epic"
        epic_dir.mkdir(parents=True)
        (epic_dir / "epic.md").write_text(
            """---
kind: epic
id: E-workflow-epic
parent: P-workflow-test
title: Workflow Epic
status: in-progress
priority: normal
created: '2025-07-20T06:01:00Z'
updated: '2025-07-20T06:01:00Z'
schema_version: '1.1'
---
Workflow epic."""
        )

        # Create deletable feature with tasks
        feature_dir = epic_dir / "features" / "F-deletable-feature"
        feature_dir.mkdir(parents=True)
        (feature_dir / "feature.md").write_text(
            """---
kind: feature
id: F-deletable-feature
parent: E-workflow-epic
title: Deletable Feature
status: in-progress
priority: normal
created: '2025-07-20T06:02:00Z'
updated: '2025-07-20T06:02:00Z'
schema_version: '1.1'
---
Feature that will be deleted."""
        )

        # Create task that will be cascade deleted
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)
        (task_dir / "T-deletable-task.md").write_text(
            """---
kind: task
id: T-deletable-task
parent: F-deletable-feature
title: Deletable Task
status: open
priority: normal
created: '2025-07-20T06:03:00Z'
updated: '2025-07-20T06:03:00Z'
schema_version: '1.1'
---
Task that will be cascade deleted."""
        )
