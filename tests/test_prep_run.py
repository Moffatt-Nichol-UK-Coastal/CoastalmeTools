from CoastalmeTools import *


ini_file = r"/home/wilfc/CoastalME/in/Exploration/Scen018/cme.ini"
run_path= r"/home/wilfc/CoastalME/"
cme_path = r"/home/wilfc/CoastalME/cme"

cme = Cme(ini_file, run_path)

cme.preflight_checks()

cme.run(cme_path)

pass