"""Unit tests for core data models."""

import pytest
from pathlib import Path
from datetime import datetime

from CoastalmeTools.core.models import (
    ConfigFormat,
    ProjectPaths,
    SimulationMetadata,
    SimulationResult,
)


class TestConfigFormat:
    """Tests for ConfigFormat enum."""

    def test_config_format_values(self):
        """Test that ConfigFormat has expected values."""
        assert ConfigFormat.DAT.value == "dat"
        assert ConfigFormat.YAML.value == "yaml"

    def test_config_format_from_string(self):
        """Test creating ConfigFormat from string."""
        assert ConfigFormat("dat") == ConfigFormat.DAT
        assert ConfigFormat("yaml") == ConfigFormat.YAML


class TestProjectPaths:
    """Tests for ProjectPaths dataclass."""

    def test_project_paths_creation(self, temp_project_dir):
        """Test creating ProjectPaths instance."""
        ini_file = temp_project_dir / "cme.ini"
        config_file = temp_project_dir / "in" / "scenario.dat"

        paths = ProjectPaths(
            ini_file=ini_file,
            exec_path=temp_project_dir,
            in_path=temp_project_dir / "in",
            out_path=temp_project_dir / "out",
            config_file=config_file,
        )

        assert paths.ini_file == ini_file
        assert paths.exec_path == temp_project_dir
        assert isinstance(paths.ini_file, Path)

    def test_project_paths_string_conversion(self, temp_project_dir):
        """Test that string paths are converted to Path objects."""
        paths = ProjectPaths(
            ini_file=str(temp_project_dir / "cme.ini"),
            exec_path=str(temp_project_dir),
            in_path=str(temp_project_dir / "in"),
            out_path=str(temp_project_dir / "out"),
            config_file=str(temp_project_dir / "in" / "scenario.dat"),
        )

        assert isinstance(paths.ini_file, Path)
        assert isinstance(paths.exec_path, Path)
        assert isinstance(paths.in_path, Path)
        assert isinstance(paths.out_path, Path)
        assert isinstance(paths.config_file, Path)

    def test_project_paths_exists_true(self, mock_project_structure):
        """Test exists property returns True when files exist."""
        project_root, ini_file, config_file, in_dir, out_dir = mock_project_structure

        paths = ProjectPaths(
            ini_file=ini_file,
            exec_path=project_root,
            in_path=in_dir,
            out_path=out_dir,
            config_file=config_file,
        )

        assert paths.exists is True

    def test_project_paths_exists_false(self, temp_project_dir):
        """Test exists property returns False when files don't exist."""
        paths = ProjectPaths(
            ini_file=temp_project_dir / "nonexistent.ini",
            exec_path=temp_project_dir,
            in_path=temp_project_dir / "in",
            out_path=temp_project_dir / "out",
            config_file=temp_project_dir / "in" / "nonexistent.dat",
        )

        assert paths.exists is False

    def test_project_paths_is_valid(self, mock_project_structure):
        """Test is_valid property."""
        project_root, ini_file, config_file, in_dir, out_dir = mock_project_structure

        paths = ProjectPaths(
            ini_file=ini_file,
            exec_path=project_root,
            in_path=in_dir,
            out_path=out_dir,
            config_file=config_file,
        )

        assert paths.is_valid is True

    def test_project_paths_is_valid_missing_ini(self, temp_project_dir):
        """Test is_valid returns False when ini_file doesn't exist."""
        paths = ProjectPaths(
            ini_file=temp_project_dir / "missing.ini",
            exec_path=temp_project_dir,
            in_path=temp_project_dir / "in",
            out_path=temp_project_dir / "out",
            config_file=temp_project_dir / "in" / "scenario.dat",
        )

        assert paths.is_valid is False


class TestSimulationMetadata:
    """Tests for SimulationMetadata dataclass."""

    def test_simulation_metadata_creation(self, sample_simulation_metadata):
        """Test creating SimulationMetadata instance."""
        metadata = SimulationMetadata(**sample_simulation_metadata)

        assert metadata.start_date == datetime(2020, 1, 1)
        assert metadata.duration_seconds == 86400.0
        assert metadata.timestep_seconds == 3600.0
        assert len(metadata.save_times) == 24
        assert metadata.config_format == ConfigFormat.DAT

    def test_num_timesteps_property(self, sample_simulation_metadata):
        """Test num_timesteps calculated property."""
        metadata = SimulationMetadata(**sample_simulation_metadata)

        # 86400 seconds / 3600 seconds per timestep = 24 timesteps
        assert metadata.num_timesteps == 24

    def test_num_timesteps_zero_timestep(self, sample_simulation_metadata):
        """Test num_timesteps when timestep_seconds is zero."""
        sample_simulation_metadata["timestep_seconds"] = 0.0
        metadata = SimulationMetadata(**sample_simulation_metadata)

        # Should fall back to length of save_times
        assert metadata.num_timesteps == 24

    def test_num_saves_property(self, sample_simulation_metadata):
        """Test num_saves property."""
        metadata = SimulationMetadata(**sample_simulation_metadata)

        assert metadata.num_saves == 24
        assert metadata.num_saves == len(metadata.save_times)


class TestSimulationResult:
    """Tests for SimulationResult dataclass."""

    def test_simulation_result_creation(self, sample_simulation_result):
        """Test creating SimulationResult instance."""
        result = SimulationResult(**sample_simulation_result)

        assert result.success is True
        assert result.return_code == 0
        assert result.log_file is None
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.execution_time == 125.5

    def test_simulation_result_with_errors(self):
        """Test SimulationResult with errors."""
        result = SimulationResult(
            success=False,
            return_code=1,
            errors={10: "ERROR: Invalid basement file"},
            warnings={5: "WARNING: Missing optional parameter"},
        )

        assert result.success is False
        assert result.crashed is True
        assert result.has_errors is True
        assert result.has_warnings is True

    def test_crashed_property(self):
        """Test crashed property mirrors success."""
        successful_result = SimulationResult(success=True, return_code=0)
        assert successful_result.crashed is False

        failed_result = SimulationResult(success=False, return_code=1)
        assert failed_result.crashed is True

    def test_has_errors_property(self):
        """Test has_errors property."""
        result_no_errors = SimulationResult(success=True, return_code=0)
        assert result_no_errors.has_errors is False

        result_with_errors = SimulationResult(
            success=False,
            return_code=1,
            errors={1: "Error message"},
        )
        assert result_with_errors.has_errors is True

    def test_has_warnings_property(self):
        """Test has_warnings property."""
        result_no_warnings = SimulationResult(success=True, return_code=0)
        assert result_no_warnings.has_warnings is False

        result_with_warnings = SimulationResult(
            success=True,
            return_code=0,
            warnings={1: "Warning message"},
        )
        assert result_with_warnings.has_warnings is True

    def test_num_outputs_property(self, temp_project_dir):
        """Test num_outputs property."""
        output_files = [
            temp_project_dir / "out" / "elevation_0001.tif",
            temp_project_dir / "out" / "elevation_0002.tif",
            temp_project_dir / "out" / "wave_height_0001.tif",
        ]

        result = SimulationResult(
            success=True,
            return_code=0,
            output_files=output_files,
        )

        assert result.num_outputs == 3

    def test_default_values(self):
        """Test that default values are set correctly."""
        result = SimulationResult(success=True, return_code=0)

        assert result.log_file is None
        assert result.errors == {}
        assert result.warnings == {}
        assert result.output_files == []
        assert result.execution_time == 0.0
