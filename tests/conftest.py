"""Pytest configuration and shared fixtures for CoastalmeTools tests."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory for tests.

    Yields:
        Path: Path to temporary directory

    Cleanup:
        Removes directory after test completes
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_dat_config():
    """Sample .dat configuration content.

    Returns:
        str: Content for a minimal CoastalME .dat config file
    """
    return """; CoastalME configuration file
output folder          : out
basement               : in/basement.tif
start date             : 00-00-00 01/01/2020
Duration of simulation : 1 year
timestep               : 1 hour
save interval          : 1 day
""".strip()


@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration content.

    Returns:
        dict: Dictionary representing a YAML config structure
    """
    return {
        "output": {"folder": "out"},
        "input": {"basement": "in/basement.tif"},
        "simulation": {
            "start_date": "00-00-00 01/01/2020",
            "duration": "1 year",
            "timestep": "1 hour",
            "save_interval": "1 day",
        },
    }


@pytest.fixture
def sample_ini_content():
    """Sample .ini file content pointing to main config.

    Returns:
        str: Content for a minimal CoastalME .ini file
    """
    return """main configuration file : in/scenario.dat
input folder : in
output folder : out
"""


@pytest.fixture
def mock_project_structure(temp_project_dir, sample_dat_config, sample_ini_content):
    """Create a complete mock project structure.

    Args:
        temp_project_dir: Temporary directory fixture
        sample_dat_config: Sample .dat config fixture
        sample_ini_content: Sample .ini content fixture

    Returns:
        tuple: (project_root, ini_file, config_file, in_dir, out_dir)
    """
    # Create directory structure
    in_dir = temp_project_dir / "in"
    out_dir = temp_project_dir / "out"
    in_dir.mkdir()
    out_dir.mkdir()

    # Create .ini file
    ini_file = temp_project_dir / "cme.ini"
    ini_file.write_text(sample_ini_content)

    # Create .dat config file
    config_file = in_dir / "scenario.dat"
    config_file.write_text(sample_dat_config)

    return temp_project_dir, ini_file, config_file, in_dir, out_dir


@pytest.fixture
def sample_simulation_metadata():
    """Sample simulation metadata for testing.

    Returns:
        dict: Dictionary with metadata fields
    """
    from CoastalmeTools.core.models import ConfigFormat

    return {
        "start_date": datetime(2020, 1, 1),
        "duration_seconds": 86400.0,  # 1 day
        "timestep_seconds": 3600.0,  # 1 hour
        "save_times": [datetime(2020, 1, 1, hour) for hour in range(24)],
        "config_format": ConfigFormat.DAT,
    }


@pytest.fixture
def sample_simulation_result():
    """Sample simulation result for testing.

    Returns:
        dict: Dictionary with result fields
    """
    return {
        "success": True,
        "return_code": 0,
        "log_file": None,
        "errors": {},
        "warnings": {},
        "output_files": [],
        "execution_time": 125.5,
    }
