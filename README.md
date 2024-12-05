# CoastalmeTools

## What is it?
Python tools to work with [CoastalME](https://github.com/coastalme/coastalme)

>CoastalME (Coastal Modelling Environment) is a Free and Open Source software for geospatial modelling to simulate decadal and longer coastal morphological changes.
>
>It is an engineering tool for advanced modellers seeking to simulate the interaction of multiple coastal landforms and different types of human interventions.

This is very much in active development

Current supported features as of version 0.0.1
- Building a single netCDF file out of raster CME results
- Building a single GeoPackage of all vector results
- CoastalMe Quickstart
   - checking if inputs exist
   - generating a basement and top file for a single layer run of coastalme using topo/bathy data (*.tiff)
- Running CoastalMe, specifying executable directory (useful if testing development versions
- Generating a basement and top file from a landXML file (useful for rapid generation of test cases)
  

## Installation
Binary distributions (wheels) are available from the [releases](https://github.com/wilfchun/CoastalmeTools/releases) tab of this repository.
Please download and install running the following form the directory containing the downloaded wheel.

```sh
    pip install CoastalmeTools-0.0.0-py3-none-any.whl
```

CoastalmeTools requires Python 3.12 or higher

## Python Usage

```py
from CoastalmeTools import Cme

# Provide path of cme ini file
ini_file = r"tests/CoastalME/in/Exploration/Scen018/cme.ini"
# Provide path where we want cme to run, this is the --home cmd ln arg
run_path= r"tests/CoastalME/"
# Provide path of cme executable
cme_path = r"tests/CoastalME/coastalme/cme"

# Setup
cme = Cme(ini_file, run_path)

# check if were good to run, also do we want to do quick start
cme.preflight_checks()

# Now we run cme
cme.run(cme_path)

out_vars = [
     'landform_class',
     'polygon_raster',
     'rcoast',
     'rcoast_normal',
     'top_elevation',
     'total_actual_beach_erosion',
     'total_actual_platform_erosion',
     'wave_height',
     ]

out_vars_v = [
    'breaking_wave_height',
    'cliff_notch',
    'coast',
    'coast_curvature',
    'invalid_normals',
    'normals',
    'wave_energy',
     ]

# Generate netcdf
results = cme.collate_results(vars=out_vars, vars_v=out_vars_v)
# All Done
print('Done!')
```