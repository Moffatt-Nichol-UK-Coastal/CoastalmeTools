"""Core domain models and exceptions for CoastalmeTools."""

from .models import (
    ConfigFormat,
    ProjectPaths,
    SimulationMetadata,
    SimulationResult,
)
from .exceptions import (
    CoastalmeToolsError,
    ConfigError,
    ConfigNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    ExecutionError,
    PreprocessingError,
    ResultProcessingError,
)

__all__ = [
    # Models
    "ConfigFormat",
    "ProjectPaths",
    "SimulationMetadata",
    "SimulationResult",
    # Exceptions
    "CoastalmeToolsError",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigParseError",
    "ConfigValidationError",
    "ExecutionError",
    "PreprocessingError",
    "ResultProcessingError",
]
