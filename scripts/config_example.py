#!/usr/bin/env python3
"""Configuration API Example (Phase 2 - New Modular API)

This script demonstrates the new type-safe configuration system introduced
in Phase 2 of the CoastalmeTools refactoring.

Key Features:
- Auto-detection of .dat and .yaml formats
- Type-safe configuration access
- Backward-compatible query methods
- Dictionary-style access
- In-memory modification with save support

Usage:
    python scripts/config_example.py
"""

from pathlib import Path
import platform

# New configuration API (Phase 2)
from CoastalmeTools.config import load_config, DatConfig, YamlConfig
from CoastalmeTools.core.models import ConfigFormat
from CoastalmeTools.core.exceptions import ConfigNotFoundError, ConfigParseError


def example_basic_usage():
    """Example 1: Basic configuration loading and querying."""
    print("=" * 70)
    print("Example 1: Basic Configuration Usage")
    print("=" * 70)

    # Determine config path based on platform
    if platform.system() == "Darwin":
        config_path = Path(
            "/Users/wilfchun/Documents/GitHub/CoastalMe/"
            "CoastalME_data_local/CSE/Thorpness/in/scenario.dat"
        )
    else:  # Linux
        config_path = Path(
            "/home/wilfchun/CoastalME/CoastalME_data_local/"
            "Typology/Cliff2/in/scenario.dat"
        )

    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        print("Skipping example 1")
        return

    # Auto-detect format and load
    config = load_config(config_path)

    print(f"Config file: {config_path.name}")
    print(f"Format detected: {config.format.value}")
    print(f"File exists: {config.exists}")
    print()

    # Query configuration values
    print("Configuration values:")

    # Method 1: find() - flexible partial matching (legacy compatible)
    try:
        basement = config.find("basement")
        print(f"  Basement DEM: {basement}")
    except KeyError as e:
        print(f"  Basement DEM: Not found ({e})")

    # Method 2: get() - exact key matching with default
    output_folder = config.get("output folder", default="out")
    print(f"  Output folder: {output_folder}")

    # Method 3: Dictionary-style access
    if "start date" in config:
        start_date = config["start date"]
        print(f"  Start date: {start_date}")

    print()


def example_query_methods():
    """Example 2: Different query methods and their use cases."""
    print("=" * 70)
    print("Example 2: Query Methods Comparison")
    print("=" * 70)

    # Create a sample config for demonstration
    sample_dat = """; Sample CoastalME configuration
output folder          : out
basement               : in/basement.tif
start date             : 00-00-00 01/01/2020
Duration of simulation : 1 year
wave height time series : in/waves.txt
"""

    # Write to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
        f.write(sample_dat)
        temp_path = Path(f.name)

    try:
        config = load_config(temp_path)

        print("1. Exact match with get():")
        print(f"   config.get('basement') = {config.get('basement')}")
        print()

        print("2. Partial match with find():")
        print(f"   config.find('basement') = {config.find('basement')}")
        print(f"   config.find('Duration') = {config.find('Duration')}")
        print(f"   config.find('wave height') = {config.find('wave height')}")
        print()

        print("3. Progressive narrowing with find():")
        print(f"   config.find('Duration simulation') = {config.find('Duration simulation')}")
        print()

        print("4. Dictionary-style access:")
        print(f"   config['output folder'] = {config['output folder']}")
        print(f"   'start date' in config = {'start date' in config}")
        print()

        print("5. Case-insensitive find() (default):")
        print(f"   config.find('BASEMENT') = {config.find('BASEMENT')}")
        print(f"   config.find('basement') = {config.find('basement')}")
        print()

    finally:
        temp_path.unlink()


def example_modification():
    """Example 3: Modifying and saving configuration."""
    print("=" * 70)
    print("Example 3: Modifying Configuration")
    print("=" * 70)

    # Create a sample config
    sample_dat = """; Sample configuration
output folder : out
basement      : in/basement.tif
duration      : 1 year
"""

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
        f.write(sample_dat)
        temp_path = Path(f.name)

    try:
        # Load config
        config = load_config(temp_path)
        print("Original values:")
        print(f"  output folder: {config['output folder']}")
        print(f"  basement: {config['basement']}")
        print(f"  Modified: {config.is_modified}")
        print()

        # Modify values
        print("Modifying values...")
        config.set("output folder", "new_output")
        config["basement"] = "in/new_basement.tif"

        print("After modification (in memory):")
        print(f"  output folder: {config['output folder']}")
        print(f"  basement: {config['basement']}")
        print(f"  Modified: {config.is_modified}")
        print()

        # Save changes
        print("Saving changes to file...")
        config.save()

        # Reload to verify
        config2 = load_config(temp_path)
        print("After reload:")
        print(f"  output folder: {config2['output folder']}")
        print(f"  basement: {config2['basement']}")
        print()

    finally:
        temp_path.unlink()


def example_format_detection():
    """Example 4: Format detection and specific adapters."""
    print("=" * 70)
    print("Example 4: Format Detection")
    print("=" * 70)

    import tempfile

    # Create .dat file
    dat_content = "output folder : out"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
        f.write(dat_content)
        dat_path = Path(f.name)

    # Create .yaml file
    yaml_content = """output:
  folder: out"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_path = Path(f.name)

    try:
        # Auto-detect .dat
        dat_config = load_config(dat_path)
        print(f"DAT file: {dat_path.suffix}")
        print(f"  Adapter type: {type(dat_config).__name__}")
        print(f"  Format enum: {dat_config.format}")
        print(f"  Is DAT: {isinstance(dat_config, DatConfig)}")
        print()

        # Auto-detect .yaml
        yaml_config = load_config(yaml_path)
        print(f"YAML file: {yaml_path.suffix}")
        print(f"  Adapter type: {type(yaml_config).__name__}")
        print(f"  Format enum: {yaml_config.format}")
        print(f"  Is YAML: {isinstance(yaml_config, YamlConfig)}")
        print()

    finally:
        dat_path.unlink()
        yaml_path.unlink()


def example_error_handling():
    """Example 5: Error handling."""
    print("=" * 70)
    print("Example 5: Error Handling")
    print("=" * 70)

    # Try loading non-existent file
    print("1. ConfigNotFoundError:")
    try:
        config = load_config(Path("nonexistent.dat"))
    except ConfigNotFoundError as e:
        print(f"   Caught: {type(e).__name__}: {e}")
    print()

    # Try unsupported format
    print("2. ConfigError (unsupported format):")
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("some content")
        txt_path = Path(f.name)

    try:
        config = load_config(txt_path)
    except Exception as e:
        print(f"   Caught: {type(e).__name__}: {e}")
    finally:
        txt_path.unlink()
    print()

    # Try accessing non-existent key
    print("3. KeyError (key not found):")
    sample_dat = "output folder : out"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
        f.write(sample_dat)
        temp_path = Path(f.name)

    try:
        config = load_config(temp_path)
        value = config.find("nonexistent_key")
    except KeyError as e:
        print(f"   Caught: {type(e).__name__}: {e}")
    finally:
        temp_path.unlink()
    print()


def example_list_all_keys():
    """Example 6: Listing all configuration keys."""
    print("=" * 70)
    print("Example 6: Listing Configuration Keys")
    print("=" * 70)

    sample_dat = """; Configuration
output folder : out
basement      : in/basement.tif
start date    : 00-00-00 01/01/2020
duration      : 1 year
"""

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
        f.write(sample_dat)
        temp_path = Path(f.name)

    try:
        config = load_config(temp_path)

        print(f"Total keys: {len(config.keys())}")
        print("\nAll keys:")
        for key in config.keys():
            value = config[key]
            print(f"  {key:20} : {value}")
        print()

        print("All items:")
        for key, value in config.items():
            print(f"  {key:20} = {value}")
        print()

    finally:
        temp_path.unlink()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  CoastalmeTools Configuration API Examples".center(68) + "*")
    print("*" + "  (Phase 2 - New Modular API)".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()

    try:
        example_basic_usage()
        print()

        example_query_methods()
        print()

        example_modification()
        print()

        example_format_detection()
        print()

        example_error_handling()
        print()

        example_list_all_keys()
        print()

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
