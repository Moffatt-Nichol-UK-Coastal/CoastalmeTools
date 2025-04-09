from bokeh.driving import count
from bokeh.layouts import column, gridplot, row
from bokeh.models import ColumnDataSource, Select, Slider
from bokeh.plotting import curdoc, figure
import sys

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import time
import os
import humanize


def file_search(path, keyword=None, ext=None):
    files = next(os.walk(path), (None, None, []))[2]
    if ext:
        files = [fi for fi in files if fi.endswith(ext)]
    if keyword:
        files = [fi for fi in files if keyword in fi]
    if len(files) == 1:
        out_path = path / files[0]
    elif len(files) > 1:
        out_path = [path / file for file in files]
        # raise Exception("Multiple {}'s found".format(ext))
    elif len(files) < 1:
        # raise Exception("no {}'s found".format(ext))
        out_path = None
    return out_path


# Lets first deal with the arguments we have been passed
path = Path(sys.argv[1])
start = sys.argv[2]
start_time = datetime.fromtimestamp(int(float(start)))
# now we need to try and open the out file, we may have to repeat if it hasnt been created yet
while True:
    f_path = file_search(path, "", "out")
    if f_path is not None:
        break
    time.sleep(2)


# Now set up our plotting source
source = ColumnDataSource(
    dict(
        simTime=[],
        timestep=[],
        elapsed_hours=[],
        elapsed_years=[],
        avg_sea_depth=[],
        potential_platform_erod_perc_sea_area=[],
        potential_platform_erod_all_sea_avg=[],
        potential_platform_erod_area_avg=[],
        actual_platform_perc_sea_area=[],
        actual_platform_erod_all_sea_avg=[],
        actual_platform_erod_area_avg=[],
        actual_platform_erod_sea_avg_F=[],
        actual_platform_erod_sea_avg_S=[],
        actual_platform_erod_sea_avg_C=[],
        potential_beach_erod_perc_sea_area=[],
        potential_beach_erod_all_sea_avg=[],
        potential_beach_erod_area_avg=[],
        actual_beach_erod_perc_sea_area=[],
        actual_beach_erod_all_sea_avg=[],
        actual_beach_erod_area_avg=[],
        actual_beach_erod_sea_avg_F=[],
        actual_beach_erod_sea_avg_S=[],
        actual_beach_erod_sea_avg_C=[],
        actual_beach_depo_perc_sea_area=[],
        actual_beach_depo_all_sea_avg=[],
        actual_beach_depo_area_avg=[],
        actual_beach_depo_sea_avg_S=[],
        actual_beach_depo_sea_avg_C=[],
        input_F=[],
        input_S=[],
        input_C=[],
        cliff_collapse_erod_F=[],
        cliff_collapse_erod_S=[],
        cliff_collapse_erod_C=[],
        cliff_collapse_depo_S=[],
        cliff_collapse_depo_C=[],
        susp_sed_F=[],
        totalInput=[],
        totalCliffErod=[],
        totalCliffDepo=[],
    )
)

calc_col = dict(simTime=[], real_time=[], row_time=[], avg_row_time=[])  # type: dict
calc_source = ColumnDataSource(calc_col)

# Create blank figure
p = figure(
    width=800,
    height=500,
    tools="xpan,xwheel_zoom,xbox_zoom,reset",
    x_axis_type="datetime",
    x_axis_location="below",
    y_axis_location="right",
    # window_axis="x",
)
p.x_range.follow = "end"
p.x_range.follow_interval = timedelta(days=30)
p.x_range.range_padding = 0

p.line(
    x="simTime",
    y="avg_sea_depth",
    line_width=3,
    color="navy",
    source=source,
    legend_label="average sea depth",
)

q = figure(
    width=800,
    height=500,
    tools="xpan,xwheel_zoom,xbox_zoom,reset",
    x_axis_type="datetime",
    x_axis_location="below",
    y_axis_location="right",
    # window_axis="x",
)
q.x_range.follow = "end"
q.x_range.follow_interval = timedelta(days=30)
q.x_range.range_padding = 0

q.line(
    x="simTime",
    y="actual_beach_erod_area_avg",
    line_width=3,
    color="navy",
    source=source,
    legend_label="actual beach erod",
)
q.line(
    x="simTime",
    y="actual_beach_depo_area_avg",
    line_width=3,
    color="orange",
    source=source,
    legend_label="actual beach depo",
)
q.line(
    x="simTime",
    y="totalCliffErod",
    line_width=3,
    color="red",
    source=source,
    legend_label="total cliff collapse",
)

r = figure(
    width=800,
    height=500,
    tools="xpan,xwheel_zoom,xbox_zoom,reset",
    x_axis_type="datetime",
    x_axis_location="below",
    y_axis_location="right",
    title="simulation efficency",
    y_axis_label="sec",
    # window_axis="x",
)
r.x_range.follow = "end"
r.x_range.follow_interval = timedelta(days=30)
r.x_range.range_padding = 0
r.legend.location = "top_left"

r.scatter(
    x="simTime",
    y="row_time",
    line_width=3,
    color="orange",
    source=calc_source,
    legend_label="timestep calculation time",
)
r.line(
    x="simTime",
    y="avg_row_time",
    line_width=3,
    alpha=0.5,
    color="blue",
    source=calc_source,
    legend_label="average timestep calculation time",
)

last_size = 0
last_time = time.perf_counter()

calc_df = pd.DataFrame.from_dict(calc_col)
i = 0


@count()
def time_update(t):
    """
    Function updates our data streams at intervals
    """
    global last_size
    global calc_df
    global last_time
    global i
    # Read updated .out file int df
    df = parse_out(f_path, start_time)
    # Whats the time now
    this_time = time.perf_counter()

    # What is the size of the dataframe now
    this_size = df.shape[0]
    # Check if it has changed since we last updated the plots
    if this_size != last_size:
        # How many new rows do we have
        new_rows = this_size - last_size
        # How long has it taken to get these extra rows
        this_ellapse_time = this_time - last_time
        row_time = this_ellapse_time / new_rows
        if i > 0:
            total_ellapse_time = this_time - calc_df.iloc[0, 1]
            avg_row_time = total_ellapse_time / this_size
        else:
            avg_row_time = row_time
        # Lets add our derived data to the log
        calc_df.loc[calc_df.shape[0]] = [
            df.loc[df.index[this_size - 1], "simTime"],
            this_time,
            row_time,
            avg_row_time,
        ]
        # Lets trim output data that we have allready seen
        df = df.iloc[last_size:]

        # Update our counters
        last_size = this_size
        last_time = this_time

        new_data = df.to_dict(orient="list")
        new_calcs = calc_df.iloc[i:].to_dict(orient="list")
        i += 1

        source.stream(new_data)
        calc_source.stream(new_calcs)


# Now west up the plot arangement and display
curdoc().add_root(
    column(
        gridplot([[r], [q], [p]], toolbar_location="left", width=1000),
    )
)
# Start recursive plot update
curdoc().add_periodic_callback(time_update, 1000)
curdoc().title = "monitor"


def parse_out(path, start_time):
    """
    This takes the path of the out file. Imports it and converts sim_time into model_time
    returns: whole dataframe
    """
    col_widths = [
        4,
        7,
        7,
        6,
        6,
        6,
        6,
        6,
        6,
        5,
        4,
        4,
        4,
        7,
        6,
        6,
        7,
        6,
        7,
        4,
        4,
        4,
        7,
        6,
        9,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        6,
    ]
    coln = [
        "timestep",
        "elapsed_hours",
        "elapsed_years",
        "avg_sea_depth",
        "potential_platform_erod_perc_sea_area",
        "potential_platform_erod_all_sea_avg",
        "potential_platform_erod_area_avg",
        "actual_platform_perc_sea_area",
        "actual_platform_erod_all_sea_avg",
        "actual_platform_erod_area_avg",
        "actual_platform_erod_sea_avg_F",
        "actual_platform_erod_sea_avg_S",
        "actual_platform_erod_sea_avg_C",
        "potential_beach_erod_perc_sea_area",
        "potential_beach_erod_all_sea_avg",
        "potential_beach_erod_area_avg",
        "actual_beach_erod_perc_sea_area",
        "actual_beach_erod_all_sea_avg",
        "actual_beach_erod_area_avg",
        "actual_beach_erod_sea_avg_F",
        "actual_beach_erod_sea_avg_S",
        "actual_beach_erod_sea_avg_C",
        "actual_beach_depo_perc_sea_area",
        "actual_beach_depo_all_sea_avg",
        "actual_beach_depo_area_avg",
        "actual_beach_depo_sea_avg_S",
        "actual_beach_depo_sea_avg_C",
        "input_F",
        "input_S",
        "input_C",
        "cliff_collapse_erod_F",
        "cliff_collapse_erod_S",
        "cliff_collapse_erod_C",
        "cliff_collapse_depo_S",
        "cliff_collapse_depo_C",
        "susp_sed_F",
    ]
    df = pd.read_fwf(path, widths=col_widths, skiprows=115, header=None, names=coln)
    # df = df.astype("float")

    df["simTime"] = [timedelta(hours=x) + start_time for x in df["elapsed_hours"]]

    df["totalInput"] = df["input_F"] + df["input_S"] + df["input_C"]

    df["totalCliffErod"] = (
        df["cliff_collapse_erod_F"]
        + df["cliff_collapse_erod_S"]
        + df["cliff_collapse_erod_C"]
    )
    df["totalCliffDepo"] = df["cliff_collapse_depo_S"] + df["cliff_collapse_depo_C"]

    return df
