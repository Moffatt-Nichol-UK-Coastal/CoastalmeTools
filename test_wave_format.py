#!/usr/bin/env python3
"""
Test script to verify that the updated wave_check method works with the new wave format.
"""

import sys
from pathlib import Path
import pandas as pd

# Add CoastalmeTools to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from CoastalmeTools import Cme

def test_wave_reading():
    """Test reading the new wave format"""

    # Path to test data with new wave format
    test_ini = Path("/home/wilfchun/CoastalME/CoastalME_data_local/Typology/Dune/cme.ini")
    test_run_path = test_ini.parent

    if not test_ini.exists():
        print(f"Test ini file not found: {test_ini}")
        return False

    try:
        # Initialize Cme object
        print(f"Initializing Cme with: {test_ini}")
        cme = Cme(ini=test_ini, run_path=test_run_path)

        # Get wave file path
        wave_file = cme.in_path.parent / cme.find_config("wave height time series")
        print(f"Wave file: {wave_file}")

        if not wave_file.exists():
            print(f"Wave file not found: {wave_file}")
            return False

        # Test reading wave file directly
        print("\nTesting direct CSV read with new format...")
        with open(wave_file, "r") as f:
            lines = f.read().splitlines()

        # Count header lines
        head_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith(';'):
                if stripped[0].isdigit() or stripped[0] == '-':
                    break
            head_lines += 1

        print(f"Detected {head_lines} header lines")
        print(f"First 3 header lines:")
        for i, line in enumerate(lines[:3]):
            print(f"  {i+1}: {line}")

        print(f"\nFirst 3 data lines:")
        for i, line in enumerate(lines[head_lines:head_lines+3]):
            print(f"  {i+1}: {line}")

        # Try reading with pandas
        df = pd.read_csv(
            wave_file,
            sep=",",
            header=None,
            names=["hours", "height", "orientation", "period"],
            skiprows=head_lines,
            skipinitialspace=True,
            on_bad_lines='skip',
            nrows=10  # Just read first 10 rows for testing
        )

        print(f"\nDataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"\nFirst 5 rows:")
        print(df.head())

        # Test wave_check method
        print("\n" + "="*60)
        print("Testing wave_check method...")
        print("="*60)
        cme.wave_check()

        # Check if wave rose was created
        wave_rose_path = cme.in_path.parent / "wave_rose.png"
        if wave_rose_path.exists():
            print(f"\n✓ Wave rose successfully created at: {wave_rose_path}")
        else:
            print(f"\n✗ Wave rose not found at: {wave_rose_path}")
            return False

        print("\n✓ All tests passed!")
        return True

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wave_reading()
    sys.exit(0 if success else 1)
