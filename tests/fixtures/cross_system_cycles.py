"""Test fixtures for creating cross-system cycle scenarios.

This module provides factories for creating various types of circular dependency
scenarios that span both hierarchical and standalone task systems.
"""

from typing import Any

from fastmcp import Client


async def create_simple_cross_system_cycle(
    client: Client,
    planning_root: str,
    feature_id: str,
) -> dict[str, Any]:
    """Create a simple 2-task cycle spanning both task systems.

    Creates: Hierarchical Task A → Standalone Task B → Hierarchical Task A

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        feature_id: Parent feature ID for hierarchical tasks

    Returns:
        dict: Contains created task IDs and cycle information
    """
    # Create hierarchical task A (no prerequisites initially)
    hierarchy_task_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Hierarchical Task A",
            "projectRoot": planning_root,
            "parent": feature_id,
            "priority": "normal",
        },
    )
    hierarchy_task_id = hierarchy_task_result.data["id"]

    # Create standalone task B with prerequisite to hierarchical task A
    standalone_task_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Standalone Task B",
            "projectRoot": planning_root,
            "priority": "normal",
            "prerequisites": [hierarchy_task_id],
        },
    )
    standalone_task_id = standalone_task_result.data["id"]

    # This would create the cycle: Try to update hierarchical task A
    # to depend on standalone task B
    cycle_prereqs = [standalone_task_id]

    return {
        "hierarchy_task_id": hierarchy_task_id,
        "standalone_task_id": standalone_task_id,
        "cycle_prereqs": cycle_prereqs,
        "cycle_description": f"{hierarchy_task_id} → {standalone_task_id} → {hierarchy_task_id}",
    }


async def create_complex_multi_task_cycle(
    client: Client,
    planning_root: str,
    feature_id: str,
) -> dict[str, Any]:
    """Create a complex 4-task cycle spanning both task systems.

    Creates: H1 → S1 → H2 → S2 → H1 (where H=hierarchical, S=standalone)

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        feature_id: Parent feature ID for hierarchical tasks

    Returns:
        dict: Contains created task IDs and cycle information
    """
    # Create hierarchical task H1 (no prerequisites initially)
    h1_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Hierarchical Task H1",
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
            "title": "Standalone Task S1",
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
            "title": "Hierarchical Task H2",
            "projectRoot": planning_root,
            "parent": feature_id,
            "priority": "normal",
            "prerequisites": [s1_id],
        },
    )
    h2_id = h2_result.data["id"]

    # Create standalone task S2 with prerequisite to H2
    s2_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Standalone Task S2",
            "projectRoot": planning_root,
            "priority": "normal",
            "prerequisites": [h2_id],
        },
    )
    s2_id = s2_result.data["id"]

    # This would create the cycle: Try to update H1 to depend on S2
    cycle_prereqs = [s2_id]

    return {
        "h1_id": h1_id,
        "s1_id": s1_id,
        "h2_id": h2_id,
        "s2_id": s2_id,
        "cycle_prereqs": cycle_prereqs,
        "cycle_description": f"{h1_id} → {s1_id} → {h2_id} → {s2_id} → {h1_id}",
        "task_ids": [h1_id, s1_id, h2_id, s2_id],
    }


async def create_nested_cycle_scenario(
    client: Client,
    planning_root: str,
    feature_id: str,
) -> dict[str, Any]:
    """Create a cycle nested within a larger dependency network.

    Creates a valid dependency network with an embedded cycle:
    - Valid branch: H1 → S1 → H3 (valid)
    - Cycle branch: H1 → S2 → H2 → S3 → H1 (cycle)

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        feature_id: Parent feature ID for hierarchical tasks

    Returns:
        dict: Contains created task IDs and cycle information
    """
    # Create hierarchical task H1 (root task)
    h1_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Root Hierarchical Task H1",
            "projectRoot": planning_root,
            "parent": feature_id,
            "priority": "normal",
        },
    )
    h1_id = h1_result.data["id"]

    # Create valid branch: S1 → H3
    s1_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Valid Branch Standalone S1",
            "projectRoot": planning_root,
            "priority": "normal",
            "prerequisites": [h1_id],
        },
    )
    s1_id = s1_result.data["id"]

    h3_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Valid Branch Hierarchical H3",
            "projectRoot": planning_root,
            "parent": feature_id,
            "priority": "normal",
            "prerequisites": [s1_id],
        },
    )
    h3_id = h3_result.data["id"]

    # Create cycle branch: S2 → H2 → S3
    s2_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Cycle Branch Standalone S2",
            "projectRoot": planning_root,
            "priority": "normal",
            "prerequisites": [h1_id],
        },
    )
    s2_id = s2_result.data["id"]

    h2_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Cycle Branch Hierarchical H2",
            "projectRoot": planning_root,
            "parent": feature_id,
            "priority": "normal",
            "prerequisites": [s2_id],
        },
    )
    h2_id = h2_result.data["id"]

    s3_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Cycle Branch Standalone S3",
            "projectRoot": planning_root,
            "priority": "normal",
            "prerequisites": [h2_id],
        },
    )
    s3_id = s3_result.data["id"]

    # This would create the cycle: Try to update H1 to depend on S3
    cycle_prereqs = [s3_id]

    return {
        "h1_id": h1_id,
        "valid_branch": {"s1_id": s1_id, "h3_id": h3_id},
        "cycle_branch": {"s2_id": s2_id, "h2_id": h2_id, "s3_id": s3_id},
        "cycle_prereqs": cycle_prereqs,
        "cycle_description": f"{h1_id} → {s2_id} → {h2_id} → {s3_id} → {h1_id}",
        "all_task_ids": [h1_id, s1_id, h3_id, s2_id, h2_id, s3_id],
    }


async def create_cross_system_cycle_with_mixed_prereqs(
    client: Client,
    planning_root: str,
    feature_id: str,
) -> dict[str, Any]:
    """Create a cycle involving tasks with multiple mixed prerequisites.

    Creates tasks with prerequisites from both systems, then introduces a cycle.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        feature_id: Parent feature ID for hierarchical tasks

    Returns:
        dict: Contains created task IDs and cycle information
    """
    # Create foundation tasks
    h1_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Foundation Hierarchical H1",
            "projectRoot": planning_root,
            "parent": feature_id,
            "priority": "normal",
        },
    )
    h1_id = h1_result.data["id"]

    s1_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Foundation Standalone S1",
            "projectRoot": planning_root,
            "priority": "normal",
        },
    )
    s1_id = s1_result.data["id"]

    # Create task with mixed prerequisites from both systems
    mixed_task_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Mixed Prerequisites Task",
            "projectRoot": planning_root,
            "parent": feature_id,
            "priority": "normal",
            "prerequisites": [h1_id, s1_id],
        },
    )
    mixed_task_id = mixed_task_result.data["id"]

    # Create final task that would complete the cycle
    final_task_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": "Final Standalone Task",
            "projectRoot": planning_root,
            "priority": "normal",
            "prerequisites": [mixed_task_id],
        },
    )
    final_task_id = final_task_result.data["id"]

    # This would create the cycle: Try to update H1 to depend on final_task
    cycle_prereqs = [final_task_id]

    return {
        "h1_id": h1_id,
        "s1_id": s1_id,
        "mixed_task_id": mixed_task_id,
        "final_task_id": final_task_id,
        "cycle_prereqs": cycle_prereqs,
        "cycle_description": f"{h1_id} → {mixed_task_id} → {final_task_id} → {h1_id}",
        "mixed_prereq_task": mixed_task_id,
    }


def get_expected_cycle_error_message(cycle_description: str) -> str:
    """Get the expected error message pattern for a cycle.

    Args:
        cycle_description: Description of the cycle path

    Returns:
        str: Expected error message pattern
    """
    return f"Circular dependency detected in prerequisites: {cycle_description}"


def validate_cycle_error(error_message: str, expected_tasks: list[str]) -> bool:
    """Validate that a cycle error message contains expected task references.

    Args:
        error_message: Actual error message from cycle detection
        expected_tasks: List of task IDs that should be in the cycle

    Returns:
        bool: True if error message is valid
    """
    # Check that error mentions circular dependency
    if "circular dependency" not in error_message.lower():
        return False

    # Check that all expected tasks are mentioned
    for task_id in expected_tasks:
        if task_id not in error_message:
            return False

    return True
