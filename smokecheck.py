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
# practice by taking today's air-quality readings and tomorrow's weather forecast, and telling them whether to
# expect unhealthy smoke (a daily average above 35 µg/m³ of PM2.5).
#
# **How to run:** Runtime → Run all. It needs no API keys or uploads, and finishes in under a minute.

# %% [markdown]
# ## 1. Load the data
#
# Three small files, all built by the scripts in this repo (`fetch_data.py`, `fetch_smoke.py`, `fetch_dayahead.py`):
#
# - `data/daily.csv`, one row per city per day for six Midwest metro areas:
#   - `obs_pm25`: what EPA monitors **measured**, averaged over the metro area (µg/m³). This is what we forecast.
#   - `cams_pm25`: what the CAMS global air-quality **model** says (via Open-Meteo). An estimate on a 45 km grid, not a measurement.
#   - weather from Open-Meteo: temperature, humidity, rain, wind speed and wind direction (`wind_u`, `wind_v`).
# - `data/smoke_days.csv`: whether NOAA analysts drew a wildfire-smoke plume over the city on satellite images
#   (`smoke`: 0 none, 1 light, 2 medium, 3 heavy).
# - `data/weather_dayahead_2025.csv`: for 2025 only, the weather that was **forecast one day ahead**.
#   Section 7 explains why we need it.
# - `data/naqfc_dayahead.csv`: NOAA's official air-quality forecast (NAQFC), the run issued the morning
#   before each target day. It's a baseline in section 5.

# %%
import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def load(name):
    """Read a file from the repo's data folder, or from GitHub when the notebook runs on its own in Colab."""
    local = f"data/{name}"
    return pd.read_csv(local if os.path.exists(local) else f"https://raw.githubusercontent.com/fruutium/smokecheck/main/{local}")


daily = load("daily.csv").merge(load("smoke_days.csv")[["city", "date", "smoke"]], on=["city", "date"])
daily = daily.merge(load("naqfc_dayahead.csv")[["city", "date", "naqfc_pm25"]], on=["city", "date"], how="left")
dayahead_wx = load("weather_dayahead_2025.csv")

THRESHOLD = 35  # µg/m³, the US EPA 24-hour PM2.5 standard. A "bad day" is a daily average above it.
print(f"{len(daily):,} city-days, {daily['city'].nunique()} cities, {daily['date'].min()} to {daily['date'].max()}")
daily.head()

# %% [markdown]
# ## 2. Look at the data first
#
# Days above 35 µg/m³ are rare (about 1 in 100), and in summer they are almost all wildfire smoke.
# June 2023 (smoke from Quebec) is by far the worst event, so most of the bad days we can learn from come from one event.

# %%
daily["bad"] = daily["obs_pm25"] > THRESHOLD
daily["year"] = daily["date"].str[:4]
print(daily.pivot_table(index="city", columns="year", values="bad", aggfunc="sum", margins=True))

chicago = daily[daily["city"] == "Chicago"].set_index(pd.to_datetime(daily.loc[daily["city"] == "Chicago", "date"]))
ax = chicago[["obs_pm25", "cams_pm25"]].plot(figsize=(11, 3), lw=0.8, title="Chicago: measured PM2.5 vs the CAMS model")
ax.axhline(THRESHOLD, color="red", ls="--", lw=0.8)
ax.set_ylabel("PM2.5 (µg/m³)");

# %% [markdown]
# ## 3. Split by time
#
# We train on earlier dates and test on later ones, and never shuffle days together:
# **train = Aug 2022 to Dec 2024, test = all of 2025.** The test year has its own smoke season
# (June and late July / early August 2025). We don't use it for any choice; we score it once, in section 7.

# %%
print(daily.groupby("split").agg(first_day=("date", "min"), last_day=("date", "max"),
                                 city_days=("date", "size"), bad_days=("bad", "sum")))

# %% [markdown]
# ## 4. What we know the evening before
#
# The athletic director decides the evening before. So each row is one **target day** (tomorrow), and the
# inputs are only things known by then:
#
# - **this city's readings:** today, yesterday and the day before (`obs_1`, `obs_2`, `obs_3`), and today's change
# - **the region:** today's highest and average reading across all six cities. Smoke drifts across the Midwest, so
#   a smoky Minneapolis today can mean a smoky Chicago tomorrow.
# - **smoke maps:** today's NOAA plume over this city, and the heaviest plume over any of the six cities
# - **the CAMS model today**, and how far off it was today compared with the monitors (`cams_miss_today`)
# - **tomorrow's weather forecast:** rain washes smoke out, wind direction says where air comes from
# - the day of the year, and which city it is

# %%
def add_features(df):
    df = df.sort_values(["city", "date"]).copy()
    by_city = df.groupby("city")
    for k in (1, 2, 3):
        df[f"obs_{k}"] = by_city["obs_pm25"].shift(k)  # shift(1) moves today's value onto tomorrow's row
    df["change_today"] = df["obs_1"] - df["obs_2"]
    df["cams_today"] = by_city["cams_pm25"].shift(1)
    df["cams_max_today"] = by_city["cams_pm25_max"].shift(1)
    df["cams_miss_today"] = df["obs_1"] - df["cams_today"]
    df["smoke_today"] = by_city["smoke"].shift(1)
    region = df.groupby("date").agg(region_max_today=("obs_pm25", "max"), region_mean_today=("obs_pm25", "mean"),
                                    region_smoke_today=("smoke", "max")).shift(1)  # shift(1): today's, not tomorrow's
    df = df.join(region, on="date")
    df["day_of_year"] = pd.to_datetime(df["date"]).dt.day_of_year
    df["city_id"] = df["city"].astype("category").cat.codes
    return df.dropna(subset=["obs_3"]).reset_index(drop=True)  # the first three days have no history


FEATURES = ["obs_1", "obs_2", "obs_3", "change_today", "region_max_today", "region_mean_today",
            "smoke_today", "region_smoke_today", "cams_today", "cams_max_today", "cams_miss_today",
            "temp_c", "humidity", "precip_mm", "wind_kmh", "wind_u", "wind_v", "day_of_year", "city_id"]
WEATHER = ["temp_c", "humidity", "precip_mm", "wind_kmh", "wind_u", "wind_v"]

df = add_features(daily)
train = df[df["split"] == "train"].copy()
print(f"training rows: {len(train):,}   features: {len(FEATURES)}")

# %% [markdown]
# ## 5. Baselines: four forecasts our model has to beat
#
# 1. **Persistence:** tomorrow will be the same as today.
# 2. **Climatology:** tomorrow will be the average for this city and month (from the training years only).
# 3. **NOAA's official forecast (NAQFC):** what the US National Air Quality Forecast Capability predicted for the
#    target day's average PM2.5, in its 12Z run the day before (6 am Central). This is the professional forecast
#    an athletic director could really have looked up. We take the grid cell nearest the city centre. Its
#    24-hour window runs 10 pm to 10 pm Central, 22 of the 24 hours of EPA's day. NOAA upgraded the model in May 2024.
# 4. **Raw CAMS:** the CAMS model's number for the target day. Open-Meteo does not keep what CAMS predicted
#    *a day ahead*: we checked, and its "previous day" values are empty for 2022 to 2025. The CAMS history it
#    serves is stitched from short-range runs that already "see" the smoke. So this baseline is **stronger than
#    any real day-ahead forecast**, and we don't let our model use it. We keep it as an optimistic upper bar.

# %%
df["month"] = df["date"].str[5:7].astype(int)
df = df.join(train.assign(month=train["date"].str[5:7].astype(int))
             .groupby(["city", "month"])["obs_pm25"].mean().rename("pred_climatology"), on=["city", "month"])
df["pred_persistence"] = df["obs_1"]
df["pred_noaa"] = df["naqfc_pm25"]
df["pred_cams"] = df["cams_pm25"]
train = df[df["split"] == "train"].copy()

# %% [markdown]
# ## 6. Choose the model and the warning rule, using the training years only
#
# **Checking choices without touching 2025.** We hide one training year at a time (Aug-Dec 2022, 2023, 2024),
# train on the other two, and predict the hidden one. Each year is kept whole, so days are never mixed.
# Every training day then gets a prediction from a model that never saw it.
#
# **Two models, averaged:**
# - a **Ridge regression** (a weighted sum of the inputs). It can go higher than anything it has seen,
#   which matters when smoke is worse than the training years.
# - a **gradient-boosted tree model** that predicts **the change from today**, not the level. Trees can't predict
#   values outside the range they were trained on, but a change added to today's reading can be large.

# %%
def make_ridge():
    # StandardScaler puts every input on the same scale, so Ridge's penalty treats them equally
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0))


def make_trees(loss="absolute_error"):
    return HistGradientBoostingRegressor(loss=loss, max_iter=300, learning_rate=0.05, random_state=0,
                                         categorical_features=[FEATURES.index("city_id")])


def fit(rows):
    ridge = make_ridge().fit(rows[FEATURES].drop(columns="city_id"), rows["obs_pm25"])
    trees = make_trees().fit(rows[FEATURES], rows["obs_pm25"] - rows["obs_1"])
    return ridge, trees


def predict(models, rows):
    ridge, trees = models
    from_ridge = ridge.predict(rows[FEATURES].drop(columns="city_id")).clip(min=0)
    from_trees = rows["obs_1"] + trees.predict(rows[FEATURES])
    return (from_ridge + from_trees) / 2


train["block"] = np.where(train["date"] < "2023-01-01", "2022 (Aug-Dec)", train["date"].str[:4])
train["pred_model"] = np.nan
train["pred_trees_level"] = np.nan  # the version we tried first and dropped (see below)
for block in train["block"].unique():
    seen, hidden = train[train["block"] != block], train[train["block"] == block]
    train.loc[hidden.index, "pred_model"] = predict(fit(seen), hidden)
    plain = make_trees("squared_error").fit(seen[FEATURES], seen["obs_pm25"])
    train.loc[hidden.index, "pred_trees_level"] = plain.predict(hidden[FEATURES])

print("bad days in each training block:", train.groupby("block")["bad"].sum().to_dict())

# %% [markdown]
# **The warning rule.** A forecast becomes a warning ("move practice indoors") when it goes above a cut-off.
# The cut-off doesn't have to be 35: a forecast that tends to come in low should warn earlier.
#
# We decided before looking at any results that **one missed bad day costs as much as 5 false alarms**.
# Sending kids to run in smoke is much worse than an unneeded indoor practice, but if SmokeCheck cries wolf every
# week, the athletic director stops listening. For **every** forecast, baselines included, we pick the cut-off
# with the lowest cost on the training years, so the comparison is fair.

# %%
COST_OF_A_MISS = 5


def warning_counts(rows, col, warn_at):
    real, warned = rows["obs_pm25"] > THRESHOLD, rows[col] > warn_at
    return {"caught": int((real & warned).sum()), "missed": int((real & ~warned).sum()),
            "false_alarms": int((~real & warned).sum())}


def best_cut_off(rows, col):
    rows = rows[rows[col].notna()]  # NOAA has no forecast for 3 run days in 2022-23
    def cost(t):
        c = warning_counts(rows, col, t)
        return COST_OF_A_MISS * c["missed"] + c["false_alarms"]
    return min(np.arange(10, 45.5, 0.5), key=cost)


FORECASTS = ["pred_persistence", "pred_climatology", "pred_noaa", "pred_cams", "pred_model"]
warn_at = {col: float(best_cut_off(train, col)) for col in FORECASTS + ["pred_trees_level"]}


def score(rows, col):
    """Average error, plus warnings using that forecast's own cut-off."""
    rows = rows[rows[col].notna()]
    out = {"mae": round(float((rows[col] - rows["obs_pm25"]).abs().mean()), 2), "days": int(len(rows)),
           "bad_days": int((rows["obs_pm25"] > THRESHOLD).sum()), "warn_at": warn_at[col]}
    out.update(warning_counts(rows, col, warn_at[col]))
    out["recall"] = round(out["caught"] / out["bad_days"], 3) if out["bad_days"] else None
    return out


print("Training years, each predicted by a model that didn't see that year")
print(pd.DataFrame({col: score(train, col) for col in FORECASTS + ["pred_trees_level"]}).T)

# %% [markdown]
# **What we tried and dropped:** one tree model predicting the PM2.5 level directly (`pred_trees_level`).
# Its average error was good, but it caught almost none of the bad days. When 2023 is hidden, the other
# training years have only 2 bad days and a highest reading of 48, and a tree model can't predict above what
# it has seen. Predicting the change from today, and averaging with Ridge, fixed most of that.
#
# **Also tried and dropped: upwind smoke.** Smoke that reaches the Midwest often comes from Canada, so we added
# the heaviest NOAA-mapped smoke 300, 600 and 900 km upwind of each city today (`fetch_upwind_smoke.py`). Upwind
# smoke came before 16 of the 21 training arrival days, against 17% of ordinary days, so the signal is real. But on
# the training-year check it changed nothing (average error 2.49 with or without it), so we left it out. Our guess:
# when 2023 is hidden, the other training years have only 2 bad days, so the model can't learn what upwind smoke means.
# We also noticed that leaving out just six rows moved the training-year warning count by a few days. With 38 bad
# days, mostly from one event, warning numbers are noisy; the average error is much steadier.

# %% [markdown]
# ## 7. The test: 2025, scored once
#
# We train on all the training years and predict every day of 2025.
#
# **Weather honesty.** The weather in our main table is almost the real weather (Open-Meteo stitches it from
# the first hours of each forecast). The evening before, the athletic director only has a forecast. For 2025,
# Open-Meteo keeps the forecast made one day earlier, so **the test uses that day-ahead forecast**. (We had to
# train on the stitched weather, because day-ahead forecasts don't exist for 2022-2023.)

# %%
models = fit(train)
test = df[df["split"] == "test"].copy()
test["pred_model_with_stitched_weather"] = predict(models, test)  # for comparison only
test = test.drop(columns=WEATHER).merge(dayahead_wx, on=["city", "date"])
test["pred_model"] = predict(models, test)
warn_at["pred_model_with_stitched_weather"] = warn_at["pred_model"]

results = pd.DataFrame({col: score(test, col) for col in FORECASTS + ["pred_model_with_stitched_weather"]}).T
print("Test year 2025, all six cities")
results

# %% [markdown]
# ### How sure is the forecast? A likely range
#
# One number hides how unsure we are, so each forecast also gets a range meant to hold the measurement 8 days out
# of 10. We sort the training days into groups by how high their out-of-fold forecast was, split at the 20th, 40th,
# 60th and 80th percentile, with forecasts above the warning cut-off as their own top group. In each group we take
# the 10th and 90th percentile of (measured − forecast), and a new forecast's range is the forecast plus those two
# numbers (never below 0).
# The ranges come only from the training years, so 80% there holds by construction; 2025 is the real check.

# %%
RANGE_EDGES = [round(float(x), 1) for x in train["pred_model"].quantile([0.2, 0.4, 0.6, 0.8])] + [warn_at["pred_model"]]


def range_bin(rows):
    # -inf: the trees half can push a forecast slightly below 0
    return pd.cut(rows["pred_model"], [-np.inf] + RANGE_EDGES + [np.inf], right=False)


miss = train["obs_pm25"] - train["pred_model"]  # positive = the measurement came in higher than the forecast
offsets = miss.groupby(range_bin(train), observed=True).quantile([0.1, 0.9]).unstack()


def add_range(rows):
    rows["range_lo"] = (rows["pred_model"] + range_bin(rows).map(offsets[0.1]).astype(float)).clip(lower=0)
    rows["range_hi"] = rows["pred_model"] + range_bin(rows).map(offsets[0.9]).astype(float)
    assert rows[["range_lo", "range_hi"]].notna().all().all()


def coverage(rows):
    inside = rows["obs_pm25"].between(rows["range_lo"], rows["range_hi"])
    width = rows["range_hi"] - rows["range_lo"]
    groups = {"all": inside == inside, "top_bin": rows["pred_model"] >= RANGE_EDGES[-1],
              "bad_days": rows["obs_pm25"] > THRESHOLD, "smoke_days": rows["smoke"] >= 2}
    return {g: {"days": int(m.sum()), "inside": round(float(inside[m].mean()), 3),
                "median_width": round(float(width[m].median()), 1)} for g, m in groups.items()}


add_range(train)
add_range(test)
print("Offsets added to the forecast in each group (µg/m³):")
print(offsets.round(1).rename(columns={0.1: "low (10th pct)", 0.9: "high (90th pct)"}))
print("\nShare of days whose measurement fell inside the range (target 0.8):")
print(pd.concat({"training years (in-sample)": pd.DataFrame(coverage(train)).T,
                 "test 2025": pd.DataFrame(coverage(test)).T}).astype({"days": int}))

# %% [markdown]
# ## 8. Where it works and where it fails
#
# **Arrival days vs continuing days.** A bad day is an *arrival* when the day before was fine (35 or below),
# and *continuing* when the day before was already bad. Persistence can never warn on an arrival day, because
# it always repeats today. Arrival days are where a forecast proves it's worth having.

# %%
test["is_smoke_day"] = test["smoke"] >= 2  # NOAA drew a medium or heavy plume over the city on the target day
bad = test[test["obs_pm25"] > THRESHOLD].copy()
bad["kind"] = np.where(bad["obs_1"] > THRESHOLD, "continuing", "arrival")
for col in ["pred_persistence", "pred_noaa", "pred_cams", "pred_model"]:
    bad[col.removeprefix("pred_") + "_warned"] = bad[col] > warn_at[col]
print(bad.groupby("kind")[["persistence_warned", "noaa_warned", "cams_warned", "model_warned"]].agg(["sum", "size"]))

# %%
print("Every bad day in 2025:")
print(bad[["date", "city", "kind", "obs_pm25", "obs_1", "pred_persistence", "pred_noaa", "pred_cams", "pred_model", "smoke"]]
      .round(1).sort_values("date").to_string(index=False))

# %%
false_alarms = test[(test["obs_pm25"] <= THRESHOLD) & (test["pred_model"] > warn_at["pred_model"])]
print(f"Model false alarms in 2025: {len(false_alarms)}")
print(false_alarms[["date", "city", "obs_pm25", "obs_1", "pred_model", "smoke"]].round(1).to_string(index=False))

# %% [markdown]
# **By city, and smoke days vs clean days** (average error, µg/m³)

# %%
by_city = test.groupby("city").apply(lambda g: pd.Series({c.removeprefix("pred_"): score(g, c)["mae"] for c in FORECASTS}),
                                     include_groups=False)
by_smoke = test.groupby("is_smoke_day").apply(lambda g: pd.Series({c.removeprefix("pred_"): score(g, c)["mae"] for c in FORECASTS}),
                                              include_groups=False)
print(by_city, "\n")
print(by_smoke.rename(index={False: "clean (no medium/heavy plume)", True: "smoke day"}))

# %% [markdown]
# ## 9. The demo day: Thursday, July 31, 2025 in Chicago
#
# On July 30, Chicago measured 12 µg/m³. On the 31st it measured 66.

# %%
week = test[(test["city"] == "Chicago") & test["date"].between("2025-07-29", "2025-08-03")]
print({c: warn_at[c] for c in ["pred_persistence", "pred_noaa", "pred_cams", "pred_model"]}, "<- warn above these")
print(week[["date", "obs_pm25", "pred_persistence", "pred_noaa", "pred_cams", "pred_model", "region_max_today", "smoke_today"]]
      .round(1).to_string(index=False))

# %% [markdown]
# ## 10. Limits we know about
#
# - **One smoke event dominates training.** 36 of the 38 bad training days are from 2023, mostly one June event.
# - **"Today" isn't fully known in the evening.** We use today's full-day average; at 6 pm the last hours are missing.
# - **Smoke maps use UTC days**, 5-6 hours ahead of Chicago, and analysts may finish them late in the day.
#   Light plumes don't count as smoke days, and 12 of the 35 bad test days had only a light plume or none.
# - **Weather mismatch:** trained on near-real weather, tested on day-ahead forecasts (section 7).
# - **CAMS is a 45 km model estimate**, and its archive isn't a real day-ahead forecast (section 5).
# - Six cities, 2.4 years of training data. Monitors are averaged over each metro area, so one neighbourhood can be worse.

# %% [markdown]
# ## 11. Save the forecasts for the app

# %%
metrics = {
    "threshold": THRESHOLD,
    "cost_of_a_miss": COST_OF_A_MISS,
    "warn_at": {c: warn_at[c] for c in FORECASTS},
    "test_period": [test["date"].min(), test["date"].max()],
    "overall": {c: score(test, c) for c in FORECASTS},
    "by_city": {city: {c: score(g, c) for c in FORECASTS} for city, g in test.groupby("city")},
    "by_smoke": {("smoke_day" if k else "clean_day"): {c: score(g, c) for c in FORECASTS} for k, g in test.groupby("is_smoke_day")},
    "training_years_out_of_fold": {c: score(train, c) for c in FORECASTS},
}
train["is_smoke_day"] = train["smoke"] >= 2
cols = ["date", "city", "lat", "lon", "obs_pm25"] + FORECASTS + ["is_smoke_day", "split"]
cols += ["range_lo", "range_hi"]  # not pred_*: the app shows every pred_* column as its own forecaster
metrics["forecast_range"] = {"method": "10th-90th percentile of training out-of-fold misses, by forecast level",
                             "level": 0.8, "bin_edges": RANGE_EDGES, "offsets_low_high": offsets.round(2).values.tolist(),
                             "coverage_train_in_sample": coverage(train), "coverage_test": coverage(test)}
os.makedirs("data", exist_ok=True)
pd.concat([train[cols], test[cols]]).sort_values(["city", "date"]).round(2).to_csv("data/predictions.csv", index=False)
with open("data/metrics.json", "w") as f:
    json.dump(metrics, f, indent=1)
print("saved data/predictions.csv and data/metrics.json")

# %% [markdown]
# ## Sources
#
# - **EPA AirData** daily PM2.5 (parameter 88101), https://aqs.epa.gov/aqsweb/airdata/download_files.html
# - **CAMS global atmospheric composition forecasts** (Copernicus Atmosphere Monitoring Service) via the
#   **Open-Meteo Air Quality API**, https://open-meteo.com/en/docs/air-quality-api
# - **Open-Meteo** Historical Forecast API and Previous Runs API (weather), https://open-meteo.com
# - **NOAA National Air Quality Forecast Capability (NAQFC)** PM2.5 forecasts, NOAA Open Data on AWS,
#   https://registry.opendata.aws/noaa-nws-naqfc-pds/ (bias-corrected 24-hour average, CONUS 5 km grid)
# - **NOAA Hazard Mapping System** smoke polygons, https://www.ospo.noaa.gov/products/land/hms.html
# - Libraries: pandas, NumPy, scikit-learn, matplotlib, pyshp, eccodes (reads NOAA's GRIB files), jupytext
# - AI tools: Claude (Anthropic), through Claude Code. It wrote most of the code (data scripts, this notebook, the app)
#   and ran the experiments, researched which datasets and forecast archives to use, and drafted the write-up.
#   We chose the track and project and picked which ideas to try from the options it proposed.
