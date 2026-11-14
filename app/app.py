"""SmokeCheck demo app. Reads data/predictions.csv and data/metrics.json and nothing else;
it never imports model code. Run:  .venv/bin/python app/app.py"""
import json
from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.express as px

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
COLOR = {OK: "#1b7a3e", INDOORS: "#b42318", NOT_READY: "#5b6470"}
SYMBOL = {OK: "circle", INDOORS: "square", NOT_READY: "circle-open"}  # shape too, not color alone
FOOTER = "Smoke levels are daily-average PM2.5 in µg/m³. Prototype, not health advice."

CSS = """
.verdict { border-radius: 14px; padding: 26px 30px; }
.verdict, .verdict * { color: #fff !important; }
.verdict .where { font-size: 1.15rem; font-weight: 600; }
.verdict .call { font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 800; line-height: 1.05; margin: 8px 0 10px; }
.verdict .why { font-size: 1.15rem; }
.check { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; align-items: stretch; }
.check > div { border: 1px solid var(--border-color-primary); border-radius: 10px; padding: 10px 16px; }
.check span { display: block; color: var(--neutral-600); font-size: 0.95rem; }
.check b { font-size: 1.5rem; }
.check .title { border: none; padding: 10px 4px; font-weight: 600; align-self: center; }
.small { color: var(--neutral-600); font-size: 0.95rem; margin-top: 10px; }
"""
FONT = [gr.themes.GoogleFont("Barlow", weights=(400, 600, 800)), "system-ui", "sans-serif"]
THEME = gr.themes.Soft(primary_hue="emerald", neutral_hue="slate", font=FONT)


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


def number(value, missing):
    """A value with one decimal, or words when it is missing (never 0)."""
    return missing if pd.isna(value) else f"{value:.1f}"


def pretty(date):
    day = pd.Timestamp(date)
    return f"{day:%A, %B} {day.day}, {day.year}"


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


def card(rows, city, date, metrics):
    v = replay_view(rows, city, date, metrics)
    why = "" if v["call"] == NOT_READY else f"Smoke forecast {v['forecast']:.1f} · indoors above {v['warn_at']:g}"
    measured_words = {None: "", True: "a bad day", False: "not a bad day"}[v["bad_day"]]
    noaa = "" if pd.isna(v["noaa"]) else f"<div><span>NOAA's forecast</span><b>{v['noaa']:.1f}</b></div>"
    return f"""
    <div class="verdict" style="background:{COLOR[v['call']]}">
      <div class="where">{city} · practice on {pretty(date)}</div>
      <div class="call">{v['call']}</div>
      <div class="why">{why}</div>
    </div>
    <div class="check">
      <div class="title">Was it right?</div>
      <div><span>Measured that day</span><b>{number(v['measured'], "no measurement")}</b> {measured_words}</div>
      {noaa}
      <div><span>SmokeCheck</span><b>{v['result']}</b></div>
    </div>"""


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


def city_map(rows, date, metrics):
    day_rows = map_points(rows, date, metrics)
    day_rows["label"] = [f"{r['city']} {r['forecast']:.0f}" if pd.notna(r["forecast"]) else r["city"]
                         for _, r in day_rows.iterrows()]
    fig = px.scatter_geo(
        day_rows, lat="lat", lon="lon", text="label", hover_name="city",
        color="call", color_discrete_map=COLOR, symbol="call", symbol_map=SYMBOL,
    )
    fig.update_traces(marker_size=16, marker_line_width=3)
    # Lakeshore cities get their label on the right (over the water) so labels do not overlap.
    for trace in fig.data:
        # Milwaukee's label goes on top, or Detroit's dot covers it.
        trace.textposition = ["top center" if name == "Milwaukee" else "middle right" if lon > -89 else "middle left"
                              for name, lon in zip(trace.hovertext, trace.lon)]
    # Zoom to the Midwest and draw state borders (no map token needed).
    fig.update_geos(scope="north america", resolution=50, showsubunits=True, showlakes=True,
                    lataxis_range=[36.5, 47.5], lonaxis_range=[-102, -75])
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0),
                      legend=dict(title="", orientation="h", y=1.08))
    return fig


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
    return rows.assign(date=rows["target_date"])  # city_map looks rows up by "date"


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


def live_card(rows, city, metrics, today, updating=False, failed=False):
    """updating: a new forecast is being made right now. failed: the last attempt to make one didn't work."""
    v = live_view(rows, city, metrics, today)
    update_note = "Updating…" if updating else "Couldn't update." if failed else ""
    if v["state"] == "none":
        return (f'<div class="verdict" style="background:{COLOR[NOT_READY]}"><div class="call">{NOT_READY}</div>'
                f'<div class="why">{update_note}</div></div>')
    why = {"out_of_date": f"The last forecast was for {pretty(v['date'])}.",
           "waiting": f"Waiting on: {v['status']}",
           "ok": f"Smoke forecast {v['forecast']:.1f} · indoors above {v['warn_at']:g}"}[v["state"]]
    note = f"Forecast made {v['made_at']:%A} at {v['made_at']:%-I:%M %p}."
    note = f"{note} {update_note}".strip()
    return f"""
    <div class="verdict" style="background:{COLOR[v['call']]}">
      <div class="where">{city} · practice on {pretty(v['date'])}</div>
      <div class="call">{v['call']}</div>
      <div class="why">{why}</div>
    </div>
    <div class="small">{note}</div>"""


ROWS = load_rows()
METRICS = load_metrics()
CITIES = sorted(ROWS["city"].unique())
DATES = sorted(ROWS["date"].unique())
DAY_CHOICES = [(f"{pd.Timestamp(d):%a %b} {pd.Timestamp(d).day}", d) for d in DATES]  # ("Thu Jul 31", "2025-07-31")


def show(city, date):
    return card(ROWS, city, date, METRICS), city_map(ROWS, date, METRICS)


def step(date, days):
    """The day before or after, staying inside 2025."""
    i = min(max(DATES.index(date) + days, 0), len(DATES) - 1)
    return DATES[i]


def today_central():
    return pd.Timestamp.now(tz="America/Chicago").strftime("%Y-%m-%d")


def show_live(city):
    rows = load_tomorrow()  # read again each time, so a new forecast shows without a restart
    updating = refresh.refresh_if_stale(rows)  # starts a background update if this one is old; never waits for it
    fresh = rows is not None and not is_out_of_date(rows["target_date"].iloc[0], today_central())
    figure = city_map(rows, rows["target_date"].iloc[0], METRICS) if fresh else None
    card_html = live_card(rows, city, METRICS, today_central(), updating, refresh.last_run_failed())
    # No forecast: hide the map instead of drawing an empty box.
    return card_html, gr.update(value=figure, visible=fresh)


def check_update(city, was_updating):
    """Every few seconds: redraw once when a background update finishes, otherwise change nothing."""
    updating = refresh.is_running()
    if was_updating and not updating:
        return *show_live(city), False
    return gr.skip(), gr.skip(), updating


with gr.Blocks(title="SmokeCheck") as demo:
    gr.Markdown("# SmokeCheck\n**Wildfire smoke: should tomorrow's practice move indoors?**")
    first_card, first_map = show(START_CITY, START_DATE)

    with gr.Tab("Tomorrow"):
        live_city = gr.Dropdown(CITIES, value=START_CITY, label="City")
        live_box = gr.HTML()  # filled by demo.load below, each time the page opens
        live_map = gr.Plot(show_label=False, visible=False)
        was_updating = gr.State(False)  # per open page: was an update running at the last check?
        timer = gr.Timer(3)

    with gr.Tab("2025 test run"):
        gr.Markdown("How we tested it: the model never saw 2025. Pick any day and see the call it would have made "
                    "the evening before, and whether it was right.")
        with gr.Row(equal_height=True):
            city = gr.Dropdown(CITIES, value=START_CITY, label="City", scale=2)
            day = gr.Dropdown(DAY_CHOICES, value=START_DATE, label="Practice day (2025)", scale=2)
            with gr.Column(scale=1, min_width=160):
                before = gr.Button("◀ Day before", size="sm")
                after = gr.Button("Next day ▶", size="sm")
        card_box = gr.HTML(first_card)
        gr.Markdown("### Every city that day")
        map_box = gr.Plot(first_map, show_label=False)
        if "overall" in METRICS:
            limit = bad_day_limit(METRICS)
            gr.Markdown(f"### All of 2025\nA bad day is measured above {limit:g}.")
            section = dict(METRICS["overall"])
            section["noaa_at_limit"] = stats_at_line(ROWS, "pred_noaa", limit, limit)
            gr.Dataframe(scoreboard(section, METRICS["cost_of_a_miss"]))
            gr.Markdown(arrival_note(ROWS, METRICS))

    gr.Markdown(FOOTER)

    live_city.change(show_live, live_city, [live_box, live_map], show_progress="hidden")
    outputs = [card_box, map_box]
    city.change(show, [city, day], outputs, show_progress="hidden")
    day.change(show, [city, day], outputs, show_progress="hidden")
    # The buttons only move the day; day.change then redraws.
    before.click(lambda d: step(d, -1), day, day, show_progress="hidden")
    after.click(lambda d: step(d, 1), day, day, show_progress="hidden")
    # Reload the live forecast whenever the page opens, so a long-running app never shows yesterday's file.
    demo.load(show_live, live_city, [live_box, live_map], show_progress="hidden")
    timer.tick(check_update, [live_city, was_updating], [live_box, live_map, was_updating], show_progress="hidden")

if __name__ == "__main__":
    # Always the light look, so it is the same on every laptop and projector.
    demo.launch(theme=THEME, css=CSS, js="() => document.body.classList.remove('dark')")
