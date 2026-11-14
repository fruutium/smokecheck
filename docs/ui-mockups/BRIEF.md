# SmokeCheck UI mockups: shared brief

## What SmokeCheck is
A next-day wildfire-smoke forecast for six Midwest cities (Chicago, Milwaukee, Madison, Minneapolis, Detroit, St. Louis).
The user is a high-school athletic director who decides the evening before whether tomorrow's practice stays outside.
The app turns a city and a day into one call: **"OK to practice outside"** or **"Move practice indoors"**.
It is a hackathon project judged by AI researchers on a livestream. The current Gradio UI looks generic and quickly made.
The team wants a full visual overhaul that looks designed by a person with taste.

## Decisions already made (do not reopen)
- **Look: "weather broadcast"**: dark, atmospheric, one huge verdict, like a TV weather desk. Your variant (in your task prompt) says which take on it.
- **Stack: one self-contained HTML file.** Plain HTML, CSS and JavaScript. No React, no build step, no npm install in the repo.
  GSAP may be loaded from cdnjs (`https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js`). Fonts from Google Fonts are fine.
- **Motion: purposeful.** The verdict reveals, numbers count up, changing city or day transitions smoothly. Nothing moves unless it helps read the call. Respect `prefers-reduced-motion`.

## Screens to mock (one file, three views with a working switch between them)
1. **Tomorrow** (the main screen, a live forecast). City picker, tomorrow's date, the verdict, "Smoke forecast 41.3 · indoors above 32",
   NOAA's official forecast for comparison, all six cities at a glance (a map or a strip), and a small "inputs as of 8 PM" freshness note.
   Live data does not exist yet, so use the Minneapolis July 31, 2025 values as if they were tomorrow.
2. **2025 replay** (how the calls went on a year the model never saw). City picker, day picker with previous/next day, the same verdict,
   then "Was it right?": measured that day, NOAA's forecast, and one of ✓ Right call / ✗ Missed a bad day / ✗ False alarm.
3. **Does it work?** One results table and the weak-spot line.

## Real data (use these exact numbers)
PM2.5 in µg/m³, daily average. A "bad day" is measured above 35 (the EPA 24-hour limit). SmokeCheck warns when its forecast is above **32**.

Demo days (the replay must step through these correctly):
| City | Day | SmokeCheck | NOAA | Measured | Call | Was it right? |
|---|---|---|---|---|---|---|
| Minneapolis | Thu Jul 31, 2025 | 41.3 | 18.7 | 69.1 | Move indoors | ✓ Right call |
| Chicago | Thu Jul 31, 2025 | 15.3 | 13.7 | 65.6 | Practice outside | ✗ Missed a bad day |
| Chicago | Fri Aug 1, 2025 | 51.8 | 8.7 | 45.5 | Move indoors | ✓ Right call |
| Milwaukee | Thu Jul 31, 2025 | 28.1 | 13.4 | 83.7 | Practice outside | ✗ Missed a bad day |

For other cities and nearby days, read real rows from
`/Users/abhiddyu/Downloads/ecs/veritas hackathon/smokecheck-aiden/data/predictions.csv`
(columns `date, city, lat, lon, obs_pm25, pred_noaa, pred_model, split`; use rows with `split == test`, 2025).
Embed roughly Jul 28 to Aug 4, 2025 for all six cities as a small JSON object inside the HTML. Do not invent values.

"Does it work?" table (2025, 2,190 city-days, 35 bad days; cost = 5 per missed bad day + 1 per false alarm, lower is better):
| Forecast | Avg error | Warns above | Caught | False alarms | Cost |
|---|---|---|---|---|---|
| SmokeCheck | 2.36 | 32 | 11 of 35 | 7 | 127 |
| NOAA official, its own line | 3.20 | 52.5 | 2 of 35 | 1 | 166 |
| NOAA official, at 35 | 3.20 | 35 | 12 of 35 | 8 | 123 |
| Yesterday's reading | 3.40 | 37 | 12 of 35 | 19 | 134 |

Weak spot: "SmokeCheck caught 0 of the 21 days when smoke first arrived. It catches smoke that lingers (11 of 14)."
The honest headline: 26% lower error than NOAA's official forecast, but its warnings were slightly worse than reading NOAA at 35 (127 vs 123).
This honesty is a selling point. Do not hide it or dress it up.

## Hard requirements
- Must look right at **1280×800** (the video is recorded at that size) and at phone width (375 px, no horizontal scroll).
- The verdict and the three key numbers must be readable from the back of a room: huge type, strong contrast (WCAG AA at least).
- Red/green must not be the only signal for the verdict: pair colour with words and an icon or shape.
- Working interactions in the mockup: switch view, switch city, previous/next day in the replay, with the transitions playing.
- Copy rules: plain words a high-schooler would say. No em dashes. No marketing filler ("seamless", "powerful", "elevate", "unlock").
  Include a small "A prototype, not medical or health advice." line.
- Avoid the usual AI-made tells: purple gradients, glassmorphism cards everywhere, emoji as icons, generic Inter-on-white, evenly sized card grids, centered everything.
- Keep the code readable: the team has to explain it to judges. Comment only the non-obvious parts.

## Skills to load before designing (use the Skill tool)
`frontend-design:frontend-design`, `ui-ux-pro-max`, `design-taste-frontend`, `impeccable`, `gsap-core`, `gsap-timeline`, `transitions-dev`.
Also `react-bits` for effect ideas only: rebuild any effect you like in plain JS/CSS, do not add React.
`extract-design` (designlang) is optional: only if you want to pull tokens from one real reference site, and skip it if it takes more than a couple of minutes.

## Deliverable
- Write **only** your one HTML file in `/Users/abhiddyu/Downloads/ecs/veritas hackathon/smokecheck-aiden/docs/ui-mockups/` (file name in your task prompt).
  Do not edit anything else in the repo, do not touch `app/`, do not commit.
- Check your own work: render it with headless Chrome at 1280×800 and at 375×812, look at the screenshots, and fix what looks wrong.
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=1280,800 --virtual-time-budget=6000 --screenshot=<out.png> file://<path>`
  Save a final 1280×800 screenshot of the Tomorrow view next to the HTML as `<same name>.png`. Put other scratch files in `/tmp`-style scratch space, not the repo.
- Final reply, at most 8 lines: file paths, the design idea in one sentence, fonts and palette, the motion you built, and anything unfinished or unchecked.

## Update from the hub (live screen spec, branch `app-live`)
- View names: **"Tomorrow"**, **"2025 test run"** (not "2025 replay"), **"Does it work?"**.
- Tomorrow has no "Was it right?" strip. Under the verdict: "Forecast made Saturday at 7:12 PM from that evening's readings."
- Tomorrow has four states: `ok` (the verdict), `waiting` (grey: "No forecast yet" / "Waiting on: {status}"),
  `out_of_date` (grey: "The last forecast was for {date}. It runs again this evening.", map hidden), `none` (grey: "The forecast runs each evening.", map hidden).
- For the build, data comes from plain functions in app/app.py: `live_view`, `replay_view`, `map_points`, `scoreboard`, `arrival_note`, and `plain(view)` for JSON-safe values.
  Live data file: `data/tomorrow.csv` (target_date, made_at, city, lat, lon, pred_model, pred_noaa, obs_today, hours_today, status, warn_at).

## Update 2 from the hub (live mode committed on `app-live` 12d143f, not merged yet)
- Live inputs and timing (for the write-up's "known by about 8 PM"): AirNow hourly (preliminary; 2-7 PM window complete about 8 PM CT;
  35 of 36 checked city-days within 1.5 of EPA's archive, exception Minneapolis Jul 30 at +3.3); NAQFC 12Z run (about noon CT);
  HMS smoke (today's file, updated through the day); Open-Meteo CAMS and tomorrow's weather.
- Fallbacks: `status` per city says what is partial; no AirNow readings means state "waiting"; no NOAA run means today's reading is used.
- Today's real file (for Sunday Nov 15, 2026): every city OK, forecasts 3.8 to 8.9. So the live screen will usually show a clean, "practice outside" day:
  the design has to look good when nothing is wrong, not only on smoke days.

## Update 3 from the hub (auto-refresh on `app-auto` 137c44b, not on main yet)
- `import refresh` (app/refresh.py). On page open: `refresh.refresh_if_stale(load_tomorrow())` (starts a background run, returns at once, True while running).
- Poll every ~3 s: `refresh.status()` gives `{"refreshing": bool, "failed": bool}`. When refreshing turns False, re-read `live_view(...)` for each city.
- While refreshing: keep the last forecast if state is "ok", plus "Getting the latest readings… about a minute". If state is "none", only the waiting card. A run takes 15 to 60 s.
- Failed: keep the last forecast plus "Couldn't reach the data sources just now; it tries again in a few minutes"; with no forecast, the grey card with that line.
- Partial inputs (state "ok", status not "ok"): "Some of today's readings weren't in yet; it updates itself as they come in."
- `data/tomorrow.csv` is git-ignored (the app makes it). requirements add scikit-learn==1.9.1, pyshp==3.1.8, eccodes==2.50.1.

## Update 4: Abhiddyu's copy rule (overrides the longer lines in updates 1 to 3)
- No explaining or justifying on screen. The live card shows only: city and practice day, the call, "Smoke forecast X · indoors above 32", "Forecast made Saturday at 12:28 PM".
- Loading and error states are one or two words: "Updating…" and "Couldn't update."
- No partial-readings note. Fallback details stay in the `status` field, never on the page.
