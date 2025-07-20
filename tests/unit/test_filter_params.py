"""Tests for FilterParams model.

Tests the FilterParams model validation and behavior for backlog filtering operations.
"""

import pytest
from pydantic import ValidationError

from trellis_mcp.models.common import Priority
from trellis_mcp.models.filter_params import FilterParams
from trellis_mcp.schema.status_enum import StatusEnum


class TestFilterParams:
    """Test FilterParams model creation and validation."""

    def test_create_empty_filter_params(self):
        """Test creating FilterParams with default empty lists."""
        filter_params = FilterParams()
        assert filter_params.status == []
        assert filter_params.priority == []

    def test_create_filter_params_with_status(self):
        """Test creating FilterParams with valid status values."""
        filter_params = FilterParams(status=[StatusEnum.OPEN, StatusEnum.IN_PROGRESS])
        assert filter_params.status == [StatusEnum.OPEN, StatusEnum.IN_PROGRESS]
        assert filter_params.priority == []

    def test_create_filter_params_with_priority(self):
        """Test creating FilterParams with valid priority values."""
        filter_params = FilterParams(priority=[Priority.HIGH, Priority.NORMAL])
        assert filter_params.priority == [Priority.HIGH, Priority.NORMAL]
        assert filter_params.status == []

    def test_create_filter_params_with_both(self):
        """Test creating FilterParams with both status and priority values."""
        filter_params = FilterParams(
            status=[StatusEnum.OPEN, StatusEnum.DONE], priority=[Priority.HIGH, Priority.LOW]
        )
        assert filter_params.status == [StatusEnum.OPEN, StatusEnum.DONE]
        assert filter_params.priority == [Priority.HIGH, Priority.LOW]

    def test_create_filter_params_with_string_status(self):
        """Test creating FilterParams with string status values."""
        filter_params = FilterParams(status=["open", "in-progress"])
        assert filter_params.status == [StatusEnum.OPEN, StatusEnum.IN_PROGRESS]

    def test_create_filter_params_with_string_priority(self):
        """Test creating FilterParams with string priority values."""
        filter_params = FilterParams(priority=["high", "normal"])
        assert filter_params.priority == [Priority.HIGH, Priority.NORMAL]

    def test_create_filter_params_with_none(self):
        """Test creating FilterParams with None values."""
        filter_params = FilterParams(status=None, priority=None)  # type: ignore
        assert filter_params.status == []
        assert filter_params.priority == []

    def test_invalid_status_value(self):
        """Test validation error with invalid status value."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(status=["invalid_status"])

        # Check that the error mentions status validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "status" in str(error_details[0])

    def test_invalid_priority_value(self):
        """Test validation error with invalid priority value."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(priority=["invalid_priority"])

        # Check that the error mentions priority validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "priority" in str(error_details[0])

    def test_mixed_valid_invalid_status(self):
        """Test validation error with mixed valid and invalid status values."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(status=[StatusEnum.OPEN, "invalid_status", StatusEnum.DONE])

        # Check that the error mentions status validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "status" in str(error_details[0])

    def test_mixed_valid_invalid_priority(self):
        """Test validation error with mixed valid and invalid priority values."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(priority=[Priority.HIGH, "invalid_priority", Priority.LOW])

        # Check that the error mentions priority validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "priority" in str(error_details[0])

    def test_all_valid_status_enum_values(self):
        """Test that all valid StatusEnum values are accepted."""
        all_statuses = [
            StatusEnum.OPEN,
            StatusEnum.IN_PROGRESS,
            StatusEnum.REVIEW,
            StatusEnum.DONE,
            StatusEnum.DRAFT,
        ]
        filter_params = FilterParams(status=all_statuses)
        assert filter_params.status == all_statuses

    def test_all_valid_priority_enum_values(self):
        """Test that all valid Priority values are accepted."""
        all_priorities = [Priority.HIGH, Priority.NORMAL, Priority.LOW]
        filter_params = FilterParams(priority=all_priorities)
        assert filter_params.priority == all_priorities

    def test_duplicate_status_values(self):
        """Test that duplicate status values are preserved."""
        filter_params = FilterParams(status=[StatusEnum.OPEN, StatusEnum.OPEN, StatusEnum.DONE])
        assert filter_params.status == [StatusEnum.OPEN, StatusEnum.OPEN, StatusEnum.DONE]

    def test_duplicate_priority_values(self):
        """Test that duplicate priority values are preserved."""
        filter_params = FilterParams(priority=[Priority.HIGH, Priority.HIGH, Priority.NORMAL])
        assert filter_params.priority == [Priority.HIGH, Priority.HIGH, Priority.NORMAL]

    def test_model_serialization(self):
        """Test that FilterParams can be serialized and deserialized."""
        original = FilterParams(
            status=[StatusEnum.OPEN, StatusEnum.IN_PROGRESS],
            priority=[Priority.HIGH, Priority.NORMAL],
        )

        # Serialize to dict
        data = original.model_dump()
        assert data == {
            "status": [StatusEnum.OPEN, StatusEnum.IN_PROGRESS],
            "priority": [Priority.HIGH, Priority.NORMAL],
            "scope": None,
        }

        # Deserialize from dict
        restored = FilterParams.model_validate(data)
        assert restored.status == original.status
        assert restored.priority == original.priority

    def test_model_validation_with_dict(self):
        """Test creating FilterParams from dictionary."""
        data = {"status": ["open", "done"], "priority": ["high", "low"]}

        filter_params = FilterParams.model_validate(data)
        assert filter_params.status == [StatusEnum.OPEN, StatusEnum.DONE]
        assert filter_params.priority == [Priority.HIGH, Priority.LOW]

    def test_create_filter_params_with_scope_none(self):
        """Test creating FilterParams with scope=None (default)."""
        filter_params = FilterParams()
        assert filter_params.scope is None

    def test_create_filter_params_with_valid_project_scope(self):
        """Test creating FilterParams with valid project scope ID."""
        filter_params = FilterParams(scope="P-example-project")
        assert filter_params.scope == "P-example-project"

    def test_create_filter_params_with_valid_epic_scope(self):
        """Test creating FilterParams with valid epic scope ID."""
        filter_params = FilterParams(scope="E-user-authentication")
        assert filter_params.scope == "E-user-authentication"

    def test_create_filter_params_with_valid_feature_scope(self):
        """Test creating FilterParams with valid feature scope ID."""
        filter_params = FilterParams(scope="F-login-form")
        assert filter_params.scope == "F-login-form"

    def test_create_filter_params_with_scope_containing_numbers(self):
        """Test creating FilterParams with scope ID containing numbers."""
        filter_params = FilterParams(scope="P-project123")
        assert filter_params.scope == "P-project123"

    def test_create_filter_params_with_scope_containing_underscores(self):
        """Test creating FilterParams with scope ID containing underscores."""
        filter_params = FilterParams(scope="E-user_auth_system")
        assert filter_params.scope == "E-user_auth_system"

    def test_create_filter_params_with_scope_containing_hyphens(self):
        """Test creating FilterParams with scope ID containing hyphens."""
        filter_params = FilterParams(scope="F-user-login-form")
        assert filter_params.scope == "F-user-login-form"

    def test_create_filter_params_with_all_fields_including_scope(self):
        """Test creating FilterParams with status, priority, and scope."""
        filter_params = FilterParams(
            status=[StatusEnum.OPEN], priority=[Priority.HIGH], scope="P-example-project"
        )
        assert filter_params.status == [StatusEnum.OPEN]
        assert filter_params.priority == [Priority.HIGH]
        assert filter_params.scope == "P-example-project"

    def test_invalid_scope_no_prefix(self):
        """Test validation error with scope ID without prefix."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(scope="invalid-id")

        # Check that the error mentions scope validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Invalid scope ID format" in str(error_details[0])

    def test_invalid_scope_wrong_prefix(self):
        """Test validation error with scope ID having wrong prefix."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(scope="T-task-id")

        # Check that the error mentions scope validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Invalid scope ID format" in str(error_details[0])

    def test_invalid_scope_no_suffix(self):
        """Test validation error with scope ID having only prefix."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(scope="P-")

        # Check that the error mentions scope validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Invalid scope ID format" in str(error_details[0])

    def test_invalid_scope_special_characters(self):
        """Test validation error with scope ID containing invalid special characters."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(scope="P-project@name")

        # Check that the error mentions scope validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Invalid scope ID format" in str(error_details[0])

    def test_invalid_scope_spaces(self):
        """Test validation error with scope ID containing spaces."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(scope="P-project name")

        # Check that the error mentions scope validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Invalid scope ID format" in str(error_details[0])

    def test_invalid_scope_lowercase_prefix(self):
        """Test validation error with scope ID having lowercase prefix."""
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(scope="p-project-name")

        # Check that the error mentions scope validation
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        assert "scope" in str(error_details[0])
        assert "Invalid scope ID format" in str(error_details[0])

    def test_scope_error_message_clarity(self):
        """Test that scope validation error messages are clear and include the invalid value."""
        invalid_scope = "invalid-scope-id"
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(scope=invalid_scope)

        # Check that the error message includes the invalid value
        error_details = exc_info.value.errors()
        assert len(error_details) > 0
        error_message = str(error_details[0])
        assert invalid_scope in error_message
        assert "Invalid scope ID format" in error_message

    def test_model_serialization_with_scope(self):
        """Test that FilterParams with scope can be serialized and deserialized."""
        original = FilterParams(
            status=[StatusEnum.OPEN, StatusEnum.IN_PROGRESS],
            priority=[Priority.HIGH, Priority.NORMAL],
            scope="P-example-project",
        )

        # Serialize to dict
        data = original.model_dump()
        assert data == {
            "status": [StatusEnum.OPEN, StatusEnum.IN_PROGRESS],
            "priority": [Priority.HIGH, Priority.NORMAL],
            "scope": "P-example-project",
        }

        # Deserialize from dict
        restored = FilterParams.model_validate(data)
        assert restored.status == original.status
        assert restored.priority == original.priority
        assert restored.scope == original.scope

    def test_model_validation_with_dict_including_scope(self):
        """Test creating FilterParams from dictionary including scope."""
        data = {"status": ["open", "done"], "priority": ["high", "low"], "scope": "E-user-auth"}

        filter_params = FilterParams.model_validate(data)
        assert filter_params.status == [StatusEnum.OPEN, StatusEnum.DONE]
        assert filter_params.priority == [Priority.HIGH, Priority.LOW]
        assert filter_params.scope == "E-user-auth"

    def test_backward_compatibility_without_scope(self):
        """Test that existing usage without scope parameter continues to work."""
        # This should work exactly as before without any scope field
        filter_params = FilterParams(status=[StatusEnum.OPEN], priority=[Priority.HIGH])
        assert filter_params.status == [StatusEnum.OPEN]
        assert filter_params.priority == [Priority.HIGH]
        assert filter_params.scope is None

    def test_valid_scope_edge_cases(self):
        """Test valid scope formats that are at the boundaries of the regex pattern."""
        valid_scopes = [
            "P-a",  # Minimum length after prefix
            "E-A",  # Single uppercase letter
            "F-1",  # Single number
            "P-a1b2c3",  # Mixed alphanumeric
            "E-test_project-123",  # Mixed with underscores and hyphens
            "F-UPPERCASE_PROJECT",  # All uppercase
        ]

        for scope in valid_scopes:
            filter_params = FilterParams(scope=scope)
            assert filter_params.scope == scope
