"""Build data/weather_dayahead_2025.csv: for each city and each day of 2025, the weather that was
FORECAST for that day one day earlier (Open-Meteo Previous Runs API, variables ending in _previous_day1).

Why: the weather in data/daily.csv comes from Open-Meteo's historical forecast archive, which is stitched
from the first hours of each model run, so it is almost the real weather. An athletic director deciding
the evening before only has yesterday's forecast. True day-ahead values exist only from 2024 on, so we
use them to score the 2025 test year honestly. No API keys needed.

Run:  python fetch_dayahead.py
"""
import numpy as np
import pandas as pd

from fetch_data import CITIES, open_meteo_hourly

VARS = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"]
URL = "https://previous-runs-api.open-meteo.com/v1/forecast"


def city_dayahead(city):
    _cbsa, lat, lon, utc_offset = CITIES[city]
    h = open_meteo_hourly(URL, lat, lon, [f"{v}_previous_day1" for v in VARS], start="2025-01-01", end="2026-01-01")
    h.columns = [c.removesuffix("_previous_day1") for c in h.columns]
    # same daily averaging as fetch_data.model_daily, so the columns mean the same thing
    rad = np.deg2rad(h["wind_direction_10m"])
    h["wind_u"] = -h["wind_speed_10m"] * np.sin(rad)
    h["wind_v"] = -h["wind_speed_10m"] * np.cos(rad)
    h.index = h.index + pd.Timedelta(hours=utc_offset)
    g = h.groupby(h.index.strftime("%Y-%m-%d"))
    day = pd.DataFrame({
        "temp_c": g["temperature_2m"].mean(), "humidity": g["relative_humidity_2m"].mean(),
        "precip_mm": g["precipitation"].sum(), "wind_kmh": g["wind_speed_10m"].mean(),
        "wind_u": g["wind_u"].mean(), "wind_v": g["wind_v"].mean(), "hours": g["temperature_2m"].count(),
    }).rename_axis("date").reset_index()
    day.insert(0, "city", city)
    return day[day["date"].between("2025-01-01", "2025-12-31")]


if __name__ == "__main__":
    df = pd.concat(city_dayahead(c) for c in CITIES).round(2)
    assert len(df) == 365 * len(CITIES), "expected every day of 2025 for every city"
    assert (df["hours"] == 24).all(), "a day is missing forecast hours"
    df.drop(columns="hours").to_csv("data/weather_dayahead_2025.csv", index=False)
    print(df.describe().round(1))
