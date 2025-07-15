"""Tests for io_utils module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from trellis_mcp.io_utils import read_markdown, write_markdown


class TestReadMarkdown:
    """Test cases for read_markdown function."""

    def test_read_markdown_with_frontmatter(self):
        """Test reading markdown file with YAML front-matter."""
        content = """---
title: Test Task
status: open
priority: high
---
This is the task description.

## Details
More details here.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            yaml_dict, body_str = read_markdown(f.name)

            assert yaml_dict == {"title": "Test Task", "status": "open", "priority": "high"}
            assert body_str == "This is the task description.\n\n## Details\nMore details here.\n"

            # Clean up
            Path(f.name).unlink()

    def test_read_markdown_without_frontmatter(self):
        """Test reading markdown file without YAML front-matter."""
        content = """# Title
This is just markdown content without front-matter.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            yaml_dict, body_str = read_markdown(f.name)

            assert yaml_dict == {}
            assert body_str == content

            # Clean up
            Path(f.name).unlink()

    def test_read_markdown_empty_frontmatter(self):
        """Test reading markdown file with empty YAML front-matter."""
        content = """---

---
Just the body content.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            yaml_dict, body_str = read_markdown(f.name)

            assert yaml_dict == {}
            assert body_str == "Just the body content.\n"

            # Clean up
            Path(f.name).unlink()

    def test_read_markdown_file_not_found(self):
        """Test reading non-existent markdown file."""
        with pytest.raises(FileNotFoundError):
            read_markdown("non_existent_file.md")

    def test_read_markdown_invalid_yaml(self):
        """Test reading markdown file with invalid YAML front-matter."""
        content = """---
title: Test Task
invalid: yaml: content: here
---
Body content.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            with pytest.raises(yaml.YAMLError):
                read_markdown(f.name)

            # Clean up
            Path(f.name).unlink()

    def test_read_markdown_invalid_frontmatter_format(self):
        """Test reading markdown file with invalid front-matter format."""
        content = """---
title: Test Task
status: open
Body content without closing front-matter delimiter.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            with pytest.raises(ValueError):
                read_markdown(f.name)

            # Clean up
            Path(f.name).unlink()

    def test_read_markdown_pathlib_path(self):
        """Test reading markdown file using pathlib.Path."""
        content = """---
title: Path Test
---
Testing with pathlib.Path.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            path = Path(f.name)
            yaml_dict, body_str = read_markdown(path)

            assert yaml_dict == {"title": "Path Test"}
            assert body_str == "Testing with pathlib.Path.\n"

            # Clean up
            path.unlink()


class TestWriteMarkdown:
    """Test cases for write_markdown function."""

    def test_write_markdown_basic(self):
        """Test writing basic markdown file with YAML front-matter."""
        yaml_dict = {"title": "Test Task", "status": "open", "priority": "high"}
        body_str = "This is the task description.\n\n## Details\nMore details here.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            write_markdown(f.name, yaml_dict, body_str)

            # Read back and verify
            yaml_result, body_result = read_markdown(f.name)

            assert yaml_result == yaml_dict
            assert body_result == body_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_pathlib_path(self):
        """Test writing markdown file using pathlib.Path."""
        yaml_dict = {"title": "Path Test"}
        body_str = "Testing with pathlib.Path.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = Path(f.name)
            write_markdown(path, yaml_dict, body_str)

            # Read back and verify
            yaml_result, body_result = read_markdown(path)

            assert yaml_result == yaml_dict
            assert body_result == body_str

            # Clean up
            path.unlink()

    def test_write_markdown_empty_yaml(self):
        """Test writing markdown file with empty YAML front-matter."""
        yaml_dict = {}
        body_str = "Just the body content.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            write_markdown(f.name, yaml_dict, body_str)

            # Read back and verify
            yaml_result, body_result = read_markdown(f.name)

            assert yaml_result == yaml_dict
            assert body_result == body_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_none_values(self):
        """Test writing markdown file with None values in YAML."""
        yaml_dict = {"title": "Test Task", "parent": None, "worktree": None, "status": "open"}
        body_str = "Task with None values.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            write_markdown(f.name, yaml_dict, body_str)

            # Read back and verify
            yaml_result, body_result = read_markdown(f.name)

            assert yaml_result == yaml_dict
            assert body_result == body_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_datetime_serialization(self):
        """Test writing markdown file with datetime objects."""
        from datetime import datetime

        test_datetime = datetime(2025, 1, 1, 12, 30, 45, 123456)
        yaml_dict = {"title": "Test Task", "created": test_datetime, "updated": test_datetime}
        body_str = "Task with datetime values.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            write_markdown(f.name, yaml_dict, body_str)

            # Read back and verify datetime serialization
            yaml_result, body_result = read_markdown(f.name)

            assert yaml_result["title"] == "Test Task"
            assert yaml_result["created"] == test_datetime.isoformat()
            assert yaml_result["updated"] == test_datetime.isoformat()
            assert body_result == body_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_enum_serialization(self):
        """Test writing markdown file with enum objects."""
        from trellis_mcp.schema.status_enum import StatusEnum

        status_enum = StatusEnum.OPEN
        yaml_dict = {"title": "Test Task", "status": status_enum}
        body_str = "Task with enum value.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            write_markdown(f.name, yaml_dict, body_str)

            # Read back and verify enum serialization
            yaml_result, body_result = read_markdown(f.name)

            assert yaml_result["title"] == "Test Task"
            assert yaml_result["status"] == status_enum.value
            assert body_result == body_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_special_characters(self):
        """Test writing markdown file with special characters."""
        yaml_dict = {
            "title": "Test with special chars: éñüíóú",
            "description": "Unicode: 🔥 and symbols: @#$%^&*()",
        }
        body_str = "Special chars in body: éñüíóú 🔥 @#$%^&*()\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            write_markdown(f.name, yaml_dict, body_str)

            # Read back and verify
            yaml_result, body_result = read_markdown(f.name)

            assert yaml_result == yaml_dict
            assert body_result == body_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_creates_parent_directories(self):
        """Test that write_markdown creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested path that doesn't exist
            nested_path = Path(temp_dir) / "nested" / "deep" / "path" / "test.md"

            yaml_dict = {"title": "Test"}
            body_str = "Test body.\n"

            write_markdown(nested_path, yaml_dict, body_str)

            # Verify file was created and parent directories exist
            assert nested_path.exists()
            assert nested_path.parent.exists()

            # Read back and verify
            yaml_result, body_result = read_markdown(nested_path)
            assert yaml_result == yaml_dict
            assert body_result == body_str

    def test_write_markdown_complex_data_structures(self):
        """Test writing markdown file with complex data structures."""
        yaml_dict = {
            "title": "Complex Task",
            "prerequisites": ["T-001", "T-002", "T-003"],
            "metadata": {"tags": ["urgent", "frontend"], "assignee": "developer@example.com"},
            "priority": "high",
        }
        body_str = "Complex task with nested data.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            write_markdown(f.name, yaml_dict, body_str)

            # Read back and verify
            yaml_result, body_result = read_markdown(f.name)

            assert yaml_result == yaml_dict
            assert body_result == body_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_roundtrip_consistency(self):
        """Test that write_markdown -> read_markdown is consistent."""
        yaml_dict = {
            "title": "Roundtrip Test",
            "status": "open",
            "priority": "normal",
            "prerequisites": [],
            "parent": None,
            "worktree": None,
        }
        body_str = "Roundtrip test content.\n\n## Section\nMore content.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            # Write and read back
            write_markdown(f.name, yaml_dict, body_str)
            yaml_result, body_result = read_markdown(f.name)

            # Write again with the read result
            write_markdown(f.name, yaml_result, body_result)
            yaml_result2, body_result2 = read_markdown(f.name)

            # Should be identical
            assert yaml_result == yaml_result2
            assert body_result == body_result2

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_datetime_roundtrip_consistency(self):
        """Test that datetime objects maintain consistency through multiple write/read cycles."""
        from datetime import datetime

        test_datetime = datetime(2025, 1, 1, 12, 30, 45, 123456)
        yaml_dict = {
            "title": "DateTime Roundtrip Test",
            "created": test_datetime,
            "updated": test_datetime,
            "status": "open",
        }
        body_str = "Task with datetime values for roundtrip testing.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            # First write/read cycle
            write_markdown(f.name, yaml_dict, body_str)
            yaml_result1, body_result1 = read_markdown(f.name)

            # Second write/read cycle with the read result
            write_markdown(f.name, yaml_result1, body_result1)
            yaml_result2, body_result2 = read_markdown(f.name)

            # Third write/read cycle to ensure stability
            write_markdown(f.name, yaml_result2, body_result2)
            yaml_result3, body_result3 = read_markdown(f.name)

            # Verify consistency across all cycles
            assert yaml_result1 == yaml_result2
            assert yaml_result2 == yaml_result3
            assert body_result1 == body_result2
            assert body_result2 == body_result3

            # Verify datetime serialization remains consistent
            expected_datetime_str = test_datetime.isoformat()
            assert yaml_result1["created"] == expected_datetime_str
            assert yaml_result2["created"] == expected_datetime_str
            assert yaml_result3["created"] == expected_datetime_str

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_enum_roundtrip_consistency(self):
        """Test that enum objects maintain consistency through multiple write/read cycles."""
        from trellis_mcp.models.common import Priority
        from trellis_mcp.schema.status_enum import StatusEnum

        status_enum = StatusEnum.OPEN
        priority_enum = Priority.HIGH
        yaml_dict = {
            "title": "Enum Roundtrip Test",
            "status": status_enum,
            "priority": priority_enum,
            "prerequisites": [],
        }
        body_str = "Task with enum values for roundtrip testing.\n"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            # First write/read cycle
            write_markdown(f.name, yaml_dict, body_str)
            yaml_result1, body_result1 = read_markdown(f.name)

            # Second write/read cycle with the read result
            write_markdown(f.name, yaml_result1, body_result1)
            yaml_result2, body_result2 = read_markdown(f.name)

            # Third write/read cycle to ensure stability
            write_markdown(f.name, yaml_result2, body_result2)
            yaml_result3, body_result3 = read_markdown(f.name)

            # Verify consistency across all cycles
            assert yaml_result1 == yaml_result2
            assert yaml_result2 == yaml_result3
            assert body_result1 == body_result2
            assert body_result2 == body_result3

            # Verify enum serialization remains consistent
            assert yaml_result1["status"] == status_enum.value
            assert yaml_result2["status"] == status_enum.value
            assert yaml_result3["status"] == status_enum.value
            assert yaml_result1["priority"] == str(priority_enum)
            assert yaml_result2["priority"] == str(priority_enum)
            assert yaml_result3["priority"] == str(priority_enum)

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_comprehensive_roundtrip(self):
        """Test comprehensive roundtrip with mixed data types including datetime,
        enums, and complex structures."""
        from datetime import datetime

        from trellis_mcp.models.common import Priority
        from trellis_mcp.schema.status_enum import StatusEnum

        test_datetime = datetime(2025, 1, 15, 9, 45, 30, 987654)
        yaml_dict = {
            "title": "Comprehensive Roundtrip Test",
            "status": StatusEnum.IN_PROGRESS,
            "priority": Priority.NORMAL,
            "created": test_datetime,
            "updated": test_datetime,
            "prerequisites": ["T-001", "T-002"],
            "metadata": {
                "tags": ["backend", "database"],
                "assignee": "developer@example.com",
                "complexity": 3,
            },
            "parent": "F-123",
            "worktree": None,
        }
        body_str = (
            "# Comprehensive Test\n\n"
            "This is a comprehensive test with:\n"
            "- Mixed data types\n"
            "- Complex structures\n"
            "- **Bold text**\n"
            "- Unicode: 🚀\n"
        )

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            # First write/read cycle
            write_markdown(f.name, yaml_dict, body_str)
            yaml_result1, body_result1 = read_markdown(f.name)

            # Second write/read cycle with the read result
            write_markdown(f.name, yaml_result1, body_result1)
            yaml_result2, body_result2 = read_markdown(f.name)

            # Third write/read cycle to ensure stability
            write_markdown(f.name, yaml_result2, body_result2)
            yaml_result3, body_result3 = read_markdown(f.name)

            # Verify consistency across all cycles
            assert yaml_result1 == yaml_result2
            assert yaml_result2 == yaml_result3
            assert body_result1 == body_result2
            assert body_result2 == body_result3

            # Verify specific serialization formats remain consistent
            expected_datetime_str = test_datetime.isoformat()
            expected_status_str = StatusEnum.IN_PROGRESS.value
            expected_priority_str = str(Priority.NORMAL)

            for result in [yaml_result1, yaml_result2, yaml_result3]:
                assert result["created"] == expected_datetime_str
                assert result["updated"] == expected_datetime_str
                assert result["status"] == expected_status_str
                assert result["priority"] == expected_priority_str
                assert result["prerequisites"] == ["T-001", "T-002"]
                assert result["metadata"]["tags"] == ["backend", "database"]
                assert result["metadata"]["complexity"] == 3
                assert result["parent"] == "F-123"
                assert result["worktree"] is None

            # Clean up
            Path(f.name).unlink()

    def test_write_markdown_edge_cases_roundtrip(self):
        """Test roundtrip consistency with edge cases and special characters."""
        yaml_dict = {
            "title": "Edge Cases Test",
            "description": "Test with special chars: àáâãäåæçèé ñü 中文 🎯",
            "status": "open",
            "prerequisites": [],
            "metadata": {
                "empty_string": "",
                "multiline": "Line 1\nLine 2\nLine 3",
                "quotes": "Single \"quotes\" and 'apostrophes'",
                "numbers": [1, 2, 3, 0, -1],
                "boolean": True,
                "null_value": None,
            },
            "parent": None,
            "worktree": None,
        }
        body_str = """# Edge Cases Test

This body contains:
- Special characters: àáâãäåæçèé ñü 中文 🎯
- Code blocks:
```python
def hello():
    print("Hello, 世界!")
```
- YAML-like content that should not be parsed:
---
fake: yaml
---

And more content...
"""

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            # First write/read cycle
            write_markdown(f.name, yaml_dict, body_str)
            yaml_result1, body_result1 = read_markdown(f.name)

            # Second write/read cycle with the read result
            write_markdown(f.name, yaml_result1, body_result1)
            yaml_result2, body_result2 = read_markdown(f.name)

            # Verify consistency
            assert yaml_result1 == yaml_result2
            assert body_result1 == body_result2

            # Verify special characters are preserved
            assert yaml_result1["description"] == "Test with special chars: àáâãäåæçèé ñü 中文 🎯"
            assert yaml_result1["metadata"]["multiline"] == "Line 1\nLine 2\nLine 3"
            assert yaml_result1["metadata"]["quotes"] == "Single \"quotes\" and 'apostrophes'"
            assert yaml_result1["metadata"]["boolean"] is True
            assert yaml_result1["metadata"]["null_value"] is None

            # Verify body content with special characters is preserved
            assert "àáâãäåæçèé ñü 中文 🎯" in body_result1
            assert "Hello, 世界!" in body_result1
            assert "```python" in body_result1

            # Clean up
            Path(f.name).unlink()
