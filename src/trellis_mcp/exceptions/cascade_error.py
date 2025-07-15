"""Exception for errors during cascade deletion operations."""


class CascadeError(Exception):
    """Raised when cascade deletion encounters an error.

    This exception is raised during parent deletion cascade operations when:
    1. Filesystem errors occur during recursive deletion
    2. Orphaned files or directories are detected after deletion
    3. Other system-level errors prevent clean cascade deletion
    """

    pass
