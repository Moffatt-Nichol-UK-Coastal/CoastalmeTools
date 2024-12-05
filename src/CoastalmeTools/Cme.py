import pandas as pd
import shutil
from pathlib import Path
import re
import numpy as np
from datetime import datetime, timedelta
import glob
from pytimeparse2 import parse as timeparse
import subprocess
from .files import *
from .xml2raster import *

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

class Cme():
	"""
	Class for absorbing coastalME runs into python wrapper
	"""

	def __init__(self, ini=None, run_path=None):
		"""Sets up an object to work with a coastalMe run

		Args:
			ini (path, optional): path to cme ini file. Defaults to None.
			run_path (path where cme is run, this is equivalent to the --home command line argument, optional): _description_. Defaults to None.
		"""
		Path.cwd()
		ini = Path(ini)
		self.ini = ini
		self.exec_path = run_path
		self.paths_df, paths = read_ini(ini)
		self.in_path = Path(run_path) / find_var(paths, 'input')
		self.config_df, self.config = read_ini(self.in_path)
		self.out_path = Path(run_path) / find_var(paths, 'output')
		if os.path.exists(self.out_path):
			self.started = True
		else:  
			self.started = False

	def run(self, ex_p, ready=True):
		if not ready:
			self.preflight_checks()
		shutil.copy(self.ini, self.exec_path)
		command = f"{ex_p} --home={self.exec_path}"
		completed_process = subprocess.run(command, shell=True)
		if completed_process.returncode == 0:
			self.started = True
			self.crashed = False
		else:
			self.started = True
			self.crashed = True
		try:
			self.retrieve_log()
		except:
			pass
		return completed_process.returncode
	
	def retrieve_log(self):
		level = int(self.find_config('Content of log file'))
		dir_path = self.out_path
		found_f = glob.glob(str(dir_path/"*.log"))
		if type(found_f) == list:
			if len(found_f) == 1:
				found_f = Path(found_f[0])
			else:
				found_f = None
		else:
			found_f = None
		self.log, self.errors, self.warnings = read_log(found_f, level)

	def return_rescue(self):
		if self.crashed:
			print("")
			er =  "\n".join("ln{!r}: {!r},".format(k, v) for k, v in self.errors.items())+ "\n"
			wa = "\n".join("ln{!r}: {!r},".format(k, v) for k, v in self.warnings.items())+ "\n"
			print(bcolors.FAIL +"CoastalME has crashed, these are the errors recorded in the log file:\n {}".format(str(er)) + bcolors.ENDC)
			print(bcolors.WARNING +"CoastalME has crashed, these are the warnings recorded in the log file:\n {}".format(str(wa))+ bcolors.ENDC)
		else:
			print("Everything seemed to go okay my end!")


	def preflight_checks(self, depth=7):
		"""This can be run to aid the user in setting up a coastalMe run

		Args:
			depth (int, optional): This is the folder depth of the run TODO assign this programmatically. Defaults to 7.

		Raises:
			ValueError: _description_
		"""
		# Check if output folder exists
		if self.started:
			print("An output folder for this run already exists, CoastalME will overwrite this.")
		# get input folder path
		dir_path = self.in_path.parent
		# get list of files in input folder
		paths = glob.glob(str(dir_path/"*"))
		files = [fi.split('/')[depth] for fi in paths]
		# separate names and types
		files_n = [fi.split('.')[0] for fi in files]
		files_t = [fi.split('.')[1] for fi in files]

		# check if basement file exists
		basement_n = self.find_config('basement').split("/")[-1].split('.')[0]
		if basement_n in files_n:
			basement = True
		elif len(basement_n) < 1:
			basement = False
		else:
			basement = False

		# Would the user like to set up a quick start model
		ans = input("Would you like to generate a quick start model \n this creates a model of uniform material using a topography/batymatry .tiff file \n (Y/N) ")
		if ans == "Y":
			# Search input folder for any tiffs
			f_list = file_search(dir_path,None,'tif')
			# if there are multiple allow the user to select
			if type(f_list) == list:
				f_quest = dict(zip(range(len(f_list)),[str(x) for x in f_list]))
				ans = int(input("Which file would you like to use: {}".format(str(f_quest))))
				file = f_list[ans]
			else:
				file = f_list
			# Using the user selected file as the top elevation, generate top.asc, basement.asc
			# and capture any elevation adjustments required to prevent -ve thickness
			base_out, top_out, uplift = genBase(file,dir_path)
			print("Basement and top file created")
			# Ask the user what material they would like there layer to be
			opts = {0:"unconsolidated fine sediment",1:"unconsolidated sand sediment",2:"unconsolidated coarse sediment",3:"consolidated fine sediment",4:"consolidated sand sediment",5:"consolidated coarse sediment"}
			opts_s = "\n".join("{!r}: {!r},".format(k, v) for k, v in opts.items())+ "\n"
			layer = opts[int(input(f'What material is your layer?\n {opts_s}'))]
			for key, opt in opts.items():
				# Clear any existing layers that have been set
				self.update_config(self.config_df, f'Initial {opt} file', "")

			# Now update the .dat input file to use these new files
			self.update_config(self.config_df, 'basement', str(base_out))
			self.update_config(self.config_df, f'Initial {layer} file', str(top_out))
			self.update_config(self.config_df, 'Initial still water level', str(uplift))
		elif ans == "N":
			# raise KeyboardInterrupt('User declined assistance')
			pass
		else:
			raise ValueError("No valid response")
		
		write_ini(self.in_path,self.config_df)
		print("Saved input file")



	def find_config(self, query):
		return find_var(self.config, query)

	def update_config(self, df, query, value):
		mask = df['key'].str.contains(query, case=False, na=False)
		entries = df[mask]
		if len(entries) == 1:
			df.loc[mask,'value'] = value
			df.loc[mask,"modified"] = True
			pass
		else:
			raise ValueError("Input file not correctly formated")
		return 
	
	def out_times(self):
		"""Get all the save times intended to be generated by coastalME

		Returns:
			list: list of all save points in simulation time
		"""
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
	
	def collate_results(self,vars=['all'],vars_v=['all']):
		# Check if CME has been run
		if self.started:
			try:
				crashed = self.crashed
			except AttributeError:
				crashed = False
		else:
			return ValueError("Simulation not run, please run coastalme before using this command")
		path = self.out_path
		# Find expected output save points
		t = self.out_times()
		print("Expected {} timesteps".format(len(t)))
		# using basement outputs, find how many have been produced
		finder = str(path/'basement_elevation*.tif')
		completed = len(glob.glob(finder))
		# Test if we have the expected number of outputs
		if completed == len(t):
			self.success = True
		else:
			# If not we know that cme crashed, save that fact and alter the number of outputs we are looking at
			self.success = False
			crashed = True
			t = t[:completed]
			print("found {} timesteps".format(len(t)))
		# how many different saves are we dealing with
		itters = len(t)
		# If cme crashed, add a fake extra timestep to store the crash outputs
		if crashed:
			delta = t[-1] - t[-2]
			faux = t[-1] + delta
			t.append(faux)
			# t.append(datetime(9999, 9, 9, 0, 0))
		# Now we will collect all the raster and vector files in the output directory
		df = collect_files(itters, path, 'tif')
		df_v = collect_files(itters, path, 'shp')


		# test if the user requested the basement elevation output
		if 'basement_elevation' not in vars:
			# if not, add it as it will be used to define our ncdf extents
			vars.append('basement_elevation')

		# collate all vector outputs into a file
		vectors(t, df_v,path,vars_v)
		# collate all raster outputs into a file
		rasters(t, df,path,vars, crashed=crashed,)
		# Generate plots of any profiles that have been output
		profiles(t, path)

def read_log(path, level, verbose=True):
	if not os.path.exists(path):
		return FileNotFoundError
	with open(path, 'r') as f:
		file = f.read().splitlines()
	if level >= 1:
		error_lines = {idx: x for idx, x in enumerate(file) if 'ERROR' in x}
		error_count = len(error_lines)
		warning_lines = {idx: x for idx, x in enumerate(file) if 'WARNING' in x}
		warning_count = len(warning_lines)
	if level >= 2:
		pass
	if level >= 3:
		pass
	if verbose:
		print(f'Log file found containing {error_count} errors, and {warning_count} warnings')
	return file, error_lines, warning_lines


def read_ini(path):
	#What are we reading
	p_type = str(path).split('.')[1]
	if not os.path.exists(path):
		# raise FileNotFoundError("No input .dat file in this folder")
		print("No input .{} file in this folder".format(p_type))
		src = Path(str(input("Please provide the path to a template input: ")))
		shutil.copyfile(src, path)
		print("template coppied")

	with open(path, 'r') as f:
		# Get each line from the ini file
		file = f.read().splitlines()
		# Assign numbers to these lines so we can reconstruct
		lines = range(len(file))
		reference = dict(zip(lines, file))
		# save to dataframe
		df = pd.DataFrame(file, index=lines, columns=['string'])
		# Categorise each of the line
		df['type'] = "setting"
		mask = (df.string.str.startswith(';')) | (df.string.str.startswith('#'))
		df.loc[mask, 'type'] = 'comment'
		mask = (df.string == "")
		df.loc[mask, 'type'] = 'blank'

		# now focus on the lines actually containing settings
		mask = (df.type == "setting")
		df['key'] = None
		df['value'] = None
		df['modified'] = False
		content = df.loc[mask, "string"]
		df.loc[mask, "key"] = df['string'].map(lambda x: parse_line(x)[0])
		df.loc[mask, "value"] = df['string'].map(lambda x: parse_line(x)[1])
		vars = dict(zip(list(df.loc[mask, "key"].values),list(df.loc[mask, "value"].values)))
	return df, vars

def write_ini(path, df):
	"""This saves any changes to a coastalme input file that have been made

	Args:
		path (string): save path (including file name)
		df (pandas dataframe): dataframe in format read from template file, any changed settings in key, value column are incorporated
	"""
	changed = (~df.key.isnull())
	# changed = (df['modified'])
	l  = max([len(x) for x in df['key'] if x])
	df.loc[changed, 'string'] = df[changed].apply(lambda row: f'{row['key']:{l}} : {row['value']}', axis=1)

	out_lines = df['string'].to_list()
	with open(str(path), mode='wt', encoding='utf-8') as f:
		f.write('\n'.join(out_lines))

def parse_line(in_str):
	split = in_str.partition(':')
	split = [x.strip() for x in split]
	split = [x for x in split if not x==':']
	split = [re.sub(' +', ' ', x) for x in split]
	return split


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