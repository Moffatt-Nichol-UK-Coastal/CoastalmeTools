import sys
import os
from CoastalmeTools import *


ini_file = r"/home/wilfc/CoastalME/in/Exploration/Scen016/cme.ini"
run_path= r"/home/wilfc/CoastalME/"

cme = Cme(ini_file, run_path)

print(cme.find_config('duration'))
print(cme.find_config('Simulation start.'))

pass


