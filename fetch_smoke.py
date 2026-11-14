"""Build data/smoke_days.csv: one row per city per day, saying whether NOAA analysts
drew a wildfire-smoke plume over the city that day. No API keys needed.

Source: NOAA Hazard Mapping System (HMS) daily smoke polygons. Analysts look at satellite
images and outline the smoke they see, labelling each outline Light, Medium or Heavy.

Run:  python fetch_smoke.py
"""
import pathlib
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import shapefile  # the "pyshp" package: reads shapefiles in plain Python
from matplotlib.path import Path  # a polygon that can answer "is this point inside me?"

from fetch_data import CITIES, START, END

URL = "https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile"
RAW = pathlib.Path("data/raw/hms")
LEVEL = {"Light": 1, "Medium": 2, "Heavy": 3}
# Light plumes are often high in the atmosphere and never reach the ground, so we only call
# Medium or Heavy a "smoke day". This threshold is our choice, not NOAA's.
SMOKE_DAY_LEVEL = 2
# Shapefile points are (x, y) = (longitude, latitude), so the city points use the same order.
CITY_POINTS = [(lon, lat) for _cbsa, lat, lon, _utc in CITIES.values()]


def get(url):
    """The bytes at a URL, or b"" when the server says 404 (NOAA has no file for that day)."""
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return b""
        raise


def download(day):
    """Save one day's zip in data/raw/hms/, unless it is already there (so reruns are fast)."""
    path = RAW / f"hms_smoke{day:%Y%m%d}.zip"
    if path.exists():
        return
    url = f"{URL}/{day:%Y}/{day:%m}/{path.name}"
    try:
        data = get(url)
    except Exception:  # network hiccup: wait and try once more; a second failure stops the script
        time.sleep(3)
        data = get(url)
    # A 404 is saved as an empty file. That marks "no file" so we don't ask the server again.
    path.write_bytes(data)


def smoke_levels(path):
    """Heaviest smoke level (0-3) drawn over each city in one day's file, in CITIES order."""
    levels = [0] * len(CITIES)
    for item in shapefile.Reader(str(path)).iterShapeRecords():
        level = LEVEL[item.record["Density"]]
        # Every outline in 2022-2025 is one simple ring (we checked), so one Path per outline is enough.
        inside = Path(item.shape.points).contains_points(CITY_POINTS)
        levels = [max(old, level) if hit else old for old, hit in zip(levels, inside)]
    return levels


def build():
    RAW.mkdir(parents=True, exist_ok=True)
    days = pd.date_range(START, END)
    # 8 downloads at a time: fast enough, and still polite to NOAA's server.
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, days))
    rows = []
    for day in days:
        path = RAW / f"hms_smoke{day:%Y%m%d}.zip"
        has_file = path.stat().st_size > 0
        # No file means we don't know. We record smoke = 0 but flag it in hms_file,
        # so it can be told apart from "analysts looked and drew no plume here".
        levels = smoke_levels(path) if has_file else [0] * len(CITIES)
        for city, level in zip(CITIES, levels):
            # Known limit: the file covers a UTC day, but EPA days are local time (5-6 hours
            # behind), so a plume drawn late in the local evening lands on the next day's file.
            rows.append({"city": city, "date": f"{day:%Y-%m-%d}", "smoke": level, "hms_file": has_file})
    df = pd.DataFrame(rows)
    df["is_smoke_day"] = df["smoke"] >= SMOKE_DAY_LEVEL
    return df.sort_values(["city", "date"]).reset_index(drop=True)


def check(df):
    """Fail loudly if the table is not what the notebook expects."""
    assert not df.duplicated(["city", "date"]).any(), "duplicate city-day rows"
    days = pd.date_range(START, END).strftime("%Y-%m-%d")
    for city in CITIES:
        assert list(df.loc[df["city"] == city, "date"]) == list(days), f"{city}: missing calendar days"
    assert df["smoke"].isin([0, 1, 2, 3]).all()
    chicago = df[df["city"] == "Chicago"].set_index("date")
    # Days we know were smoky in Chicago: the June 2023 Canadian smoke, and 31 July 2025.
    for date in ["2023-06-27", "2023-06-28", "2025-07-31"]:
        assert chicago.loc[date, "is_smoke_day"], f"Chicago {date} should be a smoke day"


if __name__ == "__main__":
    df = build()
    check(df)
    df.to_csv("data/smoke_days.csv", index=False)
    print("days with no HMS file:", (~df["hms_file"]).sum() // len(CITIES))
    print(df.groupby("city").agg(days=("date", "size"), light_or_more=("smoke", lambda s: (s >= 1).sum()),
                                 smoke_days=("is_smoke_day", "sum")))
