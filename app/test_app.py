"""Plain checks for app.py. Run:  .venv/bin/python app/test_app.py"""
import importlib.util
import shutil
import tempfile
from pathlib import Path

import pandas as pd

import app

# 1. The cut-off rule. SmokeCheck warns above its own cut-off; at the cut-off it does not.
metrics = {"threshold": 35, "warn_at": {"pred_model": 24.0}}
cut = app.cutoff(metrics, "pred_model")
assert cut == 24.0
assert app.verdict(24.0, cut) == app.OK
assert app.verdict(24.1, cut) == app.INDOORS
# No warn_at (or no entry for a forecaster): fall back to the bad-day limit, 35.
assert app.cutoff({}, "pred_model") == 35
assert app.cutoff({"threshold": 35, "warn_at": {}}, "pred_model") == 35
assert app.verdict(35.1, app.cutoff({}, "pred_model")) == app.INDOORS
# A missing forecast is never a verdict.
assert app.verdict(float("nan"), cut) == app.NOT_READY
assert app.verdict(None, cut) == app.NOT_READY

# "Was it right?": a bad day is measured ABOVE the limit; exactly 35 is not one.
assert app.right_or_wrong(app.INDOORS, 35.1, 35) == "✓ Right call"
assert app.right_or_wrong(app.OK, 35.0, 35) == "✓ Right call"
assert app.right_or_wrong(app.OK, 35.1, 35) == "✗ Missed a bad day"
assert app.right_or_wrong(app.INDOORS, 35.0, 35) == "✗ False alarm"
assert app.right_or_wrong(app.NOT_READY, 50.0, 35) == "–"
assert app.right_or_wrong(app.OK, float("nan"), 35) == "–"


def check_no_forecast_yet(rows, metrics):
    """What must hold for any file without a SmokeCheck forecast: real measurements, but no verdict."""
    assert set(rows["split"]) == {"test"}
    assert len(rows) == 6 * 365
    assert rows["pred_model"].isna().all()
    html = app.card(rows, "Chicago", "2025-07-31", metrics)
    assert "<b>65.6</b>" in html  # measured 65.648
    assert app.NOT_READY in html and app.OK not in html and app.INDOORS not in html
    assert len(app.city_map(rows, "2025-07-31", metrics).data) == 1  # one grey group, no fake colors


# 2. The not-ready path: a COPY of predictions.csv with pred_model dropped (never writes into data/).
if (app.DATA / "predictions.csv").exists():
    with tempfile.TemporaryDirectory() as folder:
        pd.read_csv(app.DATA / "predictions.csv").drop(columns="pred_model").to_csv(
            Path(folder) / "predictions.csv", index=False)
        check_no_forecast_yet(app.load_rows(Path(folder)), app.METRICS)

# 3. Only daily.csv: a temp folder with a copy of it and nothing else. No NOAA column: no NOAA chip.
with tempfile.TemporaryDirectory() as folder:
    shutil.copy(app.DATA / "daily.csv", folder)
    rows = app.load_rows(Path(folder))
    assert app.load_metrics(Path(folder)) == {}
check_no_forecast_yet(rows, {})
assert "NOAA" not in app.card(rows, "Chicago", "2025-07-31", {})

# A city/day that is not in the file shows words, not a crash and not 0.
html = app.card(rows, "Chicago", "2030-01-01", {})
assert "no measurement" in html and app.NOT_READY in html

# 4. The real files, on the demo days.
if (app.DATA / "predictions.csv").exists() and (app.DATA / "metrics.json").exists():
    rows, metrics = app.load_rows(), app.METRICS
    assert app.cutoff(metrics, "pred_model") == metrics["warn_at"]["pred_model"] == 32

    # The opening view, Minneapolis 2025-07-31: SmokeCheck 41.3 is above 32, so it warns. NOAA 18.7. Measured 69.1.
    assert (app.START_CITY, app.START_DATE) == ("Minneapolis", "2025-07-31")
    html = app.card(rows, "Minneapolis", "2025-07-31", metrics)
    assert app.INDOORS in html and "Smoke forecast 41.3 · indoors above 32" in html
    assert "practice on Thursday, July 31, 2025" in html
    assert "<b>69.1</b> a bad day" in html and "<b>18.7</b>" in html and "✓ Right call" in html

    # Milwaukee 2025-07-31: SmokeCheck 28.1 is under 32, so it says outside, but 83.7 was measured: a miss.
    html = app.card(rows, "Milwaukee", "2025-07-31", metrics)
    assert app.OK in html and "28.1" in html and "<b>83.7</b>" in html and "✗ Missed a bad day" in html

    # Chicago 2025-08-01: SmokeCheck 51.8 warns, NOAA 8.7. Measured 45.5: right.
    html = app.card(rows, "Chicago", "2025-08-01", metrics)
    assert app.INDOORS in html and "51.8" in html and "<b>8.7</b>" in html and "✓ Right call" in html

    # The call follows SmokeCheck's forecast only, never the measurement.
    for _, row in rows[rows["date"].between("2025-07-25", "2025-08-05")].iterrows():
        expected = app.verdict(row["pred_model"], app.cutoff(metrics, "pred_model"))
        assert f'<div class="call">{expected}</div>' in app.card(rows, row["city"], row["date"], metrics)

    # The map colours follow SmokeCheck's cut-off: on 2025-07-31 some cities warn and some do not.
    assert {trace.name for trace in app.city_map(rows, "2025-07-31", metrics).data} == {app.OK, app.INDOORS}

    # The day buttons step one day and stop at the ends of 2025.
    assert app.step("2025-07-31", 1) == "2025-08-01" and app.step("2025-07-31", -1) == "2025-07-30"
    assert app.step(app.DATES[0], -1) == app.DATES[0] and app.step(app.DATES[-1], 1) == app.DATES[-1]

    # "Does it work?": NOAA at the plain 35 line on 2025: 12 caught, 8 false alarms, cost 5 × 23 + 8 = 123.
    at_35 = app.stats_at_line(rows, "pred_noaa", 35, 35)
    assert (at_35["caught"], at_35["missed"], at_35["false_alarms"]) == (12, 23, 8)
    # The same counts at NOAA's own cut-off match metrics.json, so the two NOAA rows are comparable.
    own = app.stats_at_line(rows, "pred_noaa", metrics["warn_at"]["pred_noaa"], 35)
    assert (own["caught"], own["false_alarms"], own["mae"]) == tuple(
        metrics["overall"]["pred_noaa"][k] for k in ("caught", "false_alarms", "mae"))
    section = dict(metrics["overall"], noaa_at_limit=at_35)
    table = app.scoreboard(section, metrics["cost_of_a_miss"])
    cost = "Cost (a miss = 5 false alarms)"
    # The two NOAA rows share a name and differ only in the line they warn above.
    assert list(zip(table["Forecaster"], table["Warns above"])) == [
        ("SmokeCheck", 32), ("NOAA's official forecast", 52.5), ("NOAA's official forecast", 35), ("Yesterday's reading", 37)]
    model = table.iloc[0]
    assert (model["Average error"], model["Bad days caught"], model["False alarms"], model[cost]) == (2.36, "11 of 35", 7, 127)
    assert table.iloc[2][cost] == 123

    # Smoke arrival days: SmokeCheck warned on 0 of the 21 in 2025.
    assert "warned on 0 of 21 in 2025" in app.arrival_note(rows, metrics)

# 5. A Space-style layout still works: app.py with data/ next to it (no daily.csv, no ../data).
# A COPY of app.py in a temp folder, loaded under another name so it does not replace `app`.
if (app.DATA / "predictions.csv").exists() and (app.DATA / "metrics.json").exists():
    with tempfile.TemporaryDirectory() as folder:
        space = Path(folder) / "space"
        (space / "data").mkdir(parents=True)
        shutil.copy(Path(app.__file__), space / "app.py")
        shutil.copy(app.DATA / "predictions.csv", space / "data")
        shutil.copy(app.DATA / "metrics.json", space / "data")
        spec = importlib.util.spec_from_file_location("space_app", space / "app.py")
        space_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(space_app)
        assert space_app.DATA == space / "data"
        assert space_app.INDOORS in space_app.card(space_app.ROWS, "Minneapolis", "2025-07-31", space_app.METRICS)

# 6. Without metrics.json nothing breaks and the bad-day limit is 35.
assert app.bad_day_limit({}) == 35

print("all checks passed")
