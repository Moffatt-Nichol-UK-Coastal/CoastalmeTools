#!/usr/bin/env python3
"""
Test script for YAML writing functionality.

This script tests the new write_yaml() function by:
1. Reading an existing YAML config
2. Modifying a value
3. Writing it back
4. Reading it again to verify
"""

from pathlib import Path
import sys

# Add parent to path so we can import CoastalmeTools
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from CoastalmeTools.Cme import read_yaml, write_yaml

def test_yaml_roundtrip():
    """Test reading, modifying, writing, and re-reading a YAML file"""

    print("=" * 70)
    print("Testing YAML Write Functionality")
    print("=" * 70)

    # Source YAML file
    source_yaml = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/in/thorpness.yaml")

    if not source_yaml.exists():
        print(f"❌ Error: Source file not found: {source_yaml}")
        return False

    # Create a temporary copy for testing
    test_yaml = source_yaml.parent / "thorpness_test_copy.yaml"

    try:
        print(f"\n1. Reading source YAML: {source_yaml}")
        df_original, vars_original = read_yaml(source_yaml)
        print(f"   ✓ Read {len(df_original)} configuration entries")

        # Show some sample values
        print(f"\n2. Original values:")
        sample_keys = ["log_file_detail", "duration", "timestep", "random_seed"]
        for key in sample_keys:
            mask = df_original['key'] == key
            if mask.any():
                value = df_original.loc[mask, 'value'].values[0]
                section = df_original.loc[mask, 'section'].values[0]
                print(f"   - {section}.{key} = {value}")

        # Modify a value
        print(f"\n3. Modifying 'random_seed' to 999999")
        mask = df_original['key'] == 'random_seed'
        df_original.loc[mask, 'value'] = 999999
        df_original.loc[mask, 'modified'] = True

        # Write to new file
        print(f"\n4. Writing to test file: {test_yaml}")
        write_yaml(test_yaml, df_original)
        print(f"   ✓ YAML file written")

        # Read back the written file
        print(f"\n5. Reading back the test file")
        df_readback, vars_readback = read_yaml(test_yaml)
        print(f"   ✓ Read {len(df_readback)} configuration entries")

        # Verify the modification persisted
        print(f"\n6. Verifying modifications:")
        mask = df_readback['key'] == 'random_seed'
        if mask.any():
            new_value = df_readback.loc[mask, 'value'].values[0]
            if new_value == 999999:
                print(f"   ✓ random_seed correctly updated to {new_value}")
            else:
                print(f"   ❌ random_seed has unexpected value: {new_value}")
                return False

        # Check if nested keys reconstructed correctly
        print(f"\n7. Checking nested key reconstruction:")
        nested_samples = [
            ("median_sizes_fine", "sediment_and_erosion"),
            ("median_sizes_sand", "sediment_and_erosion"),
            ("median_sizes_coarse", "sediment_and_erosion"),
        ]

        for key, expected_section in nested_samples:
            mask = df_readback['key'] == key
            if mask.any():
                value = df_readback.loc[mask, 'value'].values[0]
                section = df_readback.loc[mask, 'section'].values[0]
                print(f"   ✓ {section}.{key} = {value}")

        # Verify entry count matches
        if len(df_original) == len(df_readback):
            print(f"\n8. Entry count verification:")
            print(f"   ✓ Both have {len(df_original)} entries - no data loss")
        else:
            print(f"\n8. Entry count verification:")
            print(f"   ❌ Original: {len(df_original)}, Readback: {len(df_readback)}")
            return False

        print(f"\n{'=' * 70}")
        print(f"✅ All tests passed!")
        print(f"{'=' * 70}")

        # Show location of test file for manual inspection
        print(f"\nTest file created at: {test_yaml}")
        print(f"You can inspect it to verify formatting.")
        print(f"Delete it when done: rm {test_yaml}")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_yaml_roundtrip()
    sys.exit(0 if success else 1)
