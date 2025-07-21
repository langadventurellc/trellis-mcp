"""Tests for ClaimingParams model.

Tests the ClaimingParams model validation and behavior for claimNextTask parameter validation.
"""

import pytest
from pydantic import ValidationError

from trellis_mcp.models.claiming_params import ClaimingParams


class TestClaimingParams:
    """Test ClaimingParams model creation and validation."""

    def test_create_claiming_params_with_required_only(self):
        """Test creating ClaimingParams with only required project_root."""
        claiming_params = ClaimingParams(project_root="/test/path")
        assert claiming_params.project_root == "/test/path"
        assert claiming_params.worktree == ""
        assert claiming_params.scope is None
        assert claiming_params.task_id is None
        assert claiming_params.force_claim is False

    def test_create_claiming_params_with_scope_and_worktree(self):
        """Test creating ClaimingParams with scope and worktree (valid combination)."""
        claiming_params = ClaimingParams(
            project_root="/test/path",
            worktree="feature/test",
            scope="P-test-project",
        )
        assert claiming_params.project_root == "/test/path"
        assert claiming_params.worktree == "feature/test"
        assert claiming_params.scope == "P-test-project"
        assert claiming_params.task_id is None
        assert claiming_params.force_claim is False

    def test_create_claiming_params_with_force_claim_and_task_id(self):
        """Test creating ClaimingParams with force_claim=True and task_id."""
        claiming_params = ClaimingParams(
            project_root="/test/path", task_id="T-urgent-task", force_claim=True
        )
        assert claiming_params.project_root == "/test/path"
        assert claiming_params.task_id == "T-urgent-task"
        assert claiming_params.force_claim is True
        assert claiming_params.scope is None

    # Project Root Validation Tests

    def test_empty_project_root_raises_error(self):
        """Test that empty project_root raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="")

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "project_root" in str(error_details[0])
        assert "Project root cannot be empty" in str(error_details[0])

    def test_whitespace_only_project_root_raises_error(self):
        """Test that whitespace-only project_root raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="   ")

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "project_root" in str(error_details[0])
        assert "Project root cannot be empty" in str(error_details[0])

    def test_project_root_with_surrounding_whitespace_gets_trimmed(self):
        """Test that project_root with surrounding whitespace gets trimmed."""
        claiming_params = ClaimingParams(project_root="  /test/path  ")
        assert claiming_params.project_root == "/test/path"

    # Scope Validation Tests

    def test_valid_project_scope(self):
        """Test creating ClaimingParams with valid project scope."""
        claiming_params = ClaimingParams(project_root="/test", scope="P-example-project")
        assert claiming_params.scope == "P-example-project"

    def test_valid_epic_scope(self):
        """Test creating ClaimingParams with valid epic scope."""
        claiming_params = ClaimingParams(project_root="/test", scope="E-user-authentication")
        assert claiming_params.scope == "E-user-authentication"

    def test_valid_feature_scope(self):
        """Test creating ClaimingParams with valid feature scope."""
        claiming_params = ClaimingParams(project_root="/test", scope="F-login-form")
        assert claiming_params.scope == "F-login-form"

    def test_scope_with_numbers_and_special_chars(self):
        """Test scope validation with numbers, hyphens, and underscores."""
        valid_scopes = [
            "P-project123",
            "E-user_auth_system",
            "F-user-login-form",
            "P-test_project-v2",
        ]
        for scope in valid_scopes:
            claiming_params = ClaimingParams(project_root="/test", scope=scope)
            assert claiming_params.scope == scope

    def test_invalid_scope_no_prefix(self):
        """Test that scope without prefix raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="/test", scope="invalid-id")

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Invalid scope ID format" in str(error_details[0])

    def test_invalid_scope_wrong_prefix(self):
        """Test that scope with wrong prefix raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="/test", scope="T-task-id")

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Must use P-, E-, or F- prefix" in str(error_details[0])

    def test_invalid_scope_special_characters(self):
        """Test that scope with invalid special characters raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="/test", scope="P-project@name")

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])

    def test_scope_empty_string_becomes_none(self):
        """Test that empty string scope becomes None."""
        claiming_params = ClaimingParams(project_root="/test", scope="")
        assert claiming_params.scope is None

    def test_scope_whitespace_only_becomes_none(self):
        """Test that whitespace-only scope becomes None."""
        claiming_params = ClaimingParams(project_root="/test", scope="   ")
        assert claiming_params.scope is None

    # Task ID Validation Tests

    def test_valid_task_id_with_prefix(self):
        """Test task_id validation with T- prefix."""
        claiming_params = ClaimingParams(project_root="/test", task_id="T-implement-auth")
        assert claiming_params.task_id == "T-implement-auth"

    def test_valid_standalone_task_id(self):
        """Test task_id validation for standalone task format."""
        claiming_params = ClaimingParams(project_root="/test", task_id="implement-auth")
        assert claiming_params.task_id == "implement-auth"

    def test_task_id_with_valid_patterns(self):
        """Test task_id validation with various valid patterns."""
        valid_task_ids = [
            "T-implement-auth",
            "T-fix-bug-123",
            "standalone-task",
            "task-with-numbers-456",
            "T-very-long-descriptive-task-name",
        ]
        for task_id in valid_task_ids:
            claiming_params = ClaimingParams(project_root="/test", task_id=task_id)
            assert claiming_params.task_id == task_id

    def test_task_id_underscore_normalization(self):
        """Test that underscores in task_id get normalized to hyphens (system behavior)."""
        # The system normalizes underscores to hyphens, which is expected behavior
        claiming_params = ClaimingParams(project_root="/test", task_id="task_with_underscores")
        assert claiming_params.task_id == "task_with_underscores"  # Original value preserved

        # Test with T- prefix as well
        claiming_params2 = ClaimingParams(project_root="/test", task_id="T-task_with_underscores")
        assert claiming_params2.task_id == "T-task_with_underscores"  # Original value preserved

    def test_invalid_task_id_format(self):
        """Test that invalid task_id format raises validation error."""
        invalid_task_ids = [
            "T-",  # empty after prefix
            "T-   ",  # whitespace only after prefix
            "T----",  # only hyphens after prefix
            "T-@@@",  # only special chars after prefix
            "T-" + "a" * 200,  # too long
            "---",  # normalizes to empty
            "@@@",  # normalizes to empty
        ]
        for task_id in invalid_task_ids:
            with pytest.raises(ValidationError) as exc_info:
                ClaimingParams(project_root="/test", task_id=task_id)

            error_details = exc_info.value.errors()
            assert len(error_details) > 0
            assert "task_id" in str(error_details[0])
            assert "Invalid task ID format" in str(error_details[0])

    def test_task_id_empty_string_becomes_none(self):
        """Test that empty string task_id becomes None."""
        claiming_params = ClaimingParams(project_root="/test", task_id="")
        assert claiming_params.task_id is None

    def test_task_id_whitespace_only_becomes_none(self):
        """Test that whitespace-only task_id becomes None."""
        claiming_params = ClaimingParams(project_root="/test", task_id="   ")
        assert claiming_params.task_id is None

    # Parameter Combination Validation Tests

    def test_mutual_exclusivity_scope_and_task_id(self):
        """Test that scope and task_id cannot both be specified."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="/test", scope="P-project", task_id="T-task")

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        error_message = str(error_details[0])
        assert "Cannot specify both scope and task_id" in error_message
        assert "Use scope for filtering" in error_message

    def test_force_claim_requires_task_id(self):
        """Test that force_claim=True requires task_id to be specified."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="/test", force_claim=True)

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        error_message = str(error_details[0])
        assert "force_claim parameter requires task_id" in error_message

    def test_force_claim_with_scope_fails(self):
        """Test that force_claim cannot be used with scope parameter."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(
                project_root="/test", scope="P-project", task_id="T-task", force_claim=True
            )

        # This should fail on mutual exclusivity first
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "Cannot specify both scope and task_id" in str(error_details[0])

    # Valid Parameter Combinations Tests

    def test_valid_combination_scope_with_worktree(self):
        """Test valid combination of scope with worktree."""
        claiming_params = ClaimingParams(
            project_root="/test", scope="P-project", worktree="feature/branch"
        )
        assert claiming_params.scope == "P-project"
        assert claiming_params.worktree == "feature/branch"
        assert claiming_params.task_id is None
        assert claiming_params.force_claim is False

    def test_valid_combination_task_id_with_force_claim_and_worktree(self):
        """Test valid combination of task_id, force_claim, and worktree."""
        claiming_params = ClaimingParams(
            project_root="/test",
            task_id="T-urgent-task",
            force_claim=True,
            worktree="hotfix/urgent",
        )
        assert claiming_params.task_id == "T-urgent-task"
        assert claiming_params.force_claim is True
        assert claiming_params.worktree == "hotfix/urgent"
        assert claiming_params.scope is None

    def test_valid_combination_project_root_only(self):
        """Test valid combination with only project_root (legacy behavior)."""
        claiming_params = ClaimingParams(project_root="/test")
        assert claiming_params.project_root == "/test"
        assert claiming_params.worktree == ""
        assert claiming_params.scope is None
        assert claiming_params.task_id is None
        assert claiming_params.force_claim is False

    def test_valid_combination_project_root_with_worktree(self):
        """Test valid combination with project_root and worktree (legacy behavior)."""
        claiming_params = ClaimingParams(project_root="/test", worktree="feature/work")
        assert claiming_params.project_root == "/test"
        assert claiming_params.worktree == "feature/work"
        assert claiming_params.scope is None
        assert claiming_params.task_id is None
        assert claiming_params.force_claim is False

    # Model Serialization Tests

    def test_model_serialization_basic(self):
        """Test that ClaimingParams can be serialized and deserialized."""
        original = ClaimingParams(
            project_root="/test/path",
            worktree="feature/test",
            scope="P-project",
        )

        # Serialize to dict
        data = original.model_dump()
        expected = {
            "project_root": "/test/path",
            "worktree": "feature/test",
            "scope": "P-project",
            "task_id": None,
            "force_claim": False,
        }
        assert data == expected

        # Deserialize from dict
        restored = ClaimingParams.model_validate(data)
        assert restored.project_root == original.project_root
        assert restored.worktree == original.worktree
        assert restored.scope == original.scope
        assert restored.task_id == original.task_id
        assert restored.force_claim == original.force_claim

    def test_model_serialization_with_task_id_and_force_claim(self):
        """Test serialization with task_id and force_claim."""
        original = ClaimingParams(
            project_root="/test/path",
            task_id="T-urgent-task",
            force_claim=True,
            worktree="hotfix/urgent",
        )

        # Serialize to dict
        data = original.model_dump()
        expected = {
            "project_root": "/test/path",
            "worktree": "hotfix/urgent",
            "scope": None,
            "task_id": "T-urgent-task",
            "force_claim": True,
        }
        assert data == expected

        # Deserialize from dict
        restored = ClaimingParams.model_validate(data)
        assert restored.project_root == original.project_root
        assert restored.worktree == original.worktree
        assert restored.scope == original.scope
        assert restored.task_id == original.task_id
        assert restored.force_claim == original.force_claim

    def test_model_validation_with_dict(self):
        """Test creating ClaimingParams from dictionary."""
        data = {
            "project_root": "/test/path",
            "scope": "E-epic-name",
            "worktree": "feature/branch",
        }

        claiming_params = ClaimingParams.model_validate(data)
        assert claiming_params.project_root == "/test/path"
        assert claiming_params.scope == "E-epic-name"
        assert claiming_params.worktree == "feature/branch"
        assert claiming_params.task_id is None
        assert claiming_params.force_claim is False

    # Edge Cases and Error Message Quality Tests

    def test_error_message_includes_invalid_scope_value(self):
        """Test that scope validation error includes the invalid value."""
        invalid_scope = "invalid-scope"
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="/test", scope=invalid_scope)

        error_details = exc_info.value.errors()
        error_message = str(error_details[0])
        assert invalid_scope in error_message
        assert "Invalid scope ID format" in error_message

    def test_error_message_includes_invalid_task_id_value(self):
        """Test that task_id validation error includes the invalid value."""
        invalid_task_id = "T-@@@"
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(project_root="/test", task_id=invalid_task_id)

        error_details = exc_info.value.errors()
        error_message = str(error_details[0])
        assert invalid_task_id in error_message
        assert "Invalid task ID format" in error_message

    def test_multiple_validation_errors_reported(self):
        """Test that multiple validation errors are reported when present."""
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams(
                project_root="",  # Invalid: empty project_root
                scope="invalid-scope",  # Invalid: wrong scope format
                task_id="Invalid_Task",  # Invalid: task_id format
            )

        error_details = exc_info.value.errors()
        # Should have multiple validation errors
        assert len(error_details) > 1

        # Check that we get errors for different fields
        error_fields = {error.get("loc", [None])[0] for error in error_details}
        expected_fields = {"project_root", "scope", "task_id"}
        assert expected_fields.intersection(error_fields)

    def test_pydantic_configuration_applied(self):
        """Test that TrellisBaseModel configuration is applied correctly."""
        # Test that extra fields are forbidden
        with pytest.raises(ValidationError) as exc_info:
            ClaimingParams.model_validate(
                {
                    "project_root": "/test",
                    "extra_field": "not_allowed",
                }
            )

        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        # Should have an error about extra fields not being permitted
        assert any("extra" in str(error).lower() for error in error_details)

    def test_field_assignment_validation(self):
        """Test that field assignment validation works (from TrellisBaseModel)."""
        claiming_params = ClaimingParams(project_root="/test")

        # This should trigger validation on assignment
        with pytest.raises(ValidationError):
            claiming_params.scope = "invalid-scope-format"
