from CoastalmeTools import Cme


# Provide path of cme ini file
ini_file = r"/home/wilfc/CoastalME/in/Exploration/Scen018/cme.ini"
# Provide path where we want cme to run, this is the --home cmd ln arg
run_path= r"/home/wilfc/CoastalME/"
# Provide path of cme executable
cme_path = r"/home/wilfc/CoastalME/cme"

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
cme.return_rescue()
# All Done
print('Done!')
