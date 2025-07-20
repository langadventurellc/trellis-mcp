"""
Integration tests for comprehensive mixed dependency chain scenarios.

This module tests complex dependency networks that span both hierarchical
and standalone task systems, ensuring robust cross-system dependency
resolution, workflow integration, and performance under complex scenarios.
"""

import asyncio

import pytest
from fastmcp import Client
from tests.integration.test_helpers import (
    create_test_hierarchy,
    update_task_status,
)

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestMixedDependencyChainIntegration:
    """Test complex mixed dependency chains and workflow integration."""

    @pytest.mark.asyncio
    async def test_multi_level_dependency_chain(self, temp_dir):
        """Test complex 5-level dependency chain spanning both task systems."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # Create hierarchical structure
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Multi-Level Chain Project"
            )

            # Create 5-level dependency chain:
            # Standalone A → Hierarchical B → Standalone C → Hierarchical D → Standalone E
            chain_tasks = []

            # Level 1: Standalone task with no prerequisites
            level1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Chain Level 1 - Standalone Foundation",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            chain_tasks.append(level1_result.data["id"])

            # Level 2: Hierarchical task depending on Level 1
            level2_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Chain Level 2 - Hierarchical Dependent",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": [chain_tasks[0]],
                    "priority": "high",
                },
            )
            chain_tasks.append(level2_result.data["id"])

            # Level 3: Standalone task depending on Level 2
            level3_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Chain Level 3 - Standalone Middle",
                    "projectRoot": planning_root,
                    "prerequisites": [chain_tasks[1]],
                    "priority": "high",
                },
            )
            chain_tasks.append(level3_result.data["id"])

            # Level 4: Hierarchical task depending on Level 3
            level4_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Chain Level 4 - Hierarchical Upper",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": [chain_tasks[2]],
                    "priority": "high",
                },
            )
            chain_tasks.append(level4_result.data["id"])

            # Level 5: Standalone task depending on Level 4
            level5_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Chain Level 5 - Standalone Final",
                    "projectRoot": planning_root,
                    "prerequisites": [chain_tasks[3]],
                    "priority": "high",
                },
            )
            chain_tasks.append(level5_result.data["id"])

            # Test that only Level 1 is claimable initially
            claim_result = await client.call_tool("claimNextTask", {"projectRoot": planning_root})

            assert claim_result.data["task"]["id"] == chain_tasks[0]

            # Complete tasks in sequence and verify claiming behavior
            for i, task_id in enumerate(chain_tasks[:-1]):
                # Complete current task (it's already in-progress from claiming)
                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                        "summary": f"Completed {task_id} in dependency chain",
                        "filesChanged": [f"chain-{task_id}.py"],
                    },
                )

                # Verify next task becomes claimable
                next_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
                assert next_claim.data["task"]["id"] == chain_tasks[i + 1]

                # Verify task type is preserved
                next_task = await client.call_tool(
                    "getObject",
                    {
                        "id": chain_tasks[i + 1],
                        "projectRoot": planning_root,
                    },
                )

                # Verify alternating task types in chain
                level_number = i + 2  # Next level number (i + 1  + 1 for 1-based indexing)
                if level_number % 2 == 1:  # Odd levels (1,3,5) are standalone
                    assert next_task.data["yaml"].get("parent") is None
                else:  # Even levels (2,4) are hierarchical
                    assert next_task.data["yaml"]["parent"] == hierarchy["feature_id"]

    @pytest.mark.asyncio
    async def test_complex_fan_out_fan_in_network(self, temp_dir):
        """Test complex network with fan-out and fan-in cross-system dependencies."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # Create hierarchical structure only (no extra tasks)
            hierarchy = await create_test_hierarchy(client, planning_root, "Fan Network Project")

            # Create root task (standalone)
            root_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Root Task - Foundation",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            root_task_id = root_task_result.data["id"]

            # Create fan-out tasks (3 hierarchical, 3 standalone)
            fan_out_tasks = []

            # 3 hierarchical fan-out tasks
            for i in range(3):
                task_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Hierarchical Fan-Out Task {i + 1}",
                        "projectRoot": planning_root,
                        "parent": hierarchy["feature_id"],
                        "prerequisites": [root_task_id],
                        "priority": "normal",
                    },
                )
                fan_out_tasks.append(task_result.data["id"])

            # 3 standalone fan-out tasks
            for i in range(3):
                task_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Standalone Fan-Out Task {i + 1}",
                        "projectRoot": planning_root,
                        "prerequisites": [root_task_id],
                        "priority": "normal",
                    },
                )
                fan_out_tasks.append(task_result.data["id"])

            # Create fan-in convergence tasks
            convergence_tasks = []

            # Hierarchical convergence task requiring all fan-out tasks
            convergence_h_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchical Convergence - All Dependencies",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": fan_out_tasks,
                    "priority": "high",
                },
            )
            convergence_tasks.append(convergence_h_result.data["id"])

            # Standalone convergence task requiring all fan-out tasks
            convergence_s_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Convergence - All Dependencies",
                    "projectRoot": planning_root,
                    "prerequisites": fan_out_tasks,
                    "priority": "high",
                },
            )
            convergence_tasks.append(convergence_s_result.data["id"])

            # Final convergence requiring both convergence tasks
            final_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Final Convergence - Mixed System",
                    "projectRoot": planning_root,
                    "prerequisites": convergence_tasks,
                    "priority": "high",
                },
            )

            # Test claiming behavior
            # Initially only root task should be claimable
            claim_result = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert claim_result.data["task"]["id"] == root_task_id

            # Complete root task, verify fan-out tasks become claimable
            await update_task_status(client, planning_root, root_task_id, "done")

            # All 6 fan-out tasks should now be claimable
            claimed_fan_out = []
            for _ in range(6):
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                claimed_task_id = claim_result.data["task"]["id"]
                assert claimed_task_id in fan_out_tasks
                claimed_fan_out.append(claimed_task_id)
                await update_task_status(client, planning_root, claimed_task_id, "done")

            # Verify all fan-out tasks were claimed exactly once
            assert set(claimed_fan_out) == set(fan_out_tasks)

            # Now convergence tasks should be claimable
            for convergence_task_id in convergence_tasks:
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                assert claim_result.data["task"]["id"] == convergence_task_id
                await update_task_status(client, planning_root, convergence_task_id, "done")

            # Finally, the final convergence task should be claimable
            final_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert final_claim.data["task"]["id"] == final_result.data["id"]

    @pytest.mark.asyncio
    async def test_diamond_dependency_pattern(self, temp_dir):
        """Test diamond dependency pattern across both task systems."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # Create hierarchical structure
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Diamond Pattern Project"
            )

            # Create diamond pattern:
            # Top (Standalone) → Left (Hierarchical) → Bottom (Standalone)
            #                  → Right (Standalone) → Bottom (Standalone)

            # Top of diamond - standalone task
            top_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Diamond Top - Standalone",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            top_task_id = top_result.data["id"]

            # Left path - hierarchical task
            left_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Diamond Left - Hierarchical",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": [top_task_id],
                    "priority": "normal",
                },
            )
            left_task_id = left_result.data["id"]

            # Right path - standalone task
            right_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Diamond Right - Standalone",
                    "projectRoot": planning_root,
                    "prerequisites": [top_task_id],
                    "priority": "normal",
                },
            )
            right_task_id = right_result.data["id"]

            # Bottom of diamond - standalone task requiring both paths
            bottom_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Diamond Bottom - Convergence",
                    "projectRoot": planning_root,
                    "prerequisites": [left_task_id, right_task_id],
                    "priority": "high",
                },
            )
            bottom_task_id = bottom_result.data["id"]

            # Test workflow progression
            # Start by claiming top task
            claim_result = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert claim_result.data["task"]["id"] == top_task_id

            # Complete top task (it's already in-progress from claiming)
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": top_task_id,
                    "summary": f"Completed {top_task_id} in diamond pattern",
                    "filesChanged": [f"diamond-{top_task_id}.py"],
                },
            )

            # Both left and right paths should now be claimable
            claimed_paths = []
            for _ in range(2):
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                claimed_task_id = claim_result.data["task"]["id"]
                assert claimed_task_id in [left_task_id, right_task_id]
                claimed_paths.append(claimed_task_id)

            # Verify both paths were claimed
            assert set(claimed_paths) == {left_task_id, right_task_id}

            # Complete one path - bottom should not be claimable yet
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": left_task_id,
                    "summary": f"Completed {left_task_id} in diamond left path",
                    "filesChanged": [f"diamond-left-{left_task_id}.py"],
                },
            )

            # Verify bottom is not yet claimable (right path still incomplete)
            # Should have no claimable tasks since right path is in-progress but not done
            try:
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                # If we get here, there was a claimable task when there shouldn't be
                assert (
                    False
                ), f"Expected no claimable tasks, but got: {claim_result.data['task']['id']}"
            except Exception as e:
                # This is expected - no tasks should be claimable
                assert "no unblocked tasks available" in str(e).lower()

            # Complete second path
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": right_task_id,
                    "summary": f"Completed {right_task_id} in diamond right path",
                    "filesChanged": [f"diamond-right-{right_task_id}.py"],
                },
            )

            # Now bottom should be claimable
            final_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert final_claim.data["task"]["id"] == bottom_task_id

    @pytest.mark.asyncio
    async def test_concurrent_mixed_dependency_operations(self, temp_dir):
        """Test concurrent operations on mixed dependency networks."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # Create hierarchical structure only (no extra tasks)
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Concurrent Operations Project"
            )

            # Create multiple independent dependency chains
            chain_roots = []
            for i in range(3):
                root_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Chain {i + 1} Root - Standalone",
                        "projectRoot": planning_root,
                        "priority": "high",
                    },
                )
                chain_roots.append(root_result.data["id"])

            # Create dependent tasks for each chain
            all_chains = []
            for i, root_id in enumerate(chain_roots):
                chain_tasks = [root_id]

                # Add hierarchical task
                hier_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Chain {i + 1} Level 2 - Hierarchical",
                        "projectRoot": planning_root,
                        "parent": hierarchy["feature_id"],
                        "prerequisites": [root_id],
                        "priority": "normal",
                    },
                )
                chain_tasks.append(hier_result.data["id"])

                # Add final standalone task
                final_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Chain {i + 1} Level 3 - Standalone",
                        "projectRoot": planning_root,
                        "prerequisites": [hier_result.data["id"]],
                        "priority": "low",
                    },
                )
                chain_tasks.append(final_result.data["id"])

                all_chains.append(chain_tasks)

            # Test concurrent claiming of independent chain roots

            # Create multiple claim tasks concurrently
            claim_tasks = []
            for _ in range(3):
                claim_task = asyncio.create_task(
                    client.call_tool("claimNextTask", {"projectRoot": planning_root})
                )
                claim_tasks.append(claim_task)

            # Wait for all claims to complete
            claim_results = await asyncio.gather(*claim_tasks)

            # Verify all root tasks were claimed
            claimed_ids = [result.data["task"]["id"] for result in claim_results]
            assert set(claimed_ids) == set(chain_roots)

            # Complete all claimed tasks concurrently
            complete_tasks = []
            for task_id in claimed_ids:
                complete_task = asyncio.create_task(
                    client.call_tool(
                        "completeTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": task_id,
                            "summary": f"Completed {task_id} concurrently",
                            "filesChanged": [f"test-{task_id}.py"],
                        },
                    )
                )
                complete_tasks.append(complete_task)

            # Wait for all completions
            await asyncio.gather(*complete_tasks)

            # Verify next level tasks are now claimable
            for chain in all_chains:
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                assert claim_result.data["task"]["id"] == chain[1]  # Second level task

    @pytest.mark.asyncio
    async def test_error_recovery_in_mixed_chains(self, temp_dir):
        """Test error handling and recovery in mixed dependency scenarios."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # Create hierarchical structure only
            hierarchy = await create_test_hierarchy(client, planning_root, "Error Recovery Project")

            # Test creation with invalid cross-system prerequisites
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": "Task with Invalid Prereq",
                        "projectRoot": planning_root,
                        "prerequisites": ["nonexistent-task-id"],
                        "priority": "high",
                    },
                )

            error_msg = str(exc_info.value).lower()
            assert any(
                phrase in error_msg
                for phrase in ["does not exist", "not found", "invalid prerequisite"]
            )

            # Test creation with malicious cross-system prerequisites
            malicious_prereqs = [
                "../../../etc/passwd",
                "/etc/passwd",
                "task\x00name",
                "task/../../../sensitive",
            ]

            for malicious_prereq in malicious_prereqs:
                with pytest.raises(Exception):
                    await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": "Task with Malicious Prereq",
                            "projectRoot": planning_root,
                            "prerequisites": [malicious_prereq],
                            "priority": "high",
                        },
                    )

            # Test circular dependency detection across systems
            # Create foundation task
            foundation_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Foundation for Cycle Test",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            foundation_id = foundation_result.data["id"]

            # Create hierarchical task depending on foundation
            hier_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchical Middle for Cycle",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": [foundation_id],
                    "priority": "normal",
                },
            )
            hier_id = hier_result.data["id"]

            # Attempt to create circular dependency by updating foundation
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": foundation_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [hier_id]},
                    },
                )

            error_msg = str(exc_info.value).lower()
            assert any(
                phrase in error_msg for phrase in ["circular", "cycle", "circular dependency"]
            )

            # Test recovery from partial failures
            # Create a task that will succeed
            success_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Success Task for Recovery Test",
                    "projectRoot": planning_root,
                    "prerequisites": [foundation_id],
                    "priority": "normal",
                },
            )

            # Verify the successful task was created correctly
            retrieved_task = await client.call_tool(
                "getObject",
                {
                    "id": success_task_result.data["id"],
                    "projectRoot": planning_root,
                },
            )

            assert retrieved_task.data["yaml"]["prerequisites"] == [foundation_id]
            assert retrieved_task.data["yaml"]["title"] == "Success Task for Recovery Test"

    @pytest.mark.asyncio
    async def test_deep_chain_cycle_detection(self, temp_dir):
        """Test cycle detection in deep cross-system dependency chains."""
        settings = Settings(
            planning_root=temp_dir / "planning",
            debug_mode=True,
            log_level="DEBUG",
        )
        server = create_server(settings)
        planning_root = str(temp_dir / "planning")

        async with Client(server) as client:
            # Create hierarchical structure
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Deep Chain Cycle Project"
            )

            # Create a 7-level chain alternating between standalone and hierarchical
            chain_tasks = []

            # Level 1: Standalone
            level1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Deep Chain Level 1 - Standalone",
                    "projectRoot": planning_root,
                    "priority": "high",
                },
            )
            chain_tasks.append(level1_result.data["id"])

            # Create remaining levels
            for i in range(1, 7):
                if i % 2 == 1:  # Even index = hierarchical
                    task_result = await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": f"Deep Chain Level {i + 1} - Hierarchical",
                            "projectRoot": planning_root,
                            "parent": hierarchy["feature_id"],
                            "prerequisites": [chain_tasks[i - 1]],
                            "priority": "normal",
                        },
                    )
                else:  # Odd index = standalone
                    task_result = await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": f"Deep Chain Level {i + 1} - Standalone",
                            "projectRoot": planning_root,
                            "prerequisites": [chain_tasks[i - 1]],
                            "priority": "normal",
                        },
                    )
                chain_tasks.append(task_result.data["id"])

            # Test cycle detection at different levels
            # Try to create cycle from level 7 back to level 1
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": chain_tasks[0],  # Level 1
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [chain_tasks[6]]},  # Level 7
                    },
                )

            error_msg = str(exc_info.value).lower()
            assert any(
                phrase in error_msg for phrase in ["circular", "cycle", "circular dependency"]
            )

            # Try to create cycle from level 5 back to level 3
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": chain_tasks[2],  # Level 3
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [chain_tasks[4]]},  # Level 5
                    },
                )

            error_msg = str(exc_info.value).lower()
            assert any(
                phrase in error_msg for phrase in ["circular", "cycle", "circular dependency"]
            )

            # Verify that valid operation still works
            # Add a new task depending on the last level
            valid_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Valid Final Task",
                    "projectRoot": planning_root,
                    "prerequisites": [chain_tasks[6]],
                    "priority": "low",
                },
            )

            # Verify the valid task was created
            assert valid_task_result.data["id"] is not None

            # Verify the chain is still intact
            for i, task_id in enumerate(chain_tasks[1:], 1):
                task = await client.call_tool(
                    "getObject",
                    {
                        "id": task_id,
                        "projectRoot": planning_root,
                    },
                )
                assert task.data["yaml"]["prerequisites"] == [chain_tasks[i - 1]]
