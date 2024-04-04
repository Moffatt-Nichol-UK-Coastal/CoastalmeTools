import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../coastalmetools")
from cme import cme
from collate_results import *
from parse_results import *

ini_file = r"/home/wilfc/coastalme_TESTING/in/test_suite/minimal_wave_angle_310/cme.ini"
run_path= r"/home/wilfc/coastalme_TESTING/"

cme = cme(ini_file, run_path)

t = cme.out_times()

results = collate_results(cme.out_path, t)

parse_results(results, 'top_elevation')
