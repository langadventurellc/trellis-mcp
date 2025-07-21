"""Common data models for Trellis MCP.

Contains shared enums and data structures used across the Trellis MCP system.
"""

from enum import IntEnum

import yaml


class Priority(IntEnum):
    """Priority levels for task sorting and selection.

    Lower integer values indicate higher priority.
    Used for sorting tasks when claiming next available task.
    Also supports string values for schema validation and serialization.
    """

    HIGH = 1
    NORMAL = 2
    LOW = 3

    @classmethod
    def _missing_(cls, value):
        """Support string values for Pydantic schema compatibility.

        Also supports 'medium' as an alias for 'normal' priority.
        """
        if isinstance(value, str):
            # Handle 'medium' as alias for 'normal'
            if value.lower() == "medium":
                return cls.NORMAL

            # Standard name matching for other values
            for member in cls:
                if member.name.lower() == value.lower():
                    return member
        return None

    def __str__(self) -> str:
        """Return lowercase string representation for serialization."""
        return self.name.lower()

    @classmethod
    def yaml_representer(cls, dumper, data):
        """Custom YAML representer to serialize as strings."""
        return dumper.represent_str(str(data))


# Register YAML representer for Priority enum
yaml.add_representer(Priority, Priority.yaml_representer)
yaml.SafeDumper.add_representer(Priority, Priority.yaml_representer)
