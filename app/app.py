"""SmokeCheck demo app. Reads data/predictions.csv and data/metrics.json and nothing else;
it never imports model code. Run:  .venv/bin/python app/app.py"""
import json
from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.express as px

DATA = Path(__file__).parent.parent / "data"
DEFAULT_LIMIT = 35  # µg/m³ daily mean; only used when metrics.json does not say otherwise
START_CITY, START_DATE = "Milwaukee", "2025-07-31"  # the headline smoke day
# Readable names for the forecast columns, SmokeCheck first. Any other pred_* column shows under its own name.
NAMES = {"pred_model": "SmokeCheck", "pred_cams": "Raw CAMS estimate",
         "pred_persistence": "Persistence (yesterday's measurement)",
         "pred_climatology": "Climatology (usual for this city and month)"}

OK = "✅ OK to practice outside"
INDOORS = "🚫 Move practice indoors"
NOT_READY = "⏳ SmokeCheck forecast not ready yet"
SHOWN_ELSEWHERE = ["pred_model", "pred_cams", "pred_lo", "pred_hi"]  # not repeated in the baselines line
COLOR = {OK: "#1b7a3e", INDOORS: "#b42318", NOT_READY: "#5b6470"}
SYMBOL = {OK: "circle", INDOORS: "square", NOT_READY: "circle-open"}  # shape too, not color alone
FOOTER = "Open-Meteo air-quality values are model estimates, not measurements. Prototype, not health advice."

CSS = """
.verdict { border-radius: 14px; padding: 28px 32px; }
.verdict, .verdict * { color: #fff !important; }
.verdict .where { font-size: 1.15rem; font-weight: 600; }
.verdict .call { font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 800; line-height: 1.05; margin: 8px 0 12px; }
.verdict .why { font-size: 1.1rem; }
.verdict .how { font-size: 0.95rem; margin-top: 6px; opacity: 0.95; }
.numbers { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 14px; }
.numbers div { border: 1px solid var(--border-color-primary); border-radius: 10px; padding: 12px 16px; }
.numbers span { display: block; color: var(--neutral-600); }
.numbers b { font-size: 2rem; }
.numbers i { display: block; font-style: normal; font-weight: 600; }
.small { color: var(--neutral-600); font-size: 0.9rem; margin-top: 10px; }
"""
FONT = [gr.themes.GoogleFont("Barlow", weights=(400, 600, 800)), "system-ui", "sans-serif"]
THEME = gr.themes.Soft(primary_hue="emerald", neutral_hue="slate", font=FONT)


def load_rows(data_dir=DATA):
    if (data_dir / "predictions.csv").exists():
        rows = pd.read_csv(data_dir / "predictions.csv")
    else:
        # Before the model has run we only have the raw data, and CAMS is the one estimate in it.
        rows = pd.read_csv(data_dir / "daily.csv").rename(columns={"cams_pm25": "pred_cams"})
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
    # Only the forecast decides: it is all the athletic director has the day before.
    if pd.isna(pred):
        return NOT_READY
    return OK if pred <= cut else INDOORS


def number(value, missing):
    """A value with one decimal, or words when it is missing (never 0)."""
    return missing if pd.isna(value) else f"{value:.1f}"


def call_words(value, cut):
    """What one forecaster said about the day, e.g. '→ warn (cut-off 29.5)'."""
    if pd.isna(value):
        return ""
    word = "warn" if verdict(value, cut) == INDOORS else "no warning"
    return f"→ {word} (cut-off {cut:g})"


def bad_day_words(measured, limit):
    if pd.isna(measured):
        return ""
    return f"above {limit:g}: a bad day" if measured > limit else f"{limit:g} or below: not a bad day"


def pretty(date):
    day = pd.Timestamp(date)
    return f"{day:%A, %B} {day.day}, {day.year}"


def card(rows, city, date, metrics):
    match = rows[(rows["city"] == city) & (rows["date"] == date)]
    # No row for this city and day: use an empty row so every value below reads as missing.
    row = match.iloc[0] if len(match) else pd.Series(dtype=float)
    pred, cut, limit = row.get("pred_model"), cutoff(metrics, "pred_model"), bad_day_limit(metrics)
    call = verdict(pred, cut)

    if call == NOT_READY:
        why = "No call without a forecast."
    else:
        why = f"SmokeCheck forecasts {pred:.1f} µg/m³ for this day."
        if pd.notna(row.get("pred_lo")) and pd.notna(row.get("pred_hi")):
            why += f" Likely range {row['pred_lo']:.1f} to {row['pred_hi']:.1f}."
    how = f"SmokeCheck warns above {cut:g} µg/m³."
    if "cost_of_a_miss" in metrics and cut != limit:
        # The cut-off was set on the training years (2022–2024 in predictions.csv), never on 2025.
        how = (f"SmokeCheck warns above {cut:g} µg/m³, not {limit:g}, because its forecasts run low on smoke "
               f"days. We set that cut-off on 2022–2024 so one missed bad day costs as much as "
               f"{metrics['cost_of_a_miss']:g} false alarms.")

    # Every other pred_* column in the file is a baseline, shown smaller under the three numbers.
    others = [c for c in rows.columns if c.startswith("pred_") and c not in SHOWN_ELSEWHERE]
    baselines = " · ".join(f"{NAMES.get(c, c)} said {number(row.get(c), 'nothing')} "
                           f"{call_words(row.get(c), cutoff(metrics, c))}" for c in others)
    cams = row.get("pred_cams")
    measured = row.get("obs_pm25")

    return f"""
    <div class="verdict" style="background:{COLOR[call]}">
      <div class="where">{city} · {pretty(date)}</div>
      <div class="call">{call}</div>
      <div class="why">{why}</div>
      <div class="how">{how}</div>
    </div>
    <div class="numbers">
      <div><span>Raw CAMS estimate said</span><b>{number(cams, "no estimate")}</b>
        <i>{call_words(cams, cutoff(metrics, "pred_cams"))}</i></div>
      <div><span>SmokeCheck said</span><b>{number(pred, "not ready yet")}</b><i>{call_words(pred, cut)}</i></div>
      <div><span>Monitors measured</span><b>{number(measured, "no measurement")}</b>
        <i>{bad_day_words(measured, limit)}</i></div>
    </div>
    <div class="small">
      Baselines: {baselines or "none yet"}.<br>
      All values are daily-average PM2.5 in µg/m³. The measurement is what happened; it is never used for the call.
    </div>"""


def city_map(rows, date, metrics):
    day_rows = rows[rows["date"] == date].copy()
    day_rows["call"] = [verdict(pred, cutoff(metrics, "pred_model")) for pred in day_rows["pred_model"]]
    labels = []
    for _, row in day_rows.iterrows():
        if pd.notna(row["pred_model"]):
            labels.append(f"{row['city']}<br>forecast {row['pred_model']:.1f}")
        elif pd.notna(row["obs_pm25"]):
            labels.append(f"{row['city']}<br>measured {row['obs_pm25']:.1f}")
        else:
            labels.append(f"{row['city']}<br>no measurement")
    day_rows["label"] = labels

    fig = px.scatter_geo(
        day_rows, lat="lat", lon="lon", text="label", hover_name="city",
        color="call", color_discrete_map=COLOR, symbol="call", symbol_map=SYMBOL,
    )
    fig.update_traces(marker_size=16, marker_line_width=3)
    # Lakeshore cities get their label on the right (over the water) so labels do not overlap.
    for trace in fig.data:
        trace.textposition = ["middle right" if lon > -89 else "middle left" for lon in trace.lon]
    # Zoom to the Midwest and draw state borders (no map token needed).
    fig.update_geos(scope="north america", resolution=50, showsubunits=True, showlakes=True,
                    lataxis_range=[36.5, 47.5], lonaxis_range=[-102, -75])
    fig.update_layout(height=460, margin=dict(l=0, r=0, t=40, b=0),
                      legend=dict(title="", orientation="h", y=1.1))
    return fig


def scoreboard(section):
    """One row per forecaster, SmokeCheck first. section is {pred_column: {mae, warn_at, caught, ...}}."""
    order = [c for c in NAMES if c in section] + [c for c in section if c not in NAMES]
    return pd.DataFrame([{
        "Forecaster": NAMES.get(c, c),
        "Average miss (MAE, µg/m³)": section[c].get("mae"),
        "Warns above": section[c].get("warn_at"),
        "Bad days caught": f"{section[c].get('caught')} of {section[c].get('bad_days')}",
        "False alarms": section[c].get("false_alarms"),
    } for c in order])


def grouped_scoreboard(section, group_name):
    """The same table for each group ({group: {pred_column: {...}}}), stacked, with the group in front."""
    tables = []
    for group, stats in section.items():
        table = scoreboard(stats)
        table.insert(0, group_name, group.replace("_", " ").capitalize())  # "smoke_day" -> "Smoke day"
        tables.append(table)
    return pd.concat(tables)


def worst_misses(rows, metrics):
    scored = rows.dropna(subset=["pred_model", "obs_pm25"]).copy()
    scored["miss"] = (scored["pred_model"] - scored["obs_pm25"]).abs()
    scored = scored.sort_values("miss", ascending=False)
    limit = bad_day_limit(metrics)
    table = pd.DataFrame({"Date": scored["date"], "City": scored["city"]})
    if "is_smoke_day" in scored:
        table["Smoke plume"] = scored["is_smoke_day"].map({True: "yes", False: ""})
    table["Measured"] = [f"{v:.1f}" + (" (bad day)" if v > limit else "") for v in scored["obs_pm25"]]
    table["SmokeCheck off by"] = scored["miss"]
    for column in [c for c in NAMES if c in scored] + [c for c in scored if c.startswith("pred_") and c not in NAMES]:
        cut = cutoff(metrics, column)
        short_name = NAMES.get(column, column).split(" (")[0]  # "Persistence (yesterday's ...)" -> "Persistence"
        table[short_name] = [
            number(v, "none") + (" → warn" if verdict(v, cut) == INDOORS else "") for v in scored[column]]
    return table


ROWS = load_rows()
METRICS = load_metrics()
CITIES = sorted(ROWS["city"].unique())
DATES = sorted(ROWS["date"].unique())
START_DAY = DATES.index(START_DATE) + 1 if START_DATE in DATES else 1


def show(city, day_number):
    date = DATES[int(day_number) - 1]
    return card(ROWS, city, date, METRICS), city_map(ROWS, date, METRICS), pretty(date)


with gr.Blocks(title="SmokeCheck") as demo:
    gr.Markdown("# SmokeCheck\nWildfire smoke tomorrow: does practice stay outside? "
                "A replay of every day in 2025 for six Midwest cities.")
    first_card, first_map, first_date = show(START_CITY, START_DAY)

    with gr.Tab("Tomorrow's call"):
        with gr.Row():
            city = gr.Dropdown(CITIES, value=START_CITY, label="City", scale=1)
            day = gr.Slider(1, len(DATES), value=START_DAY, step=1, scale=3,
                            label="Day of 2025 (drag, or click it and use the arrow keys)")
            date_box = gr.Textbox(first_date, label="Date", interactive=False, scale=1)
        card_box = gr.HTML(first_card)
        map_box = gr.Plot(first_map, show_label=False)

    with gr.Tab("Does it work?"):
        limit = bad_day_limit(METRICS)
        gr.Markdown(f"A **bad day** is one the monitors measured above {limit:g} µg/m³. **Caught** = a bad day "
                    f"the forecaster warned about. **False alarm** = it warned and the day was not bad. "
                    f"Test period: all of 2025, never used for training or for choosing cut-offs.")
        sections = [("overall", "All of 2025", None), ("by_smoke", "Smoke-plume days vs clean days", "Day type"),
                    ("by_city", "By city", "City"),
                    ("training_years_out_of_fold", "Training years (out-of-fold)", None)]
        shown = [s for s in sections if s[0] in METRICS]
        for key, title, group_name in shown:
            gr.Markdown(f"### {title}")
            table = scoreboard(METRICS[key]) if group_name is None else grouped_scoreboard(METRICS[key], group_name)
            gr.Dataframe(table, max_height=900)
        if not shown:
            gr.Markdown("Results appear here once the model is evaluated.")

    with gr.Tab("Where it fails"):
        misses = worst_misses(ROWS, METRICS)
        if misses.empty:
            gr.Markdown("SmokeCheck forecast not ready yet, so there are no misses to rank.")
        else:
            gr.Markdown("The 50 days of 2025 where SmokeCheck was furthest off, largest first (µg/m³). Smoke plume = NOAA "
                        "satellite maps show smoke over the city. "
                        "**Smoke arrival days are the weak spot:** yesterday's reading was fine and today's is bad. "
                        "That is when the raw CAMS estimate, which sees the smoke coming, does better. "
                        "The opposite happens too: the day after the smoke clears, SmokeCheck can still warn.")
            # Numbers get the same one-decimal format as the card; text columns are left alone.
            gr.Dataframe(misses.head(50).map(lambda v: f"{v:.1f}" if isinstance(v, float) else v), max_height=900)

    gr.Markdown(FOOTER)

    outputs = [card_box, map_box, date_box]
    city.change(show, [city, day], outputs, show_progress="hidden")
    # always_last: while the slider is dragged, skip to the newest day instead of queueing each one.
    day.change(show, [city, day], outputs, show_progress="hidden", trigger_mode="always_last")

if __name__ == "__main__":
    # Always the light look, so it is the same on every laptop and projector.
    demo.launch(theme=THEME, css=CSS, js="() => document.body.classList.remove('dark')")
