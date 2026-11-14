"""Build data/daily_early.csv: the extra TRAINING days 2018-01-01 to 2022-08-03, just before
data/daily.csv starts. One row per city per day, with the columns of daily.csv plus the smoke
columns of smoke_days.csv and upwind_smoke.csv. No API keys needed.

Why: 36 of the 38 bad days in 2022-2024 come from 2023, so a model that hides 2023 has almost
nothing to learn from. More years add more smoke seasons (2020, 2021). The locked files
(daily.csv and the rest) are not touched; the notebook stacks this file under them.

- CAMS PM2.5 is empty on Open-Meteo before 2022-08-04 (we checked: every hour is null),
  so cams_pm25, cams_pm25_max are NaN and cams_hours is 0 on every row here.
- Weather comes from the same Open-Meteo Historical Forecast API as daily.csv. It covers 2018 on,
  and its default model here is the same NOAA one (GFS/HRRR) as in 2022-2025 (we compared values),
  so it carries the same caveat: stitched from the first hours of each run, almost the real weather.
  We checked that every city-day has all 24 hours of every weather variable.
- A few city-days have no EPA reading. They stay in the file with obs_pm25 empty; we don't fill them in.

Run:  python fetch_early.py   (after fetch_data.py and fetch_smoke.py; new raw files go to data/raw_new/)
"""
import pathlib

import pandas as pd
import shapefile  # the "pyshp" package: reads shapefiles in plain Python

import fetch_smoke
import fetch_upwind_smoke
from fetch_data import CITIES, RAW, epa_daily, model_daily

EARLY_START, EARLY_END = "2018-01-01", "2022-08-03"
RAW_NEW = pathlib.Path("data/raw_new")  # new downloads only; data/raw/ keeps the 2022-2026 files


def build():
    # 2018-2021 are new downloads; Jan-Jul 2022 comes from the 2022 file fetch_data.py already saved.
    obs = pd.concat([epa_daily(range(2018, 2022), RAW_NEW), epa_daily([2022], RAW)])
    # end one day later in UTC, so the last local-time day has all 24 hours
    model = pd.concat(model_daily(city, EARLY_START, "2022-08-04") for city in CITIES)
    df = model.merge(obs, on=["city", "date"], how="left")
    df = df[(df["date"] >= EARLY_START) & (df["date"] <= EARLY_END)].copy()
    # CAMS starts at 00 UTC on 2022-08-04, which is the evening of 2022-08-03 here, so that last
    # day gets 5-6 CAMS hours. An average of a few evening hours would mislead, so we blank it.
    df.loc[df["cams_hours"] < 24, ["cams_pm25", "cams_pm25_max"]] = float("nan")
    df["lat"] = df["city"].map(lambda c: CITIES[c][1])
    df["lon"] = df["city"].map(lambda c: CITIES[c][2])
    df["split"] = "train"  # every early day is training data; the test year stays 2025

    smoke = fetch_smoke.build(EARLY_START, EARLY_END, RAW_NEW / "hms")  # downloads the missing HMS zips
    upwind = fetch_upwind_smoke.build(df[["city", "date", "wind_u", "wind_v"]], RAW_NEW / "hms")
    df = df.merge(smoke[["city", "date", "smoke", "hms_file"]], on=["city", "date"]).merge(upwind, on=["city", "date"])
    return df.sort_values(["city", "date"]).round(2).reset_index(drop=True)


def check(df):
    """Fail loudly if the table is not what the notebook expects."""
    assert not df.duplicated(["city", "date"]).any(), "duplicate city-day rows"
    days = pd.date_range(EARLY_START, EARLY_END).strftime("%Y-%m-%d")
    for city, d in df.groupby("city"):
        assert list(d["date"]) == list(days), f"{city}: missing calendar days"
    assert list(df.columns[:16]) == list(pd.read_csv("data/daily.csv", nrows=0).columns), "columns differ from daily.csv"
    assert (df["split"] == "train").all() and df["date"].max() < "2022-08-04", "early rows must all be training days"
    # Exactly these city-days have no EPA reading (Madison 5, Detroit 3). A new gap means something changed.
    missing = df.loc[df["obs_pm25"].isna(), "city"].value_counts().to_dict()
    assert missing == {"Madison": 5, "Detroit": 3}, f"unexpected EPA gaps: {missing}"
    assert df["cams_pm25"].isna().all() and (df["cams_hours"] < 24).all(), "CAMS should be empty before 2022-08-04"
    weather = ["temp_c", "humidity", "precip_mm", "wind_kmh", "wind_u", "wind_v"]
    assert df[weather].notna().all().all(), "a day is missing weather"
    assert df["smoke"].isin([0, 1, 2, 3]).all() and df["upwind_smoke_max"].isin([0, 1, 2, 3]).all()
    # smoke_levels() treats each outline as one simple ring; check that holds in the old files too.
    for path in sorted((RAW_NEW / "hms").glob("hms_smoke*.zip")):
        if path.stat().st_size > 0:
            with shapefile.Reader(str(path)) as r:  # "with" closes the file; 1,676 open files is too many
                assert all(len(s.parts) == 1 for s in r.shapes()), f"{path}: multi-ring outline"
    # A known smoke event: July 2021 smoke from Canadian fires in Minneapolis.
    mpls = df[df["city"] == "Minneapolis"].set_index("date")
    assert mpls.loc["2021-07-29", "obs_pm25"] > 60 and mpls.loc["2021-07-29", "smoke"] >= 2


if __name__ == "__main__":
    df = build()
    check(df)
    df.to_csv("data/daily_early.csv", index=False)
    print("days with no HMS file:", (~df["hms_file"]).sum() // len(CITIES))
    df["year"] = df["date"].str[:4]
    print(df.groupby(["city", "year"])["obs_pm25"].apply(lambda s: int((s > 35).sum())).unstack().assign(
        total=lambda t: t.sum(axis=1)))
