"""Exception for when task completion is attempted with incomplete prerequisites."""


class PrerequisitesNotComplete(Exception):
    """Raised when attempting to complete a task with incomplete prerequisites.

    This exception is raised by complete_task when the task has one or more
    prerequisites that are not yet in 'done' status, preventing completion.
    """

    pass
