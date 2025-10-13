"""Custom exceptions for CoastalmeTools.

This module defines a hierarchy of exceptions for different error scenarios.
All exceptions inherit from CoastalmeToolsError for easy catching.
"""


class CoastalmeToolsError(Exception):
    """Base exception for all CoastalmeTools errors.

    All custom exceptions in the toolkit inherit from this class,
    allowing users to catch all toolkit-specific errors with a single
    except clause.
    """

    pass


class ConfigError(CoastalmeToolsError):
    """Configuration file errors.

    Raised when there are issues with configuration file handling,
    including missing files, parsing errors, or validation failures.
    """

    pass


class ConfigNotFoundError(ConfigError):
    """Configuration file not found.

    Raised when a specified configuration file does not exist at the
    expected path.
    """

    pass


class ConfigParseError(ConfigError):
    """Error parsing configuration file.

    Raised when a configuration file exists but cannot be parsed due to
    syntax errors or invalid format.
    """

    pass


class ConfigValidationError(ConfigError):
    """Configuration validation failed.

    Raised when a configuration file is parsed successfully but contains
    invalid values or missing required parameters.
    """

    pass


class ExecutionError(CoastalmeToolsError):
    """Simulation execution errors.

    Raised when there are issues running the CoastalME simulation,
    including executable not found, runtime errors, or crashes.
    """

    pass


class PreprocessingError(CoastalmeToolsError):
    """Input preprocessing errors.

    Raised when there are issues preparing input data for simulation,
    such as invalid raster formats, coordinate system mismatches,
    or missing required inputs.
    """

    pass


class ResultProcessingError(CoastalmeToolsError):
    """Output processing errors.

    Raised when there are issues processing simulation results,
    including NetCDF creation failures, GeoPackage generation errors,
    or missing output files.
    """

    pass
