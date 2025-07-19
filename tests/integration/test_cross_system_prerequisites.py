"""Comprehensive test module for cross-system prerequisite validation.

Tests cross-system prerequisite scenarios between hierarchical and standalone tasks,
including dependency validation, existence checks, error handling, and edge cases.
"""

import asyncio

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestCrossSystemPrerequisiteValidation:
    """Test cross-system prerequisite validation scenarios."""

    @pytest.mark.asyncio
    async def test_standalone_task_depends_on_hierarchical_task(self, temp_dir):
        """Test standalone task with hierarchical task prerequisite."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create project
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Cross System Test Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project_result.data["id"]

            # Create epic
            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Cross System Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            # Create feature
            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Cross System Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create hierarchical task
            hierarchy_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "high",
                },
            )
            hierarchy_task_id = hierarchy_task_result.data["id"]

            # Create standalone task that depends on hierarchical task
            standalone_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task",
                    "projectRoot": planning_root,
                    "prerequisites": [hierarchy_task_id],
                    "priority": "normal",
                },
            )

            # Verify standalone task was created successfully
            standalone_task_id = standalone_task_result.data["id"]

            # Get full task data to verify prerequisites
            standalone_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": standalone_task_id,
                    "projectRoot": planning_root,
                },
            )

            # Verify standalone task has correct prerequisite and no parent
            assert standalone_retrieved.data["yaml"]["prerequisites"] == [hierarchy_task_id]
            assert standalone_retrieved.data["yaml"].get("parent") is None

    @pytest.mark.asyncio
    async def test_hierarchical_task_depends_on_standalone_task(self, temp_dir):
        """Test hierarchical task with standalone task prerequisite."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create project hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Cross System Test Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Cross System Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Cross System Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create standalone task
            standalone_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            standalone_task_id = standalone_task_result.data["id"]

            # Create hierarchical task that depends on standalone task
            hierarchy_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [standalone_task_id],
                    "priority": "normal",
                },
            )

            # Verify hierarchical task was created successfully
            hierarchy_task_id = hierarchy_task_result.data["id"]

            # Get full task data to verify prerequisites
            hierarchy_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": hierarchy_task_id,
                    "projectRoot": planning_root,
                },
            )

            # Verify hierarchical task has correct prerequisite and parent
            assert hierarchy_retrieved.data["yaml"]["prerequisites"] == [standalone_task_id]
            assert hierarchy_retrieved.data["yaml"]["parent"] == feature_id

    @pytest.mark.asyncio
    async def test_mixed_prerequisite_list_both_systems(self, temp_dir):
        """Test task with prerequisites from both hierarchical and standalone systems."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create project hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Mixed Prerequisite Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Mixed Prerequisite Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Mixed Prerequisite Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create multiple tasks in both systems
            hierarchy_task1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task 1",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "high",
                },
            )
            hierarchy_task1_id = hierarchy_task1_result.data["id"]

            hierarchy_task2_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task 2",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "high",
                },
            )
            hierarchy_task2_id = hierarchy_task2_result.data["id"]

            standalone_task1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task 1",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            standalone_task1_id = standalone_task1_result.data["id"]

            standalone_task2_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task 2",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            standalone_task2_id = standalone_task2_result.data["id"]

            # Create task with mixed prerequisites from both systems
            mixed_prereq_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Mixed Prerequisite Task",
                    "projectRoot": planning_root,
                    "prerequisites": [
                        hierarchy_task1_id,
                        standalone_task1_id,
                        hierarchy_task2_id,
                        standalone_task2_id,
                    ],
                    "priority": "normal",
                },
            )

            # Verify mixed prerequisite task was created successfully
            mixed_prereq_task_id = mixed_prereq_task_result.data["id"]

            # Get full task data to verify prerequisites
            mixed_prereq_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": mixed_prereq_task_id,
                    "projectRoot": planning_root,
                },
            )

            # Verify all prerequisites were accepted
            expected_prerequisites = [
                hierarchy_task1_id,
                standalone_task1_id,
                hierarchy_task2_id,
                standalone_task2_id,
            ]
            assert mixed_prereq_retrieved.data["yaml"]["prerequisites"] == expected_prerequisites

    @pytest.mark.asyncio
    async def test_prerequisite_id_prefix_handling(self, temp_dir):
        """Test that prerequisite IDs with prefixes are properly handled."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create project hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Prefix Test Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Prefix Test Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Prefix Test Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create tasks with known IDs
            hierarchy_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "high",
                },
            )
            hierarchy_task_id = hierarchy_task_result.data["id"]

            standalone_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            standalone_task_id = standalone_task_result.data["id"]

            # Create task with prerequisite IDs (they already have T- prefix)
            prefix_test_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Prefix Test Task",
                    "projectRoot": planning_root,
                    "prerequisites": [
                        hierarchy_task_id,  # Already has T- prefix
                        standalone_task_id,  # Already has T- prefix
                    ],
                    "priority": "normal",
                },
            )

            # Verify task was created successfully
            prefix_test_task_id = prefix_test_task_result.data["id"]

            # Get full task data to verify prerequisites
            prefix_test_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": prefix_test_task_id,
                    "projectRoot": planning_root,
                },
            )

            # Verify task was created successfully with cross-system prerequisites
            assert prefix_test_retrieved.data["yaml"]["title"] == "Prefix Test Task"
            # Prerequisites should be stored as provided (with their existing prefixes)
            expected_prerequisites = [hierarchy_task_id, standalone_task_id]
            assert prefix_test_retrieved.data["yaml"]["prerequisites"] == expected_prerequisites


class TestCrossSystemErrorHandling:
    """Test error handling for cross-system prerequisite scenarios."""

    @pytest.mark.asyncio
    async def test_nonexistent_cross_system_prerequisite(self, temp_dir):
        """Test error handling for nonexistent prerequisites in cross-system context."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Try to create task with nonexistent prerequisite
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": "Task with Invalid Prerequisite",
                        "projectRoot": planning_root,
                        "prerequisites": ["nonexistent-task-id"],
                        "priority": "normal",
                    },
                )

            # Verify error mentions cross-system checking
            error_msg = str(exc_info.value).lower()
            assert "does not exist" in error_msg or "not found" in error_msg

    @pytest.mark.asyncio
    async def test_multiple_missing_cross_system_prerequisites(self, temp_dir):
        """Test error handling for multiple missing prerequisites across systems."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create one valid task
            valid_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Valid Task",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            valid_task_id = valid_task_result.data["id"]

            # Try to create task with multiple missing prerequisites
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": "Task with Multiple Invalid Prerequisites",
                        "projectRoot": planning_root,
                        "prerequisites": [
                            valid_task_id,  # Valid
                            "missing-task-1",  # Invalid
                            "missing-task-2",  # Invalid
                            "missing-task-3",  # Invalid
                        ],
                        "priority": "normal",
                    },
                )

            # Verify error mentions the missing prerequisites
            error_msg = str(exc_info.value)
            assert (
                "missing-task-1" in error_msg
                or "missing-task-2" in error_msg
                or "missing-task-3" in error_msg
            )

    @pytest.mark.asyncio
    async def test_malicious_prerequisite_ids_blocked(self, temp_dir):
        """Test that malicious prerequisite IDs are blocked by security validation."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Test various malicious prerequisite IDs
            malicious_ids = [
                "../../../etc/passwd",  # Path traversal
                "/etc/passwd",  # Absolute path
                "task\x00name",  # Null byte injection
                "\\Windows\\System32",  # Windows path
            ]

            for malicious_id in malicious_ids:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": "Malicious Test Task",
                            "projectRoot": planning_root,
                            "prerequisites": [malicious_id],
                            "priority": "normal",
                        },
                    )

                # Verify security validation caught the issue
                error_msg = str(exc_info.value).lower()
                assert any(
                    keyword in error_msg
                    for keyword in ["security", "invalid", "malicious", "path", "characters"]
                )

    @pytest.mark.asyncio
    async def test_empty_prerequisite_ids_rejected(self, temp_dir):
        """Test that empty prerequisite IDs are properly rejected."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create valid task first
            valid_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Valid Task",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            valid_task_id = valid_task_result.data["id"]

            # Try to create task with empty prerequisite IDs
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": "Task with Empty Prerequisites",
                        "projectRoot": planning_root,
                        "prerequisites": [
                            valid_task_id,  # Valid
                            "",  # Empty
                            "  ",  # Whitespace only
                        ],
                        "priority": "normal",
                    },
                )

            # Verify error mentions empty prerequisite IDs
            error_msg = str(exc_info.value).lower()
            assert "empty" in error_msg or "invalid" in error_msg


class TestCrossSystemComplexNetworks:
    """Test complex prerequisite networks and edge cases across systems."""

    @pytest.mark.asyncio
    async def test_complex_prerequisite_chain_across_systems(self, temp_dir):
        """Test complex prerequisite chains spanning both hierarchical and standalone systems."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create project hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Complex Chain Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Complex Chain Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Complex Chain Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create a complex prerequisite chain:
            # Standalone A -> Hierarchical B -> Standalone C -> Hierarchical D

            # Create Standalone A (no prerequisites)
            standalone_a_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task A",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            standalone_a_id = standalone_a_result.data["id"]

            # Create Hierarchical B (depends on Standalone A)
            hierarchy_b_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task B",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [standalone_a_id],
                    "priority": "high",
                },
            )
            hierarchy_b_id = hierarchy_b_result.data["id"]

            # Create Standalone C (depends on Hierarchical B)
            standalone_c_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task C",
                    "projectRoot": planning_root,
                    "prerequisites": [hierarchy_b_id],
                    "priority": "normal",
                },
            )
            standalone_c_id = standalone_c_result.data["id"]

            # Create Hierarchical D (depends on Standalone C)
            hierarchy_d_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task D",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [standalone_c_id],
                    "priority": "normal",
                },
            )

            # Get full task data to verify prerequisites and types
            hierarchy_b_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": hierarchy_b_id,
                    "projectRoot": planning_root,
                },
            )

            standalone_c_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": standalone_c_id,
                    "projectRoot": planning_root,
                },
            )

            hierarchy_d_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": hierarchy_d_result.data["id"],
                    "projectRoot": planning_root,
                },
            )

            # Verify all tasks were created with correct prerequisites
            assert hierarchy_b_retrieved.data["yaml"]["prerequisites"] == [standalone_a_id]
            assert standalone_c_retrieved.data["yaml"]["prerequisites"] == [hierarchy_b_id]
            assert hierarchy_d_retrieved.data["yaml"]["prerequisites"] == [standalone_c_id]

            # Verify task types
            assert hierarchy_b_retrieved.data["yaml"]["parent"] == feature_id
            assert standalone_c_retrieved.data["yaml"].get("parent") is None
            assert hierarchy_d_retrieved.data["yaml"]["parent"] == feature_id

    @pytest.mark.asyncio
    async def test_fan_out_fan_in_cross_system_network(self, temp_dir):
        """Test fan-out/fan-in prerequisite network across both systems."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create project hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Fan Network Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Fan Network Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Fan Network Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create fan-out/fan-in network:
            # Root -> [A, B, C, D] -> Final
            # Where A,C are hierarchical and B,D are standalone

            # Create root task (standalone)
            root_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Root Task",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            root_task_id = root_task_result.data["id"]

            # Create fan-out tasks (mix of hierarchical and standalone)
            fan_out_ids = []

            # Hierarchical A
            task_a_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task A",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [root_task_id],
                    "priority": "normal",
                },
            )
            fan_out_ids.append(task_a_result.data["id"])

            # Standalone B
            task_b_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task B",
                    "projectRoot": planning_root,
                    "prerequisites": [root_task_id],
                    "priority": "normal",
                },
            )
            fan_out_ids.append(task_b_result.data["id"])

            # Hierarchical C
            task_c_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task C",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [root_task_id],
                    "priority": "normal",
                },
            )
            fan_out_ids.append(task_c_result.data["id"])

            # Standalone D
            task_d_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task D",
                    "projectRoot": planning_root,
                    "prerequisites": [root_task_id],
                    "priority": "normal",
                },
            )
            fan_out_ids.append(task_d_result.data["id"])

            # Create final task that depends on all fan-out tasks (standalone)
            final_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Final Task",
                    "projectRoot": planning_root,
                    "prerequisites": fan_out_ids,
                    "priority": "low",
                },
            )

            # Get full task data to verify prerequisites
            final_task_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": final_task_result.data["id"],
                    "projectRoot": planning_root,
                },
            )

            # Verify fan-out tasks have correct prerequisites
            for task_result in [task_a_result, task_b_result, task_c_result, task_d_result]:
                task_retrieved = await client.call_tool(
                    "getObject",
                    {
                        "kind": "task",
                        "id": task_result.data["id"],
                        "projectRoot": planning_root,
                    },
                )
                assert task_retrieved.data["yaml"]["prerequisites"] == [root_task_id]

            # Verify final task has all fan-out tasks as prerequisites
            assert set(final_task_retrieved.data["yaml"]["prerequisites"]) == set(fan_out_ids)

    @pytest.mark.asyncio
    async def test_concurrent_cross_system_operations(self, temp_dir):
        """Test concurrent creation of cross-system prerequisite relationships."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:

            # Create project hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Concurrent Test Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Concurrent Test Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Concurrent Test Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create base tasks first
            base_hierarchy_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Base Hierarchy Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "high",
                },
            )
            base_hierarchy_id = base_hierarchy_result.data["id"]

            base_standalone_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Base Standalone Task",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            base_standalone_id = base_standalone_result.data["id"]

            # Create multiple tasks concurrently that reference cross-system prerequisites
            async def create_dependent_task(task_num: int, task_type: str):
                """Create a task with cross-system prerequisites."""
                if task_type == "hierarchy":
                    return await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": f"Concurrent Hierarchy Task {task_num}",
                            "projectRoot": planning_root,
                            "parent": feature_id,
                            "prerequisites": [base_standalone_id],  # Hierarchy -> Standalone
                            "priority": "normal",
                        },
                    )
                else:
                    return await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": f"Concurrent Standalone Task {task_num}",
                            "projectRoot": planning_root,
                            "prerequisites": [base_hierarchy_id],  # Standalone -> Hierarchy
                            "priority": "normal",
                        },
                    )

            # Create tasks concurrently
            tasks = []
            for i in range(5):
                tasks.append(create_dependent_task(i, "hierarchy"))
                tasks.append(create_dependent_task(i, "standalone"))

            # Wait for all concurrent operations to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all tasks were created successfully (no exceptions)
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 10  # 5 hierarchy  +  5 standalone

            # Verify prerequisites are correct
            for i, result in enumerate(successful_results):
                # Cast to satisfy type checker - we know these are CallToolResults
                result = result  # type: ignore[assignment]

                # Get full task data to verify prerequisites
                task_retrieved = await client.call_tool(
                    "getObject",
                    {
                        "kind": "task",
                        "id": result.data["id"],  # type: ignore[attr-defined]
                        "projectRoot": planning_root,
                    },
                )

                if i % 2 == 0:  # Hierarchy tasks (even indices)
                    assert task_retrieved.data["yaml"]["prerequisites"] == [base_standalone_id]
                    assert task_retrieved.data["yaml"]["parent"] == feature_id
                else:  # Standalone tasks (odd indices)
                    assert task_retrieved.data["yaml"]["prerequisites"] == [base_hierarchy_id]
                    assert task_retrieved.data["yaml"].get("parent") is None


if __name__ == "__main__":
    pytest.main([__file__])
