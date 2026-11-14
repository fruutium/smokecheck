"""Make the three finals charts from data/predictions.csv and data/metrics.json.

Run from the repo folder:  python docs/finals/make_charts.py   (needs pandas + matplotlib)
Every number is recomputed from the data and checked against the write-up table before a chart is saved.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
preds = pd.read_csv(ROOT / "data/predictions.csv")
metrics = json.load(open(ROOT / "data/metrics.json"))
test = preds[preds["split"] == "test"]
BAD = metrics["threshold"]  # 35: a bad day
warn_at = metrics["warn_at"]

NAMES = {"pred_model": "SmokeCheck", "pred_noaa": "NOAA official", "pred_persistence": "Tomorrow = today",
         "pred_cams": "Raw CAMS (optimistic)"}
ACCENT, GREY, DARK, RED = "#d9480f", "#868e96", "#212529", "#c92a2a"

plt.rcParams.update({"font.size": 22, "font.family": ["Arial", "DejaVu Sans"], "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#495057", "svg.fonttype": "none"})


def mae(col):
    return round(float((test[col] - test["obs_pm25"]).abs().mean()), 2)


def cost(col, line):
    """5 x missed bad days + false alarms, warning when the forecast is above `line`."""
    real, warned = test["obs_pm25"] > BAD, test[col] > line
    return int(5 * (real & ~warned).sum() + (~real & warned).sum())


# Check against the write-up table (docs/writeup.md, Results) before drawing anything.
assert len(test) == 2190 and int((test["obs_pm25"] > BAD).sum()) == 35
assert [mae(c) for c in NAMES] == [2.58, 3.20, 3.40, 3.72]
assert [warn_at[c] for c in NAMES] == [24.5, 52.5, 37.0, 30.0]
assert [cost(c, warn_at[c]) for c in NAMES] == [106, 166, 134, 107]
assert cost("pred_noaa", 35) == 123

# 1. Average error by forecaster
fig, ax = plt.subplots(figsize=(14, 6))
cols = list(NAMES)[::-1]
vals = [mae(c) for c in cols]
bars = ax.barh([NAMES[c] for c in cols], vals, color=[ACCENT if c == "pred_model" else GREY for c in cols], height=0.6)
for b, v in zip(bars, vals):
    ax.text(v + 0.05, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center", fontsize=26, color=DARK, fontweight="bold")
ax.set_xlim(0, 4.4)
ax.set_xlabel("Average error in 2025, µg/m³ (lower is better)")
ax.tick_params(axis="y", length=0)
fig.tight_layout()
fig.savefig(OUT / "chart_error.svg", transparent=True)

# 2. Warning cost at each forecaster's own line (set on 2022-24) and at the plain 35 line
fig, ax = plt.subplots(figsize=(14, 6.5))
cols = list(NAMES)
own = [cost(c, warn_at[c]) for c in cols]
at35 = [cost(c, 35) for c in cols]
x = range(len(cols))
w = 0.38
b1 = ax.bar([i - w / 2 for i in x], own, w, color=[ACCENT if c == "pred_model" else "#495057" for c in cols],
            label="Own line, set on 2022–24")
b2 = ax.bar([i + w / 2 for i in x], at35, w, color="#ced4da", label="Plain 35 line")
for bars, vals in ((b1, own), (b2, at35)):
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, str(v), ha="center", fontsize=24, color=DARK, fontweight="bold")
labels = [f"{NAMES[c]}\nline {warn_at[c]:g}" for c in cols]
ax.set_xticks(list(x), labels, fontsize=20)
ax.set_ylim(0, 215)
ax.set_ylabel("5 × missed + false alarms")
ax.tick_params(axis="x", length=0)
ax.legend(frameon=False, fontsize=20, loc="upper left", ncol=2)
fig.tight_layout()
fig.savefig(OUT / "chart_cost.svg", transparent=True)

# 3. Chicago, July 27 - August 2, 2025
week = test[(test["city"] == "Chicago") & test["date"].between("2025-07-27", "2025-08-02")].copy()
row = week.set_index("date")
assert [round(row.loc["2025-07-31", c], 1) for c in ("obs_pm25", "pred_model", "pred_noaa")] == [65.6, 13.7, 13.7]
assert [round(row.loc["2025-08-01", c], 1) for c in ("obs_pm25", "pred_model", "pred_noaa")] == [45.5, 54.0, 8.7]
days = pd.to_datetime(week["date"]).dt.strftime("%b %-d")
fig, ax = plt.subplots(figsize=(15, 6.5))
ax.axhline(BAD, color=RED, lw=2, ls="--")
ax.text(-0.3, BAD + 1.5, "35: bad day", color=RED, fontsize=20)
ax.axhline(warn_at["pred_model"], color=ACCENT, lw=2, ls=":")
ax.text(-0.3, warn_at["pred_model"] + 1.5, "24.5: SmokeCheck warns", color=ACCENT, fontsize=20)
xs = range(len(week))
ax.plot(xs, week["obs_pm25"], color=DARK, lw=5, marker="o", ms=12, label="Measured")
ax.plot(xs, week["pred_model"], color=ACCENT, lw=4, marker="o", ms=10, label="SmokeCheck")
ax.plot(xs, week["pred_noaa"], color=GREY, lw=4, marker="s", ms=9, label="NOAA official")
ax.set_xticks(list(xs), days, fontsize=20)
ax.set_ylim(0, 85)
ax.set_ylabel("PM2.5, µg/m³")
ax.legend(frameon=False, fontsize=20, loc="upper left", ncol=3)
fig.tight_layout()
fig.savefig(OUT / "chart_chicago_week.svg", transparent=True)

print("saved 3 charts; all checks passed")
