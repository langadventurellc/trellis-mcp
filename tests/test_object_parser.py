"""Tests for object parser functionality."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from trellis_mcp.object_parser import parse_object
from trellis_mcp.schema.epic import EpicModel
from trellis_mcp.schema.feature import FeatureModel
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.priority_enum import PriorityEnum
from trellis_mcp.schema.project import ProjectModel
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


class TestParseObject:
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
schema_version: "1.0"
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
        assert result.priority == PriorityEnum.HIGH
        assert result.prerequisites == []
        assert result.schema_version == "1.0"

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
schema_version: "1.0"
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
        assert result.priority == PriorityEnum.NORMAL

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
schema_version: "1.0"
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
        assert result.priority == PriorityEnum.LOW

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
schema_version: "1.0"
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
        assert result.priority == PriorityEnum.HIGH

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
schema_version: "1.0"
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
schema_version: "1.0"
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
schema_version: "1.0"
---

# Feature with Worktree
"""
        feature_file.write_text(feature_content)

        result = parse_object(feature_file)

        assert isinstance(result, FeatureModel)
        assert result.worktree == "/path/to/worktree"


class TestParseObjectErrors:
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
schema_version: "1.0"
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
schema_version: "1.0"
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
schema_version: "1.0"
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


class TestParseObjectEdgeCases:
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
schema_version: "1.0"
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
schema_version: "1.0"
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
schema_version: "1.0"
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
schema_version: "1.0"
---

# Project with Review Status
"""
        invalid_file.write_text(invalid_content)

        with pytest.raises(ValidationError):
            parse_object(invalid_file)
