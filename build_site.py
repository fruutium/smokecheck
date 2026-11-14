"""Builds the copy of the app that GitHub Pages hosts, in site/ (git-ignored).

GitHub Pages only serves files; it can't run app/app.py. So this saves every answer the page would ask the Python
server for as a JSON file, made by the same functions, and marks the page so it reads those files:

    site/index.html                 app/index.html with <meta name="smokecheck-static"> added
    site/api/live.json              tomorrow's forecast for the six cities (from data/tomorrow.csv)
    site/api/test-run.json          the 2025 test run's opening day; test-run/<date>.json for every 2025 day
    site/api/results.json           the "Does it work?" table and the weak-spot line

Run after forecast_tomorrow.py:  python build_site.py   (add --forecast-failed if that run failed).
The GitHub Action in .github/workflows/pages.yml does both on a schedule and publishes site/."""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SITE = REPO / "site"
sys.path.insert(0, str(REPO / "app"))
import app  # noqa: E402  app/app.py: the same view functions the local server answers with


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def main():
    shutil.rmtree(SITE, ignore_errors=True)
    page = (REPO / "app" / "index.html").read_text(encoding="utf-8")
    marker = '<meta charset="utf-8">'
    assert page.count(marker) == 1, "app/index.html changed: put the static marker somewhere else"
    static_page = page.replace(marker, marker + '\n<meta name="smokecheck-static">')
    SITE.mkdir()
    (SITE / "index.html").write_text(static_page, encoding="utf-8")

    # Like app.live(), minus starting a background update: here the Action has just made the forecast.
    rows, today = app.load_tomorrow(), app.today_central()
    write(SITE / "api" / "live.json", {
        "start_city": app.START_CITY,
        "status": {"refreshing": False, "failed": "--forecast-failed" in sys.argv},
        "cities": app.every_city(lambda city: app.live_view(rows, city, app.METRICS, today))})

    write(SITE / "api" / "test-run.json", app.test_run())  # no date: the opening day
    for date in app.DATES:
        write(SITE / "api" / "test-run" / f"{date}.json", app.test_run(date))
    write(SITE / "api" / "results.json", app.results())
    print(f"built {SITE}: live forecast for {rows['target_date'].iloc[0] if rows is not None else 'none'}, "
          f"{len(app.DATES)} test-run days")


if __name__ == "__main__":
    main()
