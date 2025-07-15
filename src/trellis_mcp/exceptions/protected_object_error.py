"""Exception for when deletion is blocked due to protected children."""


class ProtectedObjectError(Exception):
    """Raised when attempting to delete a parent with protected children.

    This exception is raised when attempting to delete a parent object that has
    child objects in protected states:
    1. Tasks with status 'in-progress' or 'review'
    2. Other child objects that cannot be safely deleted

    The deletion is blocked unless the --force flag is used.
    """

    pass
