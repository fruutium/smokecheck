"""Build data/daily.csv: one row per city per day, with observed PM2.5 (EPA),
the CAMS model's PM2.5 (Open-Meteo) and weather (Open-Meteo). No API keys needed.

Run:  python fetch_data.py
"""
import json
import pathlib
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

# CAMS on Open-Meteo starts 2022-08-04. We stop at the end of 2025: EPA has only part of 2026,
# and not for every city (Minneapolis has none yet).
START, END = "2022-08-04", "2025-12-31"
# The split is by time, never shuffled: train on earlier dates, test on later ones.
TRAIN_END = "2024-12-31"  # train: 2022-08-04 to 2024-12-31, test: all of 2025

# city: (start of the EPA metro-area name, latitude, longitude, UTC offset of local STANDARD time)
CITIES = {
    "Chicago": ("Chicago-Naperville", 41.88, -87.63, -6),
    "Milwaukee": ("Milwaukee-Waukesha", 43.04, -87.91, -6),
    "Madison": ("Madison, WI", 43.07, -89.40, -6),
    "Minneapolis": ("Minneapolis-St. Paul", 44.98, -93.27, -6),
    "Detroit": ("Detroit-Warren", 42.33, -83.05, -5),
    "St. Louis": ("St. Louis, MO", 38.63, -90.20, -6),
}
RAW = pathlib.Path("data/raw")


def epa_daily():
    """Observed daily mean PM2.5 per city: average over all EPA monitors in the metro area."""
    RAW.mkdir(parents=True, exist_ok=True)
    frames = []
    for year in range(int(START[:4]), int(END[:4]) + 1):
        path = RAW / f"daily_88101_{year}.zip"
        if not path.exists():
            urllib.request.urlretrieve(f"https://aqs.epa.gov/aqsweb/airdata/{path.name}", path)
        frames.append(pd.read_csv(path, dtype=str, usecols=[
            "State Code", "County Code", "Site Num", "Date Local", "Event Type", "Arithmetic Mean", "CBSA Name"]))
    df = pd.concat(frames)
    # "Excluded" rows are copies with wildfire-smoke readings removed for regulatory purposes.
    # Smoke days are exactly what we forecast, so we keep the real readings and drop those copies.
    df = df[df["Event Type"] != "Excluded"]
    df["pm25"] = df["Arithmetic Mean"].astype(float)
    out = []
    for city, (cbsa, *_rest) in CITIES.items():
        d = df[df["CBSA Name"].fillna("").str.startswith(cbsa)]
        # one value per monitor per day first, so a monitor with several instruments doesn't count twice
        site = d.groupby(["Date Local", "State Code", "County Code", "Site Num"])["pm25"].mean()
        day = site.groupby("Date Local").agg(obs_pm25="mean", n_monitors="size").reset_index()
        day.insert(0, "city", city)
        out.append(day.rename(columns={"Date Local": "date"}))
    return pd.concat(out)


def open_meteo_hourly(base_url, lat, lon, variables):
    """Hourly values from an Open-Meteo API, indexed by UTC time."""
    query = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "hourly": ",".join(variables),
        "start_date": START, "end_date": "2026-01-01", "timezone": "GMT"})
    with urllib.request.urlopen(f"{base_url}?{query}", timeout=120) as r:
        hourly = json.load(r)["hourly"]
    return pd.DataFrame(hourly).assign(time=lambda d: pd.to_datetime(d["time"])).set_index("time")


def model_daily(city):
    """CAMS PM2.5 and weather for one city, averaged over the same local-standard-time day EPA uses."""
    _cbsa, lat, lon, utc_offset = CITIES[city]
    cams = open_meteo_hourly("https://air-quality-api.open-meteo.com/v1/air-quality", lat, lon, ["pm2_5"])
    wx = open_meteo_hourly("https://historical-forecast-api.open-meteo.com/v1/forecast", lat, lon, [
        "temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"])
    h = cams.join(wx)
    # Wind direction can't be averaged as an angle (350° and 10° would average to 180°),
    # so split the wind into west-to-east (u) and south-to-north (v) parts and average those.
    rad = np.deg2rad(h["wind_direction_10m"])
    h["wind_u"] = -h["wind_speed_10m"] * np.sin(rad)
    h["wind_v"] = -h["wind_speed_10m"] * np.cos(rad)
    h.index = h.index + pd.Timedelta(hours=utc_offset)  # UTC -> local standard time
    g = h.groupby(h.index.strftime("%Y-%m-%d"))
    day = pd.DataFrame({
        "cams_pm25": g["pm2_5"].mean(), "cams_pm25_max": g["pm2_5"].max(), "cams_hours": g["pm2_5"].count(),
        "temp_c": g["temperature_2m"].mean(), "humidity": g["relative_humidity_2m"].mean(),
        "precip_mm": g["precipitation"].sum(), "wind_kmh": g["wind_speed_10m"].mean(),
        "wind_u": g["wind_u"].mean(), "wind_v": g["wind_v"].mean(),
    }).rename_axis("date").reset_index()
    day.insert(0, "city", city)
    return day


def build():
    obs = epa_daily()
    model = pd.concat(model_daily(city) for city in CITIES)
    df = model.merge(obs, on=["city", "date"], how="left")
    df = df[(df["date"] >= START) & (df["date"] <= END)]
    df["lat"] = df["city"].map(lambda c: CITIES[c][1])
    df["lon"] = df["city"].map(lambda c: CITIES[c][2])
    df["split"] = np.where(df["date"] <= TRAIN_END, "train", "test")
    return df.sort_values(["city", "date"]).round(2).reset_index(drop=True)


def check(df):
    """Fail loudly if the table is not what the notebook expects."""
    assert not df.duplicated(["city", "date"]).any(), "duplicate city-day rows"
    days = pd.date_range(START, END).strftime("%Y-%m-%d")
    for city, d in df.groupby("city"):
        assert list(d["date"]) == list(days), f"{city}: missing calendar days"
    assert df.loc[df["split"] == "train", "date"].max() < df.loc[df["split"] == "test", "date"].min()
    assert df["obs_pm25"].notna().all(), "a city-day has no EPA reading"
    assert df.loc[df["date"] > START, "cams_hours"].min() == 24, "a day is missing CAMS hours"
    smoke = df[(df["city"] == "Chicago") & (df["date"] == "2023-06-27")]["obs_pm25"].item()
    assert smoke > 100, f"Chicago 2023-06-27 should be a heavy smoke day, got {smoke}"


if __name__ == "__main__":
    df = build()
    check(df)
    df.to_csv("data/daily.csv", index=False)
    print(df.groupby(["city", "split"]).agg(days=("date", "size"), over_35=("obs_pm25", lambda s: (s > 35).sum())))
