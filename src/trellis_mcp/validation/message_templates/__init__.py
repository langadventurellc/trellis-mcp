"""Message template system for validation errors.

This module provides a centralized, configurable system for generating
consistent error messages with placeholder substitution and context awareness.
"""

from .core import MessageTemplate, TemplateEngine
from .engine import TrellisMessageEngine, generate_template_message, get_default_engine
from .formatters import get_formatter
from .registry import MessageTemplateRegistry
from .templates import get_default_templates

__all__ = [
    "MessageTemplate",
    "TemplateEngine",
    "MessageTemplateRegistry",
    "TrellisMessageEngine",
    "get_default_engine",
    "generate_template_message",
    "get_formatter",
    "get_default_templates",
]
