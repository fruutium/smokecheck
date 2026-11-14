"""Plain checks for app.py. Run:  .venv/bin/python app/test_app.py"""
import shutil
import tempfile
from pathlib import Path

import pandas as pd

import app

# 1. The cut-off rule. SmokeCheck warns above its own cut-off (24 in metrics.json); at the cut-off it does not.
metrics = {"threshold": 35, "warn_at": {"pred_model": 24.0, "pred_cams": 29.5}}
cut = app.cutoff(metrics, "pred_model")
assert cut == 24.0
assert app.verdict(24.0, cut) == app.OK
assert app.verdict(24.1, cut) == app.INDOORS
# No warn_at (or no entry for a forecaster): fall back to the bad-day limit, 35.
assert app.cutoff({}, "pred_model") == 35
assert app.cutoff({"threshold": 35, "warn_at": {}}, "pred_model") == 35
assert app.verdict(35.0, app.cutoff({}, "pred_model")) == app.OK
assert app.verdict(35.1, app.cutoff({}, "pred_model")) == app.INDOORS
# A missing forecast is never a verdict.
assert app.verdict(float("nan"), cut) == app.NOT_READY
assert app.verdict(None, cut) == app.NOT_READY
assert app.call_words(float("nan"), cut) == ""
# A bad day is measured ABOVE 35; exactly 35 is not one.
assert "not a bad day" in app.bad_day_words(35.0, 35)
assert "a bad day" in app.bad_day_words(35.1, 35) and "not" not in app.bad_day_words(35.1, 35)


def check_no_forecast_yet(rows, metrics):
    """What must hold for any file without a SmokeCheck forecast: real numbers, but no verdict."""
    assert set(rows["split"]) == {"test"}
    assert len(rows) == 6 * 365
    assert rows["pred_model"].isna().all()
    html = app.card(rows, "Chicago", "2025-07-31", metrics)
    assert "34.3" in html and "<b>65.6</b>" in html  # CAMS 34.28 (box or baselines line), measured 65.648
    assert app.NOT_READY in html and "<b>not ready yet</b>" in html
    assert app.OK not in html and app.INDOORS not in html
    assert app.worst_misses(rows, metrics).empty
    assert len(app.city_map(rows, "2025-07-31", metrics).data) == 1  # one grey group, no fake colors


# 2. The not-ready path: a COPY of predictions.csv with pred_model dropped (never writes into data/).
if (app.DATA / "predictions.csv").exists():
    with tempfile.TemporaryDirectory() as folder:
        pd.read_csv(app.DATA / "predictions.csv").drop(columns="pred_model").to_csv(
            Path(folder) / "predictions.csv", index=False)
        check_no_forecast_yet(app.load_rows(Path(folder)), app.METRICS)

# 3. Only daily.csv: a temp folder with a copy of it and nothing else.
with tempfile.TemporaryDirectory() as folder:
    shutil.copy(app.DATA / "daily.csv", folder)
    rows = app.load_rows(Path(folder))
    assert app.load_metrics(Path(folder)) == {}
check_no_forecast_yet(rows, {})
html = app.card(rows, "Chicago", "2025-07-31", {})
assert "Baselines: none yet" in html and "SmokeCheck warns above 35 µg/m³." in html
# Without pred_noaa the left box falls back to raw CAMS, with CAMS's own call (35 here: no metrics.json).
assert "<span>Raw CAMS estimate said</span><b>34.3</b>" in html and "→ no warning (cut-off 35)" in html
assert "NOAA" not in html

# The same fallback from a COPY of predictions.csv without pred_noaa: CAMS moves back into the box.
if (app.DATA / "predictions.csv").exists():
    with tempfile.TemporaryDirectory() as folder:
        pd.read_csv(app.DATA / "predictions.csv").drop(columns="pred_noaa").to_csv(
            Path(folder) / "predictions.csv", index=False)
        html = app.card(app.load_rows(Path(folder)), "Chicago", "2025-07-31", app.METRICS)
    assert "<span>Raw CAMS estimate said</span><b>34.3</b>" in html and "(optimistic)" not in html

# A city/day that is not in the file shows words, not a crash and not 0.
html = app.card(rows, "Chicago", "2030-01-01", {})
assert "no measurement" in html and app.NOT_READY in html

# 4. The real files, on the demo days.
if (app.DATA / "predictions.csv").exists() and (app.DATA / "metrics.json").exists():
    rows, metrics = app.load_rows(), app.METRICS
    assert app.cutoff(metrics, "pred_model") == metrics["warn_at"]["pred_model"]

    # Milwaukee 2025-07-31: SmokeCheck 26.8 is above its cut-off of 24.5, so it warns; NOAA 13.4 does not.
    html = app.card(rows, "Milwaukee", "2025-07-31", metrics)
    assert app.INDOORS in html and "<b>26.8</b>" in html and "→ warn (cut-off 24.5)" in html and "<b>83.7</b>" in html
    assert "<span>NOAA's official forecast said</span><b>13.4</b>" in html and "→ no warning (cut-off 52.5)" in html
    assert "a bad day" in html
    assert (f"not {metrics['threshold']:g}" in html and f"as much as {metrics['cost_of_a_miss']:g} false alarms" in html)
    assert f"warns above {metrics['warn_at']['pred_model']:g} µg/m³, not" in html

    # Chicago 2025-07-31: SmokeCheck 13.7 and NOAA 13.7 both say outside; measured 65.6.
    # Raw CAMS 34.3 warns, but it sits in the baselines line, marked optimistic.
    html = app.card(rows, "Chicago", "2025-07-31", metrics)
    assert app.OK in html and "<b>65.6</b>" in html
    assert "<span>SmokeCheck said</span><b>13.7</b>" in html
    assert "Likely between 8.8 and 20.6 (80% range)" in html  # shown only, the call stays green
    assert "<span>NOAA's official forecast said</span><b>13.7</b>" in html
    assert "Raw CAMS estimate (optimistic) said 34.3 → warn (cut-off 30)" in html
    assert "Persistence (yesterday's measurement) said 12.4 → no warning (cut-off 37)" in html

    # Chicago 2025-08-01: SmokeCheck 54.0 warns, NOAA 8.7 does not.
    html = app.card(rows, "Chicago", "2025-08-01", metrics)
    assert app.INDOORS in html and "<b>54.0</b>" in html
    assert "<span>NOAA's official forecast said</span><b>8.7</b>" in html and "→ no warning (cut-off 52.5)" in html

    # Without range_lo / range_hi the card shows no range at all (a COPY with the columns dropped).
    no_range = rows.drop(columns=["range_lo", "range_hi"])
    assert "Likely between" not in app.card(no_range, "Chicago", "2025-07-31", metrics)

    # The map colours follow SmokeCheck's cut-off: on 2025-07-31 some cities warn and some do not.
    fig = app.city_map(rows, "2025-07-31", metrics)
    assert {trace.name for trace in fig.data} == {app.OK, app.INDOORS}

    # The call follows SmokeCheck's forecast only, never the measurement.
    for _, row in rows[rows["date"].between("2025-07-25", "2025-08-05")].iterrows():
        expected = app.verdict(row["pred_model"], app.cutoff(metrics, "pred_model"))
        assert f'<div class="call">{expected}</div>' in app.card(rows, row["city"], row["date"], metrics)

    misses = app.worst_misses(rows, metrics)
    assert len(misses) == len(rows)
    assert misses["SmokeCheck off by"].is_monotonic_decreasing
    assert misses.iloc[0]["SmokeCheck off by"] == (rows["pred_model"] - rows["obs_pm25"]).abs().max()
    assert "Smoke plume" in misses and "Raw CAMS estimate" in misses and "NOAA day-ahead forecast" in misses

    # "Does it work?": one row per forecaster, SmokeCheck first.
    table = app.scoreboard(metrics["overall"])
    assert table.iloc[0]["Forecaster"] == "SmokeCheck"
    model = metrics["overall"]["pred_model"]
    assert table.iloc[0]["Bad days caught"] == f"{model['caught']} of {model['bad_days']}"
    by_smoke = app.grouped_scoreboard(metrics["by_smoke"], "Day type")
    assert set(by_smoke["Day type"]) == {"Clean day", "Smoke day"}

# 5. Without metrics.json nothing breaks and the bad-day limit is 35.
assert app.bad_day_limit({}) == 35

print("all checks passed")
