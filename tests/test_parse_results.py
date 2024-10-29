import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../coastalmetools")
from cme import cme
from collate_results import *
from parse_results import *

ini_file = r"/home/wilfc/CoastalME/in/Exploration/Scen013/cme.ini"
# run_path= r"/home/wilfc/CoastalME/coastalme_TESTING/"
# ini_file = r"/home/wilfc/CoastalME/in/test_suite/Happisburgh/cme.ini"
run_path= r"/home/wilfc/CoastalME/"

cme = cme(ini_file, run_path)

t = cme.out_times()
print("Expected {} timesteps".format(len(t)))

out_vars = [
     'active_zone',
    #  'actual_beach_erosion',
    #  'actual_platform_erosion',
     'avg_sea_depth',
    #  'avg_susp_sed',
     'avg_wave_height',
    #  'avg_wave_orientation',
    #  'basement_elevation',
    #  'beach_deposition',
    #  'beach_mask',
    #  'beach_protection',
    #  'cliff_collapse_erosion_coarse', 'cliff_collapse_erosion_fine', 'cliff_collapse_erosion_sand',
    #  'cliff_collapse_talus_deposition_coarse','cliff_collapse_talus_deposition_sand',
    #  'cons_sed_coarse_layer_1','cons_sed_fine_layer_1','cons_sed_sand_layer_1',
    #  'deep_water_wave_height',
    #  'deep_water_wave_orientation',
    #  'flood_ss_mask',
    #  'flood_ssr_mask',
    #  'intervention_class',
    #  'intervention_height',
    #  'inundation_mask',
     'landform_class',
    #  'local_cons_sediment_slope',
    #  'polygon_gain_or_loss',
     'polygon_raster',
    #  'polygon_updrift_or_downdrift',
    #  'potential_beach_erosion',
    #  'potential_platform_erosion',
    #  'potential_platform_erosion_mask',
     'rcoast',
     'rcoast_normal',
     'sea_depth',
    #  'sediment_top_elevation',
    #  'shadow_downdrift_zones',
     'shadow_zones',
     'susp_sed',
     'top_elevation',
     'total_actual_beach_erosion',
     'total_actual_platform_erosion',
     'total_beach_deposition',
     'total_cliff_collapse_erosion_coarse','total_cliff_collapse_erosion_fine','total_cliff_collapse_erosion_sand',
    #  'total_cliff_collapse_talus_deposition_coarse','total_cliff_collapse_talus_deposition_sand',
    #  'total_potential_beach_erosion',
    #  'total_potential_platform_erosion',
    #  'uncons_sed_coarse_layer_1','uncons_sed_fine_layer_1','uncons_sed_sand_layer_1',
     'wave_height',
     'wave_orientation',
    #  'wave_period'
     ]

out_vars_v = [
    # 'avg_wave_angle',
    'breaking_wave_height',
    'cliff_notch',
    'coast',
    'coast_curvature',
    # 'collapse_normals',
    # 'deep_water_wave_angle',
    # 'downdrift_boundary',
    'invalid_normals',
    # 'mean_wave_energy',
    # 'node',
    'normals',
#     'polygon',
    # 'shadow_boundary',
    # 'storm_surge',
    # 'wave_angle',
    'wave_energy',
    # 'wave_setup',
     ]

results = collate_results(cme.out_path, t, vars=out_vars, vars_v=out_vars_v, sed_top=True)
# explore_nc(r'/home/wilfc/CoastalME/out/Exploration/Scen008/all_vars.nc', results)
print('Done!')
