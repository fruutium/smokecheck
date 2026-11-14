# SmokeCheck demo flow

Plan for the Gradio app. The app is the optional extra on top of the hub's Colab notebook, so it stays small.
It reads two files and nothing else: `data/predictions.csv` and `data/metrics.json`. It never imports model code.

## The 60 seconds a judge sees
1. The app opens on **Chicago, [headline 2025 smoke day]** (the hub tells us which day). No clicks needed to see a result.
2. **Verdict card**, the biggest thing on the page: "Move practice indoors" or "OK to practice outside", with the forecast number and the limit of 35 µg/m³.
3. **Three numbers** under it: "Raw CAMS estimate said X · SmokeCheck said Y · Monitors measured Z". Persistence is shown smaller.
4. **Map** of the Midwest cities, one dot per city, colored by SmokeCheck's forecast for that day (green below the limit, orange/red above).
5. Drag the **date slider** a few days either way: the dots and the verdict change as the smoke arrives and leaves.
6. Switch **city** in the dropdown: same day, different verdict.
7. Tab **"Does it work?"**: the baseline table (persistence, climatology, raw CAMS, SmokeCheck) from `metrics.json`, with the split by city and by smoke vs clean days.
8. Tab **"Where it fails"**: the worst misses in the 2025 test set, real rows, largest error first.

Footer on every tab: "Open-Meteo air-quality values are model estimates, not measurements. Prototype, not health advice."

## Where each piece gets its data
| Piece | Source |
|---|---|
| City dropdown, map dots | `city`, `lat`, `lon` |
| Date slider | `date`, test rows only (`split == "test"`) |
| Verdict | `pred_model` compared with `threshold` from `metrics.json` |
| Three numbers | `pred_cams`, `pred_model`, `obs_pm25` (+ `pred_persistence`) |
| "Does it work?" table | `metrics.json` |
| "Where it fails" list | rows sorted by `abs(pred_model - obs_pm25)`, test only |
| Uncertainty band (only if present) | `pred_lo`, `pred_hi` |
| Smoke-day markers on the slider (only if present) | `is_smoke_day` |

## Rules the app follows
- The verdict uses **only the forecast**, because that is all the athletic director would have had the day before. The measured value is shown as "what happened", never used for the call.
- Only 2025 test rows are shown. Training days would make the model look better than it is.
- A day with no monitor reading shows "no measurement", not 0. A day with no forecast shows "no forecast", not a verdict.
- The app works without `pred_lo`, `pred_hi` and `is_smoke_day`.
- No mock data. Until the hub sends real rows, the app shows nothing rather than invented numbers.

## Not building (unless there is time after the first submission)
- Hourly slider and practice-hour (3–6 PM) forecast: the first model is a daily average.
- Live "today" mode: November is outside smoke season, so the map would be all green.
- Individual schools on the map: the forecast is per city.
- A "reveal what happened" button: the measured value is simply always shown.

## Decided
- **Two verdict levels** (Aiden, Nov 13): "OK to practice outside" / "Move practice indoors", split at the single 35 µg/m³ limit. A third level would need a second cutoff we'd have to justify.
- **Two colors to match:** green at or below the limit, red above it, on the verdict card and the map dots.
