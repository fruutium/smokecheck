"""Build data/evening_pm25.csv: one row per city per day, with the average EPA hourly PM2.5 reading from
2 PM to 7 PM local standard time (hours starting 14:00 to 18:00), over the monitors in the metro area.
Smoke often arrives in the late afternoon or evening, and the daily average hides that.

When is it known? EPA's hours are in local STANDARD time, so in summer this window is 3 PM to 8 PM daylight time:
known by about 8 PM in summer, 7 PM in winter (in real life from AirNow's live feed; EPA's archive is the
checked copy of the same readings). Not every monitor reports hourly (filter-based ones give only a daily value),
so this is an average over fewer monitors than obs_pm25.

Downloads EPA's yearly hourly files (about 70 MB each) into data/raw_new/ the first time. No API keys.

Run:  python fetch_evening.py
"""
import pathlib
import urllib.request

import pandas as pd

from fetch_data import CITIES, END, RAW, START

RAW_NEW = pathlib.Path("data/raw_new")
HOURS = ["14:00", "15:00", "16:00", "17:00", "18:00"]  # start of each hour: 2 PM to 7 PM local standard time
SITE = ["State Code", "County Code", "Site Num"]


def city_sites():
    """Which monitor sites belong to which city, from the daily files (the hourly files have no metro-area name)."""
    daily = pd.concat(pd.read_csv(RAW / f"daily_88101_{y}.zip", dtype=str, usecols=SITE + ["CBSA Name"])
                      for y in range(int(START[:4]), int(END[:4]) + 1)).drop_duplicates()
    rows = [daily[daily["CBSA Name"].fillna("").str.startswith(cbsa)].assign(city=city)
            for city, (cbsa, *_rest) in CITIES.items()]
    return pd.concat(rows)[SITE + ["city"]].drop_duplicates()


def evening(year, sites):
    path = RAW_NEW / f"hourly_88101_{year}.zip"
    if not path.exists():
        RAW_NEW.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(f"https://aqs.epa.gov/aqsweb/airdata/{path.name}", path)
    keep = []
    # The national file is about 10 million rows, so read it in pieces and keep only our sites' evening hours.
    for chunk in pd.read_csv(path, dtype=str, chunksize=1_000_000,
                             usecols=SITE + ["Date Local", "Time Local", "Sample Measurement"]):
        keep.append(chunk[chunk["Time Local"].isin(HOURS)].merge(sites, on=SITE))
    h = pd.concat(keep)
    h["pm25"] = h["Sample Measurement"].astype(float)
    # one value per site per hour first (a site with two instruments counts once), then per site, then per city
    site_hour = h.groupby(["city", "Date Local", "Time Local"] + SITE)["pm25"].mean()
    site_day = site_hour.groupby(["city", "Date Local"] + SITE).mean()
    return site_day.groupby(["city", "Date Local"]).agg(evening_pm25="mean", evening_sites="size").reset_index()


def build():
    sites = city_sites()
    df = pd.concat(evening(y, sites) for y in range(int(START[:4]), int(END[:4]) + 1))
    df = df.rename(columns={"Date Local": "date"})
    df = df[df["date"].between(START, END)]
    return df.sort_values(["city", "date"]).round(2).reset_index(drop=True)


def check(df):
    """Fail loudly if the table is not what the notebook expects. Missing city-days are allowed (the notebook fills them)."""
    assert not df.duplicated(["city", "date"]).any(), "duplicate city-day rows"
    assert set(df["city"]) == set(CITIES)
    assert df["evening_pm25"].notna().all()
    days = len(pd.date_range(START, END))
    print("city-days with no evening reading:", (days - df.groupby("city").size()).to_dict())
    # Printed, not asserted: a human should see the June 2023 Canadian smoke in Chicago's evenings.
    print(df[(df["city"] == "Chicago") & df["date"].between("2023-06-25", "2023-06-29")].to_string(index=False))


if __name__ == "__main__":
    df = build()
    check(df)
    df.to_csv("data/evening_pm25.csv", index=False)
