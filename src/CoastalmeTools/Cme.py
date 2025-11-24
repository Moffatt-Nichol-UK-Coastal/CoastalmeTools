import pandas as pd
import shutil
from pathlib import Path
import re
import numpy as np
from datetime import datetime, timedelta
import glob
import os
import logging
from pytimeparse2 import parse as timeparse
from contextlib import chdir
import subprocess
from windrose import WindroseAxes
import matplotlib
import yaml
from bokeh.command.bootstrap import main

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .files import collect_files, vectors, rasters, profiles, file_search
from .xml2raster import genBase
from .hydro import wave_read

# from .monitor import monitor_run
from .tools import find_var

# Get module logger (inherits from package-level configuration)
logger = logging.getLogger(__name__)


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Cme:
    """
    Class for absorbing coastalME runs into python wrapper
    """

    def __init__(self, ini=None, run_path=None):
        """Sets up an object to work with a coastalMe run

        Args:
            ini (path, optional): path to cme ini/yaml file. Defaults to None.
                Can be either:
                - .ini file (legacy DAT format with key : value pairs)
                - .yaml file (modern YAML format with nested structure)
            run_path (path where cme is run, this is equivalent to the --home command line argument, optional): _description_. Defaults to None.
        """
        Path.cwd()
        ini = Path(ini)
        self.ini = ini
        self.exec_path = Path(run_path)

        # Detect INI file format (.ini with DAT format or .yaml)
        if ini.suffix == ".yaml" or ini.suffix == ".yml":
            self.ini_type = "yaml"
            self.paths_df, paths = read_yaml(ini)
        else:
            # Default to .ini (DAT format)
            self.ini_type = "dat"
            self.paths_df, paths = read_ini(ini)

        # Get input path - handle different key names for YAML vs DAT
        try:
            input_key = find_var(paths, "input")
        except KeyError:
            # Try YAML format key names
            try:
                input_key = find_var(paths, "input_data_file")
            except KeyError:
                raise ValueError("Could not find input/input_data_file key in ini file")

        self.in_path = Path(run_path) / input_key if not Path(input_key).is_absolute() else Path(input_key)

        # Lets get the type of input that we are using
        if self.in_path.suffix == ".dat":
            self.conf_type = "dat"
            self.config_df, self.config = read_ini(self.in_path)
        elif self.in_path.suffix == ".yaml" or self.in_path.suffix == ".yml":
            self.conf_type = "yaml"
            self.config_df, self.config = read_yaml(self.in_path)
        else:
            raise ValueError(f"Unsupported config format: {self.in_path.suffix}")

        # Get output path - handle different key names
        try:
            output_key = find_var(paths, "output")
        except KeyError:
            try:
                output_key = find_var(paths, "output_path")
            except KeyError:
                raise ValueError("Could not find output/output_path key in ini file")

        self.out_path = Path(run_path) / output_key if not Path(output_key).is_absolute() else Path(output_key)

        if os.path.exists(self.out_path):
            self.started = True
        else:
            self.started = False

    def tide_check(self, head_lines=9, t_step=6):
        tides_p = self.in_path.parent / self.find_config("tide_data")
        # with open(tides_p, 'r') as f:
        # 	file = f.read().splitlines()
        # 	header = file[0:head_lines]
        w_path = self.in_path.parent / "tides_plot.png"
        tides = pd.read_csv(
            tides_p, sep=",", header=0, names=["swl"]
        )  # , skiprows=head_lines-1)
        tides["times"] = pd.date_range("1990-1-1", periods=len(tides), freq="6h")
        tides = tides.set_index("times", drop=True)
        tides.plot()
        plt.savefig(w_path)
        pass

    def wave_check(self, invert=False, grib_read=None, cco_read=None, head_lines=4):
        """This plots a wave rose of the input wave files, there is also an ability to make minor adjustments to the wave data
            NOTE in cme: Deep water wave orientation in input CRS: this is the oceanographic convention
            i.e. direction TOWARDS which the waves move (in degrees clockwise from north)

        Args:
            invert (bool, optional): _description_. Defaults to False.
        """
        waves_p = self.in_path.parent / self.find_config("wave height time series")
        out_suf = ""
        with open(waves_p, "r") as f:
            file = f.read().splitlines()
            header = file[0:head_lines]

        lines = range(len(header))
        df = pd.DataFrame(header, index=lines, columns=["string"])
        # Categorise each of the line
        df["type"] = "setting"
        mask = (df.string.str.startswith(";")) | (df.string.str.startswith("#"))
        df.loc[mask, "type"] = "comment"
        mask = df.string == ""
        df.loc[mask, "type"] = "blank"

        # now focus on the lines actually containing settings
        mask = df.type == "setting"
        df["key"] = None
        df["value"] = None
        df["modified"] = False
        content = df.loc[mask, "string"]
        df.loc[mask, "key"] = df["string"].map(lambda x: parse_line(x)[0])
        df.loc[mask, "value"] = df["string"].map(lambda x: parse_line(x)[1])
        vars = dict(
            zip(list(df.loc[mask, "key"].values), list(df.loc[mask, "value"].values))
        )
        cco_read = True

        if grib_read:
            dir_path = self.in_path.parent
            wave_path = glob.glob(str(dir_path / "*.grib"))[0]
            geo_loc, waves = wave_read(wave_path)
            waves.to_csv(waves_p, sep=",", header=0, index=False)

            with open(waves_p, "r") as f:
                temp = f.read().splitlines()
            n_lines = len(temp)
            vars["Number of time steps"] = str(n_lines)
            header = [f"{x}:{y}" for x, y in vars.items()]
            head_lines = len(header)
            out_lines = header + temp

            with open(waves_p, mode="wt", encoding="utf-8") as f:
                f.write("\n".join(out_lines))
        elif cco_read:
            ts = 6
            cco_path = file_search(self.in_path.parent, "wave", "txt")
            if cco_path is None:
                raise FileNotFoundError("No wave data file found matching 'wave*.txt'")
            waves = pd.read_csv(
                cco_path,
                sep="\t",
                # header=True,
                # names=["height", "orientation", "period"],
                # skiprows=head_lines - 1,
            )
            waves = waves[
                ["Date/Time (GMT)", "Hs (Hm0)(m)", "Dirp (degrees)", "Tp (s)"]
            ]
            waves = waves.rename(
                columns={
                    "Date/Time (GMT)": "time",
                    "Hs (Hm0)(m)": "height",
                    "Dirp (degrees)": "orientation",
                    "Tp (s)": "period",
                }
            )
            waves["time"] = pd.to_datetime(waves["time"])
            waves = waves.astype(
                {
                    "height": np.float64,
                    "orientation": np.float64,
                    "period": np.float64,
                }
            )
            waves = waves.set_index("time")
            mask = np.abs(waves) > 900
            waves[mask] = np.nan
            waves = waves.dropna()
            waves = waves.asfreq(f"{ts}h", method="bfill")

        else:
            waves = pd.read_csv(
                waves_p,
                sep=",",
                header=0,
                names=["height", "orientation", "period"],
                skiprows=head_lines - 1,
            )
        if invert:
            waves.orientation = waves.orientation + 180
            mask = waves.orientation > 360
            waves.loc[mask, "orientation"] = waves.orientation - 360
            waves.to_csv(waves_p, sep=",", header=0, index=False)

            with open(waves_p, "r") as f:
                temp = f.read().splitlines()
            out_lines = header + temp

            with open(waves_p, mode="wt", encoding="utf-8") as f:
                f.write("\n".join(out_lines))

            out_suf = "_cor"

        w_path = self.in_path.parent / f"wave_rose{out_suf}.png"
        ax = WindroseAxes.from_ax()
        ax.bar(waves.orientation, waves.height, normed=True, opening=0.8)
        ax.set_legend()
        plt.savefig(w_path)

        pass

    def run(
        self,
        ex_p,
        ready=True,
        clear=True,
    ):
        """Wrapper to run CoastalMe

        Args:
            ex_p (path): path to cme executable
            ready (bool, optional): is the model ready to run, or do we want to run preflight checks?. Defaults to True.
            clear (bool, optional): Do we want to clear the output directory before we run. Defaults to True.

        Returns:
            int: return code from CME run
        """

        if not ready:
            self.preflight_checks()
        if clear:
            try:
                shutil.rmtree(self.out_path)
            except FileNotFoundError:
                pass
            os.makedirs(self.out_path)
        try:
            shutil.copy(self.ini, self.exec_path)
        except shutil.SameFileError:
            pass

        # Lets put together our CME run command
        params = [str(ex_p)]
        # params.append(f"--home={str(self.exec_path)}")
        # params.append("--yaml")
        try:
            with chdir(self.exec_path):
                completed_process = subprocess.Popen(params, shell=False)

            # Wait and setup our monitoring proccess for run in the background
            # Use __file__ to find monitor.py relative to this module
            m_path = Path(__file__).parent / "monitor.py"
            start_time = self.get_model_start().timestamp()
            # Start our monitoring
            monitor_proccess = subprocess.Popen(
                [
                    "bokeh",
                    "serve",
                    "--show",
                    m_path,
                    "--args",
                    str(self.out_path),
                    str(start_time),
                ]
            )

            # Wait untill CME run ends then sent stop event to bg thread
            completed_process.communicate()
            monitor_proccess.kill()
        except KeyboardInterrupt:
            # Ensure that we are killing all proccesses when we crash out
            completed_process.kill()
            monitor_proccess.kill()

        # See what the outcome of the CME run is
        if completed_process.returncode == 0:
            self.started = True
            self.crashed = False
        else:
            self.started = True
            self.crashed = True
        try:
            self.retrieve_log()
        except (FileNotFoundError, OSError) as e:
            logger.warning(f"Could not retrieve log file: {e}")
        return completed_process.returncode

    def retrieve_log(self):
        """Find the log file and save its contents along with any errors or warnings"""
        # Try YAML format first, then fall back to .dat format
        try:
            level = int(self.find_config("log_file_detail"))
        except KeyError:
            try:
                level = int(self.find_config("Content of log file"))
            except KeyError:
                logger.warning("Could not find log file detail setting in config")
                level = 1  # Default to minimal logging

        dir_path = self.out_path
        found_f = glob.glob(str(dir_path / "*.log"))
        if type(found_f) == list:
            if len(found_f) == 1:
                found_f = Path(found_f[0])
            else:
                found_f = None
        else:
            found_f = None
        self.log, self.errors, self.warnings = read_log(found_f, level)

    def return_rescue(self):
        """Use this to print a coloured summery of any errors in the log file if cme crashed"""
        # Check if we have crash information available
        if not hasattr(self, "crashed"):
            return

        if not hasattr(self, "errors") or not hasattr(self, "warnings"):
            logger.warning("Log file information not available")
            return

        if self.crashed:
            print("")
            er = (
                "\n".join("ln{!r}: {!r},".format(k, v) for k, v in self.errors.items())
                + "\n"
            )
            wa = (
                "\n".join(
                    "ln{!r}: {!r},".format(k, v) for k, v in self.warnings.items()
                )
                + "\n"
            )
            print(
                bcolors.FAIL
                + "CoastalME has crashed, these are the errors recorded in the log file:\n {}".format(
                    str(er)
                )
                + bcolors.ENDC
            )
            print(
                bcolors.WARNING
                + "CoastalME has crashed, these are the warnings recorded in the log file:\n {}".format(
                    str(wa)
                )
                + bcolors.ENDC
            )
        else:
            print("Everything seemed to go okay my end!")

    def preflight_checks(self):
        """This can be run to aid the user in setting up a coastalMe run

        Raises:
            ValueError: If user provides invalid input
        """
        # Check if output folder exists
        if self.started:
            print(
                "An output folder for this run already exists, CoastalME will overwrite this."
            )
        # get input folder path
        dir_path = self.in_path.parent
        # get list of files in input folder
        paths = glob.glob(str(dir_path / "*"))
        # Extract just the filename from each path using Path
        files = [Path(fi).name for fi in paths]
        # separate names and types
        files_n = [fi.split(".")[0] if "." in fi else fi for fi in files]
        files_t = [
            fi.split(".")[1] if "." in fi and len(fi.split(".")) > 1 else ""
            for fi in files
        ]

        # check if basement file exists
        basement_n = self.find_config("basement").split("/")[-1].split(".")[0]
        if basement_n in files_n:
            basement = True
        elif len(basement_n) < 1:
            basement = False
        else:
            basement = False

        # Would the user like to set up a quick start model
        print(f"We are curently working in {self.in_path}")
        try:
            ans = input(
                "Would you like to generate a quick start model \n this creates a model of uniform material using a topography/bathymatry .tiff file \n (Y/N) "
            )
        except EOFError:
            logger.info("Skipping interactive preflight checks (non-interactive mode)")
            return
        if ans == "Y" or ans == "y":
            # Search input folder for any tiffs
            f_list = file_search(dir_path, None, "tif")
            # if there are multiple allow the user to select
            if type(f_list) is list:
                f_quest = dict(zip(range(len(f_list)), [str(x) for x in f_list]))
                ans = int(
                    input("Which file would you like to use: {}".format(str(f_quest)))
                )
                file = f_list[ans]
            else:
                file = f_list
            # Using the user selected file as the top elevation, generate top.asc, basement.asc
            # and capture any elevation adjustments required to prevent -ve thickness
            base_out, top_out, uplift = genBase(file, dir_path)
            print("Basement and top file created")
            # Ask the user what material they would like there layer to be
            opts = {
                0: "unconsolidated fine sediment",
                1: "unconsolidated sand sediment",
                2: "unconsolidated coarse sediment",
                3: "consolidated fine sediment",
                4: "consolidated sand sediment",
                5: "consolidated coarse sediment",
            }
            opts_s = (
                "\n".join("{!r}: {!r},".format(k, v) for k, v in opts.items()) + "\n"
            )
            layer = opts[int(input(f"What material is your layer?\n {opts_s}"))]
            for key, opt in opts.items():
                # Clear any existing layers that have been set
                self.update_config(self.config_df, f"Initial {opt} file", "")

            # Now update the .dat input file to use these new files
            self.update_config(self.config_df, "basement", str(base_out))
            self.update_config(self.config_df, f"Initial {layer} file", str(top_out))
            self.update_config(self.config_df, "Initial still water level", str(uplift))
        elif ans == "N":
            # raise KeyboardInterrupt('User declined assistance')
            pass
        else:
            raise ValueError("No valid response")

        ans = input("Would you like to produce a wave rose (Y/N) ")
        if ans == "Y":
            ans = input("Do you have a grib file that you would like to read? (Y/N)")
            if ans == "Y":
                self.wave_check(invert=False, grib_read=True)
                print("Please check the wave rose saved into the run input folder")
                ans = input("Do the wave direction convention need correcting? (Y/N)")
                self.wave_check(invert=True)
            if ans == "N":
                try:
                    self.wave_check()
                    print("Please check the wave rose saved into the run input folder")
                    ans = input(
                        "Do the wave direction convention need correcting? (Y/N)"
                    )
                    self.wave_check(invert=True)
                except FileNotFoundError:
                    print("No wave file found")

        # Save changes to config file
        if self.conf_type == "dat":
            write_ini(self.in_path, self.config_df)
            print("Saved input file")
        elif self.conf_type == "yaml":
            write_yaml(self.in_path, self.config_df)
            print("Saved YAML configuration file")
        else:
            logger.warning(
                f"Unknown config type: {self.conf_type}. "
                "Changes were not saved to file."
            )

    def find_config(self, query):
        """This is used to query a setting in the current coastalme run file

        Args:
            query (string): this is a string that will be searched through the settings file

        Returns:
            string: current value of CME setting
        """
        return find_var(self.config, query)

    def update_config(self, df, query, value, save=False):
        """Use this to update the internal settings of coastaleme, note that this doesn't, by default save this out to the config file

        Args:
            df (pandas dataframe): this is the settings dataframe containing the setting we are going to change
            query (string): this is a string that will be matched in the settings file
            value (str): This is the value that the setting will be changed to
            save (bool): if True, immediately write changes to file (works for both .dat and .yaml)

        Raises:
            ValueError: If query matches multiple entries or no entries
        """
        if type(value) != str:
            value = str(value)
        mask = df["key"].str.contains(query, case=False, na=False)
        entries = df[mask]
        if len(entries) == 1:
            df.loc[mask, "value"] = value
            df.loc[mask, "modified"] = True
            pass
        else:
            raise ValueError("Input file not correctly formated")
        if save:
            if self.conf_type == "dat":
                write_ini(self.in_path, df)
            elif self.conf_type == "yaml":
                write_yaml(self.in_path, df)
            else:
                logger.warning(
                    f"Unknown config type: {self.conf_type}. "
                    "Changes are in memory only."
                )

    def out_times(self):
        """Get all the save times intended to be generated by coastalME

        Returns:
            list: list of all save points in simulation time
        """
        start = find_var(self.config, "start date")
        duration = find_var(self.config, "Duration of simulation")
        # t_steps = find_var(self.config, "Timestep ", case=True)
        steps_p = find_var(self.config, "save times")

        start = datetime.strptime(start, "%H-%M-%S %m/%d/%Y")
        duration = timedelta(seconds=timeparse(duration))
        end = start + duration
        try:
            step_units = steps_p.split(",")
        except AttributeError:
            step_units = steps_p
        steps = []
        for unit_out in step_units:
            unit_out = unit_out.strip()
            this_steps = unit_out.split(" ")
            unit = this_steps[-1]
            these_steps = [x + " " + unit for x in this_steps[0:-1]]
            steps = steps + these_steps
        if len(steps) > 1:
            # handle the defined save times
            steps = [timedelta(seconds=timeparse(x)) for x in steps]
            # saves = [start + x for x in steps]
            # saves = [x for x in saves if x <= end]

            # handle the repeted trailing save itter
            save_itter = steps[-1]
            steps.pop(-1)
            trailing_save_steps = (
                np.arange(start, end, save_itter).astype(datetime).tolist()
            )
            trailing_save_steps.pop(0)
            saves = [start + x for x in steps]
            saves = saves + trailing_save_steps + [end]

        elif len(steps) == 1:
            steps_p = steps_p[0]
            save_itter = timedelta(seconds=timeparse(steps_p))
            steps = np.arange(start, end, save_itter).astype(datetime).tolist()
            steps.append(end)
            steps.pop(0)
            saves = steps
        else:
            raise ValueError

        return saves

    def collate_results(self, vars=["all"], vars_v=["all"]):
        """Collect all the results in the output folder and combine them into a more useful format

        Args:
            vars (list, optional): list of the raster output names that will be include. Defaults to ['all'].
            vars_v (list, optional): list of the vector output names that will be include. Defaults to ['all'].
        """
        # Check if CME has been run
        if self.started:
            crashed = getattr(self, "crashed", False)
        else:
            return ValueError(
                "Simulation not run, please run coastalme before using this command"
            )
        path = self.out_path
        # Find expected output save points
        t = self.out_times()
        logger.info(f"Expected {len(t)} timesteps")
        # using basement outputs, find how many have been produced
        finder = str(path / "basement_elevation*.tif")
        completed = len(glob.glob(finder))
        # Test if we have the expected number of outputs
        if completed == len(t):
            self.success = True
        else:
            # If not we know that cme crashed, save that fact and alter the number of outputs we are looking at
            self.success = False
            crashed = True
            t = t[:completed]
            logger.warning(
                f"Found only {len(t)} timesteps (expected {len(t) + (len(t) - completed)})"
            )
        # how many different saves are we dealing with
        itters = len(t)
        if len(t) < 2:
            raise ValueError(
                "Not enough outputs to collate, probably an issue with CME"
            )
        # If cme crashed, add a fake extra timestep to store the crash outputs
        if crashed:
            delta = t[-1] - t[-2]
            faux = t[-1] + delta
            t.append(faux)
        # Now we will collect all the raster and vector files in the output directory
        df = collect_files(itters, path, "tif")
        df_v = collect_files(itters, path, "shp")

        # test if the user requested the basement elevation output
        if "basement_elevation" not in vars:
            # if not, add it as it will be used to define our ncdf extents
            vars.append("basement_elevation")

        # collate all vector outputs into a file
        vectors(t, df_v, path, vars_v)
        # collate all raster outputs into a file
        rasters(
            t,
            df,
            path,
            vars,
            crashed=crashed,
        )
        # Generate plots of any profiles that have been output
        profiles(t, path)  # , df)

    def build_model(self):
        start = find_var(self.config, ["start", "date"])
        start = datetime.strptime(start, "%H-%M-%S %m/%d/%Y")
        # what are our different layer options
        fractions = ["coarse", "sand", "fine"]
        stiffness = ["_consolidated", "unconsolidated"]
        stiffness_sh = ["cons", "uncons"]

        # Use Path for proper path handling
        base_dir = self.in_path.parent

        files = {"basement_elevation": [[str(base_dir / self.find_config("basement"))]]}

        # Now lest look at all possible combonations of these layer options
        for stiffnes, stiffnes_sh in zip(stiffness, stiffness_sh):
            for fraction in fractions:
                layer_sh = stiffnes_sh + "_sed_" + fraction + "_layer_1"
                layer_p = self.find_config([stiffnes, fraction])
                if len(layer_p) > 2:
                    files[layer_sh] = [[str(base_dir / layer_p)]]
        df = pd.DataFrame.from_dict(files, orient="index")
        df = df.reset_index()
        df = df.set_axis(["variables", "paths"], axis=1)
        # what vars do we have on start
        rasters([start], df, self.in_path.parent, [], sed_top=True)
        pass

    def get_model_start(self):
        start = find_var(self.config, "start date")
        start = datetime.strptime(start, "%H-%M-%S %m/%d/%Y")
        return start


def monitor_run(stop_event):
    # Use __file__ to find the module directory
    module_dir = Path(__file__).parent
    with chdir(module_dir):
        main(["bokeh", "serve", "--show", "monitor.py"])


def read_log(path, level, verbose=True):
    """read a coastalme log file

    Args:
        path (string): path to output file including file name (or None if not found)
        level (int): the log level specified in the coastalme run
        verbose (bool, optional): do we want to print a one line summary of the log. Defaults to True.

    Returns:
        tuple: (file_lines, error_lines_dict, warning_lines_dict)
    """
    if path is None or not os.path.exists(path):
        logger.warning("Log file not found")
        return [], {}, {}
    with open(path, "r") as f:
        file = f.read().splitlines()
    if level >= 1:
        error_lines = {idx: x for idx, x in enumerate(file) if "ERROR" in x}
        error_count = len(error_lines)
        warning_lines = {idx: x for idx, x in enumerate(file) if "WARNING" in x}
        warning_count = len(warning_lines)
    if level >= 2:
        pass
    if level >= 3:
        pass
    if verbose:
        logger.info(
            f"Log file found containing {error_count} errors, and {warning_count} warnings"
        )
    return file, error_lines, warning_lines


def read_ini(path):
    """read a coastalme input file, either an .ini or a .dat

    Args:
        path (path): path to file to be read

    Returns:
        df: dataframe containing settings
    """
    # What are we reading
    p_type = str(path).split(".")[1]
    if not os.path.exists(path):
        # raise FileNotFoundError("No input .dat file in this folder")
        print("No input .{} file in this folder".format(p_type))
        src = Path(str(input("Please provide the path to a template input: ")))
        shutil.copyfile(src, path)
        print("template copied")

    with open(path, "r") as f:
        # Get each line from the ini file
        file = f.read().splitlines()
        # Assign numbers to these lines so we can reconstruct
        lines = range(len(file))
        reference = dict(zip(lines, file))
        # save to dataframe
        df = pd.DataFrame(file, index=lines, columns=["string"])
        # Categorise each of the line
        df["type"] = "setting"
        mask = (df.string.str.startswith(";")) | (df.string.str.startswith("#"))
        df.loc[mask, "type"] = "comment"
        mask = df.string == ""
        df.loc[mask, "type"] = "blank"

        # now focus on the lines actually containing settings
        mask = df.type == "setting"
        df["key"] = None
        df["value"] = None
        df["modified"] = False
        content = df.loc[mask, "string"]
        df.loc[mask, "key"] = df["string"].map(lambda x: parse_line(x)[0])
        df.loc[mask, "value"] = df["string"].map(lambda x: parse_line(x)[1])
        vars = dict(
            zip(list(df.loc[mask, "key"].values), list(df.loc[mask, "value"].values))
        )
    return df, vars


def write_ini(path, df):
    """This saves any changes to a coastalme input file that have been made

    Args:
        path (string): save path (including file name)
        df (pandas dataframe): dataframe in format read from template file, any changed settings in key, value column are incorporated
    """
    changed = ~df.key.isnull()
    # changed = (df['modified'])
    l = max([len(x) for x in df["key"] if x])
    df.loc[changed, "string"] = df[changed].apply(
        lambda row: f"{row['key']:{l}} : {row['value']}", axis=1
    )

    out_lines = df["string"].to_list()
    with open(str(path), mode="wt", encoding="utf-8") as f:
        f.write("\n".join(out_lines))


def parse_line(in_str):
    split = in_str.partition(":")
    split = [x.strip() for x in split]
    split = [x for x in split if not x == ":"]
    split = [re.sub(" +", " ", x) for x in split]
    return split


def read_yaml(path):
    """read a coastalme input file, in yaml format
    Args:
        path (path): path to file to be read

    Returns:
        df: dataframe containing settings
    """
    # What are we reading
    p_type = str(path).split(".")[1]
    if not os.path.exists(path):
        # raise FileNotFoundError("No input .dat file in this folder")
        print("No input .{} file in this folder".format(p_type))
        src = Path(str(input("Please provide the path to a template input: ")))
        shutil.copyfile(src, path)
        print("template copied")

    with open(path, "r") as f:
        # Read yaml
        config = yaml.safe_load(f)
        data = {"section": [], "key": [], "value": []}
        # Handle both flat and nested YAML structures
        for key, value in config.items():
            if type(value) is dict:
                # Nested structure (2-tier or 3-tier)
                for keyy, valuee in value.items():
                    if type(valuee) is dict:
                        for keyyy, valueee in valuee.items():
                            data["section"].append(key)
                            data["key"].append(f"{keyy}_{keyyy}")
                            data["value"].append(valueee)
                    else:
                        data["section"].append(key)
                        data["key"].append(keyy)
                        data["value"].append(valuee)
            else:
                # Flat structure - store key-value pairs directly
                data["section"].append("")
                data["key"].append(key)
                data["value"].append(value)
        df = pd.DataFrame.from_dict(data)

        df["type"] = "setting"
        df["modified"] = False

        # now focus on the lines actually containing settings
        vars = dict(zip(list(df["key"].values), list(df["value"].values)))
    return df, vars


def write_yaml(path, df):
    """Write coastalme configuration to YAML file

    This function reconstructs the nested YAML structure from the flattened
    DataFrame format created by read_yaml(). It intelligently detects compound
    keys (e.g., "median_sizes_fine") and rebuilds nested dictionaries.

    Args:
        path (str or Path): save path (including file name)
        df (pandas DataFrame): dataframe with 'section', 'key', 'value' columns
            Keys may be simple (e.g., 'log_file_detail') or compound
            (e.g., 'median_sizes_fine') indicating nested structure

    Raises:
        ValueError: If DataFrame format is invalid

    Example:
        >>> df has rows like:
        section="sediment_and_erosion", key="median_sizes_fine", value=0.0
        section="sediment_and_erosion", key="median_sizes_sand", value=0.0
        >>> Reconstructs as:
        sediment_and_erosion:
          median_sizes:
            fine: 0.0
            sand: 0.0
    """
    if not {"section", "key", "value"}.issubset(df.columns):
        raise ValueError("DataFrame must contain 'section', 'key', and 'value' columns")

    # Build nested dictionary structure
    config = {}

    # First pass: identify which keys should be nested
    # Group by section and look for keys with common prefixes
    nested_keys = {}  # {(section, parent_key): [child_keys]}

    for section in df["section"].unique():
        section_rows = df[df["section"] == section]

        # Look for keys that could be nested (contain underscore)
        for _, row in section_rows.iterrows():
            key = row["key"]
            if pd.isna(key) or key == "":
                continue

            if "_" in key:
                # Split on first underscore to get potential parent
                parts = key.split("_", 1)
                parent_key = parts[0]
                child_key = parts[1]

                # Count how many keys share this parent prefix
                same_parent = section_rows[
                    section_rows["key"].str.startswith(parent_key + "_", na=False)
                ]

                # If multiple keys share prefix, treat as nested
                if len(same_parent) > 1:
                    key_tuple = (section, parent_key)
                    if key_tuple not in nested_keys:
                        nested_keys[key_tuple] = []
                    nested_keys[key_tuple].append(child_key)

    # Second pass: build the config dictionary
    for _, row in df.iterrows():
        section = row["section"]
        key = row["key"]
        value = row["value"]

        # Skip invalid rows
        if pd.isna(key) or key == "":
            continue

        # Handle flat structure (no section - top level)
        if section == "" or pd.isna(section):
            config[key] = value
            continue

        # Ensure section exists
        if section not in config:
            config[section] = {}

        # Check if this key should be nested
        is_nested = False
        if "_" in key:
            parent_key = key.split("_", 1)[0]
            child_key = key.split("_", 1)[1]

            if (section, parent_key) in nested_keys:
                # This is a nested key
                is_nested = True
                if parent_key not in config[section]:
                    config[section][parent_key] = {}
                config[section][parent_key][child_key] = value

        if not is_nested:
            # Simple key under section
            config[section][key] = value

    # Write YAML with nice formatting
    with open(str(path), "w", encoding="utf-8") as f:
        yaml.safe_dump(
            config,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
            indent=2,
        )

    logger.info(f"YAML configuration written to {path}")
