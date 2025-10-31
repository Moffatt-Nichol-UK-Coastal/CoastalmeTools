"""Unit tests for custom exceptions."""

import pytest

from CoastalmeTools.core.exceptions import (
    CoastalmeToolsError,
    ConfigError,
    ConfigNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    ExecutionError,
    PreprocessingError,
    ResultProcessingError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from CoastalmeToolsError."""
        assert issubclass(ConfigError, CoastalmeToolsError)
        assert issubclass(ConfigNotFoundError, CoastalmeToolsError)
        assert issubclass(ConfigParseError, CoastalmeToolsError)
        assert issubclass(ConfigValidationError, CoastalmeToolsError)
        assert issubclass(ExecutionError, CoastalmeToolsError)
        assert issubclass(PreprocessingError, CoastalmeToolsError)
        assert issubclass(ResultProcessingError, CoastalmeToolsError)

    def test_config_exceptions_inherit_from_config_error(self):
        """Test that specific config exceptions inherit from ConfigError."""
        assert issubclass(ConfigNotFoundError, ConfigError)
        assert issubclass(ConfigParseError, ConfigError)
        assert issubclass(ConfigValidationError, ConfigError)

    def test_base_exception_is_exception(self):
        """Test that base exception inherits from Exception."""
        assert issubclass(CoastalmeToolsError, Exception)


class TestExceptionRaising:
    """Tests for raising and catching exceptions."""

    def test_raise_base_exception(self):
        """Test raising base CoastalmeToolsError."""
        with pytest.raises(CoastalmeToolsError) as exc_info:
            raise CoastalmeToolsError("Base error message")

        assert str(exc_info.value) == "Base error message"

    def test_raise_config_not_found_error(self):
        """Test raising ConfigNotFoundError."""
        with pytest.raises(ConfigNotFoundError) as exc_info:
            raise ConfigNotFoundError("Config file not found: test.dat")

        assert "Config file not found" in str(exc_info.value)

    def test_raise_config_parse_error(self):
        """Test raising ConfigParseError."""
        with pytest.raises(ConfigParseError) as exc_info:
            raise ConfigParseError("Invalid YAML syntax on line 5")

        assert "Invalid YAML syntax" in str(exc_info.value)

    def test_raise_config_validation_error(self):
        """Test raising ConfigValidationError."""
        with pytest.raises(ConfigValidationError) as exc_info:
            raise ConfigValidationError("Missing required parameter: basement")

        assert "Missing required parameter" in str(exc_info.value)

    def test_raise_execution_error(self):
        """Test raising ExecutionError."""
        with pytest.raises(ExecutionError) as exc_info:
            raise ExecutionError("Simulation crashed with code 1")

        assert "Simulation crashed" in str(exc_info.value)

    def test_raise_preprocessing_error(self):
        """Test raising PreprocessingError."""
        with pytest.raises(PreprocessingError) as exc_info:
            raise PreprocessingError("Invalid raster format")

        assert "Invalid raster format" in str(exc_info.value)

    def test_raise_result_processing_error(self):
        """Test raising ResultProcessingError."""
        with pytest.raises(ResultProcessingError) as exc_info:
            raise ResultProcessingError("Failed to create NetCDF file")

        assert "Failed to create NetCDF" in str(exc_info.value)


class TestExceptionCatching:
    """Tests for catching exceptions at different hierarchy levels."""

    def test_catch_specific_config_error(self):
        """Test catching specific ConfigError subclass."""
        with pytest.raises(ConfigNotFoundError):
            raise ConfigNotFoundError("File missing")

    def test_catch_config_error_catches_subclasses(self):
        """Test that catching ConfigError catches all config subclasses."""
        with pytest.raises(ConfigError):
            raise ConfigNotFoundError("File missing")

        with pytest.raises(ConfigError):
            raise ConfigParseError("Parse failed")

        with pytest.raises(ConfigError):
            raise ConfigValidationError("Validation failed")

    def test_catch_base_error_catches_all(self):
        """Test that catching CoastalmeToolsError catches all subclasses."""
        with pytest.raises(CoastalmeToolsError):
            raise ConfigNotFoundError("Config error")

        with pytest.raises(CoastalmeToolsError):
            raise ExecutionError("Execution error")

        with pytest.raises(CoastalmeToolsError):
            raise PreprocessingError("Preprocessing error")

        with pytest.raises(CoastalmeToolsError):
            raise ResultProcessingError("Result processing error")

    def test_selective_exception_handling(self):
        """Test selective exception handling with try/except blocks."""

        def raise_config_not_found():
            raise ConfigNotFoundError("File missing")

        def raise_execution_error():
            raise ExecutionError("Simulation failed")

        # Catch specific exception
        try:
            raise_config_not_found()
        except ConfigNotFoundError as e:
            assert "File missing" in str(e)

        # Catch parent class
        try:
            raise_config_not_found()
        except ConfigError as e:
            assert "File missing" in str(e)

        # Different exception type
        try:
            raise_execution_error()
        except ExecutionError as e:
            assert "Simulation failed" in str(e)


class TestExceptionMessages:
    """Tests for exception message handling."""

    def test_exception_with_no_message(self):
        """Test exceptions can be raised without a message."""
        with pytest.raises(CoastalmeToolsError):
            raise CoastalmeToolsError()

    def test_exception_with_formatted_message(self):
        """Test exceptions with formatted messages."""
        filename = "test.dat"
        line_num = 42

        with pytest.raises(ConfigParseError) as exc_info:
            raise ConfigParseError(f"Error in {filename} at line {line_num}")

        assert "test.dat" in str(exc_info.value)
        assert "42" in str(exc_info.value)

    def test_exception_with_multiline_message(self):
        """Test exceptions with multi-line messages."""
        message = """Configuration validation failed:
- Missing required parameter: basement
- Invalid duration format: '1 yar' (should be '1 year')
- Start date out of range"""

        with pytest.raises(ConfigValidationError) as exc_info:
            raise ConfigValidationError(message)

        assert "Missing required parameter" in str(exc_info.value)
        assert "Invalid duration format" in str(exc_info.value)
        assert "Start date out of range" in str(exc_info.value)
