"""Build data/upwind_smoke.csv: one row per city per day, saying how heavy the NOAA-mapped
smoke is 300, 600 and 900 km UPWIND of the city. Smoke that reaches Chicago often starts far
away (Canada), so smoke upwind today is a warning for tomorrow.

Needs data/daily.csv (for the wind) and the HMS zips that fetch_smoke.py saved. No network.

Run:  python fetch_upwind_smoke.py
"""
import numpy as np
import pandas as pd
import shapefile  # the "pyshp" package: reads shapefiles in plain Python
from matplotlib.path import Path  # a polygon that can answer "is this point inside me?"

from fetch_data import CITIES, START, END
from fetch_smoke import LEVEL, RAW

DISTANCES_KM = [300, 600, 900]
KM_PER_DEG_LAT = 111
# Below this the mean wind has no clear direction (it may have turned during the day),
# so we don't pretend to know which way is upwind and record 0 for that day.
CALM_KMH = 1


def levels_at(path, points):
    """Heaviest smoke level (0-3) over each (lon, lat) point in one day's file.
    Same loop as fetch_smoke.smoke_levels, but for any points, not just the city centres."""
    levels = np.zeros(len(points), dtype=int)
    for item in shapefile.Reader(str(path)).iterShapeRecords():
        inside = Path(item.shape.points).contains_points(points)
        levels[inside] = np.maximum(levels[inside], LEVEL[item.record["Density"]])
    return levels


def upwind_points(lat, lon, u, v):
    """(lon, lat) of the points DISTANCES_KM upwind, or None when the wind is calm."""
    speed = np.hypot(u, v)
    if not speed >= CALM_KMH:  # "not >=" so a missing (NaN) wind counts as calm too
        return None
    # Air moves along (u, v), so it comes FROM the opposite direction.
    east, north = -u / speed, -v / speed
    # Flat-earth conversion from km to degrees. At 900 km and these latitudes the error is
    # a few percent, much smaller than the size of a smoke plume, so it is fine here.
    km_per_deg_lon = KM_PER_DEG_LAT * np.cos(np.radians(lat))
    return [(lon + east * d / km_per_deg_lon, lat + north * d / KM_PER_DEG_LAT) for d in DISTANCES_KM]


def build(daily, raw=RAW):
    """`daily` needs city, date, wind_u and wind_v; `raw` is the folder with the HMS zips."""
    rows = []
    for date, day in daily.groupby("date"):
        # Known limit: the HMS file covers a UTC day, but the wind is averaged over the
        # local-standard-time day (5-6 hours behind), so the two don't line up exactly.
        path = raw / f"hms_smoke{date.replace('-', '')}.zip"
        has_file = path.stat().st_size > 0  # an empty zip means NOAA had no file that day
        points, owners = [], []
        for r in day.itertuples():
            _cbsa, lat, lon, _utc = CITIES[r.city]
            p = upwind_points(lat, lon, r.wind_u, r.wind_v)
            if p is None:
                rows.append({"city": r.city, "date": date, "levels": [0, 0, 0]})
            else:
                points += p
                owners.append(r.city)
        # One read of the day's file for all cities at once keeps the whole run fast.
        levels = levels_at(path, points) if has_file and points else np.zeros(len(points), dtype=int)
        for i, city in enumerate(owners):
            rows.append({"city": city, "date": date, "levels": list(levels[3 * i:3 * i + 3])})
    df = pd.DataFrame(rows)
    cols = [f"upwind_smoke_{d}" for d in DISTANCES_KM]
    df[cols] = pd.DataFrame(df.pop("levels").tolist(), index=df.index)
    df["upwind_smoke_max"] = df[cols].max(axis=1)
    return df.sort_values(["city", "date"]).reset_index(drop=True)


def check(df):
    """Fail loudly if the table is not what the notebook expects."""
    assert not df.duplicated(["city", "date"]).any(), "duplicate city-day rows"
    days = pd.date_range(START, END).strftime("%Y-%m-%d")
    for city in CITIES:
        assert list(df.loc[df["city"] == city, "date"]) == list(days), f"{city}: missing calendar days"
    cols = ["upwind_smoke_300", "upwind_smoke_600", "upwind_smoke_900"]
    assert df[cols + ["upwind_smoke_max"]].isin([0, 1, 2, 3]).all().all()
    assert (df["upwind_smoke_max"] == df[cols].max(axis=1)).all()
    # Printed, not asserted: a human should eyeball known smoke events in Chicago.
    chicago = df[df["city"] == "Chicago"].set_index("date")
    for first, last in [("2025-07-29", "2025-08-01"), ("2023-06-25", "2023-06-28")]:
        print(chicago.loc[first:last].to_string())


if __name__ == "__main__":
    df = build(pd.read_csv("data/daily.csv", usecols=["city", "date", "wind_u", "wind_v"]))
    check(df)
    df.to_csv("data/upwind_smoke.csv", index=False)
    print(df.groupby("city")["upwind_smoke_max"].apply(lambda s: (s >= 2).sum()).rename("days_upwind_2plus"))
