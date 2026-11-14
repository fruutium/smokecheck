"""Plain checks for app.py. Run:  .venv/bin/python app/test_app.py"""
import asyncio
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import HTTPException

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
    v = app.plain(app.replay_view(rows, "Chicago", "2025-07-31", metrics))
    assert v["measured"] == 65.6  # measured 65.648
    assert v["call"] == app.NOT_READY and v["forecast"] is None and v["result"] == "–"
    assert set(app.map_points(rows, "2025-07-31", metrics)["call"]) == {app.NOT_READY}  # one grey group, no fake colors


# 2. The not-ready path: a COPY of predictions.csv with pred_model dropped (never writes into data/).
if (app.DATA / "predictions.csv").exists():
    with tempfile.TemporaryDirectory() as folder:
        pd.read_csv(app.DATA / "predictions.csv").drop(columns="pred_model").to_csv(
            Path(folder) / "predictions.csv", index=False)
        check_no_forecast_yet(app.load_rows(Path(folder)), app.METRICS)

# 3. Only daily.csv: a temp folder with a copy of it and nothing else. No NOAA column: no NOAA number (the page hides it).
with tempfile.TemporaryDirectory() as folder:
    shutil.copy(app.DATA / "daily.csv", folder)
    rows = app.load_rows(Path(folder))
    assert app.load_metrics(Path(folder)) == {}
check_no_forecast_yet(rows, {})
assert app.plain(app.replay_view(rows, "Chicago", "2025-07-31", {}))["noaa"] is None

# A city/day that is not in the file is missing values (the page writes "No measurement"), not a crash and not 0.
v = app.plain(app.replay_view(rows, "Chicago", "2030-01-01", {}))
assert v["measured"] is None and v["bad_day"] is None and v["call"] == app.NOT_READY

# 4. The real files, on the demo days.
if (app.DATA / "predictions.csv").exists() and (app.DATA / "metrics.json").exists():
    rows, metrics = app.load_rows(), app.METRICS
    assert app.cutoff(metrics, "pred_model") == metrics["warn_at"]["pred_model"] == 32

    # The opening view, Minneapolis 2025-07-31: SmokeCheck 41.3 is above 32, so it warns. NOAA 18.7. Measured 69.1.
    assert (app.START_CITY, app.START_DATE) == ("Minneapolis", "2025-07-31")
    # These go through the /api/test-run answer, turned into JSON text and back like the browser gets it.
    day = json.loads(json.dumps(app.test_run("2025-07-31")))
    v = day["cities"]["Minneapolis"]
    assert (v["call"], v["forecast"], v["warn_at"], v["date"]) == (app.INDOORS, 41.3, 32, "2025-07-31")
    assert (v["measured"], v["bad_day"], v["noaa"], v["result"]) == (69.1, True, 18.7, "✓ Right call")
    v = day["cities"]["Chicago"]
    assert (v["call"], v["forecast"], v["measured"], v["result"]) == (app.OK, 15.3, 65.6, "✗ Missed a bad day")

    # Milwaukee 2025-07-31: SmokeCheck 28.1 is under 32, so it says outside, but 83.7 was measured: a miss.
    v = day["cities"]["Milwaukee"]
    assert (v["call"], v["forecast"], v["measured"], v["result"]) == (app.OK, 28.1, 83.7, "✗ Missed a bad day")

    # Chicago 2025-08-01: SmokeCheck 51.8 warns, NOAA 8.7. Measured 45.5: right.
    v = json.loads(json.dumps(app.test_run("2025-08-01")))["cities"]["Chicago"]
    assert (v["call"], v["forecast"], v["noaa"], v["measured"], v["result"]) == (app.INDOORS, 51.8, 8.7, 45.5, "✓ Right call")

    # One answer carries all six cities, the days either side (for the day buttons) and the ends of 2025 (for the picker).
    assert list(day["cities"]) == app.CITIES and day["start_city"] == "Minneapolis"
    assert (day["before"], day["after"], day["first"], day["last"]) == ("2025-07-30", "2025-08-01", "2025-01-01", "2025-12-31")
    assert app.test_run()["date"] == app.START_DATE  # no day asked for: the opening day
    try:
        app.test_run("2030-01-01")
        raise AssertionError("a day outside 2025 must be refused")
    except HTTPException as error:
        assert error.status_code == 404

    # The same day as plain values, for anyone restyling the layout.
    v = app.replay_view(rows, "Minneapolis", "2025-07-31", metrics)
    assert (v["call"], round(v["forecast"], 1), v["warn_at"], round(v["measured"], 1), v["bad_day"],
            round(v["noaa"], 1), v["result"]) == (app.INDOORS, 41.3, 32, 69.1, True, 18.7, "✓ Right call")
    v = app.replay_view(rows, "Chicago", "2025-07-31", metrics)
    assert (round(v["forecast"], 1), round(v["noaa"], 1), round(v["measured"], 1), v["result"]) == (
        15.3, 13.7, 65.6, "✗ Missed a bad day")
    assert app.plain(v) == {"city": "Chicago", "date": "2025-07-31", "call": app.OK, "forecast": 15.3, "warn_at": 32.0,
                            "measured": 65.6, "bad_day": True, "noaa": 13.7, "result": "✗ Missed a bad day"}
    points = app.map_points(rows, "2025-07-31", metrics)
    assert len(points) == 6 and set(points.columns) == {"city", "lat", "lon", "forecast", "call"}

    # The call follows SmokeCheck's forecast only, never the measurement.
    for _, row in rows[rows["date"].between("2025-07-25", "2025-08-05")].iterrows():
        expected = app.verdict(row["pred_model"], app.cutoff(metrics, "pred_model"))
        assert app.replay_view(rows, row["city"], row["date"], metrics)["call"] == expected

    # The map colours follow SmokeCheck's cut-off: on 2025-07-31 some cities warn and some do not.
    assert set(app.map_points(rows, "2025-07-31", metrics)["call"]) == {app.OK, app.INDOORS}

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

    # The /api/results answer: the same table, one list per row. The page reads rows 0, 1 and 2 by position.
    out = json.loads(json.dumps(app.results()))
    assert out["columns"] == list(table.columns) and out["limit"] == 35
    assert out["rows"][0] == ["SmokeCheck", 2.36, 32, "11 of 35", 7, 127]
    assert [(row[0], row[2]) for row in out["rows"]] == list(zip(table["Forecaster"], table["Warns above"]))
    assert out["rows"][1][1] == 3.2 and out["rows"][2][5] == 123
    assert "warned on 0 of 21 in 2025" in out["note"]

# The page itself. It finds the kind of call by the words "indoors" and "outside" and draws its own icon.
page = app.page().body.decode()
assert "<title>SmokeCheck</title>" in page and "A prototype, not medical or health advice." in page
assert "indoors" in app.INDOORS
assert "outside" in app.OK and "indoors" not in app.OK
assert "indoors" not in app.NOT_READY and "outside" not in app.NOT_READY
assert "—" not in page  # no em dashes on screen
assert "view.status" not in page  # fallback details stay in the status field, never on the page

# 5. A Space-style layout still works: app.py with data/ next to it (no daily.csv, no ../data).
# A COPY of app.py in a temp folder, loaded under another name so it does not replace `app`.
if (app.DATA / "predictions.csv").exists() and (app.DATA / "metrics.json").exists():
    with tempfile.TemporaryDirectory() as folder:
        space = Path(folder) / "space"
        (space / "data").mkdir(parents=True)
        shutil.copy(Path(app.__file__), space / "app.py")
        shutil.copy(Path(app.__file__).parent / "refresh.py", space / "refresh.py")
        shutil.copy(app.DATA / "predictions.csv", space / "data")
        shutil.copy(app.DATA / "metrics.json", space / "data")
        spec = importlib.util.spec_from_file_location("space_app", space / "app.py")
        space_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(space_app)
        assert space_app.DATA == space / "data"
        view = space_app.replay_view(space_app.ROWS, "Minneapolis", "2025-07-31", space_app.METRICS)
        assert view["call"] == space_app.INDOORS

# 6. The live "Tomorrow" tab, from a made-up tomorrow.csv in a temp folder (never the real data/).
def write_tomorrow(folder, target, preds, status="ok"):
    pd.DataFrame({"target_date": target, "made_at": "2026-11-14T19:12:00-06:00", "city": app.CITIES,
                  "lat": 42.0, "lon": -88.0, "pred_model": preds, "pred_noaa": 5.0, "obs_today": 4.0,
                  "hours_today": 19, "status": status, "warn_at": 32}).to_csv(Path(folder) / "tomorrow.csv", index=False)


live_metrics = {"threshold": 35, "warn_at": {"pred_model": 32}}
with tempfile.TemporaryDirectory() as folder:
    assert app.load_tomorrow(Path(folder)) is None  # not run yet: a grey screen, no crash
    assert app.live_view(None, "Chicago", live_metrics, "2026-11-14")["call"] == app.NOT_READY
    write_tomorrow(folder, "2026-11-15", [6.2, 40.0, 7.0, 8.0, 9.0, 10.0])
    rows = app.load_tomorrow(Path(folder))
first = app.CITIES[0]  # 40.0 belongs to the second city in sorted order
# The page writes these as "Practice on Sunday, November 15", "Smoke forecast 6.2", "Indoors above 32"
# and "Forecast made Saturday at 7:12 PM".
v = app.plain(app.live_view(rows, first, live_metrics, "2026-11-14"))
assert (v["call"], v["date"], v["forecast"], v["warn_at"]) == (app.OK, "2026-11-15", 6.2, 32)
assert v["made_at"] == "2026-11-14T19:12:00-06:00"
assert app.live_view(rows, app.CITIES[1], live_metrics, "2026-11-14")["call"] == app.INDOORS
# Still good on the practice day itself; out of date the day after, with no call.
assert app.live_view(rows, first, live_metrics, "2026-11-15")["call"] == app.OK
stale = app.live_view(rows, first, live_metrics, "2026-11-16")
assert (stale["state"], stale["call"], stale["date"]) == ("out_of_date", app.NOT_READY, "2026-11-15")
# A missing forecast is "waiting", with no call; a fallback still gives a real call (its detail stays in status).
with tempfile.TemporaryDirectory() as folder:
    write_tomorrow(folder, "2026-11-15", [float("nan")] * 6, status="no AirNow readings yet")
    v = app.live_view(app.load_tomorrow(Path(folder)), first, live_metrics, "2026-11-14")
    assert (v["state"], v["call"], v["status"]) == ("waiting", app.NOT_READY, "no AirNow readings yet")
    write_tomorrow(folder, "2026-11-15", [6.2] * 6, status="NOAA run not out yet; used today's reading")
    v = app.live_view(app.load_tomorrow(Path(folder)), first, live_metrics, "2026-11-14")
    assert (v["state"], v["call"]) == ("ok", app.OK)
assert app.live_view(rows, first, live_metrics, "2026-11-14")["state"] == "ok"
assert app.live_view(rows, first, live_metrics, "2026-11-16")["state"] == "out_of_date"
assert app.live_view(None, first, live_metrics, "2026-11-14")["state"] == "none"
# A city missing from the file gets the grey screen, not a crash.
v = app.live_view(rows, "Nowhere", live_metrics, "2026-11-14")
assert (v["state"], v["call"]) == ("none", app.NOT_READY)

# The /api/live answer, fed the made-up forecast above. The stand-ins make sure this test never starts the real
# forecast script and never reads the real data/tomorrow.csv; the real functions are put back afterwards.
real = (app.load_tomorrow, app.today_central, app.refresh.refresh_if_stale)
app.load_tomorrow, app.today_central, app.refresh.refresh_if_stale = (lambda: rows), (lambda: "2026-11-14"), (lambda rows: False)
out = json.loads(json.dumps(asyncio.run(app.live())))
app.load_tomorrow, app.today_central, app.refresh.refresh_if_stale = real
assert out["status"] == {"refreshing": False, "failed": False} and out["start_city"] == app.START_CITY
assert list(out["cities"]) == app.CITIES
v = out["cities"][first]
assert (v["state"], v["call"], v["forecast"], v["date"]) == ("ok", app.OK, 6.2, "2026-11-15")
assert (v["warn_at"], v["made_at"]) == (app.cutoff(app.METRICS, "pred_model"), "2026-11-14T19:12:00-06:00")
assert out["cities"][app.CITIES[1]]["call"] == app.INDOORS

# 7. When the app remakes the forecast by itself (app/refresh.py). Times are UTC; Central standard = UTC - 6.
from datetime import datetime, timezone  # noqa: E402

import refresh  # noqa: E402


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


assert refresh.target_for(at("2026-11-15 01:00")) == "2026-11-15"  # 7 PM Saturday in Chicago: tomorrow is Sunday
assert refresh.target_for(at("2026-11-15 06:30")) == "2026-11-16"  # 12:30 AM Sunday: tomorrow is now Monday
with tempfile.TemporaryDirectory() as folder:
    assert refresh.needs_refresh(None, at("2026-11-15 01:00"))  # no file yet
    write_tomorrow(folder, "2026-11-15", [6.2] * 6)  # made 7:12 PM Saturday, all inputs ok
    done = app.load_tomorrow(Path(folder))
    write_tomorrow(folder, "2026-11-15", [6.2] * 6, status="2-7 PM window partial: 3 of 5 hours")
    partial = app.load_tomorrow(Path(folder))
assert not refresh.needs_refresh(done, at("2026-11-15 04:00"))  # complete and for the right day: leave it
assert refresh.needs_refresh(done, at("2026-11-15 06:30"))  # past midnight: tomorrow moved on
assert not refresh.needs_refresh(partial, at("2026-11-15 01:30"))  # partial, but only 18 minutes old
assert refresh.needs_refresh(partial, at("2026-11-15 01:50"))  # partial and over 30 minutes old: redo it

assert refresh.status() == {"refreshing": False, "failed": False}  # nothing started in these tests

# 8. Without metrics.json nothing breaks and the bad-day limit is 35.
assert app.bad_day_limit({}) == 35

print("all checks passed")
