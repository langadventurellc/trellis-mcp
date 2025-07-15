"""Exception for when no tasks are available to claim."""


class NoAvailableTask(Exception):
    """Raised when no unblocked tasks are available for claiming.

    This exception is raised by claim_next_task when either:
    1. No open tasks exist in the backlog
    2. All open tasks have incomplete prerequisites (are blocked)
    """

    pass
