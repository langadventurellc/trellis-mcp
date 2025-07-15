"""Exception for when task completion is attempted with invalid status."""


class InvalidStatusForCompletion(Exception):
    """Raised when attempting to complete a task with invalid status.

    This exception is raised by complete_task when the task is not in
    'in-progress' or 'review' status, which are the only valid statuses
    that allow task completion.
    """

    pass
