"""Integration tests for getObject tool children array functionality.

Tests the getObject tool's children discovery in realistic project scenarios,
including cross-system compatibility and full hierarchy integration.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestGetObjectChildrenIntegration:
    """Integration test cases for getObject children discovery."""

    @pytest.mark.asyncio
    async def test_full_hierarchy_children_discovery(self, temp_dir):
        """Test children discovery across complete project hierarchy."""
        # Create complete project hierarchy
        project_root = temp_dir / "planning"

        # Create project
        project_dir = project_root / "projects" / "P-ecommerce"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-ecommerce
title: E-commerce Platform
status: in-progress
priority: high
created: '2025-07-19T10:00:00Z'
updated: '2025-07-19T10:00:00Z'
schema_version: '1.1'
---
Complete e-commerce platform development.
"""
        project_file.write_text(project_content)

        # Create epic 1: User Management
        epic1_dir = project_dir / "epics" / "E-user-management"
        epic1_dir.mkdir(parents=True)
        epic1_file = epic1_dir / "epic.md"
        epic1_content = """---
kind: epic
id: E-user-management
parent: P-ecommerce
title: User Management
status: in-progress
priority: high
created: '2025-07-19T10:01:00Z'
updated: '2025-07-19T10:01:00Z'
schema_version: '1.1'
---
User authentication and profile management.
"""
        epic1_file.write_text(epic1_content)

        # Create epic 2: Payment Processing
        epic2_dir = project_dir / "epics" / "E-payment-processing"
        epic2_dir.mkdir(parents=True)
        epic2_file = epic2_dir / "epic.md"
        epic2_content = """---
kind: epic
id: E-payment-processing
parent: P-ecommerce
title: Payment Processing
status: open
priority: normal
created: '2025-07-19T10:02:00Z'
updated: '2025-07-19T10:02:00Z'
schema_version: '1.1'
---
Payment gateway integration and transaction handling.
"""
        epic2_file.write_text(epic2_content)

        # Create feature under epic 1: User Registration
        feature1_dir = epic1_dir / "features" / "F-user-registration"
        feature1_dir.mkdir(parents=True)
        feature1_file = feature1_dir / "feature.md"
        feature1_content = """---
kind: feature
id: F-user-registration
parent: E-user-management
title: User Registration
status: in-progress
priority: high
created: '2025-07-19T10:03:00Z'
updated: '2025-07-19T10:03:00Z'
schema_version: '1.1'
---
User registration with email verification.
"""
        feature1_file.write_text(feature1_content)

        # Create feature under epic 1: User Profile
        feature2_dir = epic1_dir / "features" / "F-user-profile"
        feature2_dir.mkdir(parents=True)
        feature2_file = feature2_dir / "feature.md"
        feature2_content = """---
kind: feature
id: F-user-profile
parent: E-user-management
title: User Profile
status: open
priority: normal
created: '2025-07-19T10:04:00Z'
updated: '2025-07-19T10:04:00Z'
schema_version: '1.1'
---
User profile management and settings.
"""
        feature2_file.write_text(feature2_content)

        # Create tasks under feature 1
        tasks_open_dir = feature1_dir / "tasks-open"
        tasks_open_dir.mkdir(parents=True)

        task1_file = tasks_open_dir / "T-create-registration-form.md"
        task1_content = """---
kind: task
id: T-create-registration-form
parent: F-user-registration
title: Create Registration Form
status: open
priority: high
created: '2025-07-19T10:05:00Z'
updated: '2025-07-19T10:05:00Z'
schema_version: '1.1'
---
Create user registration form with validation.
"""
        task1_file.write_text(task1_content)

        task2_file = tasks_open_dir / "T-implement-email-verification.md"
        task2_content = """---
kind: task
id: T-implement-email-verification
parent: F-user-registration
title: Implement Email Verification
status: in-progress
priority: high
created: '2025-07-19T10:06:00Z'
updated: '2025-07-19T10:06:00Z'
schema_version: '1.1'
---
Implement email verification for new users.
"""
        task2_file.write_text(task2_content)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test project level - should include both epics
            project_result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "ecommerce", "projectRoot": str(project_root)},
            )

            project_children = project_result.data["children"]
            assert len(project_children) == 2

            # Sort by creation date for consistent testing
            project_children.sort(key=lambda x: x["created"])

            assert project_children[0]["id"] == "user-management"
            assert project_children[0]["kind"] == "epic"
            assert project_children[1]["id"] == "payment-processing"
            assert project_children[1]["kind"] == "epic"

            # Test epic level - should include both features
            epic_result = await client.call_tool(
                "getObject",
                {"kind": "epic", "id": "user-management", "projectRoot": str(project_root)},
            )

            epic_children = epic_result.data["children"]
            assert len(epic_children) == 2

            # Sort by creation date for consistent testing
            epic_children.sort(key=lambda x: x["created"])

            assert epic_children[0]["id"] == "user-registration"
            assert epic_children[0]["kind"] == "feature"
            assert epic_children[1]["id"] == "user-profile"
            assert epic_children[1]["kind"] == "feature"

            # Test feature level - should include both tasks
            feature_result = await client.call_tool(
                "getObject",
                {"kind": "feature", "id": "user-registration", "projectRoot": str(project_root)},
            )

            feature_children = feature_result.data["children"]
            assert len(feature_children) == 2

            # Sort by creation date for consistent testing
            feature_children.sort(key=lambda x: x["created"])

            assert feature_children[0]["id"] == "create-registration-form"
            assert feature_children[0]["kind"] == "task"
            assert feature_children[0]["status"] == "open"
            assert feature_children[1]["id"] == "implement-email-verification"
            assert feature_children[1]["kind"] == "task"
            assert feature_children[1]["status"] == "in-progress"

            # Test task level - should have no children
            task_result = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": "create-registration-form",
                    "projectRoot": str(project_root),
                },
            )

            task_children = task_result.data["children"]
            assert len(task_children) == 0

    @pytest.mark.asyncio
    async def test_mixed_task_status_children_discovery(self, temp_dir):
        """Test children discovery with mixed task statuses (open, in-progress, done)."""
        # Create feature with tasks in different statuses
        project_root = temp_dir / "planning"
        feature_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-mixed-tasks"
        )

        # Create feature
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-mixed-tasks
parent: E-test-epic
title: Mixed Task Status Feature
status: in-progress
priority: normal
created: '2025-07-19T10:00:00Z'
updated: '2025-07-19T10:00:00Z'
schema_version: '1.1'
---
Feature with tasks in various statuses.
"""
        feature_file.write_text(feature_content)

        # Create tasks-open directory with open and in-progress tasks
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_open_dir.mkdir(parents=True)

        open_task_file = tasks_open_dir / "T-open-task.md"
        open_task_content = """---
kind: task
id: T-open-task
parent: F-mixed-tasks
title: Open Task
status: open
priority: normal
created: '2025-07-19T10:01:00Z'
updated: '2025-07-19T10:01:00Z'
schema_version: '1.1'
---
Task in open status.
"""
        open_task_file.write_text(open_task_content)

        progress_task_file = tasks_open_dir / "T-in-progress-task.md"
        progress_task_content = """---
kind: task
id: T-in-progress-task
parent: F-mixed-tasks
title: In Progress Task
status: in-progress
priority: high
created: '2025-07-19T10:02:00Z'
updated: '2025-07-19T10:02:00Z'
schema_version: '1.1'
---
Task in progress status.
"""
        progress_task_file.write_text(progress_task_content)

        review_task_file = tasks_open_dir / "T-review-task.md"
        review_task_content = """---
kind: task
id: T-review-task
parent: F-mixed-tasks
title: Review Task
status: review
priority: normal
created: '2025-07-19T10:03:00Z'
updated: '2025-07-19T10:03:00Z'
schema_version: '1.1'
---
Task in review status.
"""
        review_task_file.write_text(review_task_content)

        # Create tasks-done directory with completed tasks
        tasks_done_dir = feature_dir / "tasks-done"
        tasks_done_dir.mkdir(parents=True)

        done_task1_file = tasks_done_dir / "20250719_100400-T-done-task-1.md"
        done_task1_content = """---
kind: task
id: T-done-task-1
parent: F-mixed-tasks
title: First Done Task
status: done
priority: normal
created: '2025-07-19T10:04:00Z'
updated: '2025-07-19T10:04:00Z'
schema_version: '1.1'
---
First completed task.
"""
        done_task1_file.write_text(done_task1_content)

        done_task2_file = tasks_done_dir / "20250719_100500-T-done-task-2.md"
        done_task2_content = """---
kind: task
id: T-done-task-2
parent: F-mixed-tasks
title: Second Done Task
status: done
priority: low
created: '2025-07-19T10:05:00Z'
updated: '2025-07-19T10:05:00Z'
schema_version: '1.1'
---
Second completed task.
"""
        done_task2_file.write_text(done_task2_content)

        # Create server and test
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"kind": "feature", "id": "mixed-tasks", "projectRoot": str(project_root)},
            )

        # Verify all tasks are included regardless of status
        children = result.data["children"]
        assert len(children) == 5

        # Sort by creation date for consistent testing
        children.sort(key=lambda x: x["created"])

        # Verify tasks in order of creation
        assert children[0]["id"] == "open-task"
        assert children[0]["status"] == "open"

        assert children[1]["id"] == "in-progress-task"
        assert children[1]["status"] == "in-progress"

        assert children[2]["id"] == "review-task"
        assert children[2]["status"] == "review"

        assert children[3]["id"] == "done-task-1"
        assert children[3]["status"] == "done"

        assert children[4]["id"] == "done-task-2"
        assert children[4]["status"] == "done"

    @pytest.mark.asyncio
    async def test_corrupted_child_handling(self, temp_dir):
        """Test that corrupted child objects are handled gracefully."""
        # Create epic with one valid and one corrupted feature
        project_root = temp_dir / "planning"
        epic_dir = project_root / "projects" / "P-test-project" / "epics" / "E-test-epic"
        features_dir = epic_dir / "features"

        # Create epic
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-test-epic
parent: P-test-project
title: Test Epic
status: in-progress
priority: normal
created: '2025-07-19T10:00:00Z'
updated: '2025-07-19T10:00:00Z'
schema_version: '1.1'
---
Epic with one valid and one corrupted feature.
"""
        epic_file.write_text(epic_content)

        # Create valid feature
        valid_feature_dir = features_dir / "F-valid-feature"
        valid_feature_dir.mkdir(parents=True)
        valid_feature_file = valid_feature_dir / "feature.md"
        valid_feature_content = """---
kind: feature
id: F-valid-feature
parent: E-test-epic
title: Valid Feature
status: open
priority: normal
created: '2025-07-19T10:01:00Z'
updated: '2025-07-19T10:01:00Z'
schema_version: '1.1'
---
This is a valid feature.
"""
        valid_feature_file.write_text(valid_feature_content)

        # Create corrupted feature (invalid YAML)
        corrupted_feature_dir = features_dir / "F-corrupted-feature"
        corrupted_feature_dir.mkdir(parents=True)
        corrupted_feature_file = corrupted_feature_dir / "feature.md"
        corrupted_feature_content = """---
kind: feature
id: F-corrupted-feature
parent: E-test-epic
title: Corrupted Feature
status: open
priority: normal
created: INVALID_DATE_FORMAT
updated: '2025-07-19T10:02:00Z'
schema_version: '1.1'
invalid_yaml: [missing_closing_bracket
---
This feature has corrupted YAML front-matter.
"""
        corrupted_feature_file.write_text(corrupted_feature_content)

        # Create server and test
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"kind": "epic", "id": "test-epic", "projectRoot": str(project_root)},
            )

        # Verify only valid children are included
        children = result.data["children"]
        assert len(children) == 1
        assert children[0]["id"] == "valid-feature"
        assert children[0]["title"] == "Valid Feature"

    @pytest.mark.asyncio
    async def test_large_children_collection(self, temp_dir):
        """Test handling of parent objects with many children."""
        # Create project with multiple epics
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-large-project"
        epics_dir = project_dir / "epics"

        # Create project
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-large-project
title: Large Project
status: in-progress
priority: normal
created: '2025-07-19T10:00:00Z'
updated: '2025-07-19T10:00:00Z'
schema_version: '1.1'
---
Project with many epics.
"""
        project_file.write_text(project_content)

        # Create 10 epics
        epic_count = 10
        for i in range(epic_count):
            epic_dir = epics_dir / f"E-epic-{i:02d}"
            epic_dir.mkdir(parents=True)
            epic_file = epic_dir / "epic.md"
            epic_content = f"""---
kind: epic
id: E-epic-{i:02d}
parent: P-large-project
title: Epic {i:02d}
status: open
priority: normal
created: '2025-07-19T10:{i:02d}:00Z'
updated: '2025-07-19T10:{i:02d}:00Z'
schema_version: '1.1'
---
Epic number {i:02d}.
"""
            epic_file.write_text(epic_content)

        # Create server and test
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "large-project", "projectRoot": str(project_root)},
            )

        # Verify all epics are included
        children = result.data["children"]
        assert len(children) == epic_count

        # Sort by creation date and verify order
        children.sort(key=lambda x: x["created"])

        for i, child in enumerate(children):
            assert child["id"] == f"epic-{i:02d}"
            assert child["title"] == f"Epic {i:02d}"
            assert child["kind"] == "epic"
            assert child["status"] == "open"

    @pytest.mark.asyncio
    async def test_real_project_structure_compatibility(self, temp_dir):
        """Test children discovery with realistic project structure naming and content."""
        # Create a realistic project structure similar to actual usage
        project_root = temp_dir / "planning"

        # Create project for web application
        project_dir = project_root / "projects" / "P-web-app-redesign"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-web-app-redesign
title: Web Application Redesign
status: in-progress
priority: high
prerequisites: []
created: '2025-07-19T09:00:00Z'
updated: '2025-07-19T09:00:00Z'
schema_version: '1.1'
---
# Web Application Redesign Project

Complete redesign of the company web application with modern UI/UX and improved performance.

## Objectives
- Modernize user interface
- Improve performance
- Enhance user experience
- Implement responsive design

### Log

Project initiated on 2025-07-19.
"""
        project_file.write_text(project_content)

        # Create Frontend epic
        frontend_epic_dir = project_dir / "epics" / "E-frontend-redesign"
        frontend_epic_dir.mkdir(parents=True)
        frontend_epic_file = frontend_epic_dir / "epic.md"
        frontend_epic_content = """---
kind: epic
id: E-frontend-redesign
parent: P-web-app-redesign
title: Frontend Redesign
status: in-progress
priority: high
prerequisites: []
created: '2025-07-19T09:01:00Z'
updated: '2025-07-19T09:01:00Z'
schema_version: '1.1'
---
# Frontend Redesign Epic

Redesign and modernize the frontend user interface.
"""
        frontend_epic_file.write_text(frontend_epic_content)

        # Create Backend epic
        backend_epic_dir = project_dir / "epics" / "E-backend-optimization"
        backend_epic_dir.mkdir(parents=True)
        backend_epic_file = backend_epic_dir / "epic.md"
        backend_epic_content = """---
kind: epic
id: E-backend-optimization
parent: P-web-app-redesign
title: Backend Optimization
status: open
priority: normal
prerequisites: []
created: '2025-07-19T09:02:00Z'
updated: '2025-07-19T09:02:00Z'
schema_version: '1.1'
---
# Backend Optimization Epic

Optimize backend performance and scalability.
"""
        backend_epic_file.write_text(backend_epic_content)

        # Create UI Components feature under Frontend epic
        ui_components_dir = frontend_epic_dir / "features" / "F-ui-components"
        ui_components_dir.mkdir(parents=True)
        ui_components_file = ui_components_dir / "feature.md"
        ui_components_content = """---
kind: feature
id: F-ui-components
parent: E-frontend-redesign
title: UI Component Library
status: in-progress
priority: high
prerequisites: []
created: '2025-07-19T09:03:00Z'
updated: '2025-07-19T09:03:00Z'
schema_version: '1.1'
---
# UI Component Library Feature

Create reusable UI component library.
"""
        ui_components_file.write_text(ui_components_content)

        # Create task under UI Components
        ui_tasks_dir = ui_components_dir / "tasks-open"
        ui_tasks_dir.mkdir(parents=True)
        button_task_file = ui_tasks_dir / "T-create-button-component.md"
        button_task_content = """---
kind: task
id: T-create-button-component
parent: F-ui-components
title: Create Button Component
status: open
priority: high
prerequisites: []
created: '2025-07-19T09:04:00Z'
updated: '2025-07-19T09:04:00Z'
schema_version: '1.1'
---
# Create Button Component Task

Implement reusable button component with variants.

## Requirements
- Multiple button variants (primary, secondary, outline)
- Size options (small, medium, large)
- Disabled state
- Loading state
"""
        button_task_file.write_text(button_task_content)

        # Create server and test hierarchy navigation
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test project → epics
            project_result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "web-app-redesign", "projectRoot": str(project_root)},
            )

            project_children = project_result.data["children"]
            assert len(project_children) == 2
            project_children.sort(key=lambda x: x["created"])
            assert project_children[0]["title"] == "Frontend Redesign"
            assert project_children[1]["title"] == "Backend Optimization"

            # Test epic → features
            epic_result = await client.call_tool(
                "getObject",
                {"kind": "epic", "id": "frontend-redesign", "projectRoot": str(project_root)},
            )

            epic_children = epic_result.data["children"]
            assert len(epic_children) == 1
            assert epic_children[0]["title"] == "UI Component Library"

            # Test feature → tasks
            feature_result = await client.call_tool(
                "getObject",
                {"kind": "feature", "id": "ui-components", "projectRoot": str(project_root)},
            )

            feature_children = feature_result.data["children"]
            assert len(feature_children) == 1
            assert feature_children[0]["title"] == "Create Button Component"
            assert feature_children[0]["status"] == "open"
