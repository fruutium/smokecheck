"""Build data/ring_pm25.csv: one row per day with the EPA PM2.5 readings in a ring of 14 metro areas
around our six cities. Smoke that reaches Chicago is often measured in Minnesota or the Dakotas a day earlier.

- ring_max, ring_mean: highest and average daily reading over the 14 metros (those with a reading that day)
- north_max: highest over the 4 ring metros north of 45°N (Duluth, Fargo, Bismarck, St. Cloud),
  the first ones that Canadian smoke crosses on its way south

These are the readings ON that date. The notebook shifts them by one day, so a target day sees today's ring.
Reads the same EPA daily files as fetch_data.py (data/raw/). No network if they are already there.

Run:  python fetch_ring.py
"""
import pandas as pd

from fetch_data import END, START, epa_daily

# The start of each EPA metro-area name, and its latitude. Fixed before we looked at any readings: the larger
# metros on every side of our six, more of them to the north and west, where Canadian smoke comes from.
# Grand Forks, ND was on our list too, but it has no PM2.5 monitor in the EPA files.
RING = {
    "Duluth": ("Duluth", 46.96), "Fargo": ("Fargo", 46.93), "Bismarck": ("Bismarck", 46.95),
    "St. Cloud": ("St. Cloud", 45.55), "Sioux Falls": ("Sioux Falls", 43.60), "Rochester MN": ("Rochester, MN", 44.00),
    "Des Moines": ("Des Moines", 41.63), "Cedar Rapids": ("Cedar Rapids", 41.98), "Green Bay": ("Green Bay", 44.51),
    "Grand Rapids": ("Grand Rapids", 42.93), "Lansing": ("Lansing", 42.76), "Indianapolis": ("Indianapolis", 39.88),
    "Kansas City": ("Kansas City", 39.03), "Omaha": ("Omaha", 41.29),
}
NORTH = [m for m, (_cbsa, lat) in RING.items() if lat > 45]


def build():
    obs = epa_daily(cities=RING).pivot(index="date", columns="city", values="obs_pm25")
    days = pd.date_range(START, END).strftime("%Y-%m-%d")
    obs = obs.reindex(days)  # one row per calendar day, so the notebook's shift(1) always means "the day before"
    return pd.DataFrame({"date": days, "ring_max": obs.max(axis=1).values, "ring_mean": obs.mean(axis=1).values,
                         "north_max": obs[NORTH].max(axis=1).values,
                         "ring_metros": obs.notna().sum(axis=1).values}).round(2)


def check(df):
    """Fail loudly if the table is not what the notebook expects."""
    assert NORTH == ["Duluth", "Fargo", "Bismarck", "St. Cloud"]
    assert list(df["date"]) == list(pd.date_range(START, END).strftime("%Y-%m-%d")), "missing calendar days"
    assert df[["ring_max", "ring_mean", "north_max"]].notna().all().all(), "a day has no ring reading"
    assert (df["ring_max"] >= df["north_max"]).all() and (df["ring_max"] >= df["ring_mean"]).all()
    # Printed, not asserted: a human should see the June 2023 Canadian smoke reach the ring.
    print(df[df["date"].between("2023-06-25", "2023-06-30")].to_string(index=False))


if __name__ == "__main__":
    df = build()
    check(df)
    df.to_csv("data/ring_pm25.csv", index=False)
    print(df.describe().round(1).to_string())
