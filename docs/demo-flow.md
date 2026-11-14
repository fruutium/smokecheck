# SmokeCheck demo flow (live, at finals)

The same clicks as the video (`docs/video-script.md`), with more room to talk: about two and a half minutes.
The app is one page with three views in the top bar (**Tomorrow**, **2025 test run**, **Does it work?**) and a city picker in the top-right corner.
The whole backdrop is the sky over a practice field. Its colour follows the forecast: clear dusk blue on a clean day, orange-brown haze and a red sun on a smoke day.

## Before you start
- Start the app (`python app/app.py`, then http://127.0.0.1:7860) a few minutes early, with internet on. Only the Tomorrow view needs the internet.
- Backup: the hosted copy at https://fruutium.github.io/smokecheck/ shows the same screens. It needs the internet for every view, so keep the laptop copy as the main one.
- Set the picker to **Minneapolis** and reload the page. The app remembers the last city, and a reload goes back to the Tomorrow view and to July 31.
- Wait until "Updating…" is gone from the Tomorrow view.
- Browser window about 1280×800, zoom 100%.
- Keep `docs/video/demo-silent.mp4` open in another window as the backup.

## The stops (five clicks)
1. **Tomorrow**, no click. "Minneapolis · Practice on [tomorrow]", the call in big letters, "Smoke forecast [number]", "Indoors above 32", "Forecast made [day] at [time]".
   Say: this is tomorrow's real forecast for Minneapolis, made this evening from live readings. Read the call off the screen. The app remakes it by itself. In November the air is clean, so expect "OK TO PRACTICE OUTSIDE".
2. Click **2025 test run**. It opens on Minneapolis, Thursday, July 31, 2025. "MOVE PRACTICE INDOORS", smoke forecast 41.3, above the line at 32.
   The "WAS IT RIGHT?" panel: "RIGHT CALL", measured that day 69.1 ("A bad day" means measured above 35), NOAA's forecast 18.7. Our catch.
   Say why the line is 32 and not 35: SmokeCheck's forecasts run low on smoke days. The line was set on 2022 to 2024, with one missed smoke day counted as five false alarms.
   The scale under the numbers shows all three against the line: SmokeCheck (triangle), NOAA (ring), measured (diamond).
3. City picker → **Chicago**, same day. "OK TO PRACTICE OUTSIDE", forecast 15.3, "MISSED A BAD DAY", measured 65.6, NOAA's forecast 13.7.
   Our miss, and NOAA's too. The smoke arrived overnight, and the model leans on today's readings, which were still clean. In 2025 it warned on 0 of 21 days when smoke first arrived.
4. Click the **›** button next to the date, once: Friday, August 1, 2025. "MOVE PRACTICE INDOORS", forecast 51.8, "RIGHT CALL", measured 45.5, NOAA's forecast 8.7.
   Smoke that stays is our strength: 11 of 14 such days caught.
   Use the button, not the arrow key. Right after you pick a city the keyboard is still on the picker.
5. Click **Does it work?**. Headline: "26% LOWER ERROR THAN NOAA'S OFFICIAL FORECAST." Under it: "Its warnings cost 127. Reading NOAA at 35 cost 123. Lower is better."
   Table, one row per forecaster: SmokeCheck 2.36 · NOAA's official forecast 3.20 · NOAA's official forecast, read at 35 (cost 123) · Yesterday's reading 3.40 (cost 134).
   Say the takeaway: more accurate than NOAA in every city and every one of 1,000 resamples, but the move-indoors warnings were slightly worse than just reading NOAA at 35.
   Finish on the last line: "Weak spot: it misses the day smoke first arrives (warned on 0 of 21 in 2025)." Then what is next: more cities that get smoke, and a real athletic director.

If a judge asks for another city: Milwaukee, July 31, 2025. Forecast 28.1, outside, measured 83.7. Another missed arrival day.

Footer on every view: "Smoke numbers are daily average PM2.5 in µg/m³. A prototype, not medical or health advice."

## If the Tomorrow view is not ready
- **A forecast is on screen and "Updating…" sits after "Forecast made …".** The app is remaking the forecast (under a minute). The one on screen is still real. Say the line and move on. The number may change while you talk.
- **A forecast is on screen and it says "Couldn't update."** The last forecast is still shown. Say "this is the last forecast it made" and read the time off the screen. Then carry on.
- **Grey sky and only "UPDATING…", "COULDN'T UPDATE." or "NO FORECAST YET" in big letters.** There is no forecast to show. Say "the live forecast is still loading" and click **2025 test run**.
- In every case, carry on to the 2025 test run. It and "Does it work?" read saved files and need no network.
- If there is time at the end, click **Tomorrow** again. Each visit asks for a newer forecast. After a failed try the app waits five minutes before it tries again.
- If the app will not start at all, play `docs/video/demo-silent.mp4` and talk over it. The stills in `docs/video/` show the same five screens.

## Where each piece gets its data
| Piece | Source |
|---|---|
| City picker | the six cities in `data/predictions.csv` |
| Tomorrow view | `data/tomorrow.csv`, written by `forecast_tomorrow.py`. The app reruns that script in the background when the saved forecast is old (`app/refresh.py`) |
| 2025 test run, the day | `date`, test rows only (`split == "test"`) |
| The call | `pred_model` compared with `warn_at["pred_model"]` in `data/metrics.json` (32) |
| "Measured that day", "A bad day" | `obs_pm25` compared with `threshold` (35) |
| "NOAA's forecast" | `pred_noaa` |
| "Right call", "Missed a bad day", "False alarm" | the call compared with whether it was a bad day |
| "Does it work?" table | `metrics.json`. The "read at 35" row is counted in the app from `predictions.csv` |
| "Weak spot" line | days when yesterday's reading was at or under 35 and the measured value was above 35 (`pred_persistence`, `obs_pm25`), and how many of them SmokeCheck warned on |
| Sky colour | the forecast on screen. The small picture beside "Measured that day" is the sky for the measured value |

## Rules the app follows
- The call uses **only the forecast**, because that is all the athletic director has the evening before. The measured value is shown as what happened, never used for the call.
- The test run shows only 2025 test rows. Training days would make the model look better than it is.
- A day with no monitor reading shows "No measurement", not 0. With no forecast the page shows "No forecast yet" on a grey sky, not a call.
- Words and shapes carry the call, not only colour: a solid square with a house for indoors, an open ring for outside.
- No mock data. Every number comes from the data files or the live sources.

## Decided
- **Two calls** (Aiden, Nov 13): "OK to practice outside" / "Move practice indoors". SmokeCheck warns above its own line from `warn_at` (32 since the Nov 14 model change). 35 only defines a bad day.
- **Live mode is in** (Nov 14): the Tomorrow view. In November it mostly shows clean air, so the 2025 test run carries the demo.
- **Cut in the Nov 14 redesign:** the six-city map, the separate failures view and the forecast range. Each view shows one city and one call.

## Not building
- Hourly or practice-hour (3 to 6 PM) forecasts: the model forecasts a daily average.
- Individual schools: the forecast is per city.
