import sys
import os
# sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../coastalmetools")
# from cme import cme
from CoastalmeTools import *


ini_file = r"/home/wilfc/CoastalME/in/Exploration/Scen016/cme.ini"
run_path= r"/home/wilfc/CoastalME/"

cme = Cme(ini_file, run_path)

print(cme.find_config('duration'))
print(cme.find_config('Simulation start.'))

pass


