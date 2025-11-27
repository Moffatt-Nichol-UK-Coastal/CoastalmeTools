from pathlib import Path
import pandas as pd

def summary(series):
    max_level = series.max()
    min_level = series.min()
    tide_range = max_level - min_level
    print(f"Summary: \n min: {min_level} \n max: {max_level} \n range: {tide_range}")
    return max_level, min_level, tide_range


def main():
    wd = Path("~/CoastalME/CoastalME_data_local/Typology").expanduser()
    file = wd / "LongTide.csv"
    df = pd.read_csv(file, header=None, names=["tide level (m)"], on_bad_lines='warn')
    df["hours"] = df.index / 2

    df = df.loc[:, ['hours','tide level (m)']]

    t_max, t_min, t_range = summary(df['tide level (m)'])

    df['tide level (m)'] = df['tide level (m)'] - t_max
    df['tide level (m)'] = df['tide level (m)'].round(2)

    duration = 100 * 365.6 * (24/6)

    mask = df['hours'] <= duration
    df = df.loc[mask]

    df.to_csv("~/CoastalME/CoastalME_data_local/Typology/LongTide_processed.csv", index=False)
    ax = df.plot(kind = 'scatter', x = 'hours', y = 'tide level (m)')
    ax.figure.savefig(wd / 'tide.jpg')

if __name__ == '__main__':
    main()
