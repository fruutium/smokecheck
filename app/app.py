"""SmokeCheck demo app: a small web server. It sends the page (app/index.html) and the numbers the page shows, as JSON.
Reads data/predictions.csv and data/metrics.json and nothing else; it never imports model code.
Run:  .venv/bin/python app/app.py   then open http://127.0.0.1:7860"""
import json
import os
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

import refresh  # app/refresh.py: reruns forecast_tomorrow.py in the background when the forecast is stale

# In the repo the data is in ../data; in a Hugging Face Space it would sit next to app.py, in ./data.
HERE = Path(__file__).parent
DATA = HERE / "data" if (HERE / "data").exists() else HERE.parent / "data"
DEFAULT_LIMIT = 35  # µg/m³ daily mean; only used when metrics.json does not say otherwise
START_CITY, START_DATE = "Minneapolis", "2025-07-31"  # the headline smoke day
# The forecasters in the "Does it work?" table, in order. noaa_at_limit is NOAA scored at the plain 35 line.
NAMES = {"pred_model": "SmokeCheck", "pred_noaa": "NOAA's official forecast",
         "noaa_at_limit": "NOAA's official forecast", "pred_persistence": "Yesterday's reading"}

OK = "✅ OK to practice outside"
INDOORS = "🚫 Move practice indoors"
NOT_READY = "⏳ No forecast yet"


def load_rows(data_dir=DATA):
    if (data_dir / "predictions.csv").exists():
        rows = pd.read_csv(data_dir / "predictions.csv")
    else:
        # Before the model has run we only have the raw data.
        rows = pd.read_csv(data_dir / "daily.csv")
    if "pred_model" not in rows:
        rows["pred_model"] = float("nan")  # no column yet is the same as an empty one: no forecast
    # Test rows only: training days would make the model look better than it is.
    return rows[rows["split"] == "test"].sort_values(["date", "city"])


def load_metrics(data_dir=DATA):
    path = data_dir / "metrics.json"
    return json.loads(path.read_text()) if path.exists() else {}


def bad_day_limit(metrics):
    """A bad day is one the monitors measured above this (daily mean, µg/m³)."""
    return metrics.get("threshold", DEFAULT_LIMIT)


def cutoff(metrics, column):
    """Each forecaster warns above its own cut-off; without one, it warns above the bad-day limit."""
    return metrics.get("warn_at", {}).get(column, bad_day_limit(metrics))


def verdict(pred, cut):
    # Only the forecast decides: it is all the athletic director has the evening before.
    if pd.isna(pred):
        return NOT_READY
    return OK if pred <= cut else INDOORS


def right_or_wrong(call, measured, limit):
    """Compare the call with what the monitors measured: right, a missed bad day, or a false alarm."""
    if call == NOT_READY or pd.isna(measured):
        return "–"
    bad = measured > limit
    if (call == INDOORS) == bad:
        return "✓ Right call"
    return "✗ Missed a bad day" if bad else "✗ False alarm"


def replay_view(rows, city, date, metrics):
    """Everything the 2025 replay shows for one city and day, as plain values (no layout)."""
    match = rows[(rows["city"] == city) & (rows["date"] == date)]
    # No row for this city and day: use an empty row so every value below reads as missing.
    row = match.iloc[0] if len(match) else pd.Series(dtype=float)
    cut, limit = cutoff(metrics, "pred_model"), bad_day_limit(metrics)
    call, measured = verdict(row.get("pred_model"), cut), row.get("obs_pm25")
    return {"city": city, "date": date, "call": call, "forecast": row.get("pred_model"), "warn_at": cut,
            "measured": measured, "bad_day": None if pd.isna(measured) else bool(measured > limit),
            "noaa": row.get("pred_noaa"), "result": right_or_wrong(call, measured, limit)}


def plain(view):
    """A view dict with JSON-safe values: missing -> None, numbers -> float rounded to 1 dp, times -> ISO text."""
    def fix(value):
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if isinstance(value, (bool, str)) or value is None:
            return value
        return None if pd.isna(value) else round(float(value), 1)
    return {key: fix(value) for key, value in view.items()}


def map_points(rows, date, metrics):
    """One row per city for the map: city, lat, lon, forecast and call (plain values)."""
    day_rows = rows[rows["date"] == date]
    return pd.DataFrame({"city": day_rows["city"], "lat": day_rows["lat"], "lon": day_rows["lon"],
                         "forecast": day_rows["pred_model"],
                         "call": [verdict(p, cutoff(metrics, "pred_model")) for p in day_rows["pred_model"]]})


def stats_at_line(rows, column, line, limit):
    """How one forecaster would score on these rows if it warned above `line` instead of its own cut-off."""
    scored = rows.dropna(subset=[column, "obs_pm25"])
    bad, warn = scored["obs_pm25"] > limit, scored[column] > line
    return {"mae": round((scored[column] - scored["obs_pm25"]).abs().mean(), 2), "warn_at": line,
            "bad_days": int(bad.sum()), "caught": int((bad & warn).sum()),
            "missed": int((bad & ~warn).sum()), "false_alarms": int((~bad & warn).sum())}


def scoreboard(section, miss_cost):
    """One row per forecaster in NAMES, SmokeCheck first. section is {pred_column: {mae, caught, ...}}.
    The cost is what the cut-offs were chosen on: miss_cost × missed + false alarms."""
    order = [c for c in NAMES if c in section]
    return pd.DataFrame([{
        "Forecaster": NAMES[c],
        "Average error": section[c]["mae"],
        "Warns above": section[c]["warn_at"],
        "Bad days caught": f"{section[c]['caught']} of {section[c]['bad_days']}",
        "False alarms": section[c]["false_alarms"],
        f"Cost (a miss = {miss_cost:g} false alarms)": miss_cost * section[c]["missed"] + section[c]["false_alarms"],
    } for c in order])


def arrival_note(rows, metrics):
    """Smoke arrival days (yesterday's reading was fine, today's is bad) and how many SmokeCheck warned on."""
    limit = bad_day_limit(metrics)
    arrivals = rows[(rows["pred_persistence"] <= limit) & (rows["obs_pm25"] > limit)]
    warned = (arrivals["pred_model"] > cutoff(metrics, "pred_model")).sum()
    return f"**Weak spot:** it misses the day smoke first arrives (warned on {warned} of {len(arrivals)} in 2025)."


def load_tomorrow(data_dir=DATA):
    """The live forecast that forecast_tomorrow.py writes each evening, or None if it has not run yet."""
    path = data_dir / "tomorrow.csv"
    if not path.exists():
        return None
    rows = pd.read_csv(path)
    return rows.assign(date=rows["target_date"])  # map_points looks rows up by "date"


def is_out_of_date(target_date, today):
    """A forecast is out of date once its practice day has passed."""
    return target_date < today


def live_view(rows, city, metrics, today):
    """Everything the Tomorrow tab shows for one city, as plain values (no layout).
    state is "none" (no forecast file yet), "out_of_date", "waiting" (an input is missing) or "ok".
    today is 'YYYY-MM-DD' in Central time."""
    cut = cutoff(metrics, "pred_model")
    match = None if rows is None else rows[rows["city"] == city]
    if match is None or match.empty:
        return {"state": "none", "city": city, "call": NOT_READY, "warn_at": cut}
    row = match.iloc[0]
    view = {"city": city, "date": row["target_date"], "warn_at": cut, "forecast": row["pred_model"],
            "noaa": row.get("pred_noaa"), "made_at": pd.Timestamp(row["made_at"]), "status": row["status"]}
    if is_out_of_date(row["target_date"], today):
        return {**view, "state": "out_of_date", "call": NOT_READY}
    call = verdict(row["pred_model"], cut)
    return {**view, "state": "waiting" if call == NOT_READY else "ok", "call": call}


ROWS = load_rows()
METRICS = load_metrics()
CITIES = sorted(ROWS["city"].unique())
DATES = sorted(ROWS["date"].unique())


def step(date, days):
    """The day before or after, staying inside 2025."""
    i = min(max(DATES.index(date) + days, 0), len(DATES) - 1)
    return DATES[i]


def today_central():
    return pd.Timestamp.now(tz="America/Chicago").strftime("%Y-%m-%d")


# ---- The web server: one page and three small JSON answers. All the numbers come from the functions above. ----
api = FastAPI(title="SmokeCheck")


def every_city(view_of):
    """One view per city, as JSON-safe values: {"Chicago": {...}, "Detroit": {...}, ...}."""
    return {city: plain(view_of(city)) for city in CITIES}


@api.get("/")
def page():
    # Read on every request, so an edit to index.html shows on reload.
    return HTMLResponse((HERE / "index.html").read_text(encoding="utf-8"))


# async: requests to this one run one at a time, so two open tabs can never start two forecast runs at once.
@api.get("/api/live")
async def live():
    """The Tomorrow view. The page asks again every few seconds while status says a new forecast is being made."""
    rows = load_tomorrow()  # read again each time, so a new forecast shows without a restart
    refresh.refresh_if_stale(rows)  # starts a background update if this one is old; never waits for it
    today = today_central()
    return {"start_city": START_CITY, "status": refresh.status(),
            "cities": every_city(lambda city: live_view(rows, city, METRICS, today))}


@api.get("/api/test-run")
def test_run(date: str = START_DATE):
    """One day of the 2025 test run for all six cities, so switching city needs no new request."""
    if date not in DATES:
        raise HTTPException(404, "That day is not in the 2025 test run.")
    return {"start_city": START_CITY, "date": date, "before": step(date, -1), "after": step(date, 1),
            "first": DATES[0], "last": DATES[-1],
            "cities": every_city(lambda city: replay_view(ROWS, city, date, METRICS))}


@api.get("/api/results")
def results():
    """The "Does it work?" table (one list per row, SmokeCheck first) and the weak-spot line."""
    limit = bad_day_limit(METRICS)
    if "overall" not in METRICS:  # the model has not been scored yet
        return {"limit": limit, "columns": [], "rows": [], "note": ""}
    section = dict(METRICS["overall"])
    section["noaa_at_limit"] = stats_at_line(ROWS, "pred_noaa", limit, limit)
    table = scoreboard(section, METRICS["cost_of_a_miss"])
    # to_json turns pandas numbers into plain JSON numbers.
    return {"limit": limit, "columns": list(table.columns), "rows": json.loads(table.to_json(orient="values")),
            "note": arrival_note(ROWS, METRICS)}


if __name__ == "__main__":
    # A preview tool may hand out another port through PORT.
    uvicorn.run(api, host="127.0.0.1", port=int(os.environ.get("PORT", 7860)))
