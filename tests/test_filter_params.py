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
        filter_params = FilterParams(status=None, priority=None)
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
