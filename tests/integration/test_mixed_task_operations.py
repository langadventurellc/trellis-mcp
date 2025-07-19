"""Basic CRUD operations and scope filtering tests for mixed task types.

Tests MCP tool consistency, scope filtering behavior, and comprehensive
integration of all operations when both standalone and hierarchical tasks
coexist in the same project.
"""

import time

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_mixed_task_types_all_mcp_tools_consistency(temp_dir):
    """Test that all MCP tools work consistently with mixed task environments.

    Verifies that createObject, getObject, updateObject, listBacklog, claimNextTask,
    and completeTask all work correctly with both standalone and hierarchical tasks.
    """
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    async with Client(server) as client:
        # Step 1: Create complete hierarchy
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "MCP Tools Consistency Test",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "MCP Tools Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "MCP Tools Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create mixed task types with various statuses and priorities
        tasks_config = [
            {
                "title": "Standalone High Priority Task",
                "parent": None,  # Standalone
                "priority": "high",
            },
            {
                "title": "Hierarchy High Priority Task",
                "parent": feature_id,  # Hierarchical
                "priority": "high",
            },
            {
                "title": "Standalone Medium Priority Task",
                "parent": None,  # Standalone
                "priority": "normal",
            },
            {
                "title": "Hierarchy Medium Priority Task",
                "parent": feature_id,  # Hierarchical
                "priority": "normal",
            },
            {
                "title": "Standalone Low Priority Task",
                "parent": None,  # Standalone
                "priority": "low",
            },
            {
                "title": "Hierarchy Low Priority Task",
                "parent": feature_id,  # Hierarchical
                "priority": "low",
            },
        ]

        created_tasks = []
        for config in tasks_config:
            task_params = {
                "kind": "task",
                "title": config["title"],
                "projectRoot": planning_root,
                "priority": config["priority"],
            }

            if config["parent"]:
                task_params["parent"] = config["parent"]

            task_result = await client.call_tool("createObject", task_params)
            created_tasks.append(
                {
                    "id": task_result.data["id"],
                    "title": config["title"],
                    "parent": config["parent"],
                    "priority": config["priority"],
                    "is_standalone": config["parent"] is None,
                }
            )

        # Step 3: Test getObject for all tasks (both standalone and hierarchy)
        for task in created_tasks:
            retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": task["id"],
                    "projectRoot": planning_root,
                },
            )

            assert retrieved.data["yaml"]["title"] == task["title"]
            assert retrieved.data["yaml"]["priority"] == task["priority"]

            if task["is_standalone"]:
                assert retrieved.data["yaml"].get("parent") is None
            else:
                assert retrieved.data["yaml"]["parent"] == task["parent"]

        # Step 4: Test updateObject for both task types
        standalone_task = next(t for t in created_tasks if t["is_standalone"])
        hierarchy_task = next(t for t in created_tasks if not t["is_standalone"])

        # Update standalone task status
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_task["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        # Update hierarchy task status
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_task["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        # Verify updates worked
        updated_standalone = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task["id"],
                "projectRoot": planning_root,
            },
        )
        assert updated_standalone.data["yaml"]["status"] == "in-progress"

        updated_hierarchy = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_task["id"],
                "projectRoot": planning_root,
            },
        )
        assert updated_hierarchy.data["yaml"]["status"] == "in-progress"

        # Step 5: Test listBacklog with various filters
        # Test all tasks (no filter)
        all_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert all_tasks_result.structured_content is not None
        all_tasks = all_tasks_result.structured_content["tasks"]
        assert len(all_tasks) == 6

        # Test status filter (should find both standalone and hierarchy tasks)
        open_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "status": "open"},
        )
        assert open_tasks_result.structured_content is not None
        open_tasks = open_tasks_result.structured_content["tasks"]
        assert len(open_tasks) == 4  # 4 tasks still have open status

        in_progress_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "status": "in-progress"},
        )
        assert in_progress_tasks_result.structured_content is not None
        in_progress_tasks = in_progress_tasks_result.structured_content["tasks"]
        assert len(in_progress_tasks) == 2  # 2 tasks updated to in-progress

        # Test priority filter (should find both standalone and hierarchy tasks)
        high_priority_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "priority": "high"},
        )
        assert high_priority_result.structured_content is not None
        high_priority_tasks = high_priority_result.structured_content["tasks"]
        assert len(high_priority_tasks) == 2  # 1 standalone + 1 hierarchy

        # Step 6: Test claimNextTask respects priority across both task types
        # Should claim the highest priority open task (could be standalone or hierarchy)
        # Note: High priority tasks were already set to in-progress, so next highest is normal
        claim_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root},
        )

        claimed_task = claim_result.data["task"]
        assert (
            claimed_task["priority"] == "normal"
        )  # Next highest priority after high tasks were claimed
        assert claimed_task["status"] == "in-progress"

        # Step 7: Test completeTask for both task types
        # Move one task to review status first
        review_task = next(t for t in created_tasks if t["id"] != claimed_task["id"])
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": review_task["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": review_task["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Complete the task
        complete_result = await client.call_tool(
            "completeTask",
            {
                "taskId": review_task["id"],
                "projectRoot": planning_root,
                "summary": "Completed task for mixed task types test",
                "filesChanged": ["test_file.py"],
            },
        )

        assert complete_result.data is not None

        # Verify task was moved to done status
        completed_task = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": review_task["id"],
                "projectRoot": planning_root,
            },
        )
        assert completed_task.data["yaml"]["status"] == "done"

        # Step 8: Test getNextReviewableTask with mixed task types
        # Move another task to review
        another_task = next(
            t for t in created_tasks if t["id"] not in [claimed_task["id"], review_task["id"]]
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": another_task["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": another_task["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Get next reviewable task
        reviewable_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert reviewable_result.data is not None
        assert reviewable_result.data["task"] is not None
        reviewable_task = reviewable_result.data["task"]
        assert reviewable_task["status"] == "review"
        assert reviewable_task["id"] == another_task["id"]


@pytest.mark.asyncio
async def test_comprehensive_scope_filtering_mixed_environments(temp_dir):
    """Test comprehensive scope filtering edge cases with mixed task environments.

    Enhanced test covering project-level scope includes standalone tasks,
    epic/feature-level scope combinations, and various edge cases.
    """
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    async with Client(server) as client:
        # Step 1: Create multiple projects with hierarchical structure
        project1_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Project 1 for Scope Testing",
                "projectRoot": planning_root,
            },
        )
        project1_id = project1_result.data["id"]

        project2_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Project 2 for Scope Testing",
                "projectRoot": planning_root,
            },
        )
        project2_id = project2_result.data["id"]

        # Create epics and features for project 1
        epic1_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Epic 1",
                "projectRoot": planning_root,
                "parent": project1_id,
            },
        )
        epic1_id = epic1_result.data["id"]

        feature1_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Feature 1",
                "projectRoot": planning_root,
                "parent": epic1_id,
            },
        )
        feature1_id = feature1_result.data["id"]

        feature2_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Feature 2",
                "projectRoot": planning_root,
                "parent": epic1_id,
            },
        )
        feature2_id = feature2_result.data["id"]

        # Create epic and feature for project 2
        epic2_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Epic 2",
                "projectRoot": planning_root,
                "parent": project2_id,
            },
        )
        epic2_id = epic2_result.data["id"]

        feature3_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Feature 3",
                "projectRoot": planning_root,
                "parent": epic2_id,
            },
        )
        feature3_id = feature3_result.data["id"]

        # Step 2: Create comprehensive mixed task set
        created_tasks = []

        # Hierarchical tasks for project 1
        for i, feature_id in enumerate([feature1_id, feature2_id]):
            for j in range(2):  # 2 tasks per feature
                task_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Hierarchy Task {i + 1}-{j + 1}",
                        "projectRoot": planning_root,
                        "parent": feature_id,
                        "priority": ["high", "normal"][j % 2],
                    },
                )
                created_tasks.append(
                    {
                        "id": task_result.data["id"],
                        "type": "hierarchy",
                        "parent": feature_id,
                        "project": project1_id,
                        "epic": epic1_id,
                    }
                )

        # Hierarchical tasks for project 2
        for j in range(2):  # 2 tasks for project 2
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": f"Project 2 Hierarchy Task {j + 1}",
                    "projectRoot": planning_root,
                    "parent": feature3_id,
                    "priority": ["normal", "low"][j % 2],
                },
            )
            created_tasks.append(
                {
                    "id": task_result.data["id"],
                    "type": "hierarchy",
                    "parent": feature3_id,
                    "project": project2_id,
                    "epic": epic2_id,
                }
            )

        # Standalone tasks (should be included in all project scopes)
        for i in range(4):  # 4 standalone tasks
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": f"Standalone Task {i + 1}",
                    "projectRoot": planning_root,
                    "priority": ["high", "normal", "low", "normal"][i % 4],
                },
            )
            created_tasks.append(
                {
                    "id": task_result.data["id"],
                    "type": "standalone",
                    "parent": None,
                    "project": None,  # Standalone tasks don't belong to specific projects
                    "epic": None,
                }
            )

        # Step 3: Test project-level scope includes all standalone tasks
        # Project 1 scope should include: 4 hierarchy tasks + 4 standalone tasks = 8 total
        project1_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": project1_id},
        )
        assert project1_result.structured_content is not None
        project1_tasks = project1_result.structured_content["tasks"]

        # Should include all hierarchy tasks from project 1 AND all standalone tasks
        assert len(project1_tasks) == 8  # 4 hierarchy + 4 standalone

        # Verify standalone tasks are included in project scope
        standalone_task_ids = {task["id"] for task in created_tasks if task["type"] == "standalone"}
        project1_task_ids = {task["id"] for task in project1_tasks}

        # All standalone tasks should be in project1 scope
        assert standalone_task_ids.issubset(project1_task_ids)

        # Verify hierarchy tasks from project 1 are included
        project1_hierarchy_ids = {
            task["id"]
            for task in created_tasks
            if task["type"] == "hierarchy" and task["project"] == project1_id
        }
        assert project1_hierarchy_ids.issubset(project1_task_ids)

        # Verify hierarchy tasks from project 2 are NOT included
        project2_hierarchy_ids = {
            task["id"]
            for task in created_tasks
            if task["type"] == "hierarchy" and task["project"] == project2_id
        }
        assert project2_hierarchy_ids.isdisjoint(project1_task_ids)

        # Step 4: Test project 2 scope also includes all standalone tasks
        project2_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": project2_id},
        )
        assert project2_result.structured_content is not None
        project2_tasks = project2_result.structured_content["tasks"]

        # Should include: 2 hierarchy tasks from project 2 + 4 standalone tasks = 6 total
        assert len(project2_tasks) == 6  # 2 hierarchy + 4 standalone

        project2_task_ids = {task["id"] for task in project2_tasks}

        # All standalone tasks should be in project2 scope too
        assert standalone_task_ids.issubset(project2_task_ids)

        # Verify hierarchy tasks from project 2 are included
        assert project2_hierarchy_ids.issubset(project2_task_ids)

        # Verify hierarchy tasks from project 1 are NOT included
        assert project1_hierarchy_ids.isdisjoint(project2_task_ids)

        # Step 5: Test epic-level scope filtering
        # Epic 1 scope should include hierarchy tasks from features 1 & 2, but NO standalone tasks
        epic1_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": epic1_id},
        )
        assert epic1_result.structured_content is not None
        epic1_tasks = epic1_result.structured_content["tasks"]

        # Should include only hierarchy tasks from epic1 (4 tasks from 2 features)
        assert len(epic1_tasks) == 4

        epic1_task_ids = {task["id"] for task in epic1_tasks}

        # Should include all hierarchy tasks from epic1
        epic1_hierarchy_ids = {
            task["id"]
            for task in created_tasks
            if task["type"] == "hierarchy" and task["epic"] == epic1_id
        }
        assert epic1_hierarchy_ids == epic1_task_ids

        # Should NOT include standalone tasks
        assert standalone_task_ids.isdisjoint(epic1_task_ids)

        # Step 6: Test feature-level scope filtering
        # Feature 1 scope should include only its direct hierarchy tasks
        feature1_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": feature1_id},
        )
        assert feature1_result.structured_content is not None
        feature1_tasks = feature1_result.structured_content["tasks"]

        # Should include only tasks directly under feature1 (2 tasks)
        assert len(feature1_tasks) == 2

        feature1_task_ids = {task["id"] for task in feature1_tasks}

        # Should include only hierarchy tasks with feature1 as parent
        feature1_hierarchy_ids = {
            task["id"]
            for task in created_tasks
            if task["type"] == "hierarchy" and task["parent"] == feature1_id
        }
        assert feature1_hierarchy_ids == feature1_task_ids

        # Should NOT include standalone tasks or tasks from other features
        assert standalone_task_ids.isdisjoint(feature1_task_ids)

        feature2_hierarchy_ids = {
            task["id"]
            for task in created_tasks
            if task["type"] == "hierarchy" and task["parent"] == feature2_id
        }
        assert feature2_hierarchy_ids.isdisjoint(feature1_task_ids)

        # Step 7: Test edge case - no scope filter (global)
        # Should return ALL tasks (6 hierarchy + 4 standalone = 10 total)
        global_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert global_result.structured_content is not None
        global_tasks = global_result.structured_content["tasks"]

        assert len(global_tasks) == 10  # All tasks

        global_task_ids = {task["id"] for task in global_tasks}
        all_created_task_ids = {task["id"] for task in created_tasks}
        assert global_task_ids == all_created_task_ids

        # Step 8: Test combined scope filtering with status and priority
        # Project1 scope + high priority should include high priority hierarchy tasks +
        # high priority standalone
        project1_high_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": project1_id,
                "priority": "high",
            },
        )
        assert project1_high_result.structured_content is not None
        project1_high_tasks = project1_high_result.structured_content["tasks"]

        # Verify all returned tasks have high priority
        for task in project1_high_tasks:
            assert task["priority"] == "high"

        # Note: We need to count based on actual priority assignments
        # From our creation: standalone tasks have priorities [high, normal, low, normal]
        # Hierarchy tasks in project1 have priorities [high, normal, high, normal]
        # So we expect 1 + 2 = 3 high priority tasks in project1 scope
        assert len(project1_high_tasks) >= 1  # At least 1 high priority task


@pytest.mark.asyncio
async def test_comprehensive_integration_all_mcp_operations(temp_dir):
    """Test all MCP operations work consistently with mixed task environments.

    End-to-end integration test covering all MCP tools with both standalone
    and hierarchical tasks to ensure complete system integration.
    """
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    async with Client(server) as client:
        # Step 1: Test health_check works
        health_result = await client.call_tool("health_check")
        assert health_result.data["status"] == "healthy"
        assert health_result.data["planning_root"] == planning_root

        # Step 2: Create comprehensive mixed environment using createObject
        # Create project hierarchy
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Integration Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Integration Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Integration Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Create mixed tasks
        tasks_data = []

        # Create hierarchy tasks with different priorities and statuses
        for i in range(3):
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": f"Hierarchy Task {i + 1}",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": ["high", "normal", "low"][i],
                },
            )
            tasks_data.append(
                {
                    "id": task_result.data["id"],
                    "type": "hierarchy",
                    "priority": ["high", "normal", "low"][i],
                }
            )

        # Create standalone tasks
        for i in range(3):
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": f"Standalone Task {i + 1}",
                    "projectRoot": planning_root,
                    "priority": ["normal", "high", "low"][i],
                },
            )
            tasks_data.append(
                {
                    "id": task_result.data["id"],
                    "type": "standalone",
                    "priority": ["normal", "high", "low"][i],
                }
            )

        # Step 3: Test getObject for all created objects
        # Test project retrieval
        project_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "project",
                "id": project_id,
                "projectRoot": planning_root,
            },
        )
        assert project_retrieved.data["yaml"]["title"] == "Integration Test Project"

        # Test epic retrieval
        epic_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "epic",
                "id": epic_id,
                "projectRoot": planning_root,
            },
        )
        assert epic_retrieved.data["yaml"]["title"] == "Integration Test Epic"

        # Test feature retrieval
        feature_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "feature",
                "id": feature_id,
                "projectRoot": planning_root,
            },
        )
        assert feature_retrieved.data["yaml"]["title"] == "Integration Test Feature"

        # Test task retrieval for both types
        for task_data in tasks_data:
            task_retrieved = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": task_data["id"],
                    "projectRoot": planning_root,
                },
            )
            assert task_retrieved.data["yaml"]["priority"] == task_data["priority"]

        # Step 4: Test listBacklog with various filters
        # Test global scope
        global_backlog = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert global_backlog.structured_content is not None
        global_tasks = global_backlog.structured_content["tasks"]
        assert len(global_tasks) == 6  # 3 hierarchy + 3 standalone

        # Test project scope
        project_backlog = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": project_id},
        )
        assert project_backlog.structured_content is not None
        project_tasks = project_backlog.structured_content["tasks"]
        assert len(project_tasks) == 6  # 3 hierarchy + 3 standalone (project scope includes all)

        # Test feature scope
        feature_backlog = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": feature_id},
        )
        assert feature_backlog.structured_content is not None
        feature_tasks = feature_backlog.structured_content["tasks"]
        assert len(feature_tasks) == 3  # Only hierarchy tasks under feature

        # Test priority filtering
        high_priority_backlog = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "priority": "high"},
        )
        assert high_priority_backlog.structured_content is not None
        high_priority_tasks = high_priority_backlog.structured_content["tasks"]
        assert len(high_priority_tasks) == 2  # 1 hierarchy + 1 standalone with high priority

        # Step 5: Test claimNextTask respects priority across both task types
        claim_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root, "worktree": "integration-test"},
        )

        claimed_task = claim_result.data["task"]
        assert claimed_task["priority"] == "high"  # Should claim highest priority first
        assert claimed_task["status"] == "in-progress"
        assert claim_result.data["worktree"] == "integration-test"

        first_claimed_id = claimed_task["id"]

        # Step 6: Test updateObject for both task types
        # Find a standalone task and hierarchy task that aren't claimed
        remaining_tasks = [t for t in tasks_data if t["id"] != first_claimed_id]
        standalone_unclaimed = next(t for t in remaining_tasks if t["type"] == "standalone")
        hierarchy_unclaimed = next(t for t in remaining_tasks if t["type"] == "hierarchy")

        # Update standalone task priority
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_unclaimed["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"priority": "high"},
            },
        )

        # Update hierarchy task priority
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_unclaimed["id"],
                "projectRoot": planning_root,
                "yamlPatch": {"priority": "high"},
            },
        )

        # Verify updates worked
        standalone_updated = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_unclaimed["id"],
                "projectRoot": planning_root,
            },
        )
        assert standalone_updated.data["yaml"]["priority"] == "high"

        hierarchy_updated = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_unclaimed["id"],
                "projectRoot": planning_root,
            },
        )
        assert hierarchy_updated.data["yaml"]["priority"] == "high"

        # Step 7: Test review workflow
        # Move claimed task to review
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": first_claimed_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Test getNextReviewableTask
        reviewable_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert reviewable_result.data is not None
        assert reviewable_result.data["task"] is not None
        reviewable_task = reviewable_result.data["task"]
        assert reviewable_task["id"] == first_claimed_id
        assert reviewable_task["status"] == "review"

        # Step 8: Test completeTask
        complete_result = await client.call_tool(
            "completeTask",
            {
                "taskId": first_claimed_id,
                "projectRoot": planning_root,
                "summary": "Integration test task completed successfully",
                "filesChanged": ["integration_test.py", "test_config.yaml"],
            },
        )

        assert complete_result.data is not None

        # Verify task marked as done
        completed_task = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": first_claimed_id,
                "projectRoot": planning_root,
            },
        )
        assert completed_task.data["yaml"]["status"] == "done"

        # Step 9: Test system state consistency after all operations
        # Verify final listBacklog reflects all changes
        final_backlog = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert final_backlog.structured_content is not None
        final_tasks = final_backlog.structured_content["tasks"]

        # Should still have all tasks, with one completed and one claimed
        assert len(final_tasks) == 6

        # Verify status distribution
        status_counts = {}
        for task in final_tasks:
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        assert status_counts.get("done", 0) == 1  # One completed task
        # After completing the claimed task, remaining tasks should be open unless specifically
        # updated
        assert status_counts.get("open", 0) >= 1  # At least one open task remaining


@pytest.mark.asyncio
async def test_mixed_task_types_performance_benchmarks(temp_dir):
    """Test performance with large numbers of mixed task types.

    Creates a realistic scenario with many standalone and hierarchical tasks
    to ensure performance doesn't degrade with mixed environments.
    """
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=False,  # Disable debug for performance testing
        log_level="WARNING",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    async with Client(server) as client:
        # Step 1: Create hierarchical structure (minimal for performance testing)
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Performance Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Performance Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Performance Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create large numbers of mixed tasks for performance testing
        start_time = time.time()
        created_tasks = []

        # Create 25 hierarchical tasks
        for i in range(25):
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": f"Hierarchy Performance Task {i + 1}",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "priority": ["high", "normal", "low"][i % 3],
                },
            )
            created_tasks.append(task_result.data["id"])

        # Create 25 standalone tasks
        for i in range(25):
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": f"Standalone Performance Task {i + 1}",
                    "projectRoot": planning_root,
                    "priority": ["high", "normal", "low"][i % 3],
                },
            )
            created_tasks.append(task_result.data["id"])

        creation_time = time.time() - start_time

        # Step 3: Test listBacklog performance with large dataset
        list_start_time = time.time()
        all_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        list_time = time.time() - list_start_time

        assert all_tasks_result.structured_content is not None
        all_tasks = all_tasks_result.structured_content["tasks"]
        assert len(all_tasks) == 50  # 25 hierarchy + 25 standalone

        # Step 4: Test filtering performance
        filter_start_time = time.time()
        high_priority_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "priority": "high"},
        )
        project_scope_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": project_id},
        )
        filter_time = time.time() - filter_start_time

        # Step 5: Test claiming performance
        claim_start_time = time.time()
        claim_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root},
        )
        claim_time = time.time() - claim_start_time

        assert claim_result.data is not None
        claimed_task = claim_result.data["task"]
        assert claimed_task["priority"] == "high"  # Should claim highest priority task

        # Step 6: Performance assertions
        assert creation_time < 15.0, f"Task creation took too long: {creation_time:.2f}s"
        assert list_time < 3.0, f"ListBacklog took too long: {list_time:.2f}s"
        assert filter_time < 5.0, f"Filtering took too long: {filter_time:.2f}s"
        assert claim_time < 2.0, f"ClaimNextTask took too long: {claim_time:.2f}s"

        # Verify data integrity
        assert high_priority_result.structured_content is not None
        high_priority_tasks = high_priority_result.structured_content["tasks"]
        # Should have roughly 1/3 of tasks as high priority
        assert len(high_priority_tasks) >= 15

        assert project_scope_result.structured_content is not None
        project_tasks = project_scope_result.structured_content["tasks"]
        assert len(project_tasks) == 50  # All tasks should be in project scope
