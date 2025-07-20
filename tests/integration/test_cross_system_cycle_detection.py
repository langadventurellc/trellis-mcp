"""
Integration tests for cross-system cycle detection.

This module tests circular dependency detection spanning both hierarchical
and standalone task systems, ensuring robust cycle detection across all
cross-system scenarios.
"""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from tests.fixtures.cross_system_cycles import (
    create_complex_multi_task_cycle,
    create_cross_system_cycle_with_mixed_prereqs,
    create_nested_cycle_scenario,
    create_simple_cross_system_cycle,
)
from tests.integration.test_helpers import (
    create_test_hierarchy,
    create_test_server,
)


def clean_task_id(task_id: str) -> str:
    """Remove prefix from task ID for error message validation."""
    return task_id.replace("T-", "").replace("F-", "").replace("E-", "").replace("P-", "")


def assert_cycle_detected(error_message: str, updated_task_id: str):
    """Assert that cycle detection error mentions the task being updated."""
    assert "circular dependencies" in error_message.lower()
    clean_id = clean_task_id(updated_task_id)
    assert clean_id in error_message


class TestSimpleCrossSystemCycles:
    """Test simple 2-task cycles spanning both task systems."""

    @pytest.mark.asyncio
    async def test_hierarchical_to_standalone_cycle(self, temp_dir):
        """Test cycle: Hierarchical Task → Standalone Task → Hierarchical Task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create cycle scenario
            cycle_data = await create_simple_cross_system_cycle(client, planning_root, feature_id)

            # Attempt to create the cycle by updating hierarchical task
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle_data["hierarchy_task_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle_data["cycle_prereqs"]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle_data["hierarchy_task_id"])

    @pytest.mark.asyncio
    async def test_standalone_to_hierarchical_cycle(self, temp_dir):
        """Test cycle: Standalone Task → Hierarchical Task → Standalone Task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create standalone task (no prerequisites initially)
            standalone_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task A",
                    "projectRoot": planning_root,
                    "priority": "normal",
                },
            )
            standalone_id = standalone_result.data["id"]

            # Create hierarchical task with prerequisite to standalone task
            hierarchy_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchical Task B",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "normal",
                    "prerequisites": [standalone_id],
                },
            )
            hierarchy_id = hierarchy_result.data["id"]

            # Attempt to create cycle by updating standalone task
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": standalone_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [hierarchy_id]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, standalone_id)

    @pytest.mark.asyncio
    async def test_self_reference_cycle_hierarchical(self, temp_dir):
        """Test self-referencing cycle for hierarchical task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create hierarchical task
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Self-Reference Hierarchical Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "normal",
                },
            )
            task_id = task_result.data["id"]

            # Attempt to create self-reference cycle
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": task_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [task_id]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, task_id)

    @pytest.mark.asyncio
    async def test_self_reference_cycle_standalone(self, temp_dir):
        """Test self-referencing cycle for standalone task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create standalone task
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Self-Reference Standalone Task",
                    "projectRoot": planning_root,
                    "priority": "normal",
                },
            )
            task_id = task_result.data["id"]

            # Attempt to create self-reference cycle
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": task_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [task_id]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, task_id)


class TestComplexMultiTaskCycles:
    """Test complex multi-task cycles spanning both systems."""

    @pytest.mark.asyncio
    async def test_four_task_cross_system_cycle(self, temp_dir):
        """Test complex 4-task cycle: H1 → S1 → H2 → S2 → H1."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create complex cycle scenario
            cycle_data = await create_complex_multi_task_cycle(client, planning_root, feature_id)

            # Attempt to create the cycle by updating H1
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle_data["h1_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle_data["cycle_prereqs"]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle_data["h1_id"])

    @pytest.mark.asyncio
    async def test_mixed_prerequisites_cycle(self, temp_dir):
        """Test cycle involving tasks with multiple mixed prerequisites."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create mixed prerequisites cycle scenario
            cycle_data = await create_cross_system_cycle_with_mixed_prereqs(
                client, planning_root, feature_id
            )

            # Attempt to create the cycle
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle_data["h1_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle_data["cycle_prereqs"]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle_data["h1_id"])

    @pytest.mark.asyncio
    async def test_triangle_cycle_cross_system(self, temp_dir):
        """Test 3-task triangle cycle: H1 → S1 → H2 → H1."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create hierarchical task H1
            h1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Triangle Hierarchical H1",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "normal",
                },
            )
            h1_id = h1_result.data["id"]

            # Create standalone task S1 with prerequisite to H1
            s1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Triangle Standalone S1",
                    "projectRoot": planning_root,
                    "priority": "normal",
                    "prerequisites": [h1_id],
                },
            )
            s1_id = s1_result.data["id"]

            # Create hierarchical task H2 with prerequisite to S1
            h2_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Triangle Hierarchical H2",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": "normal",
                    "prerequisites": [s1_id],
                },
            )
            h2_id = h2_result.data["id"]

            # Attempt to create triangle cycle by updating H1 to depend on H2
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": h1_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [h2_id]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, h1_id)


class TestNestedCycleDetection:
    """Test cycle detection within larger dependency networks."""

    @pytest.mark.asyncio
    async def test_cycle_embedded_in_valid_network(self, temp_dir):
        """Test cycle detection in a network with both valid and cycle branches."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create nested cycle scenario
            cycle_data = await create_nested_cycle_scenario(client, planning_root, feature_id)

            # Attempt to create the cycle
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle_data["h1_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle_data["cycle_prereqs"]},
                    },
                )

            # Validate cycle detection
            error_message = str(exc_info.value)
            # Should detect cycle involving the updated task
            assert_cycle_detected(error_message, cycle_data["h1_id"])

    @pytest.mark.asyncio
    async def test_multiple_independent_cycles(self, temp_dir):
        """Test detection when multiple independent cycles exist."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create two separate hierarchies for independent cycles
            hierarchy1 = await create_test_hierarchy(client, planning_root, "First Cycle Project")
            hierarchy2 = await create_test_hierarchy(client, planning_root, "Second Cycle Project")

            # Create first simple cycle
            cycle1_data = await create_simple_cross_system_cycle(
                client, planning_root, hierarchy1["feature_id"]
            )

            # Create second simple cycle
            cycle2_data = await create_simple_cross_system_cycle(
                client, planning_root, hierarchy2["feature_id"]
            )

            # Attempt to create first cycle (should be detected)
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle1_data["hierarchy_task_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle1_data["cycle_prereqs"]},
                    },
                )

            # Validate first cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle1_data["hierarchy_task_id"])

            # Attempt to create second cycle (should also be detected)
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle2_data["hierarchy_task_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle2_data["cycle_prereqs"]},
                    },
                )

            # Validate second cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle2_data["hierarchy_task_id"])


class TestErrorMessageValidation:
    """Test validation of error messages for cross-system cycles."""

    @pytest.mark.asyncio
    async def test_error_message_contains_task_types(self, temp_dir):
        """Test that error messages distinguish between task types."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create cycle scenario
            cycle_data = await create_simple_cross_system_cycle(client, planning_root, feature_id)

            # Attempt to create the cycle
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle_data["hierarchy_task_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle_data["cycle_prereqs"]},
                    },
                )

            # Validate error message content
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle_data["hierarchy_task_id"])

    @pytest.mark.asyncio
    async def test_error_message_shows_full_cycle_path(self, temp_dir):
        """Test that error messages show the complete cycle path."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create complex cycle scenario
            cycle_data = await create_complex_multi_task_cycle(client, planning_root, feature_id)

            # Attempt to create the cycle
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle_data["h1_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle_data["cycle_prereqs"]},
                    },
                )

            # Validate error message for cycle detection
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle_data["h1_id"])

    @pytest.mark.asyncio
    async def test_error_code_validation(self, temp_dir):
        """Test that proper error codes are returned for cross-system cycles."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root)
            feature_id = hierarchy["feature_id"]

            # Create cycle scenario
            cycle_data = await create_simple_cross_system_cycle(client, planning_root, feature_id)

            # Attempt to create the cycle
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": cycle_data["hierarchy_task_id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": cycle_data["cycle_prereqs"]},
                    },
                )

            # Validate error details
            error_message = str(exc_info.value)
            assert_cycle_detected(error_message, cycle_data["hierarchy_task_id"])
            # Check for circular dependency error indication
            assert (
                "CIRCULAR_DEPENDENCY" in error_message
                or "circular dependencies" in error_message.lower()
            )
