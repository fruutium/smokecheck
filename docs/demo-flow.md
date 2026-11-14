# SmokeCheck demo flow

Plan for the Gradio app. The app is the optional extra on top of the hub's Colab notebook, so it stays small.
It reads two files and nothing else: `data/predictions.csv` and `data/metrics.json`. It never imports model code.

## The 60 seconds a judge sees (three stops, one city change, one slider step)
1. Opens on **Milwaukee, July 31, 2025**, no clicks needed. SmokeCheck forecast 26.8, above its warning line of 24.5 → **Move practice indoors**. Measured 83.7. NOAA's official forecast said 13.4. (Our success.)
2. The card says why the line is 24.5, not 35: forecasts run low on smoke days, and the line was set on 2022–2024 so one missed bad day costs as much as 5 false alarms.
3. Under the card, each forecast with its own call: NOAA's official forecast 13.4 → no warning (line 52.5) · persistence 32.3 → outside (line 37) · raw CAMS (optimistic) 38.5 → warn (line 30) · monitors measured 83.7 (a bad day).
4. Switch city to **Chicago**, same day: SmokeCheck 13.7 (likely 8.8–20.6) and NOAA 13.7 → outside, measured 65.6. (Our miss, and NOAA's: smoke arrived overnight. Only the optimistic CAMS archive, 34.3, warned.)
5. Step the slider to **August 1**: SmokeCheck 54.0 → warn, NOAA 8.7 and CAMS 19.1 → outside, measured 45.5. (Smoke lingering: our strength.)
6. Tab **"Does it work?"**: one row per forecast (MAE, warns above, bad days caught of 35, false alarms), then smoke vs clean days, then by city.
7. Tab **"Where it fails"**: the worst misses in 2025, with a note that smoke-arrival days are the weak spot.

Footer on every tab: "Open-Meteo air-quality values are model estimates, not measurements. Prototype, not health advice."

## Where each piece gets its data
| Piece | Source |
|---|---|
| City dropdown, map dots | `city`, `lat`, `lon` |
| Date slider | `date`, test rows only (`split == "test"`) |
| Verdict, map colors | `pred_model` compared with `warn_at["pred_model"]` (24.5); each baseline uses its own `warn_at` |
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
- **Two verdict levels** (Aiden, Nov 13): "OK to practice outside" / "Move practice indoors". Originally split at 35; since Nov 14 each forecast uses its own warning line from `warn_at` (SmokeCheck 24.5), and 35 only defines a bad day.
- **Two colors to match:** green at or below the warning line, red above it, on the verdict card and the map dots.
