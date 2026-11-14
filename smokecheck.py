# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # SmokeCheck: should practice move indoors tomorrow?
#
# **Veritas AI International High School Hackathon 2026 · Track: AI + Climate**
# (built on suggested project 4.3.2, next-day air quality forecast)
#
# **One-sentence pitch:** SmokeCheck helps a Midwest high-school athletic director who has to plan tomorrow's
# practice by taking today's air quality and tomorrow's forecast, and telling them whether to expect unhealthy
# smoke (a daily average above 35 µg/m³ of PM2.5).
#
# **How to run:** Runtime → Run all. It needs no API keys or uploads.

# %% [markdown]
# ## 1. Load the data
#
# `data/daily.csv` has one row per city per day for six Midwest metro areas (built by `fetch_data.py`):
#
# - `obs_pm25`: what EPA monitors **measured**, averaged over the metro area (µg/m³). This is the truth we forecast.
# - `cams_pm25`: what the CAMS global air-quality **model** says (from Open-Meteo). It is an estimate on a 45 km
#   grid, not a measurement.
# - weather from Open-Meteo: temperature, humidity, rain, wind speed and wind direction (`wind_u`, `wind_v`).

# %%
import json
import os

import numpy as np
import pandas as pd

LOCAL = "data/daily.csv"
URL = "https://raw.githubusercontent.com/fruutium/smokecheck/main/data/daily.csv"
daily = pd.read_csv(LOCAL if os.path.exists(LOCAL) else URL)

THRESHOLD = 35  # µg/m³, the US EPA 24-hour PM2.5 standard. Above it, we say "move practice indoors".
print(f"{len(daily):,} city-days, {daily['city'].nunique()} cities, {daily['date'].min()} to {daily['date'].max()}")
daily.head()

# %% [markdown]
# ## 2. Look at the data first
#
# Days above 35 µg/m³ are rare (about 1 in 100), and in summer they are almost all wildfire smoke.
# June 2023 (smoke from Quebec) is the worst event in the data. It is in the training years.

# %%
daily["over"] = daily["obs_pm25"] > THRESHOLD
print(daily.groupby("city").agg(days=("date", "size"), mean_pm25=("obs_pm25", "mean"),
                                worst_day=("obs_pm25", "max"), days_over_35=("over", "sum")).round(1))

chicago = daily[daily["city"] == "Chicago"].set_index(pd.to_datetime(daily.loc[daily["city"] == "Chicago", "date"]))
ax = chicago[["obs_pm25", "cams_pm25"]].plot(figsize=(11, 3), lw=0.8, title="Chicago: measured PM2.5 vs the CAMS model")
ax.axhline(THRESHOLD, color="red", ls="--", lw=0.8)
ax.set_ylabel("PM2.5 (µg/m³)");

# %% [markdown]
# ## 3. Split by time
#
# We train on earlier dates and test on later ones, and never shuffle days together:
# **train = Aug 2022 to Dec 2024, test = all of 2025.** The test year has its own smoke season
# (June and late July / early August 2025), which the model never sees during training.

# %%
print(daily.groupby("split").agg(first_day=("date", "min"), last_day=("date", "max"),
                                 city_days=("date", "size"), days_over_35=("over", "sum")))

# %% [markdown]
# ## 4. Set up the forecast
#
# The forecast is made **today** for **tomorrow**. So each row is one target day, and next to it we put only
# things the athletic director could know the evening before: today's measured PM2.5 (`obs_today`), and
# forecasts for the target day.

# %%
frames = []
for city, d in daily.groupby("city"):
    d = d.sort_values("date").copy()
    d["obs_today"] = d["obs_pm25"].shift(1)  # shift(1) moves yesterday's value onto this row
    frames.append(d.iloc[1:])  # the first day has no "today" before it
df = pd.concat(frames, ignore_index=True)
df["month"] = df["date"].str[5:7].astype(int)
train, test = df[df["split"] == "train"], df[df["split"] == "test"]

# %% [markdown]
# ## 5. Baselines: three simple forecasts any model has to beat
#
# 1. **Persistence:** tomorrow will be the same as today.
# 2. **Climatology:** tomorrow will be the average for this city and month (averages from the training years only).
# 3. **Raw CAMS:** use the CAMS model's number for the target day as it is.
#
# A warning about baseline 3. Open-Meteo does not keep what CAMS predicted *a day ahead*: we checked, and its
# "previous day" values are empty for 2022 to 2025. The CAMS history it serves is stitched from short-range
# runs, which are closer to the truth than a real day-ahead forecast. So this baseline is **stronger than what
# CAMS could really have told you the evening before**.

# %%
month_mean = train.groupby(["city", "month"])["obs_pm25"].mean().rename("pred_climatology")
df = df.join(month_mean, on=["city", "month"])
df["pred_persistence"] = df["obs_today"]
df["pred_cams"] = df["cams_pm25"]
test = df[df["split"] == "test"]


def score(d, col):
    """Score one forecast column: average error, and how well it calls days above the threshold."""
    real, called = d["obs_pm25"] > THRESHOLD, d[col] > THRESHOLD
    return {
        "mae": round(float((d[col] - d["obs_pm25"]).abs().mean()), 2),  # mean absolute error, µg/m³
        "days": int(len(d)),
        "bad_days": int(real.sum()),                # days that really were above 35
        "caught": int((real & called).sum()),       # bad days we warned about
        "missed": int((real & ~called).sum()),      # bad days with no warning
        "false_alarms": int((~real & called).sum()),  # warnings on days that turned out fine
        "recall": round(float((real & called).sum() / real.sum()), 3) if real.sum() else None,
    }


FORECASTS = ["pred_persistence", "pred_climatology", "pred_cams"]
print("Test year 2025, all six cities")
print(pd.DataFrame({col: score(test, col) for col in FORECASTS}).T)

# %% [markdown]
# On an ordinary day persistence is hard to beat: air quality changes slowly. But look at the day smoke
# **arrives**. On July 30, 2025 Chicago measured 12 µg/m³. The next day it measured 66.

# %%
week = test[(test["city"] == "Chicago") & test["date"].between("2025-07-29", "2025-08-03")]
print(week[["date", "obs_pm25", "pred_persistence", "pred_climatology", "pred_cams"]].round(1).to_string(index=False))

# %% [markdown]
# ## Save the forecasts for the app

# %%
metrics = {
    "threshold": THRESHOLD,
    "test_period": [test["date"].min(), test["date"].max()],
    "overall": {col: score(test, col) for col in FORECASTS},
    "by_city": {city: {col: score(d, col) for col in FORECASTS} for city, d in test.groupby("city")},
}
os.makedirs("data", exist_ok=True)
df[["date", "city", "lat", "lon", "obs_pm25"] + FORECASTS + ["split"]].round(2).to_csv("data/predictions.csv", index=False)
with open("data/metrics.json", "w") as f:
    json.dump(metrics, f, indent=1)
