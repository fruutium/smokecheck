"""SmokeCheck demo app. Reads data/predictions.csv and data/metrics.json and nothing else;
it never imports model code. Run:  .venv/bin/python app/app.py"""
import json
from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.express as px

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
NOT_READY = "⏳ No forecast for this day"
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


def card(rows, city, date, metrics):
    match = rows[(rows["city"] == city) & (rows["date"] == date)]
    # No row for this city and day: use an empty row so every value below reads as missing.
    row = match.iloc[0] if len(match) else pd.Series(dtype=float)
    pred, cut, limit = row.get("pred_model"), cutoff(metrics, "pred_model"), bad_day_limit(metrics)
    call = verdict(pred, cut)
    why = "" if call == NOT_READY else f"Smoke forecast {pred:.1f} · indoors above {cut:g}"

    measured = row.get("obs_pm25")
    measured_words = "" if pd.isna(measured) else ("a bad day" if measured > limit else "not a bad day")
    noaa = "" if pd.isna(row.get("pred_noaa")) else (
        f"<div><span>NOAA's forecast</span><b>{row['pred_noaa']:.1f}</b></div>")

    return f"""
    <div class="verdict" style="background:{COLOR[call]}">
      <div class="where">{city} · practice on {pretty(date)}</div>
      <div class="call">{call}</div>
      <div class="why">{why}</div>
    </div>
    <div class="check">
      <div class="title">Was it right?</div>
      <div><span>Measured that day</span><b>{number(measured, "no measurement")}</b> {measured_words}</div>
      {noaa}
      <div><span>SmokeCheck</span><b>{right_or_wrong(call, measured, limit)}</b></div>
    </div>"""


def city_map(rows, date, metrics):
    day_rows = rows[rows["date"] == date].copy()
    day_rows["call"] = [verdict(pred, cutoff(metrics, "pred_model")) for pred in day_rows["pred_model"]]
    day_rows["label"] = [f"{r['city']} {r['pred_model']:.0f}" if pd.notna(r["pred_model"]) else r["city"]
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


with gr.Blocks(title="SmokeCheck") as demo:
    gr.Markdown("# SmokeCheck\n**Wildfire smoke: should tomorrow's practice move indoors?** "
                "The call is made the evening before. This demo replays 2025, so you can see if each call was right.")
    first_card, first_map = show(START_CITY, START_DATE)

    with gr.Tab("The call"):
        with gr.Row(equal_height=True):
            city = gr.Dropdown(CITIES, value=START_CITY, label="City", scale=2)
            day = gr.Dropdown(DAY_CHOICES, value=START_DATE, label="Practice day (2025)", scale=2)
            with gr.Column(scale=1, min_width=160):
                before = gr.Button("◀ Day before", size="sm")
                after = gr.Button("Next day ▶", size="sm")
        card_box = gr.HTML(first_card)
        gr.Markdown("### Every city that day")
        map_box = gr.Plot(first_map, show_label=False)

    with gr.Tab("Does it work?"):
        if "overall" in METRICS:
            limit = bad_day_limit(METRICS)
            gr.Markdown(f"All of 2025, never used for training. A bad day is measured above {limit:g}.")
            section = dict(METRICS["overall"])
            section["noaa_at_limit"] = stats_at_line(ROWS, "pred_noaa", limit, limit)
            gr.Dataframe(scoreboard(section, METRICS["cost_of_a_miss"]))
            gr.Markdown(arrival_note(ROWS, METRICS))
        else:
            gr.Markdown("Results appear here once the model is evaluated.")

    gr.Markdown(FOOTER)

    outputs = [card_box, map_box]
    city.change(show, [city, day], outputs, show_progress="hidden")
    day.change(show, [city, day], outputs, show_progress="hidden")
    # The buttons only move the day; day.change then redraws.
    before.click(lambda d: step(d, -1), day, day, show_progress="hidden")
    after.click(lambda d: step(d, 1), day, day, show_progress="hidden")

if __name__ == "__main__":
    # Always the light look, so it is the same on every laptop and projector.
    demo.launch(theme=THEME, css=CSS, js="() => document.body.classList.remove('dark')")
