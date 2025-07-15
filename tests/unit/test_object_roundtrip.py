"""Tests for object load/dump round-trip functionality.

This module tests the round-trip behavior of loading objects from markdown
files and dumping them back to markdown format. Each object kind (project,
epic, feature, task) should maintain data integrity through the load/dump cycle.
"""

from datetime import datetime
from pathlib import Path

from trellis_mcp.models.common import Priority
from trellis_mcp.object_dumper import dump_object
from trellis_mcp.object_parser import parse_object
from trellis_mcp.schema.epic import EpicModel
from trellis_mcp.schema.feature import FeatureModel
from trellis_mcp.schema.kind_enum import KindEnum
from trellis_mcp.schema.project import ProjectModel
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel


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
            schema_version="1.0",
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
            schema_version="1.0",
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
            schema_version="1.0",
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

    def test_epic_roundtrip_full(self, temp_dir: Path) -> None:
        """Test round-trip for epic with all possible fields."""
        # Create full epic model
        now = datetime.now()
        epic = EpicModel(
            kind=KindEnum.EPIC,
            id="full-epic",
            parent="parent-project",
            status=StatusEnum.DONE,
            title="Full Test Epic",
            priority=Priority.LOW,
            prerequisites=["other-epic-1", "other-epic-2"],
            worktree="/path/to/epic/worktree",
            created=now,
            updated=now,
            schema_version="1.0",
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

    def test_feature_roundtrip_minimal(self, temp_dir: Path) -> None:
        """Test round-trip for feature with minimal required fields."""
        # Create minimal feature model
        now = datetime.now()
        feature = FeatureModel(
            kind=KindEnum.FEATURE,
            id="test-feature",
            parent="test-epic",
            status=StatusEnum.DRAFT,
            title="Test Feature",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
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
            schema_version="1.0",
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
            schema_version="1.0",
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
            schema_version="1.0",
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
            schema_version="1.0",
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

    def test_empty_prerequisites_roundtrip(self, temp_dir: Path) -> None:
        """Test round-trip behavior with empty prerequisites list."""
        # Create task with empty prerequisites
        now = datetime.now()
        task = TaskModel(
            kind=KindEnum.TASK,
            id="empty-prereqs-task",
            parent="test-feature",
            status=StatusEnum.OPEN,
            title="Task with Empty Prerequisites",
            priority=Priority.NORMAL,
            prerequisites=[],  # Explicitly empty
            worktree=None,
            created=now,
            updated=now,
            schema_version="1.0",
        )

        # Dump to markdown
        markdown_content = dump_object(task)

        # Write to temporary file
        task_file = temp_dir / "empty_prereqs.md"
        task_file.write_text(markdown_content)

        # Load from file
        loaded_task = parse_object(task_file)

        # Verify empty prerequisites are preserved
        assert isinstance(loaded_task, TaskModel)
        assert loaded_task.prerequisites == []

    def test_null_worktree_roundtrip(self, temp_dir: Path) -> None:
        """Test round-trip behavior with null worktree field."""
        # Create project with null worktree
        now = datetime.now()
        project = ProjectModel(
            kind=KindEnum.PROJECT,
            id="null-worktree-project",
            parent=None,
            status=StatusEnum.DRAFT,
            title="Project with Null Worktree",
            priority=Priority.NORMAL,
            prerequisites=[],
            worktree=None,  # Explicitly null
            created=now,
            updated=now,
            schema_version="1.0",
        )

        # Dump to markdown
        markdown_content = dump_object(project)

        # Write to temporary file
        project_file = temp_dir / "null_worktree.md"
        project_file.write_text(markdown_content)

        # Load from file
        loaded_project = parse_object(project_file)

        # Verify null worktree is preserved
        assert isinstance(loaded_project, ProjectModel)
        assert loaded_project.worktree is None

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
                schema_version="1.0",
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
                schema_version="1.0",
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
                schema_version="1.0",
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
            schema_version="1.0",
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
            schema_version="1.0",
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
