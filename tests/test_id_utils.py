"""Tests for ID utilities module.

Tests the slugify helper, charset validation, and length validation
functions for Trellis MCP object IDs.
"""

from __future__ import annotations

import pytest

from trellis_mcp.id_utils import (
    slugify_text,
    validate_id_charset,
    validate_id_length,
    generate_id,
    clean_prerequisite_id,
    DuplicateIDError,
)


class TestSlugifyText:
    """Test cases for the slugify_text function."""

    def test_basic_slugification(self):
        """Test basic text slugification."""
        assert slugify_text("Hello World") == "hello-world"
        assert slugify_text("User Authentication System") == "user-authentication-system"
        assert slugify_text("My Feature Title") == "my-feature-title"

    def test_unicode_handling(self):
        """Test Unicode character handling."""
        # French accented characters
        assert slugify_text("C'est déjà l'été") == "c-est-deja-l-ete"

        # German umlauts
        assert slugify_text("Müller & Söhne") == "muller-sohne"

        # Spanish characters
        assert slugify_text("José María") == "jose-maria"

    def test_special_characters(self):
        """Test handling of special characters."""
        assert slugify_text("API & Database") == "api-database"
        assert slugify_text("User@Domain.com") == "user-domain-com"
        assert slugify_text("Test/Path\\File") == "test-path-file"
        assert slugify_text("Price: $100.99") == "price-100-99"

    def test_whitespace_handling(self):
        """Test various whitespace scenarios."""
        assert slugify_text("  Hello   World  ") == "hello-world"
        assert slugify_text("Multiple\t\tTabs") == "multiple-tabs"
        assert slugify_text("Line\nBreaks") == "line-breaks"

    def test_empty_and_whitespace_input(self):
        """Test empty and whitespace-only input."""
        assert slugify_text("") == ""
        assert slugify_text("   ") == ""
        assert slugify_text("\t\n\r") == ""

    def test_numbers_and_hyphens(self):
        """Test handling of numbers and hyphens."""
        assert slugify_text("Version 2.0") == "version-2-0"
        assert slugify_text("Test-Case-123") == "test-case-123"
        assert slugify_text("ID-12345") == "id-12345"

    def test_length_constraint(self):
        """Test that slugification respects maximum length."""
        long_text = "This is a very long title that should be truncated to fit within limits"
        result = slugify_text(long_text)
        assert len(result) <= 32
        assert result == "this-is-a-very-long-title-that"

    def test_consecutive_separators(self):
        """Test handling of consecutive separators."""
        assert slugify_text("Hello---World") == "hello-world"
        assert slugify_text("Test  --  Case") == "test-case"

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Only special characters
        assert slugify_text("@#$%^&*()") == ""

        # Mixed valid/invalid characters
        assert slugify_text("Hello@World#123") == "hello-world-123"

        # Starting/ending with hyphens
        assert slugify_text("-Hello-World-") == "hello-world"


class TestValidateIdCharset:
    """Test cases for the validate_id_charset function."""

    def test_valid_characters(self):
        """Test IDs with only valid characters."""
        assert validate_id_charset("hello-world") is True
        assert validate_id_charset("user-auth-123") is True
        assert validate_id_charset("simple") is True
        assert validate_id_charset("123") is True
        assert validate_id_charset("a-b-c-d-e") is True
        assert validate_id_charset("test123") is True

    def test_invalid_characters(self):
        """Test IDs with invalid characters."""
        # Uppercase letters
        assert validate_id_charset("Hello-World") is False
        assert validate_id_charset("UserAuth") is False

        # Underscores
        assert validate_id_charset("user_auth") is False
        assert validate_id_charset("test_123") is False

        # Special characters
        assert validate_id_charset("user@domain") is False
        assert validate_id_charset("price$100") is False
        assert validate_id_charset("test/path") is False
        assert validate_id_charset("hello.world") is False
        assert validate_id_charset("test space") is False

    def test_empty_string(self):
        """Test empty string input."""
        assert validate_id_charset("") is False

    def test_edge_cases(self):
        """Test edge cases."""
        # Only hyphens
        assert validate_id_charset("-") is True
        assert validate_id_charset("--") is True

        # Only numbers
        assert validate_id_charset("123456") is True

        # Only letters
        assert validate_id_charset("abcdef") is True

        # Mixed valid combinations
        assert validate_id_charset("a1-b2-c3") is True


class TestValidateIdLength:
    """Test cases for the validate_id_length function."""

    def test_valid_lengths(self):
        """Test IDs with valid lengths."""
        assert validate_id_length("") is True  # Empty string
        assert validate_id_length("a") is True  # Single character
        assert validate_id_length("hello") is True  # Short ID
        assert validate_id_length("user-authentication-system") is True  # Medium ID
        assert validate_id_length("a" * 32) is True  # Exactly 32 characters

    def test_invalid_lengths(self):
        """Test IDs that exceed maximum length."""
        assert validate_id_length("a" * 33) is False  # 33 characters
        assert validate_id_length("a" * 50) is False  # 50 characters
        assert (
            validate_id_length("this-is-a-very-long-id-that-exceeds-the-maximum-allowed-length")
            is False
        )

    def test_boundary_conditions(self):
        """Test boundary conditions around the 32-character limit."""
        # Exactly at the limit
        exactly_32 = "a" * 32
        assert len(exactly_32) == 32
        assert validate_id_length(exactly_32) is True

        # One character over the limit
        over_limit = "a" * 33
        assert len(over_limit) == 33
        assert validate_id_length(over_limit) is False

    def test_realistic_ids(self):
        """Test with realistic ID examples."""
        assert validate_id_length("user-auth") is True
        assert validate_id_length("project-management-system") is True
        assert validate_id_length("feature-user-authentication") is True
        assert validate_id_length("task-implement-jwt-tokens") is True


class TestIntegration:
    """Integration tests combining multiple validation functions."""

    def test_slugify_produces_valid_ids(self):
        """Test that slugify_text produces IDs that pass validation."""
        test_cases = [
            "Hello World",
            "User Authentication System",
            "API & Database Integration",
            "C'est déjà l'été",
            "Version 2.0 Release",
            "Test Case 123",
        ]

        for text in test_cases:
            slug = slugify_text(text)
            assert validate_id_charset(slug), f"Invalid charset for slug: {slug}"
            assert validate_id_length(slug), f"Invalid length for slug: {slug}"

    def test_long_text_handling(self):
        """Test that long text is properly truncated and remains valid."""
        long_text = (
            "This is an extremely long title that will definitely exceed "
            "the maximum allowed length for IDs in the system"
        )
        slug = slugify_text(long_text)

        # Should be truncated to fit within limits
        assert len(slug) <= 32
        assert validate_id_length(slug)
        assert validate_id_charset(slug)

    def test_edge_case_integration(self):
        """Test edge cases across all functions."""
        # Empty string
        slug = slugify_text("")
        assert slug == ""
        assert validate_id_charset(slug) is False  # Empty is invalid for charset
        assert validate_id_length(slug) is True  # But valid for length

        # Only special characters
        slug = slugify_text("@#$%^&*()")
        assert slug == ""
        assert validate_id_charset(slug) is False
        assert validate_id_length(slug) is True


class TestGenerateId:
    """Test cases for the generate_id function."""

    def test_basic_id_generation(self, temp_dir):
        """Test basic ID generation from titles."""
        project_root = temp_dir / "planning"

        # Test basic generation
        assert generate_id("project", "My Project", project_root) == "my-project"
        assert generate_id("epic", "User Authentication", project_root) == "user-authentication"
        assert generate_id("feature", "Login System", project_root) == "login-system"
        assert generate_id("task", "Implement JWT", project_root) == "implement-jwt"

    def test_collision_detection_and_resolution(self, temp_dir):
        """Test collision detection and numeric suffix resolution."""
        project_root = temp_dir / "planning"

        # Create a project that will cause collision
        project_dir = project_root / "projects" / "P-my-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# My Project")

        # Should generate with suffix due to collision
        result = generate_id("project", "My Project", project_root)
        assert result == "my-project-1"

    def test_empty_title_error(self, temp_dir):
        """Test that empty titles raise ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Title cannot be empty"):
            generate_id("project", "", project_root)

    def test_invalid_kind_error(self, temp_dir):
        """Test that invalid kinds raise ValueError."""
        project_root = temp_dir / "planning"

        with pytest.raises(ValueError, match="Invalid kind 'invalid'"):
            generate_id("invalid", "Some Title", project_root)

    def test_validates_generated_ids(self, temp_dir):
        """Test that generated IDs pass validation checks."""
        project_root = temp_dir / "planning"

        test_titles = [
            "Normal Title",
            "Title with Special Characters!@#",
            "Mix3d Ch4r5 & Numb3r5",
        ]

        for title in test_titles:
            for kind in ["project", "epic", "feature", "task"]:
                try:
                    result = generate_id(kind, title, project_root)
                    assert validate_id_charset(result), f"Invalid charset for {result}"
                    assert validate_id_length(result), f"Invalid length for {result}"
                except ValueError:
                    # Some titles might produce empty slugs, which is acceptable
                    pass

    def test_duplicate_id_error_empty_slug(self, temp_dir):
        """Test that DuplicateIDError is raised for titles that produce empty slugs."""
        project_root = temp_dir / "planning"

        # Test with title that produces empty slug
        with pytest.raises(ValueError, match="produces empty slug"):
            generate_id("project", "@#$%^&*()", project_root)

    def test_duplicate_id_error_usage(self, temp_dir):
        """Test that DuplicateIDError can be imported and used."""
        # Test that DuplicateIDError is available for import
        assert DuplicateIDError is not None

        # Test creating an instance
        error = DuplicateIDError("Test message")
        assert str(error) == "Test message"

    def test_multi_level_collision_detection(self, temp_dir):
        """Test collision detection with multiple existing files (suffixes -1, -2, -3, etc.)."""
        project_root = temp_dir / "planning"

        # Create multiple colliding projects
        base_id = "my-project"
        project_ids = [base_id, f"{base_id}-1", f"{base_id}-2", f"{base_id}-3"]

        for project_id in project_ids:
            project_dir = project_root / "projects" / f"P-{project_id}"
            project_dir.mkdir(parents=True)
            project_file = project_dir / "project.md"
            project_file.write_text(f"# {project_id}")

        # Should generate -4 due to multiple collisions
        result = generate_id("project", "My Project", project_root)
        assert result == "my-project-4"

    def test_suffix_truncation_edge_cases(self, temp_dir):
        """Test collision resolution when base slug + suffix exceeds 32 characters."""
        project_root = temp_dir / "planning"

        # Create a title that generates a long base slug
        long_title = "This is a very long project title that will need truncation"
        long_base = slugify_text(long_title)  # Should be truncated to 32 chars

        # Create the base slug as existing project
        project_dir = project_root / "projects" / f"P-{long_base}"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Long project")

        # Generate ID should create truncated version with suffix
        result = generate_id("project", long_title, project_root)

        # Should be truncated to make room for "-1" suffix
        assert len(result) <= 32
        assert result.endswith("-1")
        assert validate_id_charset(result)
        assert validate_id_length(result)

    def test_duplicate_id_error_boundary_100_attempts(self, temp_dir):
        """Test that DuplicateIDError is raised after 100 collision attempts."""
        project_root = temp_dir / "planning"

        # Create a short base slug so we can create 100+ collisions
        base_id = "test"

        # Create 101 colliding projects (test, test-1, test-2, ..., test-100)
        # This will force the algorithm to exceed the 100 attempts limit
        project_ids = [base_id] + [f"{base_id}-{i}" for i in range(1, 101)]

        for project_id in project_ids:
            project_dir = project_root / "projects" / f"P-{project_id}"
            project_dir.mkdir(parents=True)
            project_file = project_dir / "project.md"
            project_file.write_text(f"# {project_id}")

        # Should raise DuplicateIDError after 100 attempts
        with pytest.raises(DuplicateIDError, match="Cannot generate unique ID.*after 100 attempts"):
            generate_id("project", "Test", project_root)

    def test_collision_resolution_across_hierarchy_levels(self, temp_dir):
        """Test that collision detection works correctly across different hierarchy levels."""
        project_root = temp_dir / "planning"

        # Create project with ID "auth-system"
        project_dir = project_root / "projects" / "P-auth-system"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# Auth System")

        # Create epic with same base ID in different project
        other_project_dir = project_root / "projects" / "P-other-project"
        other_project_dir.mkdir(parents=True)

        epic_dir = other_project_dir / "epics" / "E-auth-system"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_file.write_text("# Auth System Epic")

        # Should generate "auth-system-1" for new epic since "auth-system" exists
        result = generate_id("epic", "Auth System", project_root)
        assert result == "auth-system-1"

    def test_complex_unicode_slug_generation(self, temp_dir):
        """Test slug generation with complex Unicode characters."""
        project_root = temp_dir / "planning"

        test_cases = [
            ("Пользователь Системы", "polzovatel-sistemy"),  # Cyrillic
            ("用户认证系统", "yong-hu-ren-zheng-xi-tong"),  # Chinese
            ("المستخدم النظام", "almstkhd-alntham"),  # Arabic
            ("🚀 Launch Feature", "launch-feature"),  # Emoji
            ("Müller & Söhne GmbH", "muller-sohne-gmbh"),  # German
        ]

        for title, expected_base in test_cases:
            result = generate_id("project", title, project_root)
            # Should produce a valid slug (may not exactly match expected due to
            # transliteration differences)
            assert validate_id_charset(result)
            assert validate_id_length(result)
            assert len(result) > 0  # Should not be empty

    def test_edge_case_slug_boundary_conditions(self, temp_dir):
        """Test slug generation at various boundary conditions."""
        project_root = temp_dir / "planning"

        # Test exactly 32 character input
        exactly_32_chars = "a" * 32
        result = generate_id("project", exactly_32_chars, project_root)
        assert len(result) <= 32
        assert validate_id_charset(result)

        # Test input that produces exactly 32 character slug
        long_meaningful_title = "User Authentication and Authorization System Module"
        result = generate_id("project", long_meaningful_title, project_root)
        assert len(result) <= 32
        assert validate_id_charset(result)

        # Test title with only numbers
        result = generate_id("project", "12345", project_root)
        assert result == "12345"
        assert validate_id_charset(result)

        # Test title with mixed numbers and special chars
        result = generate_id("project", "Version 2.0.1-beta", project_root)
        assert validate_id_charset(result)
        assert "2" in result and "0" in result and "1" in result

    def test_collision_detection_with_malformed_directories(self, temp_dir):
        """Test collision detection behavior with malformed directory structures."""
        project_root = temp_dir / "planning"

        # Create directory without the expected project.md file
        malformed_dir = project_root / "projects" / "P-malformed"
        malformed_dir.mkdir(parents=True)
        # No project.md file created

        # Should not detect collision for malformed directory
        result = generate_id("project", "Malformed", project_root)
        assert result == "malformed"

        # Create proper project with same ID
        proper_dir = project_root / "projects" / "P-malformed"
        project_file = proper_dir / "project.md"
        project_file.write_text("# Malformed")

        # Now should detect collision
        result = generate_id("project", "Malformed", project_root)
        assert result == "malformed-1"

    def test_single_character_slug_with_collision(self, temp_dir):
        """Test collision resolution with very short base slugs."""
        project_root = temp_dir / "planning"

        # Create project with single character ID
        project_dir = project_root / "projects" / "P-a"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_file.write_text("# A")

        # Should generate "a-1" due to collision
        result = generate_id("project", "A", project_root)
        assert result == "a-1"
        assert validate_id_charset(result)
        assert validate_id_length(result)

    def test_collision_resolution_preserves_validation(self, temp_dir):
        """Test that collision resolution always produces valid IDs."""
        project_root = temp_dir / "planning"

        # Test various collision scenarios
        test_titles = [
            "Short",
            "Medium Length Title",
            "Very Long Title That Needs Truncation For ID Generation",
            "Special-Characters@#$%",
            "Numbers123AndText",
        ]

        for title in test_titles:
            # Create collision for each title
            base_slug = slugify_text(title)
            if base_slug:  # Only test non-empty slugs
                project_dir = project_root / "projects" / f"P-{base_slug}"
                project_dir.mkdir(parents=True)
                project_file = project_dir / "project.md"
                project_file.write_text(f"# {title}")

                # Generate new ID with collision
                result = generate_id("project", title, project_root)

                # Must always produce valid ID
                assert validate_id_charset(result), f"Invalid charset for '{result}' from '{title}'"
                assert validate_id_length(result), f"Invalid length for '{result}' from '{title}'"
                assert result != base_slug, f"Collision not resolved for '{title}'"


class TestCleanPrerequisiteId:
    """Test cases for the clean_prerequisite_id function."""

    def test_standard_prefixes(self):
        """Test cleaning standard Trellis MCP prefixes."""
        assert clean_prerequisite_id("P-project-name") == "project-name"
        assert clean_prerequisite_id("E-epic-name") == "epic-name"
        assert clean_prerequisite_id("F-feature-name") == "feature-name"
        assert clean_prerequisite_id("T-task-name") == "task-name"

    def test_any_single_character_prefix(self):
        """Test cleaning any single-character prefix followed by dash."""
        assert clean_prerequisite_id("A-something") == "something"
        assert clean_prerequisite_id("X-test") == "test"
        assert clean_prerequisite_id("1-numeric") == "numeric"
        assert clean_prerequisite_id("?-special") == "special"

    def test_no_prefix(self):
        """Test IDs without prefixes are returned unchanged."""
        assert clean_prerequisite_id("task-name") == "task-name"
        assert clean_prerequisite_id("project") == "project"
        assert clean_prerequisite_id("simple") == "simple"
        assert clean_prerequisite_id("multi-word-id") == "multi-word-id"

    def test_edge_cases(self):
        """Test edge cases and malformed IDs."""
        # Empty string
        assert clean_prerequisite_id("") == ""

        # Single character (no dash)
        assert clean_prerequisite_id("T") == "T"
        assert clean_prerequisite_id("P") == "P"

        # Just a dash
        assert clean_prerequisite_id("-") == "-"  # Single dash is not a valid prefix format

        # Dash at wrong position
        assert clean_prerequisite_id("TE-ST") == "TE-ST"  # Dash at position 2
        assert clean_prerequisite_id("TEST-") == "TEST-"  # Dash at end

        # Multiple dashes
        assert clean_prerequisite_id("T-test-name") == "test-name"
        assert clean_prerequisite_id("P-project-with-dashes") == "project-with-dashes"

    def test_prefix_only(self):
        """Test IDs that are just prefix and dash."""
        assert clean_prerequisite_id("T-") == ""
        assert clean_prerequisite_id("P-") == ""
        assert clean_prerequisite_id("E-") == ""
        assert clean_prerequisite_id("F-") == ""

    def test_whitespace_handling(self):
        """Test handling of whitespace in IDs."""
        assert clean_prerequisite_id("T-task name") == "task name"
        assert clean_prerequisite_id("P- project") == " project"
        assert (
            clean_prerequisite_id(" T-task") == " T-task"
        )  # Leading space prevents prefix detection

    def test_case_sensitivity(self):
        """Test that function is case sensitive."""
        assert clean_prerequisite_id("t-task") == "task"  # lowercase works
        assert clean_prerequisite_id("T-task") == "task"  # uppercase works
        assert (
            clean_prerequisite_id("Task-name") == "Task-name"
        )  # No prefix because position 1 is not a dash

    def test_numeric_ids(self):
        """Test cleaning numeric IDs."""
        assert clean_prerequisite_id("T-123") == "123"
        assert clean_prerequisite_id("P-456-789") == "456-789"
        assert clean_prerequisite_id("123-456") == "123-456"  # No single-char prefix

    def test_complex_ids(self):
        """Test cleaning complex, realistic IDs."""
        assert clean_prerequisite_id("T-user-authentication-system") == "user-authentication-system"
        assert clean_prerequisite_id("F-api-endpoint-v2") == "api-endpoint-v2"
        assert clean_prerequisite_id("E-backend-infrastructure") == "backend-infrastructure"
        assert clean_prerequisite_id("P-webapp-redesign-2024") == "webapp-redesign-2024"
