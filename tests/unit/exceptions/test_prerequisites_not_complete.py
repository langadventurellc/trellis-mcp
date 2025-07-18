"""Tests for PrerequisitesNotComplete exception class."""

import pytest

from src.trellis_mcp.exceptions.prerequisites_not_complete import PrerequisitesNotComplete


class TestPrerequisitesNotComplete:
    """Test cases for PrerequisitesNotComplete exception class."""

    def test_prerequisites_not_complete_can_be_raised(self):
        """Test that PrerequisitesNotComplete can be raised and caught."""
        with pytest.raises(PrerequisitesNotComplete):
            raise PrerequisitesNotComplete("Prerequisites not complete")

    def test_prerequisites_not_complete_with_message(self):
        """Test that PrerequisitesNotComplete correctly stores message."""
        error = PrerequisitesNotComplete("Task T-123 has incomplete prerequisites")
        assert str(error) == "Task T-123 has incomplete prerequisites"

    def test_prerequisites_not_complete_inherits_from_exception(self):
        """Test that PrerequisitesNotComplete inherits from Exception."""
        error = PrerequisitesNotComplete("Test error")
        assert isinstance(error, Exception)

    def test_prerequisites_not_complete_no_message(self):
        """Test that PrerequisitesNotComplete can be created without message."""
        error = PrerequisitesNotComplete()
        assert str(error) == ""

    def test_prerequisites_not_complete_with_task_context(self):
        """Test PrerequisitesNotComplete with task-specific context."""
        task_id = "T-implement-feature"
        incomplete_prereqs = ["T-create-model", "T-setup-database"]

        message = (
            f"Cannot complete task {task_id}. "
            f"Incomplete prerequisites: {', '.join(incomplete_prereqs)}"
        )
        error = PrerequisitesNotComplete(message)

        assert str(error) == message
        assert "T-implement-feature" in str(error)
        assert "T-create-model" in str(error)
        assert "T-setup-database" in str(error)

    def test_prerequisites_not_complete_single_prerequisite(self):
        """Test PrerequisitesNotComplete with single incomplete prerequisite."""
        error = PrerequisitesNotComplete(
            "Task T-add-validation cannot be completed. "
            "Prerequisite T-create-schema is still in 'in-progress' status."
        )

        assert "T-add-validation" in str(error)
        assert "T-create-schema" in str(error)
        assert "in-progress" in str(error)
        assert "cannot be completed" in str(error)

    def test_prerequisites_not_complete_multiple_prerequisites(self):
        """Test PrerequisitesNotComplete with multiple incomplete prerequisites."""
        error = PrerequisitesNotComplete(
            "Task T-deploy-feature blocked by 3 incomplete prerequisites: "
            "T-write-tests (open), T-code-review (review), T-security-audit (in-progress)"
        )

        assert "T-deploy-feature" in str(error)
        assert "3 incomplete prerequisites" in str(error)
        assert "T-write-tests (open)" in str(error)
        assert "T-code-review (review)" in str(error)
        assert "T-security-audit (in-progress)" in str(error)

    def test_prerequisites_not_complete_with_dependency_chain(self):
        """Test PrerequisitesNotComplete with dependency chain information."""
        error = PrerequisitesNotComplete(
            "Task completion blocked: T-final-step requires T-step-2 (open) "
            "which requires T-step-1 (in-progress)"
        )

        assert "dependency chain" not in str(error)  # This message doesn't mention chain directly
        assert "T-final-step" in str(error)
        assert "T-step-2 (open)" in str(error)
        assert "T-step-1 (in-progress)" in str(error)

    def test_prerequisites_not_complete_with_status_details(self):
        """Test PrerequisitesNotComplete with prerequisite status details."""
        error = PrerequisitesNotComplete(
            "Cannot complete T-integration-test. Prerequisites status: "
            "T-unit-tests: done, T-api-tests: in-progress, T-e2e-tests: open"
        )

        assert "T-integration-test" in str(error)
        assert "T-unit-tests: done" in str(error)
        assert "T-api-tests: in-progress" in str(error)
        assert "T-e2e-tests: open" in str(error)

    def test_prerequisites_not_complete_exception_behavior(self):
        """Test that PrerequisitesNotComplete behaves like a standard exception."""
        error = PrerequisitesNotComplete("Prerequisites incomplete")

        # Should be able to access args
        assert error.args == ("Prerequisites incomplete",)

        # Should be able to raise and catch as Exception
        with pytest.raises(Exception):
            raise error

    def test_prerequisites_not_complete_multiple_args(self):
        """Test PrerequisitesNotComplete with multiple arguments."""
        error = PrerequisitesNotComplete(
            "Task T-123", "prerequisite T-456 incomplete", "status: open"
        )

        assert error.args == ("Task T-123", "prerequisite T-456 incomplete", "status: open")
        assert "Task T-123" in str(error)

    def test_prerequisites_not_complete_with_project_context(self):
        """Test PrerequisitesNotComplete with project context."""
        error = PrerequisitesNotComplete(
            "Project P-user-auth: Task T-implement-login cannot complete. "
            "Feature F-user-registration prerequisites incomplete."
        )

        assert "P-user-auth" in str(error)
        assert "T-implement-login" in str(error)
        assert "F-user-registration" in str(error)
        assert "prerequisites incomplete" in str(error)
