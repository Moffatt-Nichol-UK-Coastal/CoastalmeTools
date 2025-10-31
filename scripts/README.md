# CoastalmeTools Example Scripts

This directory contains example scripts demonstrating how to use CoastalmeTools for various workflows.

## Scripts Overview

### 1. `template_full.py` (Original - Legacy API)
**Status:** Original version using legacy `Cme` class API

The original template demonstrating the full CoastalME workflow:
- Project setup
- Configuration loading
- Simulation execution
- Result collation

**Use this if:** You have existing scripts and want to maintain compatibility.

```bash
python scripts/template_full.py
```

---

### 2. `template_full_modern.py` (NEW - Hybrid API)
**Status:** ✨ New version showcasing both legacy and modern APIs

Enhanced version demonstrating:
- **Legacy API** - Full backward compatibility with `Cme` class
- **Modern API** - Type-safe configuration system (Phase 2)
- Comprehensive logging
- Better error handling
- Structured workflow sections
- Platform detection

**Features:**
- Shows both old and new configuration access methods
- Maintains exact same functionality as original
- Adds detailed logging and progress indicators
- Demonstrates best practices
- Includes usage examples for new API

**Use this if:** You want to learn the new API while maintaining legacy workflow.

```bash
python scripts/template_full_modern.py
```

---

### 3. `config_example.py` (NEW - Modern API Only)
**Status:** ✨ New educational script for Phase 2 configuration system

Interactive examples demonstrating the new configuration API:
- **Example 1:** Basic loading and querying
- **Example 2:** Different query methods comparison
- **Example 3:** Modifying and saving configurations
- **Example 4:** Format detection (.dat vs .yaml)
- **Example 5:** Error handling
- **Example 6:** Listing all configuration keys

**Use this if:** You want to understand the new configuration system in detail.

```bash
python scripts/config_example.py
```

---

## Quick Comparison

### Legacy API (template_full.py)
```python
from CoastalmeTools import Cme

# Setup
cme = Cme(ini_file, run_path)

# Query config (using internal methods)
basement = cme.find_config("basement")

# Run simulation
cme.run(cme_path)
cme.collate_results(vars=out_vars, vars_v=out_vars_v)
```

### Modern API (template_full_modern.py)
```python
from CoastalmeTools import Cme  # Legacy - still works!
from CoastalmeTools.config import load_config  # New!

# New: Type-safe configuration
config = load_config(config_path)
basement = config.find("basement")  # Same interface
basement = config["basement"]       # Or dictionary-style

# Legacy workflow still works
cme = Cme(ini_file, run_path)
cme.run(cme_path)
```

---

## Configuration API Quick Reference

### Loading Configuration
```python
from CoastalmeTools.config import load_config

# Auto-detects .dat or .yaml format
config = load_config(Path("scenario.dat"))
```

### Querying Values
```python
# Method 1: Flexible partial matching (backward compatible)
basement = config.find("basement")
duration = config.find("Duration simulation")

# Method 2: Exact key with default
output = config.get("output folder", default="out")

# Method 3: Dictionary-style
if "start date" in config:
    start = config["start date"]
```

### Modifying Configuration
```python
# Set values
config.set("output folder", "new_output")
config["basement"] = "in/new_basement.tif"

# Check modification status
if config.is_modified:
    config.save()
```

### Inspecting Configuration
```python
# List all keys
for key in config.keys():
    print(f"{key}: {config[key]}")

# Iterate items
for key, value in config.items():
    print(f"{key} = {value}")

# Check format
print(f"Format: {config.format}")  # ConfigFormat.DAT or .YAML
```

---

## Migration Guide

### For Existing Users

Your existing scripts **continue to work without changes**. The legacy `Cme` class is fully supported:

```python
# This still works exactly as before
from CoastalmeTools import Cme
cme = Cme(ini_file, run_path)
cme.run(cme_path)
```

### Adopting New Features

Add new features incrementally:

```python
# Keep legacy workflow
from CoastalmeTools import Cme

# Add new config inspection (optional)
from CoastalmeTools.config import load_config

# Use legacy workflow
cme = Cme(ini_file, run_path)

# Add new config inspection
config = load_config(cme.in_path)
print(f"Config format: {config.format}")
print(f"Basement: {config.find('basement')}")

# Continue with legacy workflow
cme.run(cme_path)
```

---

## Benefits of Modern API

### Type Safety
```python
# Old: Runtime error if key doesn't exist
value = cme.config["nonexistent"]  # KeyError at runtime

# New: IDE autocomplete and type checking
config.find("nonexistent")  # Clear KeyError with helpful message
```

### Format Agnostic
```python
# Automatically handles both .dat and .yaml
config = load_config(path)  # Works for both formats

# Same query interface regardless of format
basement = config.find("basement")
```

### Better Error Messages
```python
# Old: Generic KeyError
# KeyError: 'key'

# New: Descriptive exceptions
# ConfigNotFoundError: Config file not found: /path/to/file.dat
# ConfigParseError: Error parsing .dat file: Invalid syntax on line 42
# KeyError: No matches for: 'nonexistent_key'
```

### Testability
```python
# New API is fully unit tested
# 61 tests covering all configuration scenarios
# See tests/unit/test_config.py
```

---

## What's Next?

The refactoring is ongoing with these future phases:

- **Phase 3:** Execution & Results (SimulationRunner, ResultProcessor)
- **Phase 4:** Simulation Orchestrator (replacing `Cme` class)
- **Phase 5:** Interactive Features & Preprocessing
- **Phase 6:** Migration Layer & Deprecation

See `REFACTORING_PLAN.md` and `PHASE_1_2_SUMMARY.md` for details.

---

## Getting Help

- **Examples:** Run `python scripts/config_example.py` for interactive demos
- **Tests:** See `tests/unit/` for usage examples
- **Docs:** See `PHASE_1_2_SUMMARY.md` for API documentation

---

## Requirements

All scripts require:
- Python 3.9+
- CoastalmeTools installed: `pip install -e .` or `uv pip install -e .`
- CoastalME executable compiled and accessible

Platform-specific paths are auto-detected for macOS and Linux.
