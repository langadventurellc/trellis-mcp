"""Tests for comprehensive object operations including parsing and round-trip functionality.

This module consolidates tests from test_object_parser.py and test_object_roundtrip.py
to provide comprehensive coverage of object operations while eliminating redundancy.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from trellis_mcp.models.common import Priority
from trellis_mcp.object_dumper import dump_object
from trellis_mcp.object_parser import parse_object
from trellis_mcp.schema.epic import EpicModel
from trellis_mcp.schema.feature import FeatureModel
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.project import ProjectModel
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


class TestObjectParsing:
    """Test parse_object function with various object types."""

    def test_parse_project_object(self, temp_dir: Path) -> None:
        """Test parsing a valid project markdown file."""
        project_file = temp_dir / "project.md"
        project_content = """---
kind: project
id: P-001
parent: null
status: draft
title: Sample Project
priority: high
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Sample Project

This is a sample project description.
"""
        project_file.write_text(project_content)

        result = parse_object(project_file)

        assert isinstance(result, ProjectModel)
        assert result.kind == KindEnum.PROJECT
        assert result.id == "P-001"
        assert result.parent is None
        assert result.status == StatusEnum.DRAFT
        assert result.title == "Sample Project"
        assert result.priority == Priority.HIGH
        assert result.prerequisites == []
        assert result.schema_version == "1.1"

    def test_parse_epic_object(self, temp_dir: Path) -> None:
        """Test parsing a valid epic markdown file."""
        epic_file = temp_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-001
parent: P-001
status: in-progress
title: Sample Epic
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Sample Epic

This is a sample epic description.
"""
        epic_file.write_text(epic_content)

        result = parse_object(epic_file)

        assert isinstance(result, EpicModel)
        assert result.kind == KindEnum.EPIC
        assert result.id == "E-001"
        assert result.parent == "P-001"
        assert result.status == StatusEnum.IN_PROGRESS
        assert result.title == "Sample Epic"
        assert result.priority == Priority.NORMAL

    def test_parse_feature_object(self, temp_dir: Path) -> None:
        """Test parsing a valid feature markdown file."""
        feature_file = temp_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-001
parent: E-001
status: done
title: Sample Feature
priority: low
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Sample Feature

This is a sample feature description.
"""
        feature_file.write_text(feature_content)

        result = parse_object(feature_file)

        assert isinstance(result, FeatureModel)
        assert result.kind == KindEnum.FEATURE
        assert result.id == "F-001"
        assert result.parent == "E-001"
        assert result.status == StatusEnum.DONE
        assert result.title == "Sample Feature"
        assert result.priority == Priority.LOW

    def test_parse_task_object(self, temp_dir: Path) -> None:
        """Test parsing a valid task markdown file."""
        task_file = temp_dir / "task.md"
        task_content = """---
kind: task
id: T-001
parent: F-001
status: open
title: Sample Task
priority: high
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Sample Task

This is a sample task description.
"""
        task_file.write_text(task_content)

        result = parse_object(task_file)

        assert isinstance(result, TaskModel)
        assert result.kind == KindEnum.TASK
        assert result.id == "T-001"
        assert result.parent == "F-001"
        assert result.status == StatusEnum.OPEN
        assert result.title == "Sample Task"
        assert result.priority == Priority.HIGH

    def test_parse_with_string_path(self, temp_dir: Path) -> None:
        """Test parsing with string path instead of Path object."""
        project_file = temp_dir / "project.md"
        project_content = """---
kind: project
id: P-001
parent: null
status: draft
title: Sample Project
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Sample Project
"""
        project_file.write_text(project_content)

        result = parse_object(str(project_file))

        assert isinstance(result, ProjectModel)
        assert result.kind == KindEnum.PROJECT
        assert result.id == "P-001"

    def test_parse_with_prerequisites(self, temp_dir: Path) -> None:
        """Test parsing object with prerequisites."""
        task_file = temp_dir / "task.md"
        task_content = """---
kind: task
id: T-002
parent: F-001
status: open
title: Task with Prerequisites
priority: normal
prerequisites: ["T-001", "T-003"]
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Task with Prerequisites
"""
        task_file.write_text(task_content)

        result = parse_object(task_file)

        assert isinstance(result, TaskModel)
        assert result.prerequisites == ["T-001", "T-003"]

    def test_parse_with_worktree(self, temp_dir: Path) -> None:
        """Test parsing object with worktree path."""
        feature_file = temp_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-002
parent: E-001
status: in-progress
title: Feature with Worktree
priority: normal
prerequisites: []
worktree: "/path/to/worktree"
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Feature with Worktree
"""
        feature_file.write_text(feature_content)

        result = parse_object(feature_file)

        assert isinstance(result, FeatureModel)
        assert result.worktree == "/path/to/worktree"


class TestObjectParsingErrors:
    """Test error handling in parse_object function."""

    def test_parse_missing_file(self, temp_dir: Path) -> None:
        """Test error handling for missing file."""
        missing_file = temp_dir / "missing.md"

        with pytest.raises(FileNotFoundError, match="File not found"):
            parse_object(missing_file)

    def test_parse_missing_kind_field(self, temp_dir: Path) -> None:
        """Test error handling for missing kind field."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
id: P-001
status: draft
title: Invalid Object
---

# Invalid Object
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValueError, match="Missing 'kind' field"):
            parse_object(invalid_file)

    def test_parse_invalid_kind_value(self, temp_dir: Path) -> None:
        """Test error handling for invalid kind value."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: invalid_kind
id: P-001
status: draft
title: Invalid Object
---

# Invalid Object
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValueError, match="Invalid kind value 'invalid_kind'"):
            parse_object(invalid_file)

    def test_parse_invalid_yaml(self, temp_dir: Path) -> None:
        """Test error handling for invalid YAML front-matter."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: project
id: P-001
invalid: yaml: content: [
---

# Invalid YAML
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValueError, match="Failed to load markdown"):
            parse_object(invalid_file)

    def test_parse_validation_error(self, temp_dir: Path) -> None:
        """Test error handling for Pydantic validation errors."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: project
id: P-001
parent: null
status: invalid_status
title: Invalid Project
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Invalid Project
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValidationError):
            parse_object(invalid_file)

    def test_parse_missing_required_field(self, temp_dir: Path) -> None:
        """Test error handling for missing required field."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: project
# Missing required 'id' field
parent: null
status: draft
title: Invalid Project
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Invalid Project
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValidationError):
            parse_object(invalid_file)

    def test_parse_invalid_schema_version(self, temp_dir: Path) -> None:
        """Test error handling for invalid schema version."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: project
id: P-001
parent: null
status: draft
title: Invalid Project
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "2.0"
---

# Invalid Project
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValidationError):
            parse_object(invalid_file)

    def test_parse_invalid_parent_for_project(self, temp_dir: Path) -> None:
        """Test error handling for project with non-null parent."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: project
id: P-001
parent: "some-parent"
status: draft
title: Invalid Project
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Invalid Project
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValidationError):
            parse_object(invalid_file)

    def test_parse_empty_front_matter(self, temp_dir: Path) -> None:
        """Test error handling for empty front-matter."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---

---

# Empty Front Matter
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValueError, match="Missing 'kind' field"):
            parse_object(invalid_file)

    def test_parse_no_front_matter(self, temp_dir: Path) -> None:
        """Test error handling for no front-matter."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = "# No Front Matter\n\nJust markdown content."
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValueError, match="Missing 'kind' field"):
            parse_object(invalid_file)


class TestObjectParsingEdgeCases:
    """Test edge cases and special scenarios."""

    def test_parse_with_extra_fields(self, temp_dir: Path) -> None:
        """Test parsing with extra fields (should be rejected due to extra='forbid')."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: project
id: P-001
parent: null
status: draft
title: Project with Extra Field
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
extra_field: "should not be allowed"
---

# Project with Extra Field
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValidationError):
            parse_object(invalid_file)

    def test_parse_with_null_values(self, temp_dir: Path) -> None:
        """Test parsing with null values where appropriate."""
        task_file = temp_dir / "task.md"
        task_content = """---
kind: task
id: T-001
parent: F-001
status: open
title: Task with Nulls
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Task with Nulls
"""
        task_file.write_text(task_content)

        result = parse_object(task_file)

        assert isinstance(result, TaskModel)
        assert result.worktree is None
        assert result.prerequisites == []

    def test_parse_task_with_review_status(self, temp_dir: Path) -> None:
        """Test parsing task with review status (specific to tasks)."""
        task_file = temp_dir / "task.md"
        task_content = """---
kind: task
id: T-001
parent: F-001
status: review
title: Task in Review
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Task in Review
"""
        task_file.write_text(task_content)

        result = parse_object(task_file)

        assert isinstance(result, TaskModel)
        assert result.status == StatusEnum.REVIEW

    def test_parse_project_with_review_status_should_fail(self, temp_dir: Path) -> None:
        """Test that project with review status should fail validation."""
        invalid_file = temp_dir / "invalid.md"
        invalid_content = """---
kind: project
id: P-001
parent: null
status: review
title: Project with Review Status
priority: normal
prerequisites: []
worktree: null
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
schema_version: "1.1"
---

# Project with Review Status
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValidationError):
            parse_object(invalid_file)


class TestObjectRoundTrip:
    """Test round-trip load/dump functionality for all object kinds."""

    def test_project_roundtrip_minimal(self, temp_dir: Path) -> None:
        """Test round-trip for project with minimal required fields."""
        # Create minimal project model
        now = datetime.now()
        project = ProjectModel(
            kind=KindEnum.PROJECT,
            id="test-project",
            parent=None,
            status=StatusEnum.DRAFT,
            title="Test Project",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump to markdown
        markdown_content = dump_object(project)

        # Write to temporary file
        project_file = temp_dir / "project.md"
        project_file.write_text(markdown_content)

        # Load from file
        loaded_project = parse_object(project_file)

        # Verify round-trip integrity
        assert isinstance(loaded_project, ProjectModel)
        assert loaded_project.kind == project.kind
        assert loaded_project.id == project.id
        assert loaded_project.parent == project.parent
        assert loaded_project.status == project.status
        assert loaded_project.title == project.title
        assert loaded_project.priority == project.priority
        assert loaded_project.prerequisites == project.prerequisites
        assert loaded_project.worktree == project.worktree
        assert loaded_project.created == project.created
        # Note: updated timestamp is modified during dump, so we don't check exact equality
        assert loaded_project.updated >= project.updated
        assert loaded_project.schema_version == project.schema_version

    def test_project_roundtrip_full(self, temp_dir: Path) -> None:
        """Test round-trip for project with all possible fields."""
        # Create full project model
        now = datetime.now()
        project = ProjectModel(
            kind=KindEnum.PROJECT,
            id="full-project",
            parent=None,
            status=StatusEnum.IN_PROGRESS,
            title="Full Test Project",
            priority=Priority.HIGH,
            prerequisites=["other-project"],
            worktree="/path/to/worktree",
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump to markdown
        markdown_content = dump_object(project)

        # Write to temporary file
        project_file = temp_dir / "project.md"
        project_file.write_text(markdown_content)

        # Load from file
        loaded_project = parse_object(project_file)

        # Verify round-trip integrity
        assert isinstance(loaded_project, ProjectModel)
        assert loaded_project.kind == project.kind
        assert loaded_project.id == project.id
        assert loaded_project.parent == project.parent
        assert loaded_project.status == project.status
        assert loaded_project.title == project.title
        assert loaded_project.priority == project.priority
        assert loaded_project.prerequisites == project.prerequisites
        assert loaded_project.worktree == project.worktree
        assert loaded_project.created == project.created
        assert loaded_project.updated >= project.updated
        assert loaded_project.schema_version == project.schema_version

    def test_epic_roundtrip_minimal(self, temp_dir: Path) -> None:
        """Test round-trip for epic with minimal required fields."""
        # Create minimal epic model
        now = datetime.now()
        epic = EpicModel(
            kind=KindEnum.EPIC,
            id="test-epic",
            parent="test-project",
            status=StatusEnum.DRAFT,
            title="Test Epic",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump to markdown
        markdown_content = dump_object(epic)

        # Write to temporary file
        epic_file = temp_dir / "epic.md"
        epic_file.write_text(markdown_content)

        # Load from file
        loaded_epic = parse_object(epic_file)

        # Verify round-trip integrity
        assert isinstance(loaded_epic, EpicModel)
        assert loaded_epic.kind == epic.kind
        assert loaded_epic.id == epic.id
        assert loaded_epic.parent == epic.parent
        assert loaded_epic.status == epic.status
        assert loaded_epic.title == epic.title
        assert loaded_epic.priority == epic.priority
        assert loaded_epic.prerequisites == epic.prerequisites
        assert loaded_epic.worktree == epic.worktree
        assert loaded_epic.created == epic.created
        assert loaded_epic.updated >= epic.updated
        assert loaded_epic.schema_version == epic.schema_version

    def test_feature_roundtrip_full(self, temp_dir: Path) -> None:
        """Test round-trip for feature with all possible fields."""
        # Create full feature model
        now = datetime.now()
        feature = FeatureModel(
            kind=KindEnum.FEATURE,
            id="full-feature",
            parent="parent-epic",
            status=StatusEnum.IN_PROGRESS,
            title="Full Test Feature",
            priority=Priority.HIGH,
            prerequisites=["prereq-feature-1", "prereq-feature-2", "prereq-feature-3"],
            worktree="/path/to/feature/worktree",
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump to markdown
        markdown_content = dump_object(feature)

        # Write to temporary file
        feature_file = temp_dir / "feature.md"
        feature_file.write_text(markdown_content)

        # Load from file
        loaded_feature = parse_object(feature_file)

        # Verify round-trip integrity
        assert isinstance(loaded_feature, FeatureModel)
        assert loaded_feature.kind == feature.kind
        assert loaded_feature.id == feature.id
        assert loaded_feature.parent == feature.parent
        assert loaded_feature.status == feature.status
        assert loaded_feature.title == feature.title
        assert loaded_feature.priority == feature.priority
        assert loaded_feature.prerequisites == feature.prerequisites
        assert loaded_feature.worktree == feature.worktree
        assert loaded_feature.created == feature.created
        assert loaded_feature.updated >= feature.updated
        assert loaded_feature.schema_version == feature.schema_version

    def test_task_roundtrip_minimal(self, temp_dir: Path) -> None:
        """Test round-trip for task with minimal required fields."""
        # Create minimal task model
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="test-task",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump to markdown
        markdown_content = dump_object(task)

        # Write to temporary file
        task_file = temp_dir / "task.md"
        task_file.write_text(markdown_content)

        # Load from file
        loaded_task = parse_object(task_file)

        # Verify round-trip integrity
        assert isinstance(loaded_task, TaskModel)
        assert loaded_task.kind == task.kind
        assert loaded_task.id == task.id
        assert loaded_task.parent == task.parent
        assert loaded_task.status == task.status
        assert loaded_task.title == task.title
        assert loaded_task.priority == task.priority
        assert loaded_task.prerequisites == task.prerequisites
        assert loaded_task.worktree == task.worktree
        assert loaded_task.created == task.created
        assert loaded_task.updated >= task.updated
        assert loaded_task.schema_version == task.schema_version

    def test_task_roundtrip_full(self, temp_dir: Path) -> None:
        """Test round-trip for task with all possible fields."""
        # Create full task model
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="full-task",
            parent="parent-feature",
            status=StatusEnum.REVIEW,
            title="Full Test Task",
            priority=Priority.HIGH,
            prerequisites=["prereq-task-1", "prereq-task-2"],
            worktree="/path/to/task/worktree",
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump to markdown
        markdown_content = dump_object(task)

        # Write to temporary file
        task_file = temp_dir / "task.md"
        task_file.write_text(markdown_content)

        # Load from file
        loaded_task = parse_object(task_file)

        # Verify round-trip integrity
        assert isinstance(loaded_task, TaskModel)
        assert loaded_task.kind == task.kind
        assert loaded_task.id == task.id
        assert loaded_task.parent == task.parent
        assert loaded_task.status == task.status
        assert loaded_task.title == task.title
        assert loaded_task.priority == task.priority
        assert loaded_task.prerequisites == task.prerequisites
        assert loaded_task.worktree == task.worktree
        assert loaded_task.created == task.created
        assert loaded_task.updated >= task.updated
        assert loaded_task.schema_version == task.schema_version

    def test_multiple_roundtrips_preserve_integrity(self, temp_dir: Path) -> None:
        """Test that multiple round-trips preserve data integrity."""
        # Create original task
        now = datetime.now()
        original_task = TaskModel(
            kind=KindEnum.TASK,
            id="roundtrip-task",
            parent="test-feature",
            status=StatusEnum.IN_PROGRESS,
            title="Multi-Roundtrip Task",
            priority=Priority.NORMAL,
            prerequisites=["prereq-1", "prereq-2"],
            worktree="/path/to/worktree",
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Perform 3 round-trips
        current_task = original_task
        for i in range(3):
            # Dump to markdown
            markdown_content = dump_object(current_task)

            # Write to temporary file
            task_file = temp_dir / f"roundtrip_{i}.md"
            task_file.write_text(markdown_content)

            # Load from file
            current_task = parse_object(task_file)

        # Verify final result maintains integrity (except updated timestamp)
        assert isinstance(current_task, TaskModel)
        assert current_task.kind == original_task.kind
        assert current_task.id == original_task.id
        assert current_task.parent == original_task.parent
        assert current_task.status == original_task.status
        assert current_task.title == original_task.title
        assert current_task.priority == original_task.priority
        assert current_task.prerequisites == original_task.prerequisites
        assert current_task.worktree == original_task.worktree
        assert current_task.created == original_task.created
        assert current_task.updated >= original_task.updated
        assert current_task.schema_version == original_task.schema_version

    def test_all_status_values_roundtrip(self, temp_dir: Path) -> None:
        """Test round-trip behavior for all valid status values per kind."""
        now = datetime.now()

        # Test all valid project statuses
        project_statuses = [StatusEnum.DRAFT, StatusEnum.IN_PROGRESS, StatusEnum.DONE]
        for status in project_statuses:
            project = ProjectModel(
                kind=KindEnum.PROJECT,
                id=f"project-{status.value}",
                parent=None,
                status=status,
                title=f"Project with {status.value} Status",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=now,
                updated=now,
                schema_version="1.1",
            )

            # Round-trip
            markdown_content = dump_object(project)
            project_file = temp_dir / f"project_{status.value}.md"
            project_file.write_text(markdown_content)
            loaded_project = parse_object(project_file)

            assert isinstance(loaded_project, ProjectModel)
            assert loaded_project.status == status

        # Test all valid task statuses
        task_statuses = [
            StatusEnum.OPEN,
            StatusEnum.IN_PROGRESS,
            StatusEnum.REVIEW,
            StatusEnum.DONE,
        ]
        for status in task_statuses:
            task = TaskModel(
                kind=KindEnum.TASK,
                id=f"task-{status.value}",
                parent="test-feature",
                status=status,
                title=f"Task with {status.value} Status",
                priority=Priority.NORMAL,
                prerequisites=[],
                worktree=None,
                created=now,
                updated=now,
                schema_version="1.1",
            )

            # Round-trip
            markdown_content = dump_object(task)
            task_file = temp_dir / f"task_{status.value}.md"
            task_file.write_text(markdown_content)
            loaded_task = parse_object(task_file)

            assert isinstance(loaded_task, TaskModel)
            assert loaded_task.status == status

    def test_all_priority_values_roundtrip(self, temp_dir: Path) -> None:
        """Test round-trip behavior for all priority values."""
        now = datetime.now()

        priorities = [Priority.HIGH, Priority.NORMAL, Priority.LOW]
        for priority in priorities:
            feature = FeatureModel(
                kind=KindEnum.FEATURE,
                id=f"feature-{priority.value}",
                parent="test-epic",
                status=StatusEnum.DRAFT,
                title=f"Feature with {priority.value} Priority",
                priority=priority,
                prerequisites=[],
                worktree=None,
                created=now,
                updated=now,
                schema_version="1.1",
            )

            # Round-trip
            markdown_content = dump_object(feature)
            feature_file = temp_dir / f"feature_{priority.value}.md"
            feature_file.write_text(markdown_content)
            loaded_feature = parse_object(feature_file)

            assert isinstance(loaded_feature, FeatureModel)
            assert loaded_feature.priority == priority

    def test_complex_prerequisites_roundtrip(self, temp_dir: Path) -> None:
        """Test round-trip behavior with complex prerequisites."""
        now = datetime.now()

        # Create epic with multiple prerequisites including prefixed and non-prefixed IDs
        epic = EpicModel(
            kind=KindEnum.EPIC,
            id="complex-prereqs-epic",
            parent="test-project",
            status=StatusEnum.IN_PROGRESS,
            title="Epic with Complex Prerequisites",
            priority=Priority.NORMAL,
            prerequisites=[
                "E-first-epic",
                "second-epic",
                "E-third-epic",
                "fourth-epic-with-dashes",
                "E-fifth-epic-with-many-dashes",
            ],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Round-trip
        markdown_content = dump_object(epic)
        epic_file = temp_dir / "complex_prereqs.md"
        epic_file.write_text(markdown_content)
        loaded_epic = parse_object(epic_file)

        # Verify complex prerequisites are preserved exactly
        assert isinstance(loaded_epic, EpicModel)
        assert loaded_epic.prerequisites == [
            "E-first-epic",
            "second-epic",
            "E-third-epic",
            "fourth-epic-with-dashes",
            "E-fifth-epic-with-many-dashes",
        ]

    def test_datetime_precision_roundtrip(self, temp_dir: Path) -> None:
        """Test that datetime precision is preserved through round-trip."""
        # Create datetime with microseconds
        created_time = datetime(2025, 1, 15, 14, 30, 45, 123456)
        updated_time = datetime(2025, 1, 15, 15, 45, 30, 654321)

        task = TaskModel(
            kind=KindEnum.TASK,
            id="datetime-precision-task",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="DateTime Precision Test Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=created_time,
            updated=updated_time,
            schema_version="1.1",
        )

        # Round-trip
        markdown_content = dump_object(task)
        task_file = temp_dir / "datetime_precision.md"
        task_file.write_text(markdown_content)
        loaded_task = parse_object(task_file)

        # Verify datetime precision is preserved
        assert isinstance(loaded_task, TaskModel)
        assert loaded_task.created == created_time
        # Note: updated timestamp is modified during dump_object,
        # so we only check that it's >= the original timestamp
        assert loaded_task.updated >= updated_time

    def test_standalone_task_roundtrip_minimal(self, temp_dir: Path) -> None:
        """Test round-trip for standalone task with minimal required fields."""
        # Create minimal standalone task model (parent=None)
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="standalone-task",
            parent=None,  # Explicitly standalone
            status=StatusEnum.OPEN,
            title="Standalone Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump to markdown
        markdown_content = dump_object(task)

        # Verify parent field is not included in serialized output
        assert "parent:" not in markdown_content
        assert "parent: null" not in markdown_content

        # Write to temporary file
        task_file = temp_dir / "standalone_task.md"
        task_file.write_text(markdown_content)

        # Load from file
        loaded_task = parse_object(task_file)

        # Verify round-trip integrity
        assert isinstance(loaded_task, TaskModel)
        assert loaded_task.kind == task.kind
        assert loaded_task.id == task.id
        assert loaded_task.parent is None  # Should default to None when missing
        assert loaded_task.status == task.status
        assert loaded_task.title == task.title
        assert loaded_task.priority == task.priority
        assert loaded_task.prerequisites == task.prerequisites
        assert loaded_task.worktree == task.worktree
        assert loaded_task.created == task.created
        assert loaded_task.updated >= task.updated
        assert loaded_task.schema_version == task.schema_version

    def test_standalone_task_vs_hierarchy_task_serialization(self, temp_dir: Path) -> None:
        """Test that standalone and hierarchy tasks serialize differently."""
        now = datetime.now()

        # Create standalone task
        standalone_task = TaskModel(
            kind=KindEnum.TASK,
            id="standalone-task-compare",
            parent=None,
            status=StatusEnum.OPEN,
            title="Standalone Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Create hierarchy task
        hierarchy_task = TaskModel(
            kind=KindEnum.TASK,
            id="hierarchy-task-compare",
            parent="F-parent-feature",
            status=StatusEnum.OPEN,
            title="Hierarchy Task",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Dump both to markdown
        standalone_content = dump_object(standalone_task)
        hierarchy_content = dump_object(hierarchy_task)

        # Verify standalone task omits parent field
        assert "parent:" not in standalone_content
        assert "parent: null" not in standalone_content

        # Verify hierarchy task includes parent field
        assert "parent: F-parent-feature" in hierarchy_content

        # Test round-trip for both
        standalone_file = temp_dir / "standalone_compare.md"
        standalone_file.write_text(standalone_content)
        loaded_standalone = parse_object(standalone_file)

        hierarchy_file = temp_dir / "hierarchy_compare.md"
        hierarchy_file.write_text(hierarchy_content)
        loaded_hierarchy = parse_object(hierarchy_file)

        # Verify both load correctly
        assert isinstance(loaded_standalone, TaskModel)
        assert loaded_standalone.parent is None

        assert isinstance(loaded_hierarchy, TaskModel)
        assert loaded_hierarchy.parent == "F-parent-feature"

    def test_task_with_missing_parent_field_in_yaml(self, temp_dir: Path) -> None:
        """Test deserialization of task YAML that completely lacks parent field."""
        # Create YAML content without parent field at all
        yaml_content = """---
kind: task
id: missing-parent-field-task
status: open
title: Task Missing Parent Field
priority: normal
prerequisites: []
created: '2025-01-15T14:30:45.123456'
updated: '2025-01-15T15:45:30.654321'
schema_version: '1.1'
---
Task description here.
"""

        # Write to file and load
        task_file = temp_dir / "missing_parent.md"
        task_file.write_text(yaml_content)
        loaded_task = parse_object(task_file)

        # Verify task loads correctly as standalone task
        assert isinstance(loaded_task, TaskModel)
        assert loaded_task.kind == KindEnum.TASK
        assert loaded_task.id == "missing-parent-field-task"
        assert loaded_task.parent is None  # Should default to None
        assert loaded_task.status == StatusEnum.OPEN
        assert loaded_task.title == "Task Missing Parent Field"

    def test_task_with_empty_string_parent_conversion(self, temp_dir: Path) -> None:
        """Test that empty string parent is converted to None and serialized consistently."""
        # Create task with empty string parent (should be converted to None)
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="empty-string-parent-task",
            parent="",  # Empty string should be converted to None
            status=StatusEnum.OPEN,
            title="Task with Empty String Parent",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.1",
        )

        # Verify empty string was converted to None
        assert task.parent is None

        # Dump to markdown
        markdown_content = dump_object(task)

        # Verify parent field is not included in serialized output (since it's None)
        assert "parent:" not in markdown_content
        assert "parent: null" not in markdown_content

        # Write to file and load back
        task_file = temp_dir / "empty_string_parent.md"
        task_file.write_text(markdown_content)
        loaded_task = parse_object(task_file)

        # Verify round-trip integrity
        assert isinstance(loaded_task, TaskModel)
        assert loaded_task.parent is None
        assert loaded_task.id == "empty-string-parent-task"
