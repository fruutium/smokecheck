"""Do new inputs help the model? Training years only (2022-08-04 to 2024-12-31); 2025 is never read.

THE RULE, committed before any of these inputs was built or scored:

Inputs tried (all known by the evening before the target day):
  a  naqfc_tomorrow: NOAA NAQFC's forecast for the target day (data/naqfc_dayahead.csv), from the 12Z run
     the day before (about 6 AM Central). 18 training city-days (3 run days) have none: we fill them with
     today's reading (obs_1), for both models. None of the 2025 rows is missing.
  b  today's EPA readings in a ring of 14 metros around our six, from the same EPA daily files:
     Duluth, Fargo, Bismarck, St. Cloud, Sioux Falls, Rochester MN, Des Moines, Cedar Rapids, Green Bay,
     Grand Rapids, Lansing, Indianapolis, Kansas City, Omaha. (The list given in our plan; Grand Forks was on it
     but has no PM2.5 monitor in the EPA files.) Three columns: ring_max_today, ring_mean_today (over the metros
     with a reading that day), and north_max_today = the highest of the 4 ring metros north of 45°N
     (Duluth, Fargo, Bismarck, St. Cloud), the first ones Canadian smoke crosses. Every day has at least one
     ring metro and one north metro, so no filling is needed.
  c  evening_today: this city's mean of EPA hourly readings from 2 PM to 7 PM local standard time today
     (hours starting 14:00 to 18:00; 3-8 PM in summer daylight time, so known by 8 PM). From EPA's hourly files
     (hourly_88101_YYYY.zip). City-days with no hourly reading in that window are filled with obs_1.

Variants, each the notebook's Ridge + trees average with these inputs appended after the current ones:
  current, +a, +b, +c, +a+b, +a+b+c

How they are compared: the notebook's training rows (2022-08-07 to 2024-12-31, 5,268 city-days), the same rows
for every variant; leave-one-block-out (2022 Aug-Dec, 2023, 2024), each block predicted by a model trained on
the other two. Average error (MAE, 2 decimals) and warning cost (5 x missed + false alarms) at the cut-off from
the notebook's best_cut_off (median over 200 week-resampled copies, seed 0) on the out-of-fold forecasts.
The current model must reproduce MAE 2.49 and cost 117 (cut-off 24.5, 19 missed, 22 false alarms).

Decision: take the variant with the lowest MAE (a tie at 2 decimals goes to the one with fewer inputs).
Adopt it only if its MAE is at most 2.44 (at least 0.05 below 2.49) AND its cost is at most 122
(not more than 5 above 117). Otherwise nothing is adopted: we do not fall back to the runner-up.
Warning counts are noisy (38 bad days, mostly one event); the average error is the steady number.
If one is adopted, 2025 is scored exactly once with it. If none is, 2025 is not scored for any variant.

Run:  python compare_features.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

THRESHOLD, COST_OF_A_MISS = 35, 5  # same as the notebook
CUT_OFFS = np.arange(10, 60.5, 0.5)
RING = ["ring_max", "ring_mean", "north_max"]

daily = pd.read_csv("data/daily.csv").query("split == 'train'")  # the test year never enters this script
daily = daily.merge(pd.read_csv("data/smoke_days.csv")[["city", "date", "smoke"]], on=["city", "date"])
daily = daily.merge(pd.read_csv("data/naqfc_dayahead.csv")[["city", "date", "naqfc_pm25"]], on=["city", "date"], how="left")
daily = daily.merge(pd.read_csv("data/ring_pm25.csv")[["date"] + RING], on="date", how="left")
daily = daily.merge(pd.read_csv("data/evening_pm25.csv"), on=["city", "date"], how="left")
assert daily["date"].max() < "2025-01-01" and len(daily) == 6 * daily["date"].nunique()


def add_features(df):
    """The notebook's add_features (section 4), plus the three candidate inputs."""
    df = df.sort_values(["city", "date"]).copy()
    by_city = df.groupby("city")
    for k in (1, 2, 3):
        df[f"obs_{k}"] = by_city["obs_pm25"].shift(k)
    df["change_today"] = df["obs_1"] - df["obs_2"]
    df["cams_today"] = by_city["cams_pm25"].shift(1)
    df["cams_max_today"] = by_city["cams_pm25_max"].shift(1)
    df["cams_miss_today"] = df["obs_1"] - df["cams_today"]
    df["smoke_today"] = by_city["smoke"].shift(1)
    region = df.groupby("date").agg(region_max_today=("obs_pm25", "max"), region_mean_today=("obs_pm25", "mean"),
                                    region_smoke_today=("smoke", "max")).shift(1)
    df = df.join(region, on="date")
    df["day_of_year"] = pd.to_datetime(df["date"]).dt.day_of_year
    df["city_id"] = df["city"].astype("category").cat.codes
    # (a) NOAA's forecast FOR the target day, issued the morning before: no shift. Missing -> today's reading.
    df["naqfc_tomorrow"] = df["naqfc_pm25"].fillna(df["obs_1"])
    # (b) today's ring readings: one value per date, shifted like the region columns above
    df = df.join(df.groupby("date")[RING].first().shift(1).add_suffix("_today"), on="date")
    # (c) this city's 2-7 PM reading today. Missing -> today's daily reading.
    df["evening_today"] = by_city["evening_pm25"].shift(1).fillna(df["obs_1"])
    return df.dropna(subset=["obs_3"]).reset_index(drop=True)


FEATURES = ["obs_1", "obs_2", "obs_3", "change_today", "region_max_today", "region_mean_today",
            "smoke_today", "region_smoke_today", "cams_today", "cams_max_today", "cams_miss_today",
            "temp_c", "humidity", "precip_mm", "wind_kmh", "wind_u", "wind_v", "day_of_year", "city_id"]
A, B, C = ["naqfc_tomorrow"], [f"{c}_today" for c in RING], ["evening_today"]
VARIANTS = {"current": FEATURES, "+a": FEATURES + A, "+b": FEATURES + B, "+c": FEATURES + C,
            "+a+b": FEATURES + A + B, "+a+b+c": FEATURES + A + B + C}


def out_of_fold(rows, features):
    """The notebook's Ridge + trees average, each block predicted by a model trained on the other blocks."""
    pred = pd.Series(np.nan, index=rows.index)
    for b in rows["block"].unique():
        seen, hidden = rows[rows["block"] != b], rows[rows["block"] == b]
        ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(seen[features].drop(columns="city_id"), seen["obs_pm25"])
        trees = HistGradientBoostingRegressor(loss="absolute_error", max_iter=300, learning_rate=0.05, random_state=0,
                                              categorical_features=[features.index("city_id")])
        trees.fit(seen[features], seen["obs_pm25"] - seen["obs_1"])
        from_ridge = ridge.predict(hidden[features].drop(columns="city_id")).clip(min=0)
        pred[hidden.index] = (from_ridge + hidden["obs_1"] + trees.predict(hidden[features])) / 2
    return pred


def cost_by_cut_off(rows, col):
    """The notebook's: 5 x missed + false alarms, for every cut-off in CUT_OFFS at once."""
    real = rows["obs_pm25"].to_numpy()[:, None] > THRESHOLD
    warned = rows[col].to_numpy()[:, None] > CUT_OFFS[None, :]
    return COST_OF_A_MISS * (real & ~warned).sum(axis=0) + (~real & warned).sum(axis=0)


def best_cut_off(rows, col, copies=200):
    """The notebook's: median, over copies made by drawing whole weeks with replacement, of the lowest-cost cut-off."""
    week = pd.to_datetime(rows["date"]).dt.to_period("W").astype(str).to_numpy()
    rows_of_week = {w: np.flatnonzero(week == w) for w in np.unique(week)}
    weeks = list(rows_of_week)
    rng = np.random.default_rng(0)
    best = [CUT_OFFS[np.argmin(cost_by_cut_off(rows.iloc[np.concatenate([rows_of_week[w] for w in rng.choice(weeks, len(weeks))])], col))]
            for _ in range(copies)]
    return float(np.median(best))


def summary(rows, col):
    real, pred = rows["obs_pm25"] > THRESHOLD, rows[col]
    arrival = real & (rows["obs_1"] <= THRESHOLD)  # the day before was fine
    t = best_cut_off(rows, col)
    missed, false_alarms = int((real & (pred <= t)).sum()), int((~real & (pred > t)).sum())
    return {"inputs": len(VARIANTS[col]), "mae": round(float((pred - rows["obs_pm25"]).abs().mean()), 2), "warn_at": t,
            "caught": int((real & (pred > t)).sum()), "missed": missed, "false_alarms": false_alarms,
            "cost": COST_OF_A_MISS * missed + false_alarms,
            "arrivals_caught": f"{int((arrival & (pred > t)).sum())} of {int(arrival.sum())}"}


train = add_features(daily)
train["block"] = np.where(train["date"] < "2023-01-01", "2022 (Aug-Dec)", train["date"].str[:4])
assert len(train) == 5268 and train[sum(VARIANTS.values(), [])].notna().all().all()
for name, features in VARIANTS.items():
    train[name] = out_of_fold(train, features)

table = pd.DataFrame({v: summary(train, v) for v in VARIANTS}).T
print("Training years, 2022-08-07 to 2024-12-31, each block predicted by a model that didn't see it")
print(table.to_string())
print("\nAverage error in each held-out block")
print(pd.DataFrame({v: train.groupby("block").apply(lambda g: (g[v] - g["obs_pm25"]).abs().mean(), include_groups=False)
                    for v in VARIANTS}).round(2).to_string())

current = table.loc["current"]
assert current["mae"] == 2.49 and current["cost"] == 117, "the current model should reproduce the notebook"
best = table.drop(index="current").sort_values(["mae", "inputs"]).index[0]  # lowest error; a tie goes to fewer inputs
adopt = table.loc[best, "mae"] <= current["mae"] - 0.05 and table.loc[best, "cost"] <= current["cost"] + 5
print(f"\nLowest error: {best} ({table.loc[best, 'mae']}, cost {table.loc[best, 'cost']}). Adopt: {bool(adopt)}")
