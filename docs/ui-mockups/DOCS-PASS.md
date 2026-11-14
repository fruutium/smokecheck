# Docs pass after the app redesign: shared facts (Nov 14, 2026)

Every agent in this pass reads this first. Work in `/Users/abhiddyu/Downloads/ecs/veritas hackathon/smokecheck-aiden` (branch `aiden`).
Do not commit, push or switch branches. Do not edit `app/`, `README.md`, the notebook, `data/`, or `forecast_tomorrow.py`.

## What the app is now (commit e005d8a)
- `python app/app.py` starts a small FastAPI server. It serves one hand-built page (`app/index.html`: plain HTML, CSS and JavaScript, GSAP for motion, no React) and JSON from the unchanged logic functions in `app/app.py`.
  A copy is running at **http://localhost:7863** for captures. Do not stop it. Read `app/index.html` for the exact on-screen words and for deep links (hash routes) you can use in captures.
- Three views, switched in the top bar. The city picker is in the top-right corner and the choice is remembered. Only the selected city is on screen.
  1. **Tomorrow** (live): the real forecast for the next practice day, refreshed by the app itself each evening from live data
     (AirNow hourly readings, NOAA's NAQFC forecast, NOAA HMS smoke maps, Open-Meteo CAMS and weather). Shows only: city and practice day,
     "OK to practice OUTSIDE" or "Move practice INDOORS", "Smoke forecast X", "Indoors above 32", "Forecast made Saturday at …". Status is one or two words ("Updating…", "Couldn't update.").
     Today every city is clean (Minneapolis 8.9), so this view shows "OUTSIDE" on a clear dusk-blue sky.
  2. **2025 test run**: any day of 2025 (date picker, previous/next buttons, left/right arrow keys; opens on Thursday, July 31, 2025).
     Same verdict, plus a "Was it right?" panel: measured that day, NOAA's forecast, the result (Right call / Missed a bad day / False alarm), and a scale against the line at 32.
  3. **Does it work?**: headline "26% lower error than NOAA's official forecast.", then "Its warnings cost 127. Reading NOAA at 35 cost 123. Lower is better.",
     the table (SmokeCheck; NOAA's official forecast; NOAA's official forecast, read at 35; Yesterday's reading), and "Weak spot: it misses the day smoke first arrives (warned on 0 of 21 in 2025)."
- The design idea: the whole backdrop is the sky over a practice field, and its colour follows the forecast (clear dusk blue when clean, orange-brown haze and a red sun on a smoke day).
- Gone since the old docs were written: Gradio, Plotly, the slider, the "Where it fails" tab, the six-city map, the 80% range, the baselines line, the long warning-line paragraph on the card, the "not 35" sentence.

## Numbers (unchanged; verify any number you write against `data/predictions.csv` and `data/metrics.json`)
- Demo days: Minneapolis Jul 31, 2025: SmokeCheck 41.3, NOAA 18.7, measured 69.1, indoors, right call. Chicago Jul 31: 15.3, NOAA 13.7, measured 65.6, outside, missed a bad day.
  Chicago Aug 1: 51.8, NOAA 8.7, measured 45.5, indoors, right call. Milwaukee Jul 31: 28.1, NOAA 13.4, measured 83.7, missed.
- Results (2025, 2,190 city-days, 35 bad days): SmokeCheck 2.36 / warns above 32 / 11 caught / 7 false alarms / cost 127. NOAA at its own line 3.20 / 52.5 / 2 / 1 / 166.
  NOAA at 35: 3.20 / 35 / 12 / 8 / 123. Persistence 3.40 / 37 / 12 / 19 / 134. Arrival days 0 of 21; lingering days 11 of 14.
- The one takeaway sentence, identical in the video, write-up and deck:
  "SmokeCheck's forecast is 26% more accurate than NOAA's official one, in every resample and every city. But its move-indoors warnings were slightly worse than just reading NOAA at 35, and it missed every day smoke first arrived."
- Live mode facts (source: the repo `README.md` and the notebook's section 10 "Live mode"; read them, do not guess): AirNow readings are preliminary;
  the 2 to 7 PM window is complete about 8 PM Central; run earlier, the forecast uses the day's readings so far.

## Decisions
- The **80% range is cut** from the write-up and deck (the app no longer shows it). Do not describe it as a feature.
- New things to cite wherever sources are listed: AirNow (EPA) hourly data, FastAPI and uvicorn, GSAP, Google Fonts (Big Shoulders Display, Schibsted Grotesk),
  and React Bits (reactbits.dev: the BlurText, SpotlightCard and Aurora effects, rebuilt in plain JavaScript). Gradio and Plotly are no longer used: remove them.

## Writing rules
- Plain words a high-schooler would say. Short sentences. No em dashes. No filler words ("seamless", "powerful", "leverage", "robust", "delve").
- Honest: never soften the weak results. Never say "beat NOAA" without the warnings caveat.
- Every number spoken or written must match the data files.
