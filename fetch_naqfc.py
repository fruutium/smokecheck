"""Build data/naqfc_dayahead.csv: for each city and each day, the daily-mean PM2.5 that NOAA's
official air-quality model (NAQFC, the "AQM" model) forecast ONE DAY AHEAD. This is the baseline
to beat: what an athletic director could have looked up the evening before. No API keys needed.

Source: NOAA's National Air Quality Forecast Capability on AWS Open Data (bucket noaa-nws-naqfc-pds).
About 1,250 GRIB2 files (about 3.1 GB) are cached in data/raw/naqfc/, so reruns are quick.

Run:  python fetch_naqfc.py
"""
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor

import eccodes  # reads GRIB2, the file format weather models use; the pip wheel includes the C library
import numpy as np
import pandas as pd

from fetch_data import CITIES, START, END
from fetch_smoke import get

URL = "https://noaa-nws-naqfc-pds.s3.amazonaws.com"
RAW = pathlib.Path("data/raw/naqfc")
# NOAA replaced AQMv6 with AQMv7 on this run date. The bucket has no day with both, so we use whichever ran.
V7_FROM = "20240514"
# The model grid: 1473 x 1025 cells of about 5 km over North America (Lambert projection).
GRID = (1473, 1025)

# Which forecast counts as "available the evening before target day D"?
# We use the 12Z run of day D-1 (12Z = 6 AM CST; NOAA publishes it a few hours later).
# Each of these files has three 24-hour averages. We checked the GRIB headers, and they end at:
#   validity 04Z on D            -> window 04Z D-1 to 04Z D    (0 hours of local day D)
#   validity 04Z on D+1          -> window 04Z D   to 04Z D+1  (steps 17-40)
#   validity 04Z on D+2          -> window 04Z D+1 to 04Z D+2  (2 hours of local day D)
# The middle one is 22:00 CST D-1 to 22:00 CST D (22 of 24 hours of the EPA day) for the Central
# cities, and 23:00 EST to 23:00 EST (23 of 24) for Detroit. So we keep the message valid at 04Z D+1.
# (NOAA's 04Z day = midnight to midnight Eastern DAYLIGHT time, which is not the EPA day.)
# Known quirk: the header says "steps 17 to 40", a 23-hour range; it averages the 24 hourly values
# ending at hours 17..40, i.e. hours 16 to 40. Either way the window ends at 04Z D+1.
#
# Bias-corrected ("_bc") or raw? We listed the whole bucket: the 12Z _bc file is missing for only
# 3 run days (2022-09-19, 2023-05-20, 2023-08-09) in both AQMv6 and AQMv7; raw is missing those
# 3 plus 2024-02-08. So we use _bc for the whole period: it has the best coverage (3 missing run days vs 4 for raw).
# We do NOT fall back to the 06Z run: it is missing on exactly the same 3 days, so it would add nothing.


def run_path(run_day):
    """Local cache path and bucket key for the 12Z bias-corrected 24-hour-average file of one run day."""
    ymd = f"{run_day:%Y%m%d}"
    model = "AQMv7" if ymd >= V7_FROM else "AQMv6"
    name = f"aqm.t12z.ave_24hr_pm25_bc.{ymd}.227.grib2"
    return RAW / name, f"{model}/CS/{ymd}/12/{name}", model


def download(run_day):
    """Save one run's file in data/raw/naqfc/, unless it is already there."""
    path, key, _model = run_path(run_day)
    if path.exists():
        return
    try:
        data = get(f"{URL}/{key}")
    except Exception:  # network hiccup: wait and try once more; a second failure stops the script
        time.sleep(3)
        data = get(f"{URL}/{key}")
    # Write to a temporary name first, so a killed run never leaves a half file that looks finished.
    # A 404 is saved as an empty file, meaning "NOAA has no run that day", so we don't ask again.
    tmp = path.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.rename(path)


def nearest_cells(handle):
    """Index of the grid cell nearest each city centre, in CITIES order.
    Shortcut: one 5 km cell per city, not an average over the metro area like the EPA number;
    averaging all cells inside the metro boundary would match better but needs the boundary shapes."""
    lat = eccodes.codes_get_array(handle, "latitudes")
    lon = eccodes.codes_get_array(handle, "longitudes")  # 0-360 on this grid, e.g. Chicago is 272.4
    cells = []
    for _cbsa, city_lat, city_lon, _utc in CITIES.values():
        east = ((lon - city_lon + 180) % 360 - 180) * np.cos(np.radians(city_lat))  # works for 0-360 or -180-180
        cells.append(np.argmin((lat - city_lat) ** 2 + east ** 2))
    return cells


def read_run(path, target_day, cells):
    """The forecast PM2.5 for each city on target_day from one file (NaN if no file)."""
    if path.stat().st_size == 0:
        return [np.nan] * len(CITIES), cells
    want = (int(f"{target_day + pd.Timedelta(days=1):%Y%m%d}"), 400)  # the message valid at 04Z D+1
    found = []
    with open(path, "rb") as f:
        while (h := eccodes.codes_grib_new_from_file(f)) is not None:
            if (eccodes.codes_get(h, "validityDate"), eccodes.codes_get(h, "validityTime")) == want:
                assert (eccodes.codes_get(h, "Ni"), eccodes.codes_get(h, "Nj")) == GRID, f"{path}: grid changed"
                cells = cells or nearest_cells(h)  # same grid in every file, so find the cells once
                values = eccodes.codes_get_values(h)
                found.append([np.nan if values[i] == 9999 else values[i] for i in cells])  # 9999 = no data
            eccodes.codes_release(h)
    assert len(found) == 1, f"{path}: expected one 24-hour average ending 04Z {want[0]}, found {len(found)}"
    return found[0], cells


def build():
    RAW.mkdir(parents=True, exist_ok=True)
    # Target days start one day after START, because the first one needs the run from START.
    targets = pd.date_range(pd.Timestamp(START) + pd.Timedelta(days=1), END)
    runs = targets - pd.Timedelta(days=1)
    # 8 downloads at a time: fast enough, and still polite to NOAA's server.
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, runs))
    rows, cells = [], None
    # Reading is done one file at a time: eccodes is not safe to use from several threads at once.
    for run, target in zip(runs, targets):
        path, _key, model = run_path(run)
        values, cells = read_run(path, target, cells)
        has_file = path.stat().st_size > 0
        for city, pm in zip(CITIES, values):
            rows.append({"city": city, "date": f"{target:%Y-%m-%d}", "naqfc_pm25": pm,
                         "naqfc_model": model if has_file else None,
                         "issued": f"{run:%Y%m%d} 12z" if has_file else None})
    return pd.DataFrame(rows).sort_values(["city", "date"]).round(2).reset_index(drop=True)


def check(df):
    """Fail loudly if the table is not what we expect, and print rows a human can compare with EPA."""
    assert not df.duplicated(["city", "date"]).any(), "duplicate city-day rows"
    days = pd.date_range(pd.Timestamp(START) + pd.Timedelta(days=1), END).strftime("%Y-%m-%d")
    for city, d in df.groupby("city"):
        assert list(d["date"]) == list(days), f"{city}: missing calendar days"
    pm = df["naqfc_pm25"].dropna()
    assert pm.between(0, 1000).all(), "a forecast is outside 0-1000 µg/m³"
    print("NaN city-days per year:")
    print(df["naqfc_pm25"].isna().groupby(df["date"].str[:4]).sum().to_string())
    # EPA measured 31.6, 130.0, 112.2, 53.6 (June 2023 smoke) and 9.4, 12.4, 65.6, 45.5, 26.2 (summer 2025).
    chicago = df[df["city"] == "Chicago"]
    print(chicago[chicago["date"].between("2023-06-26", "2023-06-29")
                  | chicago["date"].between("2025-07-29", "2025-08-02")].to_string(index=False))


if __name__ == "__main__":
    df = build()
    check(df)
    df.to_csv("data/naqfc_dayahead.csv", index=False)
    print(df.groupby("naqfc_model").agg(days=("date", "size"), first=("date", "min"), last=("date", "max")))
