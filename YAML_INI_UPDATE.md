# YAML INI File Support - Update Summary

**Date:** 2025-10-13
**Status:** ✅ Complete

---

## 🎯 Overview

CoastalmeTools has been updated to support CoastalME's new YAML initialization file format (`cme.yaml` / `cme.yml`). This update maintains full backward compatibility with legacy `.ini` files while supporting the new YAML format.

---

## 📋 Changes Made

### 1. Updated `Cme.__init__()` in `src/CoastalmeTools/Cme.py`

**Key Modifications:**

```python
# Detect INI file format (.ini with DAT format or .yaml)
if ini.suffix == ".yaml" or ini.suffix == ".yml":
    self.ini_type = "yaml"
    self.paths_df, paths = read_yaml(ini)
else:
    # Default to .ini (DAT format)
    self.ini_type = "dat"
    self.paths_df, paths = read_ini(ini)

# Get input path - handle different key names for YAML vs DAT
try:
    input_key = find_var(paths, "input")
except KeyError:
    # Try YAML format key names
    try:
        input_key = find_var(paths, "input_data_file")
    except KeyError:
        raise ValueError("Could not find input/input_data_file key in ini file")

# Get output path - handle different key names
try:
    output_key = find_var(paths, "output")
except KeyError:
    try:
        output_key = find_var(paths, "output_path")
    except KeyError:
        raise ValueError("Could not find output/output_path key in ini file")
```

**Features:**
- ✅ Auto-detects YAML format by extension (`.yaml` or `.yml`)
- ✅ Supports legacy key names: `input` and `output`
- ✅ Supports new YAML key names: `input_data_file` and `output_path`
- ✅ Handles both absolute and relative paths correctly
- ✅ Stores INI type in `self.ini_type` attribute

---

## 📝 File Format Examples

### Legacy Format: `cme.ini`
```ini
; CoastalME initialization file
input  : /path/to/scenario.dat
output : /path/to/output/
```

### New Format: `cme.yaml`
```yaml
# CoastalME initialization file (YAML format)
input_data_file: /home/user/CoastalME_data/Cliff2/in/thorpness.yaml
output_path: /home/user/CoastalME_data/Cliff2/out/
```

### Backward Compatible YAML (legacy keys)
```yaml
# YAML with legacy key names
input: /path/to/scenario.dat
output: /path/to/output/
```

---

## 🧪 Testing

### Unit Tests Created

**File:** `tests/unit/test_cme_yaml_ini.py`

**Test Coverage:**
1. ✅ Legacy `.ini` format with DAT keys
2. ✅ YAML `.yaml` format with absolute paths
3. ✅ YAML `.yaml` format with relative paths
4. ✅ YAML INI pointing to YAML config file
5. ✅ Error handling for missing `input`/`input_data_file` key
6. ✅ Error handling for missing `output`/`output_path` key
7. ✅ Legacy keys (`input`, `output`) still work in YAML
8. ✅ `.yml` extension also recognized as YAML

**Results:** 8 new tests, all passing ✅

**Total Test Suite:** 69 tests passing (61 from Phases 1-2 + 8 new YAML INI tests)

### Real-World Validation

Tested with actual CoastalME `cme.yaml` file:

```bash
Testing with: /home/wilfchun/CoastalME/coastalme/cme.yaml
Run path: /home/wilfchun/CoastalME/coastalme

✅ Success! Cme initialized with YAML INI file

INI type: yaml
Config type: yaml
Input path: /home/wilfchun/CoastalME/CoastalME_data_local/Typology/Cliff2/in/thorpness.yaml
Output path: /home/wilfchun/CoastalME/CoastalME_data_local/Typology/Cliff2/out

Input config exists: True
Output dir exists: True
```

---

## 🔍 Implementation Details

### Path Resolution Logic

```python
# For input path
self.in_path = Path(run_path) / input_key if not Path(input_key).is_absolute() else Path(input_key)

# For output path
self.out_path = Path(run_path) / output_key if not Path(output_key).is_absolute() else Path(output_key)
```

**Behavior:**
- **Absolute paths:** Used as-is
- **Relative paths:** Resolved relative to `run_path`

### Configuration Type Detection

The code detects **two separate formats**:

1. **INI file format** (`self.ini_type`):
   - `"dat"` for `.ini` files
   - `"yaml"` for `.yaml`/`.yml` files

2. **Config file format** (`self.conf_type`):
   - `"dat"` for `.dat` configuration files
   - `"yaml"` for `.yaml`/`.yml` configuration files

This allows for mixed scenarios:
- YAML INI → DAT config
- YAML INI → YAML config
- DAT INI → DAT config (legacy)

---

## ✅ Compatibility Matrix

| INI Format | INI Keys | Config Format | Status |
|------------|----------|---------------|--------|
| `.ini` (DAT) | `input`, `output` | `.dat` | ✅ Legacy (works) |
| `.ini` (DAT) | `input`, `output` | `.yaml` | ✅ Works |
| `.yaml` | `input_data_file`, `output_path` | `.dat` | ✅ New format |
| `.yaml` | `input_data_file`, `output_path` | `.yaml` | ✅ Full YAML |
| `.yaml` | `input`, `output` | `.dat` | ✅ Backward compat |
| `.yml` | `input_data_file`, `output_path` | `.yaml` | ✅ Works |

---

## 📚 Usage Examples

### Example 1: Basic YAML INI Usage

```python
from pathlib import Path
from CoastalmeTools import Cme

# Initialize with YAML INI file
ini_file = Path("cme.yaml")
run_path = Path("/home/user/coastalme")

cme = Cme(ini=ini_file, run_path=run_path)

# Check format
print(f"INI format: {cme.ini_type}")        # "yaml"
print(f"Config format: {cme.conf_type}")    # "yaml" or "dat"

# Paths are automatically resolved
print(f"Input: {cme.in_path}")
print(f"Output: {cme.out_path}")
```

### Example 2: Legacy INI Still Works

```python
# Existing code continues to work without changes
ini_file = Path("cme.ini")
cme = Cme(ini=ini_file, run_path=run_path)

print(f"INI format: {cme.ini_type}")  # "dat"
```

### Example 3: Mixed Formats

```python
# YAML INI pointing to DAT config
# cme.yaml contains: input_data_file: in/scenario.dat
cme = Cme(ini="cme.yaml", run_path=".")

print(f"INI: {cme.ini_type}")      # "yaml"
print(f"Config: {cme.conf_type}")  # "dat"
```

---

## 🔧 Error Handling

### Missing Key Errors

The code provides clear error messages when required keys are missing:

**Missing Input Key:**
```
ValueError: Could not find input/input_data_file key in ini file
```

**Missing Output Key:**
```
ValueError: Could not find output/output_path key in ini file
```

### Key Fallback Strategy

```
1. Try "input" key (legacy)
   ↓ KeyError
2. Try "input_data_file" key (YAML)
   ↓ KeyError
3. Raise ValueError with helpful message
```

---

## 📦 Benefits

1. **✅ Full Backward Compatibility**
   - All existing `.ini` files continue to work
   - No changes needed to existing scripts

2. **✅ Future-Proof**
   - Supports new YAML format from CoastalME
   - Ready for full YAML adoption

3. **✅ Flexible**
   - Supports both absolute and relative paths
   - Works with legacy and new key names
   - Mixed format combinations supported

4. **✅ Tested**
   - 8 comprehensive unit tests
   - Validated with real CoastalME files
   - All 69 tests in suite passing

5. **✅ Clear**
   - Explicit error messages
   - Type information preserved (`ini_type`, `conf_type`)
   - Straightforward logic flow

---

## 🚀 Migration Guide

### For Existing Users

**You don't need to change anything!** Your existing `.ini` files continue to work exactly as before.

### To Adopt New YAML Format

1. **Create `cme.yaml`** instead of `cme.ini`:

```yaml
input_data_file: /path/to/scenario.yaml
output_path: /path/to/output/
```

2. **Use it the same way:**

```python
cme = Cme(ini="cme.yaml", run_path=".")
```

That's it! Everything else works identically.

---

## 📊 Test Results Summary

```
============================= test session starts ==============================
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_legacy_ini_format PASSED
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_yaml_ini_format_absolute_paths PASSED
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_yaml_ini_format_relative_paths PASSED
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_yaml_ini_with_yaml_config PASSED
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_missing_input_key_error PASSED
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_missing_output_key_error PASSED
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_legacy_keys_still_work_in_yaml PASSED
CoastalmeTools/tests/unit/test_cme_yaml_ini.py::test_yml_extension_also_works PASSED

============================== 69 passed in 1.57s ===============================
```

All tests passing! ✅

---

## 📝 Files Modified

1. **src/CoastalmeTools/Cme.py**
   - Updated `__init__()` method (lines 48-103)
   - Added YAML INI format detection
   - Added fallback key logic

2. **tests/unit/test_cme_yaml_ini.py** (NEW)
   - 8 comprehensive unit tests
   - 281 lines of test code
   - Full coverage of all scenarios

---

## 💡 Key Insights

`★ Insight ─────────────────────────────────────`
1. **Fallback Strategy**: The implementation uses try-except
   blocks to gracefully fall back from legacy to new key names,
   ensuring compatibility without complex conditional logic.

2. **Two-Level Format Detection**: Separating INI format from
   config format allows mixed scenarios and provides better
   debugging information.

3. **Path Resolution Pattern**: Checking `Path().is_absolute()`
   before joining paths prevents issues with absolute paths
   being incorrectly joined to relative base paths.
`─────────────────────────────────────────────────`

---

## ✨ What's Next?

This update is **complete and production-ready**. The implementation:

- ✅ Handles all file format combinations
- ✅ Maintains full backward compatibility
- ✅ Is fully tested (8 new tests, 69 total passing)
- ✅ Works with real CoastalME files
- ✅ Provides clear error messages

The legacy `Cme` class now seamlessly supports both `.ini` and `.yaml` initialization files with no breaking changes to existing code.

---

## 🔗 Related Documentation

- **PHASE_1_2_SUMMARY.md**: Overall refactoring progress
- **REFACTORING_PLAN.md**: Original refactoring plan
- **scripts/README.md**: Usage examples and migration guide
- **coastalme/CLAUDE.md**: CoastalME C++ engine documentation
- **CoastalmeTools/CLAUDE.md**: Python toolkit documentation
