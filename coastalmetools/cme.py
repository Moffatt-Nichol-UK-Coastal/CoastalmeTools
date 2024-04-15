import pandas as pd
from pathlib import Path
import re
import numpy as np
from datetime import datetime, timedelta
# from pytimeparse.timeparse import timeparse
from pytimeparse2 import parse as timeparse

class cme():
    """
    Class for absorbing coastalME runs into python wrapper
    """

    def __init__(self, ini=None, run_path=None):
        Path.cwd()
        ini = Path(ini)
        paths = read_ini(ini)
        self.in_path = Path(run_path) / find_var(paths, 'input')
        self.config = read_ini(self.in_path)
        self.out_path = Path(run_path) / find_var(paths, 'output')
        pass

    def find_config(self, query):
         return find_var(self.config, query)

    def out_times(self):
        start = find_var(self.config, 'Simulation start date')
        duration = find_var(self.config, 'Duration of simulation')
        t_steps = find_var(self.config, 'Timestep ', case=True)
        steps_p = find_var(self.config, 'save times')


        start = datetime.strptime(start, '%H-%M-%S %m/%d/%Y')
        duration = timedelta(seconds=timeparse(duration))
        end = start + duration
        steps = steps_p.split(' ')
        unit = steps[-1]
        steps = [x+' '+unit for x in steps[0:-1]]
        if len(steps) == 1:
            save_itter = timedelta(seconds=timeparse(steps_p))
            steps = np.arange(start,end,save_itter).astype(datetime).tolist()
            steps.append(end)
            steps.pop(0)
            saves = steps
        else:
            steps = [timedelta(seconds=timeparse(x)) for x in steps]

            saves = [start + x for x in steps]

            saves = [x for x in saves if x <= end]

        return saves

def read_ini(path):
    with open(path, 'r') as f:
        file = f.read().splitlines()
        content = [x for x in file if not x.startswith(';')]
        content = [x for x in content if not x.startswith('#')]
        content = [x for x in content if not x=='']
        vars = {}
        for entry in content:
            split = entry.partition(':')
            split = [x.strip() for x in split]
            split = [x for x in split if not x==':']
            split = [re.sub(' +', ' ', x) for x in split]
            if len(split) == 2:
                vars[split[0]] = split[1]
            pass
    return vars

def find_var(dict, query, case=False):
        if case:
            results = {key: val for key, val in dict.items() if re.search(query, key)}
        else:
            results = {key: val for key, val in dict.items() if re.search(query, key, re.I)}
        if len(results) == 0:
            raise KeyError('No matches for: {}'.format(query))
        if len(results) != 1:
            raise KeyError('Multiple matches for variable in input file: {}'.format(list(results.keys())))
        
        out = next(iter(results.values()))

        if ';' in out:
            out = out.partition(';')[0]
        
                
        return out 

