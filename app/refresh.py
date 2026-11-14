"""Keeps data/tomorrow.csv current by itself, so nobody has to run forecast_tomorrow.py by hand.

When the page opens, the app calls refresh_if_stale(). If the forecast is missing, is for the wrong day, or was made
from partial readings more than 30 minutes ago, it starts forecast_tomorrow.py in the background (about 30 s) and
returns at once. The page keeps showing the last forecast until the new file is written."""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "forecast_tomorrow.py"
LOG = REPO / "data" / "raw_new" / "forecast.log"  # git-ignored; what the last run printed
RECHECK_PARTIAL = timedelta(minutes=30)  # how often to redo a forecast made before today's readings were all in
RETRY_AFTER_FAILURE = timedelta(minutes=5)  # if a run failed (say, no internet), wait before trying again

_run = None  # the last forecast_tomorrow.py process (running or finished), else None
_started = None  # when it started (UTC)


def target_for(now_utc):
    """Tomorrow, counted in Central STANDARD time like EPA's day and forecast_tomorrow.py (UTC minus 6 hours)."""
    return f"{(now_utc - timedelta(hours=6)).date() + timedelta(days=1):%Y-%m-%d}"


def needs_refresh(rows, now_utc):
    """True when the saved forecast should be redone. rows is data/tomorrow.csv as a DataFrame, or None."""
    if rows is None or rows.empty:
        return True
    if rows["target_date"].iloc[0] != target_for(now_utc):
        return True  # yesterday's forecast, or the day just rolled over
    partial = (rows["status"] != "ok").any()  # e.g. made before the 2-7 PM reading was in
    made_at = pd.Timestamp(rows["made_at"].iloc[0]).to_pydatetime()
    return bool(partial and now_utc - made_at > RECHECK_PARTIAL)


def is_running():
    return _run is not None and _run.poll() is None


def last_run_failed():
    """True if the last background run ended with an error (no internet, a source down, a failed check)."""
    return _run is not None and _run.poll() not in (None, 0)


def refresh_if_stale(rows, now_utc=None):
    """Start forecast_tomorrow.py in the background if the forecast needs it. Returns True while a run is going."""
    global _run, _started
    now_utc = now_utc or datetime.now(timezone.utc)
    waiting_after_failure = last_run_failed() and now_utc - _started < RETRY_AFTER_FAILURE
    if not is_running() and not waiting_after_failure and needs_refresh(rows, now_utc):
        _started = now_utc
        LOG.parent.mkdir(parents=True, exist_ok=True)
        # Same Python as the app, so the app's requirements cover the script too.
        # -u: print each line as it happens, so the log shows how far a slow run got.
        _run = subprocess.Popen([sys.executable, "-u", str(SCRIPT)], cwd=REPO, stdout=LOG.open("w"),
                                stderr=subprocess.STDOUT)
    return is_running()


def status():
    """For a page that polls: {"refreshing": a new forecast is being made, "failed": the last try didn't work}.
    After a failure the page keeps the last forecast (if any) and says it couldn't update; a retry starts on the
    next refresh_if_stale() call once RETRY_AFTER_FAILURE has passed."""
    return {"refreshing": is_running(), "failed": last_run_failed()}
