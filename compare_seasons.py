"""Does a longer history (2018-2024) beat the current model (2022-08-04 to 2024)? Training years only.

Reads data/daily.csv, data/daily_early.csv (fetch_early.py) and the smoke files. 2025 rows are dropped
on the first line that reads them, so nothing here can see the test year. Takes about a minute.

  A  the notebook's model, current training years, held-out blocks 2022 (Aug-Dec), 2023, 2024
  B  the same model without the 3 CAMS inputs (CAMS doesn't exist before 2022-08-04), 2018-2024,
     held-out blocks 2018, 2019, ..., 2024 (whole calendar years)
  C  B plus today's NOAA-mapped smoke 300, 600 and 900 km upwind (fetch_upwind_smoke.py)
  A without CAMS is printed to show what dropping CAMS alone does. It can't be adopted.

The rule, committed before running this: B or C is adopted only if, on the rows A predicts, its average
error is lower than A's (at 2 decimals) AND its warning cost (5 x missed + false alarms, each forecast
with its own best cut-off) is not higher. If both qualify, C must also beat B by the same test.

Run:  python compare_seasons.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

THRESHOLD, COST_OF_A_MISS = 35, 5  # same as the notebook
UPWIND = ["upwind_smoke_300", "upwind_smoke_600", "upwind_smoke_900"]

current = pd.read_csv("data/daily.csv").query("split == 'train'")  # the test year never enters this script
current = current.merge(pd.read_csv("data/smoke_days.csv")[["city", "date", "smoke"]], on=["city", "date"])
current = current.merge(pd.read_csv("data/upwind_smoke.csv")[["city", "date"] + UPWIND], on=["city", "date"])
early = pd.read_csv("data/daily_early.csv")[current.columns]
assert current["date"].max() < "2025-01-01" and early["date"].max() < current["date"].min()


def add_features(df):
    """The notebook's add_features (section 4), plus today's upwind smoke."""
    df = df.sort_values(["city", "date"]).copy()
    by_city = df.groupby("city")
    for k in (1, 2, 3):
        df[f"obs_{k}"] = by_city["obs_pm25"].shift(k)
    df["change_today"] = df["obs_1"] - df["obs_2"]
    df["cams_today"] = by_city["cams_pm25"].shift(1)
    df["cams_max_today"] = by_city["cams_pm25_max"].shift(1)
    df["cams_miss_today"] = df["obs_1"] - df["cams_today"]
    df["smoke_today"] = by_city["smoke"].shift(1)
    for col in UPWIND:
        df[f"{col}_today"] = by_city[col].shift(1)
    region = df.groupby("date").agg(region_max_today=("obs_pm25", "max"), region_mean_today=("obs_pm25", "mean"),
                                    region_smoke_today=("smoke", "max")).shift(1)
    df = df.join(region, on="date")
    df["day_of_year"] = pd.to_datetime(df["date"]).dt.day_of_year
    df["city_id"] = df["city"].astype("category").cat.codes
    return df.dropna(subset=["obs_3"]).reset_index(drop=True)


FEATURES = ["obs_1", "obs_2", "obs_3", "change_today", "region_max_today", "region_mean_today",
            "smoke_today", "region_smoke_today", "cams_today", "cams_max_today", "cams_miss_today",
            "temp_c", "humidity", "precip_mm", "wind_kmh", "wind_u", "wind_v", "day_of_year", "city_id"]
NO_CAMS = [f for f in FEATURES if not f.startswith("cams_")]
WITH_UPWIND = NO_CAMS + [f"{col}_today" for col in UPWIND]


def out_of_fold(rows, features, block):
    """The notebook's Ridge + trees average, each block predicted by a model trained on the other blocks."""
    pred = pd.Series(np.nan, index=rows.index)
    for b in block.unique():
        seen, hidden = rows[block != b], rows[block == b]
        ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(seen[features].drop(columns="city_id"), seen["obs_pm25"])
        trees = HistGradientBoostingRegressor(loss="absolute_error", max_iter=300, learning_rate=0.05, random_state=0,
                                              categorical_features=[features.index("city_id")])
        trees.fit(seen[features], seen["obs_pm25"] - seen["obs_1"])
        from_ridge = ridge.predict(hidden[features].drop(columns="city_id")).clip(min=0)
        pred[hidden.index] = (from_ridge + hidden["obs_1"] + trees.predict(hidden[features])) / 2
    return pred


def summary(rows, pred):
    real = rows["obs_pm25"] > THRESHOLD
    arrival = real & (rows["obs_1"] <= THRESHOLD)  # the day before was fine
    cost = lambda t: COST_OF_A_MISS * (real & (pred <= t)).sum() + (~real & (pred > t)).sum()
    t = float(min(np.arange(10, 45.5, 0.5), key=cost))  # the notebook's cut-off search
    return {"days": len(rows), "bad_days": int(real.sum()), "mae": round(float((pred - rows["obs_pm25"]).abs().mean()), 2),
            "warn_at": t, "caught": int((real & (pred > t)).sum()), "missed": int((real & (pred <= t)).sum()),
            "false_alarms": int((~real & (pred > t)).sum()), "cost": int(cost(t)),
            "arrivals_caught": f"{int((arrival & (pred > t)).sum())} of {int(arrival.sum())}"}


a = add_features(current)
a_block = pd.Series(np.where(a["date"] < "2023-01-01", "2022 (Aug-Dec)", a["date"].str[:4]), index=a.index)
a["A"] = out_of_fold(a, FEATURES, a_block)
a["A without CAMS"] = out_of_fold(a, NO_CAMS, a_block)

# 8 early city-days have no EPA reading; a row can't be used when its target or a lag is one of them.
long = add_features(pd.concat([early, current])).dropna(subset=NO_CAMS + ["obs_pm25"]).reset_index(drop=True)
year = long["date"].str[:4]
long["B"] = out_of_fold(long, NO_CAMS, year)
long["C"] = out_of_fold(long, WITH_UPWIND, year)
print("bad days in each training year:", (long["obs_pm25"] > THRESHOLD).groupby(year).sum().to_dict())

# Score everyone on exactly the rows A predicts. (B and C also have 2022-08-04..06, which A has no history for.)
common = a.merge(long[["city", "date", "B", "C"]], on=["city", "date"], how="left")
assert len(common) == len(a) and common[["B", "C"]].notna().all().all()
variants = ["A", "A without CAMS", "B", "C"]
print("\nThe rows every variant predicts: 2022-08-07 to 2024-12-31")
print(pd.DataFrame({v: summary(common, common[v]) for v in variants}).T.to_string())
print("\nAll 2018-2024 rows (B and C only)")
print(pd.DataFrame({v: summary(long, long[v]) for v in ["B", "C"]}).T.to_string())
print("\nAverage error in each held-out block of the common rows")
by_block = common.groupby(a_block.values)
print(pd.DataFrame({v: by_block.apply(lambda g: (g[v] - g["obs_pm25"]).abs().mean(), include_groups=False)
                    for v in variants}).round(2).to_string())

assert summary(common, common["A"])["mae"] == 2.49, "A should reproduce the notebook's training-year error"
