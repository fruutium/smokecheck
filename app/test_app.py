"""Plain checks for app.py. Run:  .venv/bin/python app/test_app.py"""
import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd

import app

# 1. Verdict at the boundary: at the limit is still outside, just above is indoors.
assert app.verdict(35.0, 35) == app.OK
assert app.verdict(35.1, 35) == app.INDOORS
# A missing forecast is never a verdict.
assert app.verdict(float("nan"), 35) == app.NOT_READY
assert app.verdict(None, 35) == app.NOT_READY
assert "not ready" in app.NOT_READY


def check_no_forecast_yet(rows):
    """What must hold for any file that has no SmokeCheck forecast in it."""
    assert set(rows["split"]) == {"test"}
    assert len(rows) == 6 * 365
    assert rows["pred_model"].isna().all()
    # The opening view: Chicago on the headline smoke day, real numbers, no verdict.
    html = app.card(rows, "Chicago", "2025-07-31", 35)
    assert "<b>34.3</b>" in html and "<b>65.7</b>" in html  # CAMS 34.28, measured 65.65
    assert app.NOT_READY in html and "<b>not ready yet</b>" in html
    assert app.OK not in html and app.INDOORS not in html
    assert app.worst_misses(rows).empty
    assert len(app.city_map(rows, "2025-07-31", 35).data) == 1  # one grey group, no fake colors
    return html


# 2. The real data/predictions.csv, which has no pred_model column at all yet.
if (app.DATA / "predictions.csv").exists():
    html = check_no_forecast_yet(app.load_rows())
    assert "Persistence (yesterday's measurement) said 12.4" in html
    assert "Climatology (usual for this city and month) said 11.3" in html

# 3. Only daily.csv: a temp folder with a copy of it and nothing else (never writes into data/).
with tempfile.TemporaryDirectory() as folder:
    shutil.copy(app.DATA / "daily.csv", folder)
    rows = app.load_rows(Path(folder))
    assert app.load_metrics(Path(folder)) is None
html = check_no_forecast_yet(rows)
assert "Baselines: none yet" in html

# A city/day that is not in the file shows words, not a crash and not 0.
html = app.card(rows, "Chicago", "2030-01-01", 35)
assert "no measurement" in html and app.NOT_READY in html

# 4. A small predictions-shaped file WITH a forecast, without the optional columns.
# Built from real daily.csv rows. pred_persistence is real (yesterday's measurement).
# pred_model is a STAND-IN: the real CAMS values copied over, only so the green/red path
# can be checked before the model exists. It lives in a temp folder and never reaches the app.
daily = pd.read_csv(app.DATA / "daily.csv")
daily = daily[daily["date"].between("2025-07-25", "2025-08-05")]
preds = daily[["date", "city", "lat", "lon", "obs_pm25", "split"]].copy()
preds["pred_cams"] = daily["cams_pm25"]
preds["pred_persistence"] = daily.groupby("city")["obs_pm25"].shift(1)
preds["pred_model"] = daily["cams_pm25"]

with tempfile.TemporaryDirectory() as folder:
    preds.to_csv(Path(folder) / "predictions.csv", index=False)
    rows = app.load_rows(Path(folder))

assert "pred_lo" not in rows and "is_smoke_day" not in rows and "pred_climatology" not in rows

html = app.card(rows, "Chicago", "2025-07-31", 35)  # stand-in forecast 34.28 -> at or below 35
assert app.OK in html and "Likely range" not in html and "Climatology" not in html
html = app.card(rows, "Chicago", "2025-07-25", 35)  # first day: no yesterday, so no persistence
assert "said nothing" in html

# The call follows the forecast only, never the measurement.
for _, row in rows.iterrows():
    expected = app.OK if row["pred_model"] <= 35 else app.INDOORS
    assert expected in app.card(rows, row["city"], row["date"], 35)
assert len(app.city_map(rows, "2025-07-31", 35).data) == 2  # that day has both green and red cities

misses = app.worst_misses(rows)
assert len(misses) == len(rows)
assert misses["Miss"].is_monotonic_decreasing
assert misses.iloc[0]["Miss"] == (rows["pred_model"] - rows["obs_pm25"]).abs().max()

# 5. metrics.json: any nesting becomes one row per forecaster, one column per number.
table = app.metrics_table({"threshold": 35, "a": {"pred_cams": {"days": 365}}, "b": {"x": {"pred_new": {"days": 12}}}})
assert list(table["Forecast"]) == ["a / Raw CAMS estimate", "b / x / pred_new"]
assert list(table["days"]) == [365, 12]
assert app.metrics_table({"threshold": 35}).empty

if (app.DATA / "metrics.json").exists():
    metrics = json.loads((app.DATA / "metrics.json").read_text())
    assert app.LIMIT == metrics["threshold"]
    table = app.metrics_table(metrics)
    first = table.iloc[0]  # the real file starts with overall / pred_persistence
    assert first["Forecast"] == "overall / Persistence (yesterday's measurement)"
    assert first["mae"] == metrics["overall"]["pred_persistence"]["mae"]
    assert len(table) == sum(len(group) for group in metrics["by_city"].values()) + len(metrics["overall"])

print("all checks passed")
