"""Object parser for Trellis MCP markdown files.

This module provides functionality to parse markdown files with YAML front-matter
into typed Pydantic model instances based on the object kind.
"""

from pathlib import Path
from typing import Union

from pydantic import ValidationError

from .markdown_loader import load_markdown
from .schema.epic import EpicModel
from .schema.feature import FeatureModel
from .schema.kind_enum import KindEnum
from .schema.project import ProjectModel
from .schema.task import TaskModel

# Type alias for all possible model instances
TrellisObjectModel = Union[ProjectModel, EpicModel, FeatureModel, TaskModel]

# Mapping from kind enum values to model classes
KIND_TO_MODEL = {
    KindEnum.PROJECT: ProjectModel,
    KindEnum.EPIC: EpicModel,
    KindEnum.FEATURE: FeatureModel,
    KindEnum.TASK: TaskModel,
}


def parse_object(path: Union[str, Path]) -> TrellisObjectModel:
    """Parse a markdown file into a typed Trellis MCP object model.

    Args:
        path: Path to the markdown file to parse

    Returns:
        Typed model instance (ProjectModel, EpicModel, FeatureModel, or TaskModel)

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the kind field is missing or invalid
        ValidationError: If the model data is invalid
    """
    file_path = Path(path)

    # Load markdown and extract front-matter
    try:
        frontmatter, _ = load_markdown(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Failed to load markdown from {file_path}: {e}")

    # Extract and validate kind field
    if "kind" not in frontmatter:
        raise ValueError(f"Missing 'kind' field in {file_path}")

    kind_value = frontmatter["kind"]

    # Convert string to KindEnum if needed
    try:
        if isinstance(kind_value, str):
            kind_enum = KindEnum(kind_value)
        else:
            kind_enum = kind_value
    except ValueError:
        raise ValueError(f"Invalid kind value '{kind_value}' in {file_path}")

    # Get appropriate model class
    model_class = KIND_TO_MODEL.get(kind_enum)
    if model_class is None:
        raise ValueError(f"Unknown kind '{kind_enum}' in {file_path}")

    # Instantiate and validate model
    try:
        model_instance = model_class(**frontmatter)
    except ValidationError:
        # Re-raise ValidationError as-is (Pydantic provides detailed error info)
        raise

    return model_instance
