"""Tests for exception classes.

This module tests the exception classes for proper initialization and inheritance.
"""

import pytest

from trellis_mcp.exceptions import CascadeError, ProtectedObjectError


class TestCascadeError:
    """Test CascadeError exception class."""

    def test_cascade_error_can_be_raised(self):
        """Test that CascadeError can be raised and caught."""
        with pytest.raises(CascadeError):
            raise CascadeError("Test cascade error")

    def test_cascade_error_with_message(self):
        """Test that CascadeError correctly stores message."""
        error = CascadeError("Test cascade error message")
        assert str(error) == "Test cascade error message"

    def test_cascade_error_inherits_from_exception(self):
        """Test that CascadeError inherits from Exception."""
        error = CascadeError("Test error")
        assert isinstance(error, Exception)

    def test_cascade_error_no_message(self):
        """Test that CascadeError can be created without message."""
        error = CascadeError()
        assert str(error) == ""


class TestProtectedObjectError:
    """Test ProtectedObjectError exception class."""

    def test_protected_object_error_can_be_raised(self):
        """Test that ProtectedObjectError can be raised and caught."""
        with pytest.raises(ProtectedObjectError):
            raise ProtectedObjectError("Test protected object error")

    def test_protected_object_error_with_message(self):
        """Test that ProtectedObjectError correctly stores message."""
        error = ProtectedObjectError("Test protected object error message")
        assert str(error) == "Test protected object error message"

    def test_protected_object_error_inherits_from_exception(self):
        """Test that ProtectedObjectError inherits from Exception."""
        error = ProtectedObjectError("Test error")
        assert isinstance(error, Exception)

    def test_protected_object_error_no_message(self):
        """Test that ProtectedObjectError can be created without message."""
        error = ProtectedObjectError()
        assert str(error) == ""
