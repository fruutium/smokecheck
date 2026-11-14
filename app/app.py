"""SmokeCheck demo app. Reads data/predictions.csv and data/metrics.json and nothing else;
it never imports model code. Run:  .venv/bin/python app/app.py"""
import json
from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.express as px

DATA = Path(__file__).parent.parent / "data"
DEFAULT_LIMIT = 35  # µg/m³ daily mean; only used until metrics.json brings the real threshold
START_CITY, START_DATE = "Chicago", "2025-07-31"  # the headline smoke day
# Readable names for the forecast columns. A pred_* column that is not listed shows under its own name.
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
.verdict .why { font-size: 1.05rem; }
.numbers { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 14px; }
.numbers div { border: 1px solid var(--border-color-primary); border-radius: 10px; padding: 12px 16px; }
.numbers span { display: block; color: var(--neutral-600); }
.numbers b { font-size: 2rem; }
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
    return json.loads(path.read_text()) if path.exists() else None


def verdict(pred, limit):
    # Only the forecast decides: it is all the athletic director has the day before.
    if pd.isna(pred):
        return NOT_READY
    return OK if pred <= limit else INDOORS


def number(value, missing):
    """A value with one decimal, or words when it is missing (never 0)."""
    return missing if pd.isna(value) else f"{value:.1f}"


def card(rows, city, date, limit):
    match = rows[(rows["city"] == city) & (rows["date"] == date)]
    # No row for this city and day: use an empty row so every value below reads as missing.
    row = match.iloc[0] if len(match) else pd.Series(dtype=float)
    pred = row.get("pred_model")
    call = verdict(pred, limit)
    day = pd.Timestamp(date)

    if call == NOT_READY:
        why = f"No call without a forecast. The limit is {limit} µg/m³."
    else:
        why = f"SmokeCheck forecasts {pred:.1f} µg/m³. The limit is {limit} µg/m³."
        if pd.notna(row.get("pred_lo")) and pd.notna(row.get("pred_hi")):
            why += f" Likely range {row['pred_lo']:.1f} to {row['pred_hi']:.1f}."

    # Every other pred_* column in the file is a baseline, shown smaller under the three numbers.
    others = [c for c in rows.columns if c.startswith("pred_") and c not in SHOWN_ELSEWHERE]
    baselines = " · ".join(f"{NAMES.get(c, c)} said {number(row.get(c), 'nothing')}" for c in others)

    return f"""
    <div class="verdict" style="background:{COLOR[call]}">
      <div class="where">{city} · {day:%A, %B} {day.day}, {day.year}</div>
      <div class="call">{call}</div>
      <div class="why">{why}</div>
    </div>
    <div class="numbers">
      <div><span>Raw CAMS estimate said</span><b>{number(row.get("pred_cams"), "no estimate")}</b></div>
      <div><span>SmokeCheck said</span><b>{number(pred, "not ready yet")}</b></div>
      <div><span>Monitors measured</span><b>{number(row.get("obs_pm25"), "no measurement")}</b></div>
    </div>
    <div class="small">
      Baselines: {baselines or "none yet"}.<br>
      All values are daily-average PM2.5 in µg/m³. The measurement is what happened; it is never used for the call.
    </div>"""


def city_map(rows, date, limit):
    day_rows = rows[rows["date"] == date].copy()
    day_rows["call"] = [verdict(pred, limit) for pred in day_rows["pred_model"]]
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


def metrics_table(metrics):
    # The nesting of metrics.json is not fixed (overall / by city / later by smoke), so flatten it:
    # "by_city / Chicago / pred_cams / mae" becomes row "by_city / Chicago / pred_cams", column "mae".
    nested = {key: value for key, value in metrics.items() if isinstance(value, dict)}
    if not nested:
        return pd.DataFrame()
    table = {}
    for key, value in pd.json_normalize(nested, sep=" / ").to_dict("records")[0].items():
        label, _, stat = key.rpartition(" / ")
        for column, name in NAMES.items():
            label = label.replace(column, name)
        table.setdefault(label, {})[stat] = value
    return pd.DataFrame.from_dict(table, orient="index").rename_axis("Forecast").reset_index()


def worst_misses(rows):
    scored = rows.dropna(subset=["pred_model", "obs_pm25"]).copy()
    scored["Miss"] = (scored["pred_model"] - scored["obs_pm25"]).abs()
    baselines = [c for c in rows.columns if c.startswith("pred_") and c != "pred_model"]
    scored = scored.sort_values("Miss", ascending=False)
    scored = scored[["date", "city", "pred_model", "obs_pm25", "Miss"] + baselines]
    return scored.rename(columns={"date": "Date", "city": "City", "obs_pm25": "Monitors measured", **NAMES})


ROWS = load_rows()
METRICS = load_metrics()
LIMIT = (METRICS or {}).get("threshold", DEFAULT_LIMIT)
CITIES = sorted(ROWS["city"].unique())
DATES = sorted(ROWS["date"].unique())
START_DAY = DATES.index(START_DATE) + 1 if START_DATE in DATES else 1


def show(city, day_number):
    date = DATES[int(day_number) - 1]
    return card(ROWS, city, date, LIMIT), city_map(ROWS, date, LIMIT)


with gr.Blocks(title="SmokeCheck") as demo:
    gr.Markdown("# SmokeCheck\nWildfire smoke tomorrow: does practice stay outside? "
                "A replay of every day in 2025 for six Midwest cities.")
    first_card, first_map = show(START_CITY, START_DAY)

    with gr.Tab("Tomorrow's call"):
        with gr.Row():
            city = gr.Dropdown(CITIES, value=START_CITY, label="City", scale=1)
            day = gr.Slider(1, len(DATES), value=START_DAY, step=1, scale=3,
                            label="Day of 2025 (drag, or use the arrow keys; the date shows in the card)")
        card_box = gr.HTML(first_card)
        map_box = gr.Plot(first_map, show_label=False)

    with gr.Tab("Does it work?"):
        if METRICS:
            # Top-level values that are not tables (the limit, the test period) go in one line.
            gr.Markdown(" · ".join(f"{k}: {v}" for k, v in METRICS.items() if not isinstance(v, dict)))
            gr.Dataframe(metrics_table(METRICS), max_height=900)
            gr.Markdown("mae = average miss in µg/m³ · bad_days = days measured above the limit · "
                        "caught / missed = bad days the forecast did / did not flag · "
                        "false_alarms = flagged days that stayed under the limit · recall = caught ÷ bad_days")
        # Look for SmokeCheck's rows anywhere in the file's text, whatever the nesting.
        if "pred_model" not in json.dumps(METRICS):
            gr.Markdown("SmokeCheck's results appear here once the model is evaluated.")

    with gr.Tab("Where it fails"):
        misses = worst_misses(ROWS)
        if misses.empty:
            gr.Markdown("SmokeCheck forecast not ready yet, so there are no misses to rank.")
        else:
            gr.Markdown("The 50 worst misses of the 2025 test year, largest first (µg/m³).")
            # Numbers get the same one-decimal format as the card; text columns are left alone.
            gr.Dataframe(misses.head(50).map(lambda v: f"{v:.1f}" if isinstance(v, float) else v))

    gr.Markdown(FOOTER)

    city.change(show, [city, day], [card_box, map_box], show_progress="hidden")
    # always_last: while the slider is dragged, skip to the newest day instead of queueing each one.
    day.change(show, [city, day], [card_box, map_box], show_progress="hidden", trigger_mode="always_last")

if __name__ == "__main__":
    # Always the light look, so it is the same on every laptop and projector.
    demo.launch(theme=THEME, css=CSS, js="() => document.body.classList.remove('dark')")
