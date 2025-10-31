"""Unit tests for configuration system."""

import pytest
from pathlib import Path
import yaml

from CoastalmeTools.config import load_config, DatConfig, YamlConfig
from CoastalmeTools.core.models import ConfigFormat
from CoastalmeTools.core.exceptions import (
    ConfigNotFoundError,
    ConfigParseError,
    ConfigError,
)


class TestDatConfig:
    """Tests for DatConfig adapter."""

    def test_dat_config_load(self, temp_project_dir, sample_dat_config):
        """Test loading .dat configuration."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        assert config.format == ConfigFormat.DAT
        assert config.get("output folder") == "out"
        assert config.get("basement") == "in/basement.tif"

    def test_dat_config_get_with_default(self, temp_project_dir, sample_dat_config):
        """Test get method with default value."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        assert config.get("nonexistent_key", "default_value") == "default_value"
        assert config.get("basement") == "in/basement.tif"

    def test_dat_config_set_and_save(self, temp_project_dir, sample_dat_config):
        """Test modifying and saving .dat config."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = load_config(config_file)
        config.set("output folder", "new_out")
        assert config.is_modified
        config.save()

        # Reload and verify
        config2 = load_config(config_file)
        assert config2.get("output folder") == "new_out"

    def test_dat_config_find_exact_match(self, temp_project_dir, sample_dat_config):
        """Test find method with exact match."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        assert config.find("basement") == "in/basement.tif"

    def test_dat_config_find_progressive(self, temp_project_dir, sample_dat_config):
        """Test find method with progressive narrowing."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        # Progressive narrowing: "duration simulation"
        assert config.find("Duration simulation") == "1 year"

    def test_dat_config_find_case_insensitive(self, temp_project_dir, sample_dat_config):
        """Test case-insensitive find."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        assert config.find("BASEMENT") == "in/basement.tif"
        assert config.find("basement") == "in/basement.tif"

    def test_dat_config_find_no_match(self, temp_project_dir, sample_dat_config):
        """Test find raises KeyError when no match."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        with pytest.raises(KeyError, match="No matches"):
            config.find("nonexistent_key")

    def test_dat_config_not_found(self, temp_project_dir):
        """Test error when config file doesn't exist."""
        config_file = temp_project_dir / "nonexistent.dat"

        config = DatConfig(config_file)
        with pytest.raises(ConfigNotFoundError):
            config.load()

    def test_dat_config_set_nonexistent_key(self, temp_project_dir, sample_dat_config):
        """Test setting nonexistent key raises KeyError."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        with pytest.raises(KeyError):
            config.set("nonexistent_key", "value")

    def test_dat_config_dictionary_access(self, temp_project_dir, sample_dat_config):
        """Test dictionary-style access."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        # Get
        assert config["basement"] == "in/basement.tif"

        # Set
        config["output folder"] = "modified_out"
        assert config["output folder"] == "modified_out"

    def test_dat_config_contains(self, temp_project_dir, sample_dat_config):
        """Test __contains__ method."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        assert "basement" in config
        assert "nonexistent" not in config

    def test_dat_config_keys_values_items(self, temp_project_dir, sample_dat_config):
        """Test keys(), values(), items() methods."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = DatConfig(config_file)
        config.load()

        assert "basement" in config.keys()
        assert "in/basement.tif" in config.values()
        assert ("basement", "in/basement.tif") in config.items()

    def test_dat_config_with_comments(self, temp_project_dir):
        """Test parsing config with comments."""
        config_content = """; This is a comment
output folder : out
; Another comment
basement      : in/basement.tif  ; inline comment
"""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(config_content)

        config = DatConfig(config_file)
        config.load()

        # get() returns the raw value with inline comment
        assert config.get("basement") == "in/basement.tif ; inline comment"
        # find() strips inline comments
        assert config.find("basement") == "in/basement.tif"


class TestYamlConfig:
    """Tests for YamlConfig adapter."""

    def test_yaml_config_load(self, temp_project_dir, sample_yaml_config):
        """Test loading YAML configuration."""
        config_file = temp_project_dir / "test.yaml"
        with open(config_file, "w") as f:
            yaml.safe_dump(sample_yaml_config, f)

        config = YamlConfig(config_file)
        config.load()

        assert config.format == ConfigFormat.YAML
        assert config.get("folder") == "out"
        assert config.get("basement") == "in/basement.tif"

    def test_yaml_config_nested_structure(self, temp_project_dir):
        """Test YAML with nested structure."""
        yaml_content = {
            "simulation": {
                "start_date": "00-00-00 01/01/2020",
                "duration": "1 year",
            },
            "output": {"folder": "out"},
        }
        config_file = temp_project_dir / "test.yaml"
        with open(config_file, "w") as f:
            yaml.safe_dump(yaml_content, f)

        config = YamlConfig(config_file)
        config.load()

        assert config.get("start_date") == "00-00-00 01/01/2020"
        assert config.get("duration") == "1 year"
        assert config.get("folder") == "out"

    def test_yaml_config_set_and_save(self, temp_project_dir, sample_yaml_config):
        """Test modifying and saving YAML config."""
        config_file = temp_project_dir / "test.yaml"
        with open(config_file, "w") as f:
            yaml.safe_dump(sample_yaml_config, f)

        config = YamlConfig(config_file)
        config.load()
        config.set("folder", "new_out")
        config.save()

        # Reload and verify
        config2 = YamlConfig(config_file)
        config2.load()
        assert config2.get("folder") == "new_out"

    def test_yaml_config_find(self, temp_project_dir, sample_yaml_config):
        """Test find method on YAML config."""
        config_file = temp_project_dir / "test.yaml"
        with open(config_file, "w") as f:
            yaml.safe_dump(sample_yaml_config, f)

        config = YamlConfig(config_file)
        config.load()

        assert config.find("basement") == "in/basement.tif"
        assert config.find("folder") == "out"

    def test_yaml_config_not_found(self, temp_project_dir):
        """Test error when YAML file doesn't exist."""
        config_file = temp_project_dir / "nonexistent.yaml"

        config = YamlConfig(config_file)
        with pytest.raises(ConfigNotFoundError):
            config.load()


class TestConfigFactory:
    """Tests for load_config factory function."""

    def test_factory_loads_dat(self, temp_project_dir, sample_dat_config):
        """Test factory function loads .dat files."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = load_config(config_file)
        assert isinstance(config, DatConfig)
        assert config.format == ConfigFormat.DAT

    def test_factory_loads_yaml(self, temp_project_dir, sample_yaml_config):
        """Test factory function loads .yaml files."""
        config_file = temp_project_dir / "test.yaml"
        with open(config_file, "w") as f:
            yaml.safe_dump(sample_yaml_config, f)

        config = load_config(config_file)
        assert isinstance(config, YamlConfig)
        assert config.format == ConfigFormat.YAML

    def test_factory_loads_yml(self, temp_project_dir, sample_yaml_config):
        """Test factory function loads .yml files."""
        config_file = temp_project_dir / "test.yml"
        with open(config_file, "w") as f:
            yaml.safe_dump(sample_yaml_config, f)

        config = load_config(config_file)
        assert isinstance(config, YamlConfig)

    def test_factory_unsupported_format(self, temp_project_dir):
        """Test factory raises error for unsupported formats."""
        config_file = temp_project_dir / "test.txt"
        config_file.write_text("some content")

        with pytest.raises(ConfigError, match="Unsupported config format"):
            load_config(config_file)

    def test_factory_with_string_path(self, temp_project_dir, sample_dat_config):
        """Test factory function accepts string paths."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        config = load_config(str(config_file))
        assert isinstance(config, DatConfig)


class TestConfigRoundTrip:
    """Integration tests for configuration round-trip (load-modify-save-load)."""

    def test_dat_round_trip(self, temp_project_dir, sample_dat_config):
        """Test DAT config round-trip preserves data."""
        config_file = temp_project_dir / "test.dat"
        config_file.write_text(sample_dat_config)

        # Load, modify, save
        config1 = load_config(config_file)
        original_basement = config1.get("basement")
        config1.set("basement", "modified/basement.tif")
        config1.save()

        # Reload and verify
        config2 = load_config(config_file)
        assert config2.get("basement") == "modified/basement.tif"
        assert config2.get("output folder") == "out"  # Other values preserved

    def test_yaml_round_trip(self, temp_project_dir, sample_yaml_config):
        """Test YAML config round-trip preserves data."""
        config_file = temp_project_dir / "test.yaml"
        with open(config_file, "w") as f:
            yaml.safe_dump(sample_yaml_config, f)

        # Load, modify, save
        config1 = load_config(config_file)
        config1.set("basement", "modified/basement.tif")
        config1.save()

        # Reload and verify
        config2 = load_config(config_file)
        assert config2.get("basement") == "modified/basement.tif"
