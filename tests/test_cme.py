import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../coastalmetools")
from cme import cme


ini_file = r"/home/wilfc/coastalme_TESTING/in/test_suite/minimal_wave_angle_310/cme.ini"
run_path= r"/home/wilfc/coastalme_TESTING/"

cme = cme(ini_file, run_path)

print(cme.find_config('duration'))
print(cme.find_config('Simulation start.'))

pass


