# SmokeCheck: practice outside, or move indoors?

<!-- Numbers from data/metrics.json and data/predictions.csv (main after the app redesign (e005d8a), Nov 14; scikit-learn 1.9.1), all recomputed from predictions.csv. Re-check against the final files before submitting.
     Target: about one page (~650 words). Lines marked FORM are reused word for word on the submission form.
     FORM, team details: Abhiddyu Chandiwal and Aiden Patel. School and emails are typed on the form by us, not stored here.
     One-sentence pitch (FORM): SmokeCheck helps a Midwest high-school athletic director who has to decide whether tomorrow's practice is safe outdoors on a wildfire-smoke day by taking their city and tomorrow's date and telling them "practice outside" or "move indoors", with the PM2.5 forecast behind the call. -->

**Track:** AI + Climate · **Team:** Abhiddyu Chandiwal and Aiden Patel · *A prototype, not medical or health advice.*

## The problem
An athletic director decides the evening before whether practice stays outside. On July 31, 2025, Minneapolis's air reached 69.1 µg/m³ of fine particles (PM2.5), almost twice the EPA's 24-hour limit of 35. NOAA's official forecast the day before said 18.7.

## What we built
SmokeCheck gives an athletic director two things: tonight's real call for tomorrow's practice in their city (a live forecast the app refreshes by itself each evening), and a replay of every 2025 day showing whether each call was right: *Minneapolis, July 31, 2025 → **Move practice indoors** (forecast 41.3, above SmokeCheck's warning line of 32; measured 69.1).*

## What we added
<!-- FORM: the paragraph below is reused word for word as the form's "What we added" answer. -->
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting from one station's history, we combine this city's EPA monitors (including its afternoon reading), 19 other Midwest metros, NOAA's own forecast, NOAA satellite smoke maps, the CAMS model estimate and the day-ahead weather forecast. We judge it on the athletic director's decision, missed smoke days versus false alarms, against NOAA's official day-ahead forecast.

## How it works
- **Data:** daily EPA PM2.5 for Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis (7,476 city-days). Train Aug 2022 – Dec 2024; test all of 2025, never shuffled. **Open-Meteo air-quality values (CAMS) are model estimates, not measurements.**
- **Model:** the average of a Ridge regression (predicts tomorrow's PM2.5) and gradient-boosted trees (predict the change from today). Every input is known by about 8 PM (the latest is the 2–7 PM reading).
- **Warning lines:** a missed bad day (above 35) counts as 5 false alarms. Each forecast's line is the middle of the cheapest lines over 200 resampled copies of 2022–2024, a rule fixed beforehand. SmokeCheck's is 32; other random seeds give about 27 to 32.
- **Live mode:** the same frozen model on live data. AirNow readings are preliminary (35 of 36 checked city-days within 1.5 µg/m³ of EPA's archive). The 2–7 PM reading is complete about 8 PM Central; earlier, it uses the day's readings so far. Not yet scored.

## Results (2025, 35 bad city-days)

| Forecast | Avg error (µg/m³) | Warns above | Caught | False alarms | Cost (5 per miss + 1 per false alarm) |
|---|---|---|---|---|---|
| **SmokeCheck** | **2.36** | 32 | 11 | 7 | 127 |
| SmokeCheck before its last 3 inputs | 2.58 | 24.5 | 18 | 21 | 106 |
| NOAA day-ahead (NAQFC) | 3.20 | 52.5 | 2 | 1 | 166 |
| NOAA at the plain 35 line | 3.20 | 35 | 12 | 8 | 123 |
| Persistence (tomorrow = today) | 3.40 | 37 | 12 | 19 | 134 |
| Raw CAMS (optimistic*) | 3.72 | 30 | 17 | 17 | 107 |

**Takeaway:** SmokeCheck's forecast is clearly more accurate than NOAA's official one: 26% lower error (2.36 vs 3.20), better in every city and in all 1,000 resamples of 2025's weeks (gap 0.83, 95% range 0.55–1.17). But its move-indoors warnings, at the line the training years gave it, were worse than reading NOAA at 35 (cost 127 vs 123; ahead in only 42% of resamples), and it caught none of the 21 days when smoke first arrived. With one big smoke event in training, the warning line can't be set reliably (27 would have cost 117). *Raw CAMS's archive partly "sees" the day's smoke.

**Where it fails.** When smoke *arrives* it caught 0 of 21: on July 31 it said 15.3 for Chicago (measured 65.6) and 28.1 for Milwaukee (measured 83.7), below its line. When it *lingers* it caught 11 of 14: next day in Chicago it said 51.8, NOAA 8.7 (measured 45.5).

**Tried and dropped:** trees predicting the PM2.5 level (1 of 38 bad training days caught), smoke mapped 300–900 km upwind (no change in error), and adding 2018–2022 (higher training-year warning cost). We kept our last three inputs by a rule written beforehand on the training years' error and warning cost (error 2.49 → 2.22, cost 117 → 112). On 2025 error improved and warnings got worse.

**Honesty notes:** the notebook's section 10 lists all 8 times we looked at 2025 before the final numbers, such as choosing the cities and making NOAA the main comparison after scoring our model.

## What we'd do next
Set the warning line on more smoke events by adding smoky cities such as Duluth, then test SmokeCheck with a real athletic director.

## Sources
- **Data:** [EPA AirData daily and hourly PM2.5](https://aqs.epa.gov/aqsweb/airdata/download_files.html) · [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/) · [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (Copernicus Atmosphere Monitoring Service) · Open-Meteo [Historical Forecast](https://open-meteo.com/en/docs/historical-forecast-api) and [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) · [NOAA HMS smoke polygons](https://www.ospo.noaa.gov/products/land/hms.html) · [AirNow](https://files.airnowtech.org/) (live mode)
- **Libraries:** scikit-learn 1.9.1, pandas, NumPy, matplotlib, pyshp, eccodes, jupytext, FastAPI, uvicorn, GSAP, Google Fonts (Big Shoulders Display, Schibsted Grotesk), [React Bits](https://reactbits.dev) (BlurText, SpotlightCard and Aurora effects, rebuilt in plain JavaScript)
- **AI tools:** Claude (Anthropic), through Claude Code. It wrote most of the code (the data scripts, the model and evaluation notebook, and the web app, designed from mockups we chose between) and ran the experiments. Before the event it researched datasets and project ideas; during it, it checked which forecast archives were truly day-ahead and drafted this write-up and the video script, which we edited. We chose the track and project, picked which improvements to try from the options it proposed (an upwind-smoke feature, which we dropped, and the NOAA baseline), and read through all the code so we can explain it.
