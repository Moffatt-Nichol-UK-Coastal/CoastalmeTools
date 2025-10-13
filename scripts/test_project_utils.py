#!/usr/bin/env python3
"""
Test script for project_tools utility functions.

Tests each utility function to verify it works correctly before
implementing the main copy_project() function.
"""

from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from CoastalmeTools import Cme
from CoastalmeTools.project_tools import (
    get_project_extent,
    calculate_grid_parameters,
    validate_crop_bbox,
    get_raster_files_in_project,
    check_wave_stations_in_domain,
    estimate_runtime_change,
    ProjectCopyReport
)
import rasterio

def test_get_project_extent():
    """Test extracting extent from project"""
    print("\n" + "=" * 70)
    print("Test 1: get_project_extent()")
    print("=" * 70)

    ini_path = "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.ini"

    try:
        extent = get_project_extent(ini_path)
        print(f"✓ Project extent: {extent}")
        print(f"  Width:  {extent[2] - extent[0]:.1f} m")
        print(f"  Height: {extent[3] - extent[1]:.1f} m")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculate_grid_parameters():
    """Test grid parameter calculations"""
    print("\n" + "=" * 70)
    print("Test 2: calculate_grid_parameters()")
    print("=" * 70)

    # Load a real raster to get transform and shape
    ini_path = "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.ini"
    cme = Cme(ini=ini_path, run_path=Path(ini_path).parent)
    basement_path = cme.in_path.parent / cme.find_config("basement")

    with rasterio.open(basement_path) as src:
        source_transform = src.transform
        source_shape = src.shape
        source_bounds = src.bounds

    print(f"Source grid: {source_shape[1]} x {source_shape[0]} cells")
    print(f"Source cell size: {abs(source_transform.a):.2f} m")

    # Test 1: Crop only
    print("\n--- Test 2a: Crop only ---")
    crop_bbox = (
        source_bounds.left + 100,
        source_bounds.bottom + 100,
        source_bounds.right - 100,
        source_bounds.top - 100
    )
    params = calculate_grid_parameters(
        source_transform=source_transform,
        source_shape=source_shape,
        crop_bbox=crop_bbox,
        target_cell_size=None
    )
    print(f"✓ Cropped grid: {params['nx']} x {params['ny']} cells")
    print(f"  Cell size unchanged: {params['dx']:.2f} m")
    print(f"  New extent: {params['extent']}")

    # Test 2: Resample only
    print("\n--- Test 2b: Resample only (5m cells) ---")
    params = calculate_grid_parameters(
        source_transform=source_transform,
        source_shape=source_shape,
        crop_bbox=None,
        target_cell_size=5.0
    )
    print(f"✓ Resampled grid: {params['nx']} x {params['ny']} cells")
    print(f"  New cell size: {params['dx']:.2f} m")

    # Test 3: Both
    print("\n--- Test 2c: Crop AND resample ---")
    params = calculate_grid_parameters(
        source_transform=source_transform,
        source_shape=source_shape,
        crop_bbox=crop_bbox,
        target_cell_size=2.0
    )
    print(f"✓ Cropped & resampled grid: {params['nx']} x {params['ny']} cells")
    print(f"  New cell size: {params['dx']:.2f} m")

    return True


def test_validate_crop_bbox():
    """Test crop bbox validation"""
    print("\n" + "=" * 70)
    print("Test 3: validate_crop_bbox()")
    print("=" * 70)

    source_extent = (640000, 263000, 642000, 265000)

    # Test 1: Valid crop
    print("\n--- Test 3a: Valid crop (inside source) ---")
    crop_bbox = (640100, 263100, 641900, 264900)
    valid, warnings = validate_crop_bbox(source_extent, crop_bbox)
    print(f"Valid: {valid}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    else:
        print("  ✓ No warnings")

    # Test 2: Crop extends beyond source
    print("\n--- Test 3b: Crop extends beyond source ---")
    crop_bbox = (639000, 262000, 643000, 266000)
    valid, warnings = validate_crop_bbox(source_extent, crop_bbox)
    print(f"Valid: {valid}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")

    # Test 3: Crop completely outside
    print("\n--- Test 3c: Crop completely outside ---")
    crop_bbox = (650000, 270000, 651000, 271000)
    valid, warnings = validate_crop_bbox(source_extent, crop_bbox)
    print(f"Valid: {valid}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")

    return True


def test_get_raster_files():
    """Test raster file discovery"""
    print("\n" + "=" * 70)
    print("Test 4: get_raster_files_in_project()")
    print("=" * 70)

    ini_path = "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.ini"
    cme = Cme(ini=ini_path, run_path=Path(ini_path).parent)

    files = get_raster_files_in_project(cme)

    print(f"Basement: {files['basement']}")
    print(f"Sediment layers found: {len(files['sediment_layers'])}")
    for layer, sed_type, path in files['sediment_layers']:
        print(f"  Layer {layer} - {sed_type}: {path.name}")
    print(f"Intervention files: {len(files['interventions'])}")
    for path in files['interventions']:
        print(f"  {path.name}")

    return True


def test_check_wave_stations():
    """Test wave station validation"""
    print("\n" + "=" * 70)
    print("Test 5: check_wave_stations_in_domain()")
    print("=" * 70)

    ini_path = "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.ini"
    cme = Cme(ini=ini_path, run_path=Path(ini_path).parent)

    try:
        wave_shp_name = cme.find_config("wave_height_shape")
        wave_shp = cme.in_path.parent / wave_shp_name

        # Test with current domain (should all be inside)
        extent = get_project_extent(ini_path)
        all_inside, warnings = check_wave_stations_in_domain(wave_shp, extent)

        print(f"Wave stations file: {wave_shp.name}")
        print(f"All inside domain: {all_inside}")
        if warnings:
            print(f"Stations outside: {warnings}")
        else:
            print("✓ All stations within domain")

        # Test with smaller domain
        print("\n--- Testing with smaller domain ---")
        small_domain = (
            extent[0] + 500,
            extent[1] + 500,
            extent[2] - 500,
            extent[3] - 500
        )
        all_inside, warnings = check_wave_stations_in_domain(wave_shp, small_domain)
        print(f"All inside: {all_inside}")
        if warnings:
            print(f"⚠️  Stations outside: {warnings}")

    except (KeyError, FileNotFoundError) as e:
        print(f"⚠️  No wave stations shapefile found (this is okay): {e}")

    return True


def test_estimate_runtime():
    """Test runtime estimation"""
    print("\n" + "=" * 70)
    print("Test 6: estimate_runtime_change()")
    print("=" * 70)

    scenarios = [
        (1000 * 500, 500 * 250, "Crop to 1/4 size"),
        (1000 * 500, 2000 * 1000, "Double each dimension"),
        (1000 * 500, 1000 * 500, "No change"),
    ]

    for old, new, desc in scenarios:
        ratio = estimate_runtime_change(old, new)
        print(f"{desc}:")
        print(f"  {old:,} → {new:,} cells")
        print(f"  Estimated runtime: {ratio:.1%} of original")

    return True


def test_report_class():
    """Test ProjectCopyReport"""
    print("\n" + "=" * 70)
    print("Test 7: ProjectCopyReport")
    print("=" * 70)

    report = ProjectCopyReport()
    report.old_extent = (640000, 263000, 642000, 265000)
    report.new_extent = (640500, 263500, 641500, 264500)
    report.old_cell_size = (1.0, 1.0)
    report.new_cell_size = (2.0, 2.0)
    report.old_grid_dims = (2000, 2000)
    report.new_grid_dims = (500, 500)
    report.runtime_ratio = 0.25
    report.files_processed = {
        'basement': 1,
        'sediment_layers': 6,
        'vectors': 2
    }
    report.warnings = [
        "Crop is close to western edge",
        "Wave station 'Station_1' falls outside new domain"
    ]

    report.print_summary()

    return True


if __name__ == "__main__":
    print("Testing CoastalmeTools project_tools utilities")

    tests = [
        ("get_project_extent", test_get_project_extent),
        ("calculate_grid_parameters", test_calculate_grid_parameters),
        ("validate_crop_bbox", test_validate_crop_bbox),
        ("get_raster_files_in_project", test_get_raster_files),
        ("check_wave_stations_in_domain", test_check_wave_stations),
        ("estimate_runtime_change", test_estimate_runtime),
        ("ProjectCopyReport", test_report_class),
    ]

    results = {}
    for name, test_func in tests:
        try:
            success = test_func()
            results[name] = success
        except Exception as e:
            print(f"\n❌ Test {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(results.values())
    print("=" * 70)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

    sys.exit(0 if all_passed else 1)
