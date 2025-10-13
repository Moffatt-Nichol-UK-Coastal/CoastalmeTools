#!/usr/bin/env python3
"""Unit tests for Cme class YAML INI file support

Tests the updated Cme.__init__() method's ability to handle YAML initialization
files (.yaml/.yml) with different key naming conventions (input_data_file vs input,
output_path vs output).
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import yaml

from CoastalmeTools import Cme


@pytest.fixture
def temp_project_structure():
    """Create temporary directory structure for testing"""
    temp_dir = Path(tempfile.mkdtemp())

    # Create input directory with config file
    in_dir = temp_dir / "in"
    in_dir.mkdir()

    # Create output directory
    out_dir = temp_dir / "out"
    out_dir.mkdir()

    # Create a simple scenario.dat file
    scenario_dat = in_dir / "scenario.dat"
    with open(scenario_dat, "w") as f:
        f.write("""; CoastalME configuration
output folder : out
basement      : in/basement.tif
start date    : 00-00-00 01/01/2020
Duration of simulation : 1 year
save times    : 1 month
log_file_detail : 1
""")

    yield temp_dir, in_dir, out_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_legacy_ini_format(temp_project_structure):
    """Test Cme with legacy .ini file (DAT format)"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create legacy cme.ini file
    ini_file = temp_dir / "cme.ini"
    with open(ini_file, "w") as f:
        f.write(f"""; CoastalME ini file
input  : {in_dir / 'scenario.dat'}
output : {out_dir}
""")

    # Initialize Cme
    cme = Cme(ini=ini_file, run_path=temp_dir)

    # Verify paths
    assert cme.ini_type == "dat"
    assert cme.in_path == in_dir / "scenario.dat"
    assert cme.out_path == out_dir
    assert cme.conf_type == "dat"


def test_yaml_ini_format_absolute_paths(temp_project_structure):
    """Test Cme with YAML .ini file using absolute paths"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create YAML cme.yaml file with absolute paths
    ini_file = temp_dir / "cme.yaml"
    config = {
        "input_data_file": str(in_dir / "scenario.dat"),
        "output_path": str(out_dir)
    }

    with open(ini_file, "w") as f:
        yaml.safe_dump(config, f)

    # Initialize Cme
    cme = Cme(ini=ini_file, run_path=temp_dir)

    # Verify paths
    assert cme.ini_type == "yaml"
    assert cme.in_path == in_dir / "scenario.dat"
    assert cme.out_path == out_dir
    assert cme.conf_type == "dat"


def test_yaml_ini_format_relative_paths(temp_project_structure):
    """Test Cme with YAML .ini file using relative paths"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create YAML cme.yaml file with relative paths
    ini_file = temp_dir / "cme.yaml"
    config = {
        "input_data_file": "in/scenario.dat",
        "output_path": "out/"
    }

    with open(ini_file, "w") as f:
        yaml.safe_dump(config, f)

    # Initialize Cme
    cme = Cme(ini=ini_file, run_path=temp_dir)

    # Verify paths (should be resolved relative to run_path)
    assert cme.ini_type == "yaml"
    assert cme.in_path == temp_dir / "in" / "scenario.dat"
    assert cme.out_path == temp_dir / "out"
    assert cme.conf_type == "dat"


def test_yaml_ini_with_yaml_config(temp_project_structure):
    """Test Cme with YAML .ini file pointing to YAML config"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create a YAML scenario file
    scenario_yaml = in_dir / "scenario.yaml"
    scenario_config = {
        "run_data": {
            "output_folder": "out"
        },
        "raster_GIS": {
            "basement": "in/basement.tif"
        },
        "start_date": "00-00-00 01/01/2020",
        "duration": "1 year",
        "save_times": "1 month",
        "log_file_detail": 1
    }

    with open(scenario_yaml, "w") as f:
        yaml.safe_dump(scenario_config, f)

    # Create YAML cme.yaml file
    ini_file = temp_dir / "cme.yaml"
    config = {
        "input_data_file": str(in_dir / "scenario.yaml"),
        "output_path": str(out_dir)
    }

    with open(ini_file, "w") as f:
        yaml.safe_dump(config, f)

    # Initialize Cme
    cme = Cme(ini=ini_file, run_path=temp_dir)

    # Verify paths
    assert cme.ini_type == "yaml"
    assert cme.in_path == in_dir / "scenario.yaml"
    assert cme.out_path == out_dir
    assert cme.conf_type == "yaml"


def test_missing_input_key_error(temp_project_structure):
    """Test that missing input key raises appropriate error"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create YAML file without input or input_data_file key
    ini_file = temp_dir / "cme.yaml"
    config = {
        "output_path": str(out_dir)
    }

    with open(ini_file, "w") as f:
        yaml.safe_dump(config, f)

    # Should raise ValueError
    with pytest.raises(ValueError, match="Could not find input/input_data_file"):
        Cme(ini=ini_file, run_path=temp_dir)


def test_missing_output_key_error(temp_project_structure):
    """Test that missing output key raises appropriate error"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create YAML file without output or output_path key
    ini_file = temp_dir / "cme.yaml"
    config = {
        "input_data_file": str(in_dir / "scenario.dat")
    }

    with open(ini_file, "w") as f:
        yaml.safe_dump(config, f)

    # Should raise ValueError
    with pytest.raises(ValueError, match="Could not find output/output_path"):
        Cme(ini=ini_file, run_path=temp_dir)


def test_legacy_keys_still_work_in_yaml(temp_project_structure):
    """Test that legacy 'input' and 'output' keys still work in YAML"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create YAML file with legacy key names
    ini_file = temp_dir / "cme.yaml"
    config = {
        "input": str(in_dir / "scenario.dat"),
        "output": str(out_dir)
    }

    with open(ini_file, "w") as f:
        yaml.safe_dump(config, f)

    # Initialize Cme - should work with legacy keys
    cme = Cme(ini=ini_file, run_path=temp_dir)

    # Verify paths
    assert cme.ini_type == "yaml"
    assert cme.in_path == in_dir / "scenario.dat"
    assert cme.out_path == out_dir


def test_yml_extension_also_works(temp_project_structure):
    """Test that .yml extension is also recognized as YAML"""
    temp_dir, in_dir, out_dir = temp_project_structure

    # Create .yml file
    ini_file = temp_dir / "cme.yml"
    config = {
        "input_data_file": str(in_dir / "scenario.dat"),
        "output_path": str(out_dir)
    }

    with open(ini_file, "w") as f:
        yaml.safe_dump(config, f)

    # Initialize Cme
    cme = Cme(ini=ini_file, run_path=temp_dir)

    # Verify YAML format detected
    assert cme.ini_type == "yaml"
    assert cme.in_path == in_dir / "scenario.dat"
    assert cme.out_path == out_dir
