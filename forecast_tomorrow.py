"""SmokeCheck live: forecast TOMORROW's daily-average PM2.5 for our six cities, from data known this evening.

What it does:
  1. Refits the exact model tested in the notebook (smokecheck.py, sections 4, 6 and 7) from the repo's CSVs,
     predicts the 2025 test year again and stops if that doesn't match data/predictions.csv within 0.01 µg/m³.
  2. Rebuilds the 24 model inputs for tomorrow from live public data (no API keys), the same way the
     fetch_*.py scripts built the training columns, and runs the notebook's own add_features() on them.
  3. Writes data/tomorrow.csv: one row per city, with a `status` column that names every missing input
     or fallback. A city with no AirNow readings gets no forecast.

Run (from anywhere):
    <venv python> forecast_tomorrow.py            # tonight's forecast -> data/tomorrow.csv
    <venv python> forecast_tomorrow.py --parity   # compare our AirNow numbers with EPA's archive on 2025 days

Sources (all public, no keys):
  - AirNow hourly files (files.airnowtech.org): this city's, the region's and the ring's PM2.5 readings.
    We keep only the monitor sites EPA's daily files place in each metro area (matched by AQS site ID).
  - EPA AirData daily files (aqs.epa.gov/aqsweb/airdata): only to know which sites belong to which metro area.
  - NOAA NAQFC on AWS (noaa-nws-naqfc-pds): today's 12Z bias-corrected 24-hour PM2.5 forecast for tomorrow.
  - NOAA HMS smoke polygons (satepsanone.nesdis.noaa.gov): today's smoke plumes over each city.
  - Open-Meteo: CAMS PM2.5 for today (air-quality API) and the weather forecast for tomorrow (forecast API).

Limits (say these out loud):
  - The model is frozen as tested on 2025 (trained on Aug 2022 - Dec 2024). It never saw this season.
  - Live readings are preliminary AirNow data, not EPA's checked archive the model was trained on. AirNow has
    only continuous monitors, so filter-only sites drop out (see the parity check, --parity).
  - Today's mean is partial: only the hours reported so far (`hours_today`). The model was trained on full days.
  - Before about 7 PM Central the 2-7 PM reading is partial or missing (status says which).
  - Today's CAMS mixes past hours with forecast hours; today's HMS smoke file is updated during the day.
  - Training weather was the stitched archive weather of the target day; here it is tomorrow's forecast,
    the same swap section 7 makes for the 2025 test.
"""
import csv
import io
import json
import os
import pathlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

os.chdir(pathlib.Path(__file__).resolve().parent)  # the data/ paths below are relative to the repo root

# Reused, not copied, so the definitions can't drift apart from the ones that built the training CSVs.
from fetch_data import CITIES, open_meteo_hourly  # noqa: E402  city -> (EPA metro name, lat, lon, UTC offset)
from fetch_evening import HOURS  # noqa: E402  the 2-7 PM window, hours starting 14:00 to 18:00 local standard
from fetch_naqfc import URL as NAQFC_URL, read_run, run_path  # noqa: E402
from fetch_ring import NORTH, RING  # noqa: E402  the 14 ring metros and the 4 north of 45°N
from fetch_smoke import get, smoke_levels  # noqa: E402  get() returns b"" on a 404

CACHE = pathlib.Path("data/raw_new")  # git-ignored
AIRNOW = "https://files.airnowtech.org/airnow"
HMS = "https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile"
NOTES = pathlib.Path.home() / ("Library/Application Support/Claude/side-session-notes/"
                               "local_66091600-8541-4983-a483-184329d20e50/live-parity.md")


# ---------------------------------------------------------------------------------------------------------------
# 1. The tested model. Copied from smokecheck.py: data loading from section 1, add_features and FEATURES from
#    section 4, make_ridge / make_trees / fit / predict from section 6, and the 2025 weather swap from section 7.
# ---------------------------------------------------------------------------------------------------------------
def load(name):
    return pd.read_csv(f"data/{name}")


def add_features(df):  # smokecheck.py section 4, unchanged
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
    # NOAA's forecast FOR the target day, issued the morning before, so no shift. Missing (18 rows) -> today's reading.
    df["naqfc_tomorrow"] = df["naqfc_pm25"].fillna(df["obs_1"])
    ring = df.groupby("date")[["ring_max", "ring_mean", "north_max"]].first().shift(1)  # shift(1): today's ring
    df = df.join(ring.add_suffix("_today"), on="date")
    df["evening_today"] = by_city["evening_pm25"].shift(1)  # this afternoon, 2-7 PM
    return df.dropna(subset=["obs_3"]).reset_index(drop=True)  # the first three days have no history


FEATURES = ["obs_1", "obs_2", "obs_3", "change_today", "region_max_today", "region_mean_today",
            "smoke_today", "region_smoke_today", "cams_today", "cams_max_today", "cams_miss_today",
            "temp_c", "humidity", "precip_mm", "wind_kmh", "wind_u", "wind_v", "day_of_year", "city_id",
            "naqfc_tomorrow", "ring_max_today", "ring_mean_today", "north_max_today", "evening_today"]
WEATHER = ["temp_c", "humidity", "precip_mm", "wind_kmh", "wind_u", "wind_v"]


def make_ridge():  # smokecheck.py section 6, unchanged
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


def tested_model():
    """Refit on the training years exactly like section 7, and prove it is the tested model by
    re-predicting 2025 (with the day-ahead weather swap) and comparing with data/predictions.csv."""
    daily = load("daily.csv").merge(load("smoke_days.csv")[["city", "date", "smoke"]], on=["city", "date"])
    daily = daily.merge(load("naqfc_dayahead.csv")[["city", "date", "naqfc_pm25"]], on=["city", "date"], how="left")
    daily = daily.merge(load("ring_pm25.csv")[["date", "ring_max", "ring_mean", "north_max"]], on="date", how="left")
    daily = daily.merge(load("evening_pm25.csv")[["city", "date", "evening_pm25"]], on=["city", "date"], how="left")
    df = add_features(daily)
    models = fit(df[df["split"] == "train"])
    test = df[df["split"] == "test"].drop(columns=WEATHER).merge(load("weather_dayahead_2025.csv"), on=["city", "date"])
    test["pred_model"] = predict(models, test)
    saved = load("predictions.csv").query("split == 'test'")[["city", "date", "pred_model"]]
    both = test.merge(saved, on=["city", "date"], suffixes=("", "_saved"))
    assert len(both) == len(saved) == len(test) == 365 * 6, "2025 rows don't line up with data/predictions.csv"
    max_diff = float((both["pred_model"] - both["pred_model_saved"]).abs().max())
    assert max_diff < 0.01, f"refit model is NOT the tested one: max difference {max_diff:.4f} µg/m³ on 2025"
    return models, max_diff


# ---------------------------------------------------------------------------------------------------------------
# 2. AirNow readings, averaged the way fetch_data.py / fetch_evening.py average EPA's.
# ---------------------------------------------------------------------------------------------------------------
def cached_get(url, path, reuse):
    """The bytes at url, saved at path. Reuse a saved copy only when `reuse` (files that can still change, like
    the last few AirNow hours or today's smoke map, are fetched fresh). A 404 is never saved, so we ask again later."""
    if reuse and path.exists():
        return path.read_bytes()
    try:
        data = get(url)
    except Exception:  # network hiccup: wait and try once more; a second failure stops the script
        time.sleep(3)
        data = get(url)
    if data:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")  # write then rename, so a killed run never leaves half a file
        tmp.write_bytes(data)
        tmp.rename(path)
    return data


def epa_sites(cities):
    """AQS site ID -> metro name, from the EPA daily files, using the same "metro name starts with" rule as
    fetch_data.epa_daily. 2025 for the parity days, 2026 so monitors added this year count too."""
    frames = []
    for year in (2025, 2026):
        path = pathlib.Path(f"data/raw/daily_88101_{year}.zip")  # same cache as fetch_data.py
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"https://aqs.epa.gov/aqsweb/airdata/{path.name}", path)
        frames.append(pd.read_csv(path, dtype=str, usecols=["State Code", "County Code", "Site Num", "CBSA Name"]))
    d = pd.concat(frames).drop_duplicates()
    d["aqsid"] = d["State Code"] + d["County Code"] + d["Site Num"]  # e.g. 17 + 031 + 0076 = AirNow's 170310076
    rows = [d[d["CBSA Name"].fillna("").str.startswith(cbsa)].assign(city=name)
            for name, (cbsa, *_rest) in cities.items()]
    return pd.concat(rows)[["aqsid", "city"]].drop_duplicates()


def airnow_hour(utc):
    """PM2.5 readings in one AirNow hourly file (named by UTC hour), with each site's local STANDARD date and hour.
    Empty if the file isn't there (yet)."""
    name = f"HourlyData_{utc:%Y%m%d%H}.dat"
    old = utc < datetime.now(timezone.utc) - timedelta(hours=3)  # late monitors can still fill in the last hours
    data = cached_get(f"{AIRNOW}/{utc:%Y}/{utc:%Y%m%d}/{name}", CACHE / "airnow" / name, reuse=old)
    if not data:
        return pd.DataFrame()
    cols = ["date", "time", "aqsid", "site", "utc_offset", "param", "units", "value", "source"]
    h = pd.read_csv(io.BytesIO(data), sep="|", header=None, names=cols, dtype=str,
                    encoding="latin-1", quoting=csv.QUOTE_NONE)
    h = h[(h["param"] == "PM2.5") & (h["units"] == "UG/M3")].copy()
    # US sites come either as 9 digits or with the country code 840 in front; strip it so both match EPA's ID
    us12 = (h["aqsid"].str.len() == 12) & h["aqsid"].str.startswith("840")
    h.loc[us12, "aqsid"] = h.loc[us12, "aqsid"].str[3:]
    h["pm25"] = pd.to_numeric(h["value"], errors="coerce")
    h = h[h["pm25"] > -900]  # drop "no data" codes like -999; small negatives stay, as in EPA's files
    # The offset in each row is the site's standard-time offset (-6 Central, -5 Eastern), all year round, so
    # this gives EPA's "local standard time" day without us hard-coding a time zone per city.
    local = pd.Timestamp(utc.replace(tzinfo=None)) + pd.to_timedelta(h["utc_offset"].astype(float), unit="h")
    h["date_local"] = local.dt.strftime("%Y-%m-%d")
    h["hour_local"] = local.dt.strftime("%H:00")
    return h[["aqsid", "date_local", "hour_local", "pm25"]]


def airnow_hours(first_utc, last_utc):
    hours = pd.date_range(first_utc, last_utc, freq="h").to_pydatetime()
    with ThreadPoolExecutor(max_workers=8) as pool:  # 8 at a time, like the other fetch scripts
        return pd.concat(pool.map(airnow_hour, hours))


def by_city_day(h, sites, evening_hours=HOURS):
    """Per metro and local day: the daily mean (obs_pm25), how many sites and hours went in, and the 2-7 PM mean.
    Same order as EPA's numbers: one value per site per hour first (a site with two instruments counts once),
    then per site per day, then the average over the metro's sites."""
    h = h.merge(sites, on="aqsid")
    site_hour = h.groupby(["city", "date_local", "aqsid", "hour_local"])["pm25"].mean().reset_index()
    site_day = site_hour.groupby(["city", "date_local", "aqsid"])["pm25"].mean()
    out = site_day.groupby(["city", "date_local"]).agg(obs_pm25="mean", sites="size")
    out["hours"] = site_hour.groupby(["city", "date_local"])["hour_local"].nunique()
    eve = site_hour[site_hour["hour_local"].isin(evening_hours)]
    eve_site = eve.groupby(["city", "date_local", "aqsid"])["pm25"].mean()
    out["evening_pm25"] = eve_site.groupby(["city", "date_local"]).mean()
    out["evening_sites"] = eve_site.groupby(["city", "date_local"]).size()
    out["evening_hours"] = eve.groupby(["city", "date_local"])["hour_local"].nunique()
    return out.reset_index().rename(columns={"date_local": "date"})


def ring_by_day(ring):
    """fetch_ring.py's three numbers per day, over the ring metros that have a reading."""
    wide = ring.pivot(index="date", columns="city", values="obs_pm25")
    return pd.DataFrame({"ring_max": wide.max(axis=1), "ring_mean": wide.mean(axis=1),
                         "north_max": wide.reindex(columns=NORTH).max(axis=1),
                         "ring_metros": wide.notna().sum(axis=1)})


# ---------------------------------------------------------------------------------------------------------------
# 3. The other live inputs.
# ---------------------------------------------------------------------------------------------------------------
def open_meteo_local_day(url, city, day, variables):
    """Hourly Open-Meteo values for one city over one local-standard-time day (24 hours, or it fails)."""
    _cbsa, lat, lon, utc_offset = CITIES[city]
    h = open_meteo_hourly(url, lat, lon, variables, start=day, end=f"{pd.Timestamp(day) + pd.Timedelta(days=1):%Y-%m-%d}")
    h.index = h.index + pd.Timedelta(hours=utc_offset)  # UTC -> local standard time, as fetch_data.model_daily
    h = h[h.index.strftime("%Y-%m-%d") == day].dropna()
    assert len(h) == 24, f"{city} {day}: Open-Meteo gave {len(h)} of 24 hours"
    return h


def cams_today(city, today):
    h = open_meteo_local_day("https://air-quality-api.open-meteo.com/v1/air-quality", city, today, ["pm2_5"])
    return {"cams_pm25": h["pm2_5"].mean(), "cams_pm25_max": h["pm2_5"].max()}


def weather_tomorrow(city, target):
    """Tomorrow's forecast weather, averaged exactly like fetch_data.model_daily (wind split into u and v first)."""
    h = open_meteo_local_day("https://api.open-meteo.com/v1/forecast", city, target, [
        "temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"])
    rad = np.deg2rad(h["wind_direction_10m"])
    h["wind_u"] = -h["wind_speed_10m"] * np.sin(rad)
    h["wind_v"] = -h["wind_speed_10m"] * np.cos(rad)
    return {"temp_c": h["temperature_2m"].mean(), "humidity": h["relative_humidity_2m"].mean(),
            "precip_mm": h["precipitation"].sum(), "wind_kmh": h["wind_speed_10m"].mean(),
            "wind_u": h["wind_u"].mean(), "wind_v": h["wind_v"].mean()}


def try_or_none(fn, *args):
    """Run one live download; on failure print why and return None, so that input shows up as missing."""
    try:
        return fn(*args)
    except Exception as e:
        print(f"  {fn.__name__}{args}: {e}")
        return None


def smoke_today(today):
    """Heaviest HMS smoke level (0-3) over each city today, or None if NOAA hasn't posted today's file yet."""
    day = pd.Timestamp(today)
    name = f"hms_smoke{day:%Y%m%d}.zip"
    path = CACHE / "hms" / name
    if not cached_get(f"{HMS}/{day:%Y}/{day:%m}/{name}", path, reuse=False):  # today's map is still being drawn
        return None
    return dict(zip(CITIES, smoke_levels(path)))


def naqfc_for(target):
    """NAQFC for the target day from the 12Z run of the day before (same file, cell and window as
    fetch_naqfc.py), or None if that run isn't published yet (it comes out around noon Central)."""
    run = pd.Timestamp(target) - pd.Timedelta(days=1)
    path, key, _model = run_path(run)
    if not path.exists() or path.stat().st_size == 0:  # an empty file is fetch_naqfc.py's "404" marker: ask again
        path.unlink(missing_ok=True)
        if not cached_get(f"{NAQFC_URL}/{key}", path, reuse=False):
            return None
    values, _cells = read_run(path, pd.Timestamp(target), None)
    return dict(zip(CITIES, values))


# ---------------------------------------------------------------------------------------------------------------
# 4. Tonight's forecast.
# ---------------------------------------------------------------------------------------------------------------
def forecast():
    started = time.time()
    models, max_diff = tested_model()
    print(f"refit check passed: 2025 predictions match data/predictions.csv (max difference {max_diff:.4f} µg/m³)")

    now_utc = datetime.now(timezone.utc)
    made_at = now_utc.astimezone(ZoneInfo("America/Chicago")).isoformat(timespec="seconds")
    # "Today" is the local STANDARD time day in Central (EPA's day), so it never jumps an hour in summer.
    today = (now_utc - timedelta(hours=6)).date()
    days = [f"{today - timedelta(days=k):%Y-%m-%d}" for k in (2, 1, 0)]  # day before, yesterday, today
    target = f"{today + timedelta(days=1):%Y-%m-%d}"
    print(f"made at {made_at}: forecasting {target} from {days}")

    # AirNow: from the first hour of the day before (05Z starts an Eastern day) up to now.
    first = datetime(today.year, today.month, today.day, 5, tzinfo=timezone.utc) - timedelta(days=2)
    hours = airnow_hours(first, now_utc.replace(minute=0, second=0, microsecond=0))
    obs = by_city_day(hours, epa_sites(CITIES))
    ring = ring_by_day(by_city_day(hours, epa_sites(RING)))

    cams = {c: try_or_none(cams_today, c, days[-1]) for c in CITIES}
    weather = {c: try_or_none(weather_tomorrow, c, target) for c in CITIES}
    smoke = try_or_none(smoke_today, days[-1])
    naqfc = try_or_none(naqfc_for, target)

    # One frame shaped like the notebook's `daily` (same columns), 4 days x 6 cities, so the notebook's own
    # add_features() makes tomorrow's row: shifts, region numbers, ring shift, NAQFC fallback and city_id included.
    frame = pd.DataFrame([(c, d) for c in CITIES for d in days + [target]], columns=["city", "date"])
    frame = frame.merge(obs[["city", "date", "obs_pm25", "evening_pm25"]], on=["city", "date"], how="left")
    frame = frame.merge(ring[["ring_max", "ring_mean", "north_max"]], left_on="date", right_index=True, how="left")
    notes = {c: [] for c in CITIES}
    is_today, is_target = frame["date"] == days[-1], frame["date"] == target
    for c in CITIES:
        row_today, row_target = is_today & (frame["city"] == c), is_target & (frame["city"] == c)
        for col, val in (cams[c] or {"cams_pm25": np.nan, "cams_pm25_max": np.nan}).items():
            frame.loc[row_today, col] = val
        for col, val in (weather[c] or dict.fromkeys(WEATHER, np.nan)).items():
            frame.loc[row_target, col] = val
        frame.loc[row_today, "smoke"] = smoke[c] if smoke else 0
        frame.loc[row_target, "naqfc_pm25"] = naqfc[c] if naqfc else np.nan
        if not smoke:
            notes[c].append("no HMS smoke file for today yet, smoke = 0 (as training does when a file is missing)")
        if not naqfc:
            notes[c].append("today's 12Z NAQFC run not out, naqfc_tomorrow = today's reading (notebook's fallback)")
    frame["smoke"] = frame["smoke"].fillna(0)  # smoke only matters on today's row (it is shifted onto tomorrow)

    # The 2-7 PM reading: if none of today's window is in yet, use today's mean so far, and say so.
    for c in CITIES:
        today_obs = obs[(obs["city"] == c) & (obs["date"] == days[-1])]
        eve_hours = int(today_obs["evening_hours"].fillna(0).sum())
        row_today = is_today & (frame["city"] == c)
        if eve_hours == 0 and len(today_obs):
            frame.loc[row_today, "evening_pm25"] = frame.loc[row_today, "obs_pm25"]
            notes[c].append("2-7 PM window not reported yet, evening_today = today's mean so far")
        elif eve_hours < len(HOURS):
            notes[c].append(f"2-7 PM window partial: {eve_hours} of {len(HOURS)} hours")
    for c in CITIES:  # yesterday and the day before should be full days; say so when an hour is missing
        for label, day in (("day before", days[0]), ("yesterday", days[1])):
            n = int(obs.loc[(obs["city"] == c) & (obs["date"] == day), "hours"].sum())
            if 0 < n < 24:
                notes[c].append(f"{label}: {n} of 24 hours")
    reporting = obs.loc[obs["date"] == days[-1], "city"].nunique()
    if reporting < len(CITIES):  # region_max/mean_today then cover fewer cities than in training
        for c in CITIES:
            notes[c].append(f"region: {reporting} of {len(CITIES)} cities reporting today")
    today_ring = ring.reindex([days[-1]])
    if today_ring["ring_metros"].fillna(0).item() < len(RING):
        for c in CITIES:
            notes[c].append(f"ring: {int(today_ring['ring_metros'].fillna(0).item())} of {len(RING)} metros reporting today")

    rows = add_features(frame).set_index("city").reindex(list(CITIES))  # every city, even one with no readings
    ids = rows["city_id"].dropna()  # must be the training codes: position in the sorted list of six names
    assert all(ids[c] == sorted(CITIES).index(c) for c in ids.index), "city_id codes differ from training"
    with open("data/metrics.json") as f:
        warn_at = json.load(f)["warn_at"]["pred_model"]  # the warning line chosen on the training years (32)
    out = []
    for c in CITIES:
        r = rows.loc[c]
        city_days = obs[obs["city"] == c].set_index("date")
        no_obs = [d for d in days if d not in city_days.index]
        missing = [f for f in FEATURES if pd.isna(r[f])]
        if no_obs:
            pred, status = np.nan, f"no forecast: waiting on AirNow readings for {', '.join(no_obs)}"
        elif missing:
            pred, status = np.nan, f"no forecast: missing {', '.join(missing)}"
        else:
            pred = round(float(predict(models, rows.loc[[c]]).iloc[0]), 2)
            status = "; ".join(notes[c]) or "ok"
        _cbsa, lat, lon, _utc = CITIES[c]
        out.append({"target_date": target, "made_at": made_at, "city": c, "lat": lat, "lon": lon,
                    "pred_model": pred, "pred_noaa": round(naqfc[c], 2) if naqfc else np.nan,
                    "obs_today": round(city_days["obs_pm25"].get(days[-1], np.nan), 2),
                    "hours_today": int(city_days["hours"].get(days[-1], 0)), "status": status,
                    "warn_at": warn_at})
    out = pd.DataFrame(out)
    out.to_csv("data/tomorrow.csv", index=False)
    print(rows[FEATURES].round(2).T.to_string())
    print(out.drop(columns=["made_at", "lat", "lon"]).to_string(index=False))
    print(f"saved data/tomorrow.csv in {time.time() - started:.0f} s")


# ---------------------------------------------------------------------------------------------------------------
# 5. Parity check: our AirNow numbers vs EPA's archive (what the model was trained on), on past days.
# ---------------------------------------------------------------------------------------------------------------
PARITY_DAYS = ["2025-07-30", "2025-07-31", "2025-08-01", "2025-03-12", "2025-05-20", "2025-10-08"]


def parity():
    epa = load("daily.csv").merge(load("evening_pm25.csv"), on=["city", "date"], how="left")
    epa_ring = load("ring_pm25.csv").set_index("date")
    city_sites, ring_sites = epa_sites(CITIES), epa_sites(RING)
    lines = ["# Live parity: AirNow (our live aggregation) vs EPA AirData (training CSVs)", "",
             f"Made by `forecast_tomorrow.py --parity` on {datetime.now(ZoneInfo('America/Chicago')):%Y-%m-%d %H:%M %Z}. "
             "µg/m³. diff = AirNow - EPA. Sites = monitor sites averaged (EPA `n_monitors` / `evening_sites`).", "",
             "| date | city | EPA obs | AirNow obs | diff | EPA sites | AirNow sites | AirNow hours "
             "| EPA 2-7 PM | AirNow 2-7 PM | diff | AirNow 1-6 PM | AirNow 3-8 PM |", "|" + "---|" * 13]
    ring_lines = ["", "| date | ring_max EPA / AirNow | ring_mean EPA / AirNow | north_max EPA / AirNow | metros EPA / AirNow |",
                  "|---|---|---|---|---|"]
    early = [f"{h - 1:02d}:00" for h in range(14, 19)]  # the window one hour earlier, to test AirNow's hour label
    late = [f"{h + 1:02d}:00" for h in range(14, 19)]
    for day in PARITY_DAYS:
        d0 = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        hours = airnow_hours(d0 + timedelta(hours=5), d0 + timedelta(hours=29))  # covers Eastern and Central days
        ours = by_city_day(hours, city_sites).query("date == @day").set_index("city")
        shifted = {name: by_city_day(hours, city_sites, w).query("date == @day").set_index("city")["evening_pm25"]
                   for name, w in (("early", early), ("late", late))}
        for c in CITIES:
            e = epa[(epa["city"] == c) & (epa["date"] == day)].iloc[0]
            a = ours.loc[c] if c in ours.index else pd.Series(dtype=float)
            lines.append(f"| {day} | {c} | {e['obs_pm25']:.2f} | {a.get('obs_pm25', np.nan):.2f} "
                         f"| {a.get('obs_pm25', np.nan) - e['obs_pm25']:+.2f} | {e['n_monitors']:.0f} | {a.get('sites', 0):.0f} "
                         f"| {a.get('hours', 0):.0f} | {e['evening_pm25']:.2f} | {a.get('evening_pm25', np.nan):.2f} "
                         f"| {a.get('evening_pm25', np.nan) - e['evening_pm25']:+.2f} "
                         f"| {shifted['early'].get(c, np.nan):.2f} | {shifted['late'].get(c, np.nan):.2f} |")
        r_ours, r_epa = ring_by_day(by_city_day(hours, ring_sites)).loc[day], epa_ring.loc[day]
        ring_lines.append(f"| {day} | " + " | ".join(
            f"{r_epa[k]:.2f} / {r_ours[k]:.2f}" for k in ("ring_max", "ring_mean", "north_max")) +
            f" | {r_epa['ring_metros']:.0f} / {r_ours['ring_metros']:.0f} |")
        print(f"parity {day} done")
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    NOTES.write_text("\n".join(lines + ring_lines) + "\n")
    print("\n".join(lines + ring_lines))
    print(f"wrote {NOTES}")


if __name__ == "__main__":
    parity() if "--parity" in sys.argv else forecast()
