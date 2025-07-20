"""Test fixtures for comprehensive children discovery integration tests.

This module provides factory functions for creating realistic project structures
that test various children discovery scenarios including hierarchical structures,
cross-system compatibility, edge cases, and error scenarios.
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest


def create_integration_project_structure(planning_root: Path) -> Dict[str, Any]:
    """Create comprehensive test project structure for integration tests.

    Creates a realistic project hierarchy with:
    - 1 project with multiple epics
    - Each epic has multiple features
    - Features contain mixed task collections (open/done)
    - Cross-system standalone tasks
    - Edge cases and error scenarios

    Args:
        planning_root: Root directory for planning structure

    Returns:
        Dictionary containing created object metadata and structure info
    """
    planning_root.mkdir(parents=True, exist_ok=True)

    # Create main test project hierarchy
    project_structure = _create_large_project_hierarchy(planning_root)

    # Add standalone tasks for cross-system testing
    standalone_structure = _create_standalone_task_collection(planning_root)

    # Add edge case structures
    edge_case_structure = _create_edge_case_structures(planning_root)

    return {
        "planning_root": str(planning_root),
        "hierarchical": project_structure,
        "standalone": standalone_structure,
        "edge_cases": edge_case_structure,
        "total_projects": 1 + len(edge_case_structure.get("projects", [])),
        "total_epics": len(project_structure["epics"])
        + sum(len(p.get("epics", [])) for p in edge_case_structure.get("projects", [])),
        "total_features": sum(len(e.get("features", [])) for e in project_structure["epics"]),
        "total_hierarchical_tasks": sum(
            sum(len(f.get("tasks", [])) for f in e.get("features", []))
            for e in project_structure["epics"]
        ),
        "total_standalone_tasks": len(standalone_structure["tasks"]),
    }


def _create_large_project_hierarchy(planning_root: Path) -> Dict[str, Any]:
    """Create a large project with comprehensive hierarchy for testing."""

    # Create project
    project_dir = planning_root / "projects" / "P-large-project"
    project_dir.mkdir(parents=True)
    project_file = project_dir / "project.md"
    project_content = """---
kind: project
id: P-large-project
title: Large Integration Test Project
status: in-progress
priority: high
prerequisites: []
created: '2025-07-19T09:00:00Z'
updated: '2025-07-19T09:00:00Z'
schema_version: '1.1'
---
# Large Integration Test Project

Comprehensive project structure for testing children discovery across
all hierarchical levels with realistic content and metadata.

## Objectives
- Test project → epic discovery workflows
- Validate epic → feature discovery workflows
- Test feature → task discovery workflows
- Verify cross-system compatibility
- Test edge cases and error scenarios

### Log

Project created for comprehensive children discovery integration testing.
"""
    project_file.write_text(project_content)

    # Create epics with different characteristics
    epics_data = [
        {
            "id": "E-user-management",
            "title": "User Management System",
            "status": "in-progress",
            "priority": "high",
            "created": "2025-07-19T09:01:00Z",
            "features": [
                {
                    "id": "F-user-registration",
                    "title": "User Registration",
                    "status": "in-progress",
                    "priority": "high",
                    "created": "2025-07-19T09:05:00Z",
                    "tasks": [
                        (
                            "T-create-registration-form",
                            "Create Registration Form",
                            "open",
                            "high",
                            "2025-07-19T09:10:00Z",
                        ),
                        (
                            "T-implement-email-validation",
                            "Implement Email Validation",
                            "in-progress",
                            "high",
                            "2025-07-19T09:11:00Z",
                        ),
                        (
                            "T-add-password-strength",
                            "Add Password Strength Check",
                            "review",
                            "normal",
                            "2025-07-19T09:12:00Z",
                        ),
                        (
                            "T-setup-user-database",
                            "Setup User Database Schema",
                            "open",
                            "normal",
                            "2025-07-19T09:13:00Z",
                        ),
                    ],
                    "done_tasks": [
                        (
                            "T-design-registration-ui",
                            "Design Registration UI",
                            "done",
                            "normal",
                            "2025-07-19T09:08:00Z",
                        ),
                        (
                            "T-research-validation-libs",
                            "Research Validation Libraries",
                            "done",
                            "low",
                            "2025-07-19T09:09:00Z",
                        ),
                    ],
                },
                {
                    "id": "F-user-authentication",
                    "title": "User Authentication",
                    "status": "open",
                    "priority": "high",
                    "created": "2025-07-19T09:06:00Z",
                    "tasks": [
                        (
                            "T-implement-jwt-auth",
                            "Implement JWT Authentication",
                            "open",
                            "high",
                            "2025-07-19T09:14:00Z",
                        ),
                        (
                            "T-add-session-management",
                            "Add Session Management",
                            "open",
                            "normal",
                            "2025-07-19T09:15:00Z",
                        ),
                        (
                            "T-implement-logout",
                            "Implement Logout Flow",
                            "open",
                            "normal",
                            "2025-07-19T09:16:00Z",
                        ),
                    ],
                    "done_tasks": [],
                },
                {
                    "id": "F-user-profile",
                    "title": "User Profile Management",
                    "status": "open",
                    "priority": "normal",
                    "created": "2025-07-19T09:07:00Z",
                    "tasks": [
                        (
                            "T-create-profile-page",
                            "Create Profile Page",
                            "open",
                            "normal",
                            "2025-07-19T09:17:00Z",
                        ),
                        (
                            "T-implement-profile-edit",
                            "Implement Profile Editing",
                            "open",
                            "normal",
                            "2025-07-19T09:18:00Z",
                        ),
                    ],
                    "done_tasks": [],
                },
            ],
        },
        {
            "id": "E-payment-processing",
            "title": "Payment Processing System",
            "status": "open",
            "priority": "normal",
            "created": "2025-07-19T09:02:00Z",
            "features": [
                {
                    "id": "F-payment-gateway",
                    "title": "Payment Gateway Integration",
                    "status": "open",
                    "priority": "high",
                    "created": "2025-07-19T09:20:00Z",
                    "tasks": [
                        (
                            "T-integrate-stripe",
                            "Integrate Stripe API",
                            "open",
                            "high",
                            "2025-07-19T09:25:00Z",
                        ),
                        (
                            "T-implement-webhooks",
                            "Implement Payment Webhooks",
                            "open",
                            "normal",
                            "2025-07-19T09:26:00Z",
                        ),
                    ],
                    "done_tasks": [],
                },
                {
                    "id": "F-billing-system",
                    "title": "Billing and Invoicing",
                    "status": "open",
                    "priority": "normal",
                    "created": "2025-07-19T09:21:00Z",
                    "tasks": [
                        (
                            "T-generate-invoices",
                            "Generate PDF Invoices",
                            "open",
                            "normal",
                            "2025-07-19T09:27:00Z",
                        ),
                        (
                            "T-email-notifications",
                            "Email Invoice Notifications",
                            "open",
                            "low",
                            "2025-07-19T09:28:00Z",
                        ),
                    ],
                    "done_tasks": [],
                },
            ],
        },
        {
            "id": "E-reporting-analytics",
            "title": "Reporting and Analytics",
            "status": "open",
            "priority": "low",
            "created": "2025-07-19T09:03:00Z",
            "features": [
                {
                    "id": "F-dashboard",
                    "title": "Analytics Dashboard",
                    "status": "open",
                    "priority": "normal",
                    "created": "2025-07-19T09:22:00Z",
                    "tasks": [
                        (
                            "T-create-dashboard-ui",
                            "Create Dashboard UI",
                            "open",
                            "normal",
                            "2025-07-19T09:29:00Z",
                        ),
                        (
                            "T-implement-charts",
                            "Implement Chart Components",
                            "open",
                            "normal",
                            "2025-07-19T09:30:00Z",
                        ),
                    ],
                    "done_tasks": [],
                }
            ],
        },
    ]

    created_structure = {"project_id": "large-project", "epics": []}

    for epic_data in epics_data:
        epic_dir = project_dir / "epics" / epic_data["id"]
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = f"""---
kind: epic
id: {epic_data["id"]}
parent: P-large-project
title: {epic_data["title"]}
status: {epic_data["status"]}
priority: {epic_data["priority"]}
prerequisites: []
created: '{epic_data["created"]}'
updated: '{epic_data["created"]}'
schema_version: '1.1'
---
# {epic_data["title"]}

Epic for comprehensive children discovery testing with realistic
business requirements and technical specifications.

## Features Overview
{chr(10).join(f"- {f['title']}: {f['status']}" for f in epic_data["features"])}

### Log

Epic created for integration testing purposes.
"""
        epic_file.write_text(epic_content)

        epic_structure = {"epic_id": epic_data["id"].replace("E-", ""), "features": []}

        for feature_data in epic_data["features"]:
            feature_dir = epic_dir / "features" / feature_data["id"]
            feature_dir.mkdir(parents=True)
            feature_file = feature_dir / "feature.md"
            feature_content = f"""---
kind: feature
id: {feature_data["id"]}
parent: {epic_data["id"]}
title: {feature_data["title"]}
status: {feature_data["status"]}
priority: {feature_data["priority"]}
prerequisites: []
created: '{feature_data["created"]}'
updated: '{feature_data["created"]}'
schema_version: '1.1'
---
# {feature_data["title"]}

Feature implementation for {epic_data["title"]} with comprehensive
task breakdown and realistic development workflow.

## Tasks Overview
- Open tasks: {len(feature_data["tasks"])}
- Completed tasks: {len(feature_data["done_tasks"])}

### Log

Feature created for children discovery integration testing.
"""
            feature_file.write_text(feature_content)

            # Create tasks-open directory and tasks
            tasks_open_dir = feature_dir / "tasks-open"
            tasks_open_dir.mkdir(parents=True)

            feature_structure = {"feature_id": feature_data["id"].replace("F-", ""), "tasks": []}

            for task_id, task_title, status, priority, created in feature_data["tasks"]:
                task_file = tasks_open_dir / f"{task_id}.md"
                task_content = f"""---
kind: task
id: {task_id}
parent: {feature_data["id"]}
title: {task_title}
status: {status}
priority: {priority}
prerequisites: []
created: '{created}'
updated: '{created}'
schema_version: '1.1'
---
# {task_title}

Detailed task implementation for {feature_data["title"]} feature.

## Requirements
- Implement core functionality
- Add comprehensive tests
- Update documentation
- Ensure security compliance

## Acceptance Criteria
- [ ] Feature works as specified
- [ ] Tests pass with >90% coverage
- [ ] Code review completed
- [ ] Documentation updated

### Log

Task created for integration testing workflow validation.
"""
                task_file.write_text(task_content)
                feature_structure["tasks"].append(
                    {"task_id": task_id.replace("T-", ""), "status": status, "priority": priority}
                )

            # Create tasks-done directory and completed tasks
            if feature_data["done_tasks"]:
                tasks_done_dir = feature_dir / "tasks-done"
                tasks_done_dir.mkdir(parents=True)

                for task_id, task_title, status, priority, created in feature_data["done_tasks"]:
                    # Use timestamp prefix for done tasks
                    task_file = tasks_done_dir / f"20250719_090800-{task_id}.md"
                    task_content = f"""---
kind: task
id: {task_id}
parent: {feature_data["id"]}
title: {task_title}
status: {status}
priority: {priority}
prerequisites: []
created: '{created}'
updated: '{created}'
schema_version: '1.1'
---
# {task_title}

Completed task for {feature_data["title"]} feature.

## Implementation Summary
Task successfully completed with all acceptance criteria met.
Code reviewed and merged to main branch.

### Log

Task completed during integration testing setup.
"""
                    task_file.write_text(task_content)
                    feature_structure["tasks"].append(
                        {
                            "task_id": task_id.replace("T-", ""),
                            "status": status,
                            "priority": priority,
                        }
                    )

            epic_structure["features"].append(feature_structure)

        created_structure["epics"].append(epic_structure)

    return created_structure


def _create_standalone_task_collection(planning_root: Path) -> Dict[str, Any]:
    """Create collection of standalone tasks for cross-system testing."""

    standalone_dir = planning_root / "tasks-open"
    standalone_dir.mkdir(parents=True)

    standalone_tasks_data = [
        ("T-infrastructure-setup", "Infrastructure Setup", "open", "high", "2025-07-19T10:00:00Z"),
        (
            "T-database-migration",
            "Database Migration Scripts",
            "in-progress",
            "high",
            "2025-07-19T10:01:00Z",
        ),
        (
            "T-monitoring-configuration",
            "Monitoring Configuration",
            "open",
            "normal",
            "2025-07-19T10:02:00Z",
        ),
        ("T-security-audit", "Security Audit", "open", "high", "2025-07-19T10:03:00Z"),
        (
            "T-performance-optimization",
            "Performance Optimization",
            "review",
            "normal",
            "2025-07-19T10:04:00Z",
        ),
        ("T-backup-procedures", "Backup Procedures", "open", "low", "2025-07-19T10:05:00Z"),
        ("T-documentation-update", "Documentation Update", "open", "low", "2025-07-19T10:06:00Z"),
    ]

    created_tasks = []

    for task_id, task_title, status, priority, created in standalone_tasks_data:
        task_file = standalone_dir / f"{task_id}.md"
        task_content = f"""---
kind: task
id: {task_id}
title: {task_title}
status: {status}
priority: {priority}
prerequisites: []
created: '{created}'
updated: '{created}'
schema_version: '1.1'
---
# {task_title}

Standalone task for cross-system integration testing and validation
of children discovery across mixed hierarchical/standalone environments.

## Scope
This task operates independently of the hierarchical project structure
and serves to validate cross-system compatibility and isolation.

## Requirements
- Complete standalone implementation
- Maintain system isolation
- Validate cross-system compatibility

### Log

Standalone task created for integration testing.
"""
        task_file.write_text(task_content)
        created_tasks.append(
            {"task_id": task_id.replace("T-", ""), "status": status, "priority": priority}
        )

    return {"tasks": created_tasks}


def _create_edge_case_structures(planning_root: Path) -> Dict[str, Any]:
    """Create edge case structures for comprehensive testing."""

    edge_cases = {"projects": []}

    # 1. Empty project (no epics)
    empty_project_dir = planning_root / "projects" / "P-empty-project"
    empty_project_dir.mkdir(parents=True)
    empty_project_file = empty_project_dir / "project.md"
    empty_project_content = """---
kind: project
id: P-empty-project
title: Empty Project for Edge Case Testing
status: open
priority: low
prerequisites: []
created: '2025-07-19T11:00:00Z'
updated: '2025-07-19T11:00:00Z'
schema_version: '1.1'
---
# Empty Project for Edge Case Testing

This project intentionally has no epics to test empty children discovery.
"""
    empty_project_file.write_text(empty_project_content)
    edge_cases["projects"].append({"project_id": "empty-project", "epics": []})

    # 2. Project with empty epic
    project_with_empty_epic_dir = planning_root / "projects" / "P-project-with-empty-epic"
    project_with_empty_epic_dir.mkdir(parents=True)
    project_with_empty_epic_file = project_with_empty_epic_dir / "project.md"
    project_with_empty_epic_content = """---
kind: project
id: P-project-with-empty-epic
title: Project with Empty Epic
status: open
priority: normal
prerequisites: []
created: '2025-07-19T11:01:00Z'
updated: '2025-07-19T11:01:00Z'
schema_version: '1.1'
---
# Project with Empty Epic

Project containing an epic with no features for edge case testing.
"""
    project_with_empty_epic_file.write_text(project_with_empty_epic_content)

    empty_epic_dir = project_with_empty_epic_dir / "epics" / "E-empty-epic"
    empty_epic_dir.mkdir(parents=True)
    empty_epic_file = empty_epic_dir / "epic.md"
    empty_epic_content = """---
kind: epic
id: E-empty-epic
parent: P-project-with-empty-epic
title: Empty Epic for Testing
status: open
priority: normal
prerequisites: []
created: '2025-07-19T11:02:00Z'
updated: '2025-07-19T11:02:00Z'
schema_version: '1.1'
---
# Empty Epic for Testing

This epic intentionally has no features to test empty children discovery.
"""
    empty_epic_file.write_text(empty_epic_content)

    edge_cases["projects"].append(
        {
            "project_id": "project-with-empty-epic",
            "epics": [{"epic_id": "empty-epic", "features": []}],
        }
    )

    # 3. Epic with empty feature
    empty_feature_dir = empty_epic_dir / "features" / "F-empty-feature"
    empty_feature_dir.mkdir(parents=True)
    empty_feature_file = empty_feature_dir / "feature.md"
    empty_feature_content = """---
kind: feature
id: F-empty-feature
parent: E-empty-epic
title: Empty Feature for Testing
status: open
priority: normal
prerequisites: []
created: '2025-07-19T11:03:00Z'
updated: '2025-07-19T11:03:00Z'
schema_version: '1.1'
---
# Empty Feature for Testing

This feature intentionally has no tasks to test empty children discovery.
"""
    empty_feature_file.write_text(empty_feature_content)

    edge_cases["projects"][-1]["epics"][0]["features"].append(
        {"feature_id": "empty-feature", "tasks": []}
    )

    # 4. Project with corrupted children
    corrupted_project_dir = planning_root / "projects" / "P-corrupted-project"
    corrupted_project_dir.mkdir(parents=True)
    corrupted_project_file = corrupted_project_dir / "project.md"
    corrupted_project_content = """---
kind: project
id: P-corrupted-project
title: Project with Corrupted Children
status: in-progress
priority: normal
prerequisites: []
created: '2025-07-19T11:10:00Z'
updated: '2025-07-19T11:10:00Z'
schema_version: '1.1'
---
# Project with Corrupted Children

Project containing corrupted child objects for error handling testing.
"""
    corrupted_project_file.write_text(corrupted_project_content)

    # Create valid epic
    valid_epic_dir = corrupted_project_dir / "epics" / "E-valid-epic"
    valid_epic_dir.mkdir(parents=True)
    valid_epic_file = valid_epic_dir / "epic.md"
    valid_epic_content = """---
kind: epic
id: E-valid-epic
parent: P-corrupted-project
title: Valid Epic
status: open
priority: normal
prerequisites: []
created: '2025-07-19T11:11:00Z'
updated: '2025-07-19T11:11:00Z'
schema_version: '1.1'
---
# Valid Epic

This is a valid epic for testing error isolation.
"""
    valid_epic_file.write_text(valid_epic_content)

    # Create corrupted epic with malformed YAML
    corrupted_epic_dir = corrupted_project_dir / "epics" / "E-corrupted-epic"
    corrupted_epic_dir.mkdir(parents=True)
    corrupted_epic_file = corrupted_epic_dir / "epic.md"
    corrupted_epic_content = """---
kind: epic
id: E-corrupted-epic
parent: P-corrupted-project
title: Corrupted Epic
status: open
priority: normal
created: INVALID_DATE_FORMAT
updated: '2025-07-19T11:12:00Z'
malformed_yaml: [missing_closing_bracket
schema_version: '1.1'
---
# Corrupted Epic

This epic has corrupted YAML front-matter for error testing.
"""
    corrupted_epic_file.write_text(corrupted_epic_content)

    # Create empty epic file
    empty_epic_file_dir = corrupted_project_dir / "epics" / "E-empty-file-epic"
    empty_epic_file_dir.mkdir(parents=True)
    empty_epic_file_path = empty_epic_file_dir / "epic.md"
    empty_epic_file_path.write_text("")

    edge_cases["projects"].append(
        {
            "project_id": "corrupted-project",
            "epics": [{"epic_id": "valid-epic", "features": []}],
            "corrupted_children": 2,
        }
    )

    return edge_cases


@pytest.fixture
def integration_project_fixture(temp_dir):
    """Pytest fixture that creates comprehensive project structure for integration tests."""
    return create_integration_project_structure(temp_dir / "planning")


def validate_children_metadata(children: List[Dict[str, str]], expected_types: List[str]) -> None:
    """Validate children array structure and metadata.

    Args:
        children: List of child objects from getObject response
        expected_types: List of expected child kinds

    Raises:
        AssertionError: If validation fails
    """
    # Check required fields are present (file_path excluded for simplified tools)
    required_fields = ["id", "title", "status", "kind", "created"]
    for child in children:
        for field in required_fields:
            assert (
                field in child
            ), f"Missing required field '{field}' in child {child.get('id', 'unknown')}"

        # Validate field types and formats
        assert isinstance(child["id"], str) and child["id"], "Child ID must be non-empty string"
        assert (
            isinstance(child["title"], str) and child["title"]
        ), "Child title must be non-empty string"
        assert child["status"] in [
            "open",
            "in-progress",
            "review",
            "done",
        ], f"Invalid status: {child['status']}"
        assert child["kind"] in expected_types, f"Unexpected child kind: {child['kind']}"

        # Validate ISO timestamp format
        import re

        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
        assert re.match(
            iso_pattern, child["created"]
        ), f"Invalid created timestamp: {child['created']}"


def validate_children_ordering(children: List[Dict[str, str]]) -> None:
    """Validate children are ordered by creation date.

    Args:
        children: List of child objects from getObject response

    Raises:
        AssertionError: If ordering is incorrect
    """
    if len(children) <= 1:
        return

    # Check chronological ordering
    for i in range(1, len(children)):
        current_time = children[i]["created"]
        previous_time = children[i - 1]["created"]
        assert (
            current_time >= previous_time
        ), f"Children not ordered by creation date: {previous_time} should be <= {current_time}"


def validate_cross_system_isolation(
    hierarchical_children: List[Dict[str, str]], standalone_tasks: List[Dict[str, str]]
) -> None:
    """Validate that hierarchical and standalone systems maintain proper isolation.

    Args:
        hierarchical_children: Children discovered from hierarchical objects
        standalone_tasks: Standalone tasks from listBacklog

    Raises:
        AssertionError: If cross-system isolation is violated
    """
    # Hierarchical children should not include standalone tasks
    hierarchical_ids = {child["id"] for child in hierarchical_children}
    standalone_ids = {task["id"] for task in standalone_tasks if not task.get("parent")}

    overlap = hierarchical_ids.intersection(standalone_ids)
    assert not overlap, f"Cross-system isolation violated: {overlap}"

    # All hierarchical children should have parent relationships when queried
    for child in hierarchical_children:
        if child["kind"] in ["epic", "feature", "task"]:
            # These should have parent references in their YAML
            assert (
                "parent" in child or child["kind"] == "task"
            ), f"Missing parent reference for {child['id']}"


def assert_children_discovery_performance(
    response_time_ms: float, max_time_ms: float = 100
) -> None:
    """Assert that children discovery meets performance requirements.

    Args:
        response_time_ms: Actual response time in milliseconds
        max_time_ms: Maximum allowed response time in milliseconds

    Raises:
        AssertionError: If performance requirements not met
    """
    assert (
        response_time_ms < max_time_ms
    ), f"Children discovery took {response_time_ms:.2f}ms, should be <{max_time_ms}ms"


def assert_error_isolation(valid_children: List[Dict[str, str]], expected_valid_count: int) -> None:
    """Assert that corrupted children are properly isolated from valid results.

    Args:
        valid_children: Children that were successfully discovered
        expected_valid_count: Expected number of valid children

    Raises:
        AssertionError: If error isolation failed
    """
    assert (
        len(valid_children) == expected_valid_count
    ), f"Expected {expected_valid_count} valid children, got {len(valid_children)}"

    # All returned children should be valid and complete
    validate_children_metadata(valid_children, ["project", "epic", "feature", "task"])
