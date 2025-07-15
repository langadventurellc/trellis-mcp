"""Base configuration for Trellis MCP Pydantic models.

Provides common configuration for all Pydantic models in the Trellis MCP schema package.
This includes validation settings, field behavior, and other shared model configurations.
"""

from pydantic import BaseModel, ConfigDict


class TrellisBaseModel(BaseModel):
    """Base Pydantic model for all Trellis MCP schema objects.

    Provides common configuration for all Pydantic models in the Trellis MCP
    schema package. This includes validation on assignment and strict field control.

    Configuration:
        validate_assignment: Enables validation when model fields are assigned new values
        extra: Forbids extra fields not defined in the model schema
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )
