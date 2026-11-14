# SmokeCheck demo flow

Plan for the Gradio app. The app is the optional extra on top of the hub's Colab notebook, so it stays small.
It reads two files and nothing else: `data/predictions.csv` and `data/metrics.json`. It never imports model code.

## The 60 seconds a judge sees (three stops, one city change, one slider step)
1. Opens on **Minneapolis, July 31, 2025**, no clicks needed. SmokeCheck forecast 41.3, above its warning line of 32 → **Move practice indoors**. Measured 69.1. NOAA's official forecast said 18.7. (Our catch.)
2. The card says why the line is 32, not 35 (forecasts run low on smoke days), how it was set on 2022–2024, and that those years can't pin it down (anywhere from about 27 to 32).
3. Under the card, each forecast with its own call: NOAA 18.7 → no warning (line 52.5, and also none at 35) · persistence and raw CAMS (optimistic) in the small line · monitors measured 69.1 (a bad day).
4. Switch city to **Chicago**, same day: SmokeCheck 15.3 (likely 10.1–21.0) and NOAA 13.7 → outside, measured 65.6. (Our miss, and NOAA's: smoke arrived overnight. SmokeCheck caught 0 of 21 arrival days in 2025.)
5. Step the slider to **August 1**: SmokeCheck 51.8 → warn, NOAA 8.7 → outside, measured 45.5. (Smoke lingering: our strength, 11 of 14.)
6. Tab **"Does it work?"**: one row per forecast (MAE, warns above, bad days caught of 35, false alarms, cost), with NOAA at the plain 35 line too.
7. Tab **"Where it fails"**: the worst misses in 2025, with a note on smoke-arrival days.

Footer on every tab: "Open-Meteo air-quality values are model estimates, not measurements. Prototype, not health advice."

## Where each piece gets its data
| Piece | Source |
|---|---|
| City dropdown, map dots | `city`, `lat`, `lon` |
| Date slider | `date`, test rows only (`split == "test"`) |
| Verdict, map colors | `pred_model` compared with `warn_at["pred_model"]` (32); each baseline uses its own `warn_at` |
| "Was it a bad day?" | `obs_pm25` compared with `threshold` (35) |
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
- **Two verdict levels** (Aiden, Nov 13): "OK to practice outside" / "Move practice indoors". Originally split at 35; since Nov 14 each forecast uses its own warning line from `warn_at` (SmokeCheck 32 since the Nov 14 model change), and 35 only defines a bad day.
- **Two colors to match:** green at or below the warning line, red above it, on the verdict card and the map dots.
