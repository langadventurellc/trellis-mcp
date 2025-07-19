"""Comprehensive integration workflow tests for complete task lifecycle operations.

This module tests realistic end-to-end workflow scenarios that validate complete
task lifecycle operations with cross-system dependencies, combining multiple
MCP tool operations in realistic development workflows.

These tests go beyond individual operation testing to verify complete workflow
integration across both hierarchical and standalone task systems.
"""

import time

import pytest
from fastmcp import Client
from tests.integration.test_helpers import (
    assert_mixed_task_consistency,
    assert_task_structure,
    create_mixed_task_environment,
    create_standalone_task,
    create_test_hierarchy,
    create_test_server,
    update_task_status,
)


class TestComprehensiveIntegrationWorkflows:
    """Test comprehensive integration workflow scenarios."""

    @pytest.mark.asyncio
    async def test_complete_multi_project_workflow_integration(self, temp_dir):
        """Test complete multi-project workflow with mixed task dependencies.

        This test simulates a realistic multi-project development scenario with:
        - Multiple projects with cross-project dependencies
        - Mixed task types (hierarchical and standalone)
        - Complete workflow: Creation → Claiming → Review → Completion
        - Cross-system dependency resolution throughout lifecycle
        """
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Phase 1: Create multiple projects with mixed dependencies
            projects = []
            for i in range(3):
                project_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "project",
                        "title": f"Integration Project {i + 1}",
                        "description": f"Multi-project workflow test project {i + 1}",
                        "projectRoot": planning_root,
                    },
                )
                projects.append(
                    {
                        "id": project_result.data["id"],
                        "title": f"Integration Project {i + 1}",
                    }
                )

            # Create epic and feature structure for each project
            features = []
            for i, project in enumerate(projects):
                epic_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "epic",
                        "title": f"Integration Epic {i + 1}",
                        "projectRoot": planning_root,
                        "parent": project["id"],
                    },
                )

                feature_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "feature",
                        "title": f"Integration Feature {i + 1}",
                        "projectRoot": planning_root,
                        "parent": epic_result.data["id"],
                    },
                )
                features.append(feature_result.data["id"])

            # Phase 2: Create foundation tasks (no dependencies)
            foundation_tasks = []

            # Create standalone foundation tasks
            for i in range(2):
                task_result = await create_standalone_task(
                    client,
                    planning_root,
                    f"Foundation Standalone Task {i + 1}",
                    "high",
                    "Foundation task for multi-project workflow",
                )
                foundation_tasks.append(
                    {
                        "id": task_result["id"],
                        "type": "standalone",
                        "title": f"Foundation Standalone Task {i + 1}",
                    }
                )

            # Create hierarchical foundation task
            foundation_hier_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Foundation Hierarchical Task",
                    "projectRoot": planning_root,
                    "parent": features[0],
                    "priority": "high",
                },
            )
            foundation_tasks.append(
                {
                    "id": foundation_hier_result.data["id"],
                    "type": "hierarchical",
                    "title": "Foundation Hierarchical Task",
                }
            )

            # Phase 3: Create dependent tasks with cross-system dependencies
            dependent_tasks = []

            # Create tasks that depend on foundation tasks (mix of systems)
            for i in range(4):
                if i % 2 == 0:  # Even indices: hierarchical tasks
                    hier_result = await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": f"Dependent Hierarchical Task {i + 1}",
                            "projectRoot": planning_root,
                            "parent": features[i % len(features)],
                            "prerequisites": [foundation_tasks[i % len(foundation_tasks)]["id"]],
                            "priority": "normal",
                        },
                    )
                    task_id = hier_result.data["id"]
                else:  # Odd indices: standalone tasks
                    standalone_result = await create_standalone_task(
                        client,
                        planning_root,
                        f"Dependent Standalone Task {i + 1}",
                        "normal",
                        (
                            "Standalone task depending on "
                            f"{foundation_tasks[i % len(foundation_tasks)]['title']}"
                        ),
                    )
                    task_id = standalone_result["id"]
                    # Add prerequisites to standalone task
                    await client.call_tool(
                        "updateObject",
                        {
                            "kind": "task",
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {
                                "prerequisites": [foundation_tasks[i % len(foundation_tasks)]["id"]]
                            },
                        },
                    )
                dependent_tasks.append(
                    {
                        "id": task_id,
                        "type": "hierarchical" if i % 2 == 0 else "standalone",
                        "title": (
                            f"Dependent {'Hierarchical' if i % 2 == 0 else 'Standalone'} "
                            f"Task {i + 1}"
                        ),
                    }
                )

            # Phase 4: Create final integration tasks
            integration_tasks = []

            # Create tasks that require multiple dependent tasks (simulating feature completion)
            for i in range(2):
                prereq_tasks = dependent_tasks[i * 2 : (i + 1) * 2]  # Take 2 dependent tasks each

                task_result = await create_standalone_task(
                    client,
                    planning_root,
                    f"Integration Task {i + 1}",
                    "high",
                    "Final integration task requiring multiple dependencies",
                )

                # Add multiple prerequisites from different systems
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": task_result["id"],
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [t["id"] for t in prereq_tasks]},
                    },
                )

                integration_tasks.append(
                    {
                        "id": task_result["id"],
                        "type": "standalone",
                        "title": f"Integration Task {i + 1}",
                        "prerequisites": [t["id"] for t in prereq_tasks],
                    }
                )

            # Phase 5: Test complete workflow execution
            start_time = time.perf_counter()

            # Step 1: Verify initial state - only foundation tasks should be claimable
            initial_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert initial_backlog.structured_content is not None
            all_tasks = initial_backlog.structured_content["tasks"]

            # Verify we have the expected total number of tasks
            expected_total = len(foundation_tasks) + len(dependent_tasks) + len(integration_tasks)
            assert len(all_tasks) == expected_total

            # Debug: Check task states and prerequisites
            for task in all_tasks:
                if task["id"] in [t["id"] for t in integration_tasks]:
                    # Verify integration tasks have prerequisites
                    integration_task = next(t for t in integration_tasks if t["id"] == task["id"])
                    task_obj = await client.call_tool(
                        "getObject",
                        {
                            "kind": "task",
                            "id": task["id"],
                            "projectRoot": planning_root,
                        },
                    )
                    task_prereqs = task_obj.data["yaml"].get("prerequisites", [])
                    assert (
                        task_prereqs == integration_task["prerequisites"]
                    ), f"Integration task {task['id']} prerequisites mismatch"

            # Step 2: Claim and complete foundation tasks in sequence
            completed_foundation = []
            for foundation_task in foundation_tasks:
                # Claim the task
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                claimed_task = claim_result.data["task"]
                assert claimed_task["id"] == foundation_task["id"]
                assert claimed_task["status"] == "in-progress"

                # Move to review status
                await update_task_status(client, planning_root, foundation_task["id"], "review")

                # Complete the task
                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": foundation_task["id"],
                        "summary": (
                            f"Completed {foundation_task['title']} in " "multi-project workflow"
                        ),
                        "filesChanged": [
                            f"foundation-{foundation_task['type']}-{foundation_task['id']}.py"
                        ],
                    },
                )
                completed_foundation.append(foundation_task["id"])

            # Step 3: Verify dependent tasks become claimable as foundations complete
            # Note: claimNextTask returns tasks by priority, not by creation order
            # We need to claim all available tasks and verify they're the expected ones
            claimed_dependent_tasks = []
            for _ in range(len(dependent_tasks)):
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                claimed_task = claim_result.data["task"]
                claimed_dependent_tasks.append(claimed_task["id"])

            # Verify all dependent tasks were claimed (order may vary)
            dependent_task_ids = [t["id"] for t in dependent_tasks]
            assert set(claimed_dependent_tasks) == set(dependent_task_ids)

            # Complete all claimed dependent tasks
            for task_id in claimed_dependent_tasks:
                # Find the original task info
                dependent_task = next(t for t in dependent_tasks if t["id"] == task_id)

                # Complete dependent task workflow
                await update_task_status(client, planning_root, task_id, "review")

                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                        "summary": (
                            f"Completed {dependent_task['title']} with " "cross-system dependencies"
                        ),
                        "filesChanged": [f"dependent-{dependent_task['type']}-{task_id}.py"],
                    },
                )

            # Step 4: Verify integration tasks become claimable
            for integration_task in integration_tasks:
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                claimed_task = claim_result.data["task"]
                assert claimed_task["id"] == integration_task["id"]

                # Complete integration workflow
                await update_task_status(client, planning_root, integration_task["id"], "review")

                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": integration_task["id"],
                        "summary": f"Completed {integration_task['title']} - final integration",
                        "filesChanged": [
                            f"integration-{integration_task['id']}.py",
                            "deployment.yaml",
                        ],
                    },
                )

            end_time = time.perf_counter()
            total_workflow_time = (end_time - start_time) * 1000

            # Phase 6: Validate final state
            final_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert final_backlog.structured_content is not None
            final_tasks = final_backlog.structured_content["tasks"]

            # All tasks should be completed
            for task in final_tasks:
                assert (
                    task["status"] == "done"
                ), f"Task {task['id']} should be done but is {task['status']}"

            # Verify no more claimable tasks
            try:
                await client.call_tool("claimNextTask", {"projectRoot": planning_root})
                assert False, "Expected no claimable tasks remaining"
            except Exception as e:
                assert "no" in str(e).lower() and "available" in str(e).lower()

            # Performance validation
            assert (
                total_workflow_time < 10000
            ), f"Complete workflow took {total_workflow_time:.2f}ms, should be <10s"

            # Consistency validation
            expected_hierarchy = 1 + len(
                [t for t in dependent_tasks if t["type"] == "hierarchical"]
            )  # foundation + dependents
            expected_standalone = (
                2
                + len([t for t in dependent_tasks if t["type"] == "standalone"])
                + len(integration_tasks)
            )  # foundations + dependents + integrations

            assert_mixed_task_consistency(final_tasks, expected_hierarchy, expected_standalone)

    @pytest.mark.asyncio
    async def test_complex_dependency_chain_workflow_integration(self, temp_dir):
        """Test complex dependency chain workflows with realistic development patterns.

        This test simulates realistic development scenarios with:
        - Multi-level dependency chains across both task systems
        - Parallel development streams that converge
        - Feature branch workflows with cross-system coordination
        """
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create project hierarchy
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Complex Dependency Project"
            )

            # Phase 1: Create foundation infrastructure tasks (parallel streams)
            infrastructure_tasks = []

            # Database setup stream (standalone)
            db_task = await create_standalone_task(
                client,
                planning_root,
                "Database Schema Setup",
                "high",
                "Set up initial database schema",
            )
            infrastructure_tasks.append(
                {"id": db_task["id"], "type": "standalone", "stream": "database"}
            )

            # API framework stream (hierarchical)
            api_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "API Framework Setup",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "priority": "high",
                },
            )
            infrastructure_tasks.append(
                {"id": api_task_result.data["id"], "type": "hierarchical", "stream": "api"}
            )

            # Frontend framework stream (standalone)
            fe_task = await create_standalone_task(
                client,
                planning_root,
                "Frontend Framework Setup",
                "high",
                "Set up frontend development environment",
            )
            infrastructure_tasks.append(
                {"id": fe_task["id"], "type": "standalone", "stream": "frontend"}
            )

            # Phase 2: Create feature development tasks (dependent on infrastructure)
            feature_tasks = []

            # User authentication feature (depends on DB + API)
            auth_api_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "User Authentication API",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": [
                        next(t["id"] for t in infrastructure_tasks if t["stream"] == "database"),
                        next(t["id"] for t in infrastructure_tasks if t["stream"] == "api"),
                    ],
                    "priority": "normal",
                },
            )
            feature_tasks.append(
                {"id": auth_api_result.data["id"], "type": "hierarchical", "feature": "auth"}
            )

            # User authentication UI (depends on Frontend + Auth API)
            auth_ui_task = await create_standalone_task(
                client,
                planning_root,
                "User Authentication UI",
                "normal",
                "User interface for authentication",
            )
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": auth_ui_task["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {
                        "prerequisites": [
                            next(
                                t["id"] for t in infrastructure_tasks if t["stream"] == "frontend"
                            ),
                            auth_api_result.data["id"],
                        ]
                    },
                },
            )
            feature_tasks.append(
                {"id": auth_ui_task["id"], "type": "standalone", "feature": "auth"}
            )

            # Data management feature (depends on DB)
            data_api_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Data Management API",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": [
                        next(t["id"] for t in infrastructure_tasks if t["stream"] == "database")
                    ],
                    "priority": "normal",
                },
            )
            feature_tasks.append(
                {"id": data_api_result.data["id"], "type": "hierarchical", "feature": "data"}
            )

            # Phase 3: Create integration tasks (depend on multiple features)
            integration_tasks = []

            # End-to-end testing (requires all features)
            e2e_task = await create_standalone_task(
                client,
                planning_root,
                "End-to-End Testing",
                "high",
                "Complete end-to-end testing across all features",
            )
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": e2e_task["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"prerequisites": [t["id"] for t in feature_tasks]},
                },
            )
            integration_tasks.append({"id": e2e_task["id"], "type": "standalone"})

            # Deployment pipeline (hierarchical, requires E2E)
            deploy_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Deployment Pipeline Setup",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": [e2e_task["id"]],
                    "priority": "high",
                },
            )
            integration_tasks.append({"id": deploy_result.data["id"], "type": "hierarchical"})

            # Phase 4: Execute workflow with realistic development patterns

            # Start by claiming all infrastructure tasks in parallel (simulating team work)
            start_time = time.perf_counter()

            claimed_infrastructure = []
            for infra_task in infrastructure_tasks:
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                claimed_task_id = claim_result.data["task"]["id"]
                assert claimed_task_id == infra_task["id"]
                claimed_infrastructure.append(claimed_task_id)

            # Complete infrastructure tasks in realistic order (DB first, then parallel)
            # Complete DB first (other tasks depend on it)
            db_task_id = next(t["id"] for t in infrastructure_tasks if t["stream"] == "database")
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": db_task_id,
                    "summary": "Database schema setup completed",
                    "filesChanged": ["schema.sql", "migrations/001_initial.sql"],
                },
            )

            # Complete API and Frontend in parallel (simulate concurrent development)
            remaining_infra = [t["id"] for t in infrastructure_tasks if t["stream"] != "database"]
            for task_id in remaining_infra:
                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                        "summary": f"Infrastructure task {task_id} completed",
                        "filesChanged": [f"infra-{task_id}.py", f"config-{task_id}.yaml"],
                    },
                )

            # Claim and work on feature tasks (some can be parallel, some dependent)
            # Both Data API and Auth API can start now (their prerequisites are met)
            # Claim both tasks - order may vary since they have same priority
            claimed_feature_tasks = []
            for _ in range(2):  # We expect 2 tasks to be claimable
                claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
                claimed_feature_tasks.append(claim.data["task"]["id"])

            # Verify we got both expected tasks (order doesn't matter)
            expected_ids = {data_api_result.data["id"], auth_api_result.data["id"]}
            assert set(claimed_feature_tasks) == expected_ids

            # Complete both feature API tasks (order doesn't matter for the test)
            for task_id in claimed_feature_tasks:
                if task_id == data_api_result.data["id"]:
                    summary = "Data management API implementation completed"
                    files = ["api/data.py", "tests/test_data_api.py"]
                else:  # auth_api_result
                    summary = "User authentication API completed"
                    files = ["api/auth.py", "tests/test_auth_api.py"]

                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                        "summary": summary,
                        "filesChanged": files,
                    },
                )

            # Now auth UI should be claimable (depends on Frontend + Auth API)
            auth_ui_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert auth_ui_claim.data["task"]["id"] == auth_ui_task["id"]

            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": auth_ui_task["id"],
                    "summary": "User authentication UI completed",
                    "filesChanged": ["ui/auth.js", "ui/auth.css", "tests/test_auth_ui.js"],
                },
            )

            # Integration tasks should now be claimable
            e2e_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert e2e_claim.data["task"]["id"] == e2e_task["id"]

            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": e2e_task["id"],
                    "summary": "End-to-end testing completed across all features",
                    "filesChanged": [
                        "tests/e2e/auth_flow.js",
                        "tests/e2e/data_flow.js",
                        "cypress.json",
                    ],
                },
            )

            # Final deployment task
            deploy_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert deploy_claim.data["task"]["id"] == deploy_result.data["id"]

            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": deploy_result.data["id"],
                    "summary": "Deployment pipeline setup completed",
                    "filesChanged": ["deploy/pipeline.yaml", "deploy/production.yaml"],
                },
            )

            end_time = time.perf_counter()
            workflow_time = (end_time - start_time) * 1000

            # Validation
            final_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert final_backlog.structured_content is not None
            final_tasks = final_backlog.structured_content["tasks"]

            # All tasks should be completed
            for task in final_tasks:
                assert task["status"] == "done"

            # Verify realistic development performance
            assert (
                workflow_time < 5000
            ), f"Complex workflow took {workflow_time:.2f}ms, should be <5s"

            # Verify task distribution across systems
            hierarchy_tasks = [t for t in final_tasks if t.get("parent")]
            standalone_tasks = [t for t in final_tasks if not t.get("parent")]

            assert len(hierarchy_tasks) >= 3  # API, Auth API, Deploy
            assert len(standalone_tasks) >= 4  # DB, Frontend, Auth UI, E2E

    @pytest.mark.asyncio
    async def test_team_collaboration_workflow_simulation(self, temp_dir):
        """Test team collaboration workflow with multiple developers working on mixed tasks.

        Simulates realistic team development patterns with:
        - Multiple developers claiming tasks concurrently
        - Review workflow across different team members
        - Realistic task completion patterns
        - Cross-system coordination in team environment
        """
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create mixed task environment for team collaboration
            team_env = await create_mixed_task_environment(
                client, planning_root, "Team Collaboration Project"
            )

            # Add additional tasks to simulate realistic team workload
            additional_tasks = []

            # Add more hierarchical tasks
            for i in range(3):
                task_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Additional Hierarchy Task {i + 1}",
                        "projectRoot": planning_root,
                        "parent": team_env["hierarchy"]["feature_id"],
                        "priority": ["high", "normal", "low"][i % 3],
                    },
                )
                additional_tasks.append({"id": task_result.data["id"], "type": "hierarchical"})

            # Add more standalone tasks
            for i in range(4):
                task_result = await create_standalone_task(
                    client,
                    planning_root,
                    f"Additional Standalone Task {i + 1}",
                    ["high", "normal", "low"][i % 3],
                    "Additional standalone task for team collaboration testing",
                )
                additional_tasks.append({"id": task_result["id"], "type": "standalone"})

            # Phase 1: Simulate multiple developers claiming tasks simultaneously
            start_time = time.perf_counter()

            # Simulate 4 developers each claiming 2-3 tasks
            developers = [
                {"name": "dev1", "workspace": "/workspace/dev1", "claimed_tasks": []},
                {"name": "dev2", "workspace": "/workspace/dev2", "claimed_tasks": []},
                {"name": "dev3", "workspace": "/workspace/dev3", "claimed_tasks": []},
                {"name": "dev4", "workspace": "/workspace/dev4", "claimed_tasks": []},
            ]

            # Claim tasks for each developer
            for dev in developers:
                for claim_count in range(2):  # Each dev claims 2 tasks
                    try:
                        claim_result = await client.call_tool(
                            "claimNextTask",
                            {"projectRoot": planning_root, "worktree": dev["workspace"]},
                        )
                        dev["claimed_tasks"].append(claim_result.data["task"]["id"])
                    except Exception:
                        # No more tasks available
                        break

            # Verify all high priority tasks were claimed first
            claimed_task_ids = [task_id for dev in developers for task_id in dev["claimed_tasks"]]

            # Get initial task info to verify priority ordering
            initial_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert initial_backlog.structured_content is not None
            all_tasks = initial_backlog.structured_content["tasks"]

            high_priority_tasks = [t["id"] for t in all_tasks if t["priority"] == "high"]
            claimed_high_priority = [tid for tid in claimed_task_ids if tid in high_priority_tasks]

            # Most high priority tasks should be claimed
            assert len(claimed_high_priority) >= len(high_priority_tasks) * 0.8

            # Phase 2: Simulate realistic development workflow

            # Developer 1 & 2: Complete their first tasks quickly (simulating small tasks)
            for dev_name in ["dev1", "dev2"]:
                dev = next(d for d in developers if d["name"] == dev_name)
                if dev["claimed_tasks"]:
                    task_id = dev["claimed_tasks"][0]
                    await client.call_tool(
                        "completeTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": task_id,
                            "summary": f"Quick completion by {dev_name}",
                            "filesChanged": [f"{dev_name}-quick-{task_id}.py"],
                        },
                    )

            # Developer 3: Move first task to review (simulating PR workflow)
            dev3 = next(d for d in developers if d["name"] == "dev3")
            if dev3["claimed_tasks"]:
                await update_task_status(client, planning_root, dev3["claimed_tasks"][0], "review")

            # Developer 4: Still working (keep in in-progress)
            # No action needed - tasks remain in-progress

            # Phase 3: Simulate review workflow

            # Get next reviewable task (should be dev3's task)
            review_result = await client.call_tool(
                "getNextReviewableTask", {"projectRoot": planning_root}
            )

            if review_result.data["task"]:
                reviewable_task = review_result.data["task"]
                assert reviewable_task["id"] == dev3["claimed_tasks"][0]
                assert reviewable_task["status"] == "review"

                # Complete the review (simulate approval)
                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": reviewable_task["id"],
                        "summary": "Review completed and approved",
                        "filesChanged": [f"reviewed-{reviewable_task['id']}.py"],
                    },
                )

            # Phase 4: Simulate task handoff and continued development

            # Developers 1 & 2 claim new tasks (simulating continuous work)
            for dev_name in ["dev1", "dev2"]:
                dev = next(d for d in developers if d["name"] == dev_name)
                try:
                    claim_result = await client.call_tool(
                        "claimNextTask",
                        {"projectRoot": planning_root, "worktree": dev["workspace"]},
                    )
                    dev["claimed_tasks"].append(claim_result.data["task"]["id"])
                except Exception:
                    # No more tasks available
                    pass

            # Phase 5: Complete remaining work

            # First, claim and complete any remaining open tasks
            while True:
                try:
                    claim_result = await client.call_tool(
                        "claimNextTask", {"projectRoot": planning_root}
                    )
                    remaining_task_id = claim_result.data["task"]["id"]

                    # Move to review and complete
                    await update_task_status(client, planning_root, remaining_task_id, "review")
                    await client.call_tool(
                        "completeTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": remaining_task_id,
                            "summary": "Remaining task completed",
                            "filesChanged": [f"remaining-{remaining_task_id}.py"],
                        },
                    )
                except Exception:
                    # No more claimable tasks
                    break

            # Complete all remaining in-progress tasks
            remaining_backlog = await client.call_tool(
                "listBacklog", {"projectRoot": planning_root}
            )
            assert remaining_backlog.structured_content is not None
            remaining_tasks = remaining_backlog.structured_content["tasks"]

            in_progress_tasks = [t for t in remaining_tasks if t["status"] == "in-progress"]

            for task in in_progress_tasks:
                # Move to review first
                await update_task_status(client, planning_root, task["id"], "review")

                # Complete the task
                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task["id"],
                        "summary": "Team collaboration task completed",
                        "filesChanged": [f"team-{task['id']}.py", "team.md"],
                    },
                )

            end_time = time.perf_counter()
            collaboration_time = (end_time - start_time) * 1000

            # Phase 6: Validation

            final_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert final_backlog.structured_content is not None
            final_tasks = final_backlog.structured_content["tasks"]

            # All tasks should be completed
            for task in final_tasks:
                assert task["status"] == "done"

            # Verify no reviewable tasks remain
            final_review = await client.call_tool(
                "getNextReviewableTask", {"projectRoot": planning_root}
            )
            assert final_review.data["task"] is None

            # Verify no claimable tasks remain
            try:
                await client.call_tool("claimNextTask", {"projectRoot": planning_root})
                assert False, "Expected no claimable tasks remaining"
            except Exception as e:
                assert "no" in str(e).lower() and "available" in str(e).lower()

            # Performance validation for team workflow
            assert (
                collaboration_time < 8000
            ), f"Team collaboration took {collaboration_time:.2f}ms, should be <8s"

            # Verify mixed task consistency
            expected_hierarchy = len(team_env["hierarchy_tasks"]) + len(
                [t for t in additional_tasks if t["type"] == "hierarchical"]
            )
            expected_standalone = len(team_env["standalone_tasks"]) + len(
                [t for t in additional_tasks if t["type"] == "standalone"]
            )

            assert_mixed_task_consistency(final_tasks, expected_hierarchy, expected_standalone)

    @pytest.mark.asyncio
    async def test_release_management_integration_workflow(self, temp_dir):
        """Test release management workflow with cross-system coordination.

        Simulates a realistic software release scenario with:
        - Feature development across both task systems
        - Release preparation tasks triggered by feature completion
        - Cross-system coordination for release workflows
        - Integration testing and deployment coordination
        """
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create release project structure
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Release Management Project"
            )

            # Phase 1: Create feature development tasks
            features = []

            # Feature 1: User Management (mixed tasks)
            user_mgmt_tasks = []

            # Backend API (hierarchical)
            user_api_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "User Management API",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "priority": "high",
                },
            )
            user_mgmt_tasks.append(user_api_result.data["id"])

            # Frontend UI (standalone)
            user_ui_task = await create_standalone_task(
                client,
                planning_root,
                "User Management UI",
                "high",
                "User interface for user management features",
            )
            user_mgmt_tasks.append(user_ui_task["id"])

            # Database migration (standalone)
            user_db_task = await create_standalone_task(
                client,
                planning_root,
                "User Management Database",
                "high",
                "Database schema for user management",
            )
            user_mgmt_tasks.append(user_db_task["id"])

            features.append(
                {"name": "User Management", "tasks": user_mgmt_tasks, "priority": "high"}
            )

            # Feature 2: Reporting System (mixed tasks)
            reporting_tasks = []

            # Reporting API (hierarchical)
            report_api_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Reporting API",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "priority": "normal",
                },
            )
            reporting_tasks.append(report_api_result.data["id"])

            # Reporting UI (standalone)
            report_ui_task = await create_standalone_task(
                client,
                planning_root,
                "Reporting Dashboard",
                "normal",
                "Dashboard interface for reporting system",
            )
            reporting_tasks.append(report_ui_task["id"])

            features.append(
                {"name": "Reporting System", "tasks": reporting_tasks, "priority": "normal"}
            )

            # Phase 2: Create release preparation tasks (depend on features)
            release_tasks = []

            # Integration testing (requires all features)
            all_feature_tasks = [task_id for feature in features for task_id in feature["tasks"]]

            integration_test_task = await create_standalone_task(
                client,
                planning_root,
                "Release Integration Testing",
                "high",
                "Integration testing for release candidate",
            )
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": integration_test_task["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"prerequisites": all_feature_tasks},
                },
            )
            release_tasks.append(integration_test_task["id"])

            # Release documentation (hierarchical, depends on features)
            release_docs_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Release Documentation",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": all_feature_tasks,
                    "priority": "normal",
                },
            )
            release_tasks.append(release_docs_result.data["id"])

            # Security audit (standalone, depends on integration testing)
            security_audit_task = await create_standalone_task(
                client,
                planning_root,
                "Security Audit",
                "high",
                "Security audit for release candidate",
            )
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": security_audit_task["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"prerequisites": [integration_test_task["id"]]},
                },
            )
            release_tasks.append(security_audit_task["id"])

            # Phase 3: Create deployment tasks (depend on release preparation)
            deployment_tasks = []

            # Production deployment (hierarchical)
            deployment_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Production Deployment",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "prerequisites": release_tasks,
                    "priority": "high",
                },
            )
            deployment_tasks.append(deployment_result.data["id"])

            # Post-deployment verification (standalone)
            verification_task = await create_standalone_task(
                client,
                planning_root,
                "Post-Deployment Verification",
                "high",
                "Verify deployment success and system health",
            )
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": verification_task["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"prerequisites": [deployment_result.data["id"]]},
                },
            )
            deployment_tasks.append(verification_task["id"])

            # Phase 4: Execute release workflow
            start_time = time.perf_counter()

            # Step 1: Complete feature development (can be done in parallel)
            # Complete User Management feature tasks
            for feature in features:
                if feature["name"] == "User Management":
                    # All user management tasks can be done in parallel
                    for task_id in feature["tasks"]:
                        claim_result = await client.call_tool(
                            "claimNextTask", {"projectRoot": planning_root}
                        )
                        assert claim_result.data["task"]["id"] == task_id

                        await client.call_tool(
                            "completeTask",
                            {
                                "projectRoot": planning_root,
                                "taskId": task_id,
                                "summary": "User Management feature task completed",
                                "filesChanged": [f"user-mgmt-{task_id}.py", "user-mgmt.md"],
                            },
                        )

            # Step 2: Complete Reporting feature tasks (can be parallel to some extent)
            for feature in features:
                if feature["name"] == "Reporting System":
                    for task_id in feature["tasks"]:
                        claim_result = await client.call_tool(
                            "claimNextTask", {"projectRoot": planning_root}
                        )
                        assert claim_result.data["task"]["id"] == task_id

                        await client.call_tool(
                            "completeTask",
                            {
                                "projectRoot": planning_root,
                                "taskId": task_id,
                                "summary": "Reporting System feature task completed",
                                "filesChanged": [f"reporting-{task_id}.py", "reporting.md"],
                            },
                        )

            # Step 3: Release preparation tasks should now be claimable
            # Integration testing should be claimable first
            integration_claim = await client.call_tool(
                "claimNextTask", {"projectRoot": planning_root}
            )
            assert integration_claim.data["task"]["id"] == integration_test_task["id"]

            # Documentation can be claimed in parallel
            docs_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert docs_claim.data["task"]["id"] == release_docs_result.data["id"]

            # Complete documentation first
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": release_docs_result.data["id"],
                    "summary": "Release documentation completed",
                    "filesChanged": ["CHANGELOG.md", "RELEASE_NOTES.md", "docs/api.md"],
                },
            )

            # Complete integration testing
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": integration_test_task["id"],
                    "summary": "Release integration testing completed",
                    "filesChanged": ["tests/integration/release.js", "test-results.xml"],
                },
            )

            # Step 4: Security audit should now be claimable
            security_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert security_claim.data["task"]["id"] == security_audit_task["id"]

            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": security_audit_task["id"],
                    "summary": "Security audit completed successfully",
                    "filesChanged": ["security-audit.pdf", "vulnerability-report.md"],
                },
            )

            # Step 5: Deployment tasks should now be claimable
            deploy_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert deploy_claim.data["task"]["id"] == deployment_result.data["id"]

            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": deployment_result.data["id"],
                    "summary": "Production deployment completed successfully",
                    "filesChanged": ["deploy.log", "production.yaml", "rollback.sh"],
                },
            )

            # Step 6: Post-deployment verification
            verify_claim = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert verify_claim.data["task"]["id"] == verification_task["id"]

            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": verification_task["id"],
                    "summary": "Post-deployment verification completed - release successful",
                    "filesChanged": ["health-check.log", "monitoring-setup.yaml"],
                },
            )

            end_time = time.perf_counter()
            release_time = (end_time - start_time) * 1000

            # Phase 5: Validation
            final_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert final_backlog.structured_content is not None
            final_tasks = final_backlog.structured_content["tasks"]

            # All tasks should be completed
            for task in final_tasks:
                assert task["status"] == "done"

            # Verify release workflow performance
            assert release_time < 6000, f"Release workflow took {release_time:.2f}ms, should be <6s"

            # Verify task distribution and completion order was correct
            hierarchy_tasks = [t for t in final_tasks if t.get("parent")]
            standalone_tasks = [t for t in final_tasks if not t.get("parent")]

            # Should have hierarchical tasks for APIs, docs, deployment
            assert len(hierarchy_tasks) >= 4
            # Should have standalone tasks for UI, DB, testing, audit, verification
            assert len(standalone_tasks) >= 5

            # Verify no tasks remain claimable
            try:
                await client.call_tool("claimNextTask", {"projectRoot": planning_root})
                assert False, "Expected no claimable tasks after release completion"
            except Exception as e:
                assert "no" in str(e).lower() and "available" in str(e).lower()

    @pytest.mark.asyncio
    async def test_error_recovery_and_workflow_resilience(self, temp_dir):
        """Test workflow recovery from various failure scenarios.

        Tests system resilience and recovery capabilities with:
        - Invalid dependency scenarios and recovery
        - Partial failure recovery workflows
        - System consistency during error conditions
        - Graceful degradation and recovery patterns
        """
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy for error scenarios
            hierarchy = await create_test_hierarchy(client, planning_root, "Error Recovery Project")

            # Phase 1: Test invalid prerequisite handling and recovery

            # Create valid foundation task
            foundation_task = await create_standalone_task(
                client,
                planning_root,
                "Foundation Task",
                "high",
                "Valid foundation task for error recovery testing",
            )

            # Attempt to create task with invalid prerequisite
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": "Task with Invalid Prerequisite",
                        "projectRoot": planning_root,
                        "prerequisites": ["nonexistent-task-123"],
                        "priority": "high",
                    },
                )

            error_msg = str(exc_info.value).lower()
            assert any(phrase in error_msg for phrase in ["does not exist", "not found", "invalid"])

            # Verify system state remains consistent after error
            backlog_after_error = await client.call_tool(
                "listBacklog", {"projectRoot": planning_root}
            )
            assert backlog_after_error.structured_content is not None
            tasks_after_error = backlog_after_error.structured_content["tasks"]

            # Should only have the valid foundation task
            foundation_tasks = [t for t in tasks_after_error if t["title"] == "Foundation Task"]
            assert len(foundation_tasks) == 1

            # Recovery: Create valid task with correct prerequisite
            recovery_task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Recovered Task with Valid Prerequisite",
                    "projectRoot": planning_root,
                    "prerequisites": [foundation_task["id"]],
                    "priority": "normal",
                },
            )

            # Verify recovery was successful
            assert recovery_task_result.data["id"] is not None

            # Phase 2: Test circular dependency detection and recovery

            # Create task that will be part of circular dependency attempt
            task_a_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task A for Circular Test",
                    "projectRoot": planning_root,
                    "parent": hierarchy["feature_id"],
                    "priority": "normal",
                },
            )
            task_a_id = task_a_result.data["id"]

            # Create task B depending on task A
            task_b_result = await create_standalone_task(
                client,
                planning_root,
                "Task B for Circular Test",
                "normal",
                "Task B that depends on Task A",
            )
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_b_result["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"prerequisites": [task_a_id]},
                },
            )
            task_b_id = task_b_result["id"]

            # Attempt to create circular dependency (A depends on B)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": task_a_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {"prerequisites": [task_b_id]},
                    },
                )

            error_msg = str(exc_info.value).lower()
            assert any(
                phrase in error_msg for phrase in ["circular", "cycle", "circular dependency"]
            )

            # Verify tasks remain in valid state after circular dependency rejection
            task_a_check = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": task_a_id,
                    "projectRoot": planning_root,
                },
            )
            task_b_check = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": task_b_id,
                    "projectRoot": planning_root,
                },
            )

            # Task A should have no prerequisites (circular dependency was rejected)
            assert task_a_check.data["yaml"].get("prerequisites", []) == []
            # Task B should still depend on Task A
            assert task_b_check.data["yaml"]["prerequisites"] == [task_a_id]

            # Phase 3: Test partial workflow failure and recovery

            # Clean up any remaining open tasks before starting workflow test
            remaining_backlog = await client.call_tool(
                "listBacklog", {"projectRoot": planning_root}
            )
            assert remaining_backlog.structured_content is not None
            remaining_tasks = remaining_backlog.structured_content["tasks"]

            # Complete any open tasks to have a clean state
            for task in remaining_tasks:
                if task["status"] == "open":
                    claim_result = await client.call_tool(
                        "claimNextTask", {"projectRoot": planning_root}
                    )
                    await client.call_tool(
                        "completeTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": claim_result.data["task"]["id"],
                            "summary": "Cleanup task before workflow test",
                            "filesChanged": [f"cleanup-{claim_result.data['task']['id']}.py"],
                        },
                    )

            # Create a workflow that will partially fail
            workflow_tasks = []

            # Create base task
            base_task = await create_standalone_task(
                client,
                planning_root,
                "Workflow Base Task",
                "high",
                "Base task for partial failure testing",
            )
            workflow_tasks.append(base_task["id"])

            # Create dependent tasks
            for i in range(3):
                if i == 1:  # Create hierarchical task
                    hier_result = await client.call_tool(
                        "createObject",
                        {
                            "kind": "task",
                            "title": f"Workflow Hierarchical Task {i + 1}",
                            "projectRoot": planning_root,
                            "parent": hierarchy["feature_id"],
                            "prerequisites": [base_task["id"]],
                            "priority": "normal",
                        },
                    )
                    task_id = hier_result.data["id"]
                else:  # Create standalone task
                    standalone_result = await create_standalone_task(
                        client,
                        planning_root,
                        f"Workflow Standalone Task {i + 1}",
                        "normal",
                        f"Workflow standalone task {i + 1}",
                    )
                    task_id = standalone_result["id"]
                    await client.call_tool(
                        "updateObject",
                        {
                            "kind": "task",
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"prerequisites": [base_task["id"]]},
                        },
                    )

                workflow_tasks.append(task_id)

            # Start workflow by completing base task
            claim_base = await client.call_tool("claimNextTask", {"projectRoot": planning_root})
            assert claim_base.data["task"]["id"] == base_task["id"]

            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": base_task["id"],
                    "summary": "Base task completed for workflow test",
                    "filesChanged": ["base-workflow.py"],
                },
            )

            # Claim some dependent tasks but simulate partial failure
            claimed_workflow_tasks = []
            for i in range(2):  # Claim 2 out of 3 dependent tasks
                claim_result = await client.call_tool(
                    "claimNextTask", {"projectRoot": planning_root}
                )
                claimed_task_id = claim_result.data["task"]["id"]
                claimed_workflow_tasks.append(claimed_task_id)

            # Complete one task successfully
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": claimed_workflow_tasks[0],
                    "summary": "Partial workflow task completed successfully",
                    "filesChanged": ["partial-success.py"],
                },
            )

            # Simulate failure scenario: leave second task in in-progress
            # (In real scenario, this could be a developer leaving, system failure, etc.)

            # Verify system can recover by having another developer claim remaining work
            remaining_claim = await client.call_tool(
                "claimNextTask", {"projectRoot": planning_root}
            )
            remaining_task_id = remaining_claim.data["task"]["id"]

            # Should be the third dependent task (not the stuck in-progress one)
            assert remaining_task_id not in claimed_workflow_tasks

            # Complete the remaining available task
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": remaining_task_id,
                    "summary": "Recovery task completed",
                    "filesChanged": ["recovery.py"],
                },
            )

            # Simulate recovery: complete the stuck task
            stuck_task_id = claimed_workflow_tasks[1]
            await client.call_tool(
                "completeTask",
                {
                    "projectRoot": planning_root,
                    "taskId": stuck_task_id,
                    "summary": "Stuck task recovered and completed",
                    "filesChanged": ["recovery-stuck.py"],
                },
            )

            # Phase 4: Test system consistency during error conditions

            # Verify all tasks are in expected final state
            final_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert final_backlog.structured_content is not None
            final_tasks = final_backlog.structured_content["tasks"]

            # Count completed tasks
            completed_tasks = [t for t in final_tasks if t["status"] == "done"]
            in_progress_tasks = [t for t in final_tasks if t["status"] == "in-progress"]

            # Most tasks should be completed after recovery
            assert len(completed_tasks) >= 6  # Foundation, recovery, base, workflow tasks

            # Should have minimal or no stuck tasks
            assert len(in_progress_tasks) <= 1  # At most one task might still be in progress

            # Verify system can still operate normally after errors
            test_task = await create_standalone_task(
                client,
                planning_root,
                "Post-Recovery Test Task",
                "low",
                "Task to verify system works after error recovery",
            )

            # Should be able to claim and complete normally
            post_recovery_claim = await client.call_tool(
                "claimNextTask", {"projectRoot": planning_root}
            )

            if post_recovery_claim.data["task"]["id"] == test_task["id"]:
                await client.call_tool(
                    "completeTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": test_task["id"],
                        "summary": "Post-recovery test completed successfully",
                        "filesChanged": ["post-recovery-test.py"],
                    },
                )

            # Final validation
            ultimate_backlog = await client.call_tool("listBacklog", {"projectRoot": planning_root})
            assert ultimate_backlog.structured_content is not None
            ultimate_tasks = ultimate_backlog.structured_content["tasks"]

            # Verify system maintained consistency across both task systems
            hierarchy_tasks = [t for t in ultimate_tasks if t.get("parent")]
            standalone_tasks = [t for t in ultimate_tasks if not t.get("parent")]

            assert len(hierarchy_tasks) >= 2  # At least task A and one workflow task
            assert len(standalone_tasks) >= 5  # Foundation, recovery, workflow tasks, etc.

            # Verify no data corruption occurred
            for task in ultimate_tasks:
                assert_task_structure(task)
                assert task["status"] in ["open", "in-progress", "review", "done"]
                assert task["priority"] in ["high", "normal", "low"]
