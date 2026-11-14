# SmokeCheck: practice outside, or move indoors?

<!-- Numbers from data/metrics.json and data/predictions.csv (main b6ac3e2, Nov 14). Re-check every number against the final files before submitting.
     [Brackets] = still to fill. Must fit ONE page when exported. Lines marked FORM are reused word for word on the submission form.
     FORM, team details: Abhiddyu Chandiwal and Aiden Patel, both Jordan High School. Emails are typed on the form by us, not stored here. -->

**Track:** AI + Climate · **Team:** Abhiddyu Chandiwal and Aiden Patel · *A prototype, not medical or health advice.*

**One-sentence pitch (FORM):** SmokeCheck helps a Midwest high-school athletic director who has to decide whether tomorrow's practice is safe outdoors on a wildfire-smoke day by taking their city and tomorrow's date and telling them "practice outside" or "move indoors", with the PM2.5 forecast behind the call.

## The problem
When wildfire smoke drifts over the Midwest, an athletic director decides the day before whether practice stays outside. On July 31, 2025, Milwaukee's air reached 83.7 µg/m³ of fine particles (PM2.5), more than twice the EPA's 24-hour limit of 35, and NOAA's official forecast the day before said 13.4.

## What we built
SmokeCheck takes a city and a date and returns tomorrow's PM2.5 forecast and a call: *Milwaukee, July 31, 2025 → **Move practice indoors** (forecast 27.6, above SmokeCheck's warning line of 24; measured 83.7).* It runs in our Colab notebook, with an optional Gradio app: a map of six cities, a slider across 2025, and each forecast's call side by side.

## What we added (FORM)
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting from one station's history, we combine this city's EPA monitors, the five other Midwest cities, NOAA satellite smoke maps, the CAMS model estimate and the day-ahead weather forecast. We test it on the athletic director's decision, how many 2025 days above 35 µg/m³ it warns about and at what cost in false alarms, against NOAA's official day-ahead forecast.

## How it works
- **Data:** daily PM2.5 from EPA monitors in Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis (7,476 city-days) is what we predict. Inputs come from Open-Meteo (CAMS estimate, weather forecasts) and NOAA's HMS smoke maps. **Open-Meteo air-quality values are model estimates, not measurements.**
- **Split:** train Aug 2022 – Dec 2024, test all of 2025 (2,190 city-days). Days are never shuffled.
- **Model:** the average of two scikit-learn models: a Ridge regression that predicts tomorrow's PM2.5, and a gradient-boosted tree model that predicts the change from today (trees can't predict above values they've seen, but a change added to today's reading can be large).
- **Warning lines:** each forecast warns above its own cut-off, chosen on 2022–2024 so one missed bad day costs as much as 5 false alarms. SmokeCheck's is 24, not 35, because its forecasts run low on smoke days.

## Results (2025, never used in training or tuning)

| Forecast | Average error (µg/m³) | Warns above | Bad days caught (of 35) | False alarms |
|---|---|---|---|---|
| **SmokeCheck** | **2.59** | 24 | **18** | 22 |
| NOAA day-ahead forecast (NAQFC) | 3.20 | 45* | 6 | 1 |
| Persistence (tomorrow = today) | 3.40 | 37 | 12 | 19 |
| Climatology (usual for that city and month) | 4.33 | 19.5 | 0 | 0 |
| Raw CAMS estimate (optimistic†) | 3.72 | 29.5 | 18 | 21 |

\*The highest line we allowed: NOAA's forecasts above 35 were mostly false alarms in training. †Open-Meteo keeps no true day-ahead CAMS archive, so the archived value already partly "sees" that day's smoke.

**Takeaway:** against the forecast an athletic director could really have looked up the day before, SmokeCheck's error is 19% lower and it warns on 3× as many bad days (18 vs 6). The price is more false alarms (22 vs 1).

**Where it fails.** When smoke *arrives* (yesterday clean, today bad), SmokeCheck caught only 6 of 21 days (NOAA 4, CAMS archive 11). On July 31 in Chicago, SmokeCheck said 13.9 and NOAA 13.7, and the air measured 65.7: our model leans on today's readings, which are still clean the day before smoke arrives. When smoke *lingers*, SmokeCheck caught 12 of 14 and NOAA 2. On August 1 in Chicago, NOAA said 8.7, SmokeCheck said 54.8, and the air measured 45.5.

**Tried and dropped:** a tree model predicting the PM2.5 level directly caught 1 of 38 bad training days, because trees can't predict above values they've seen. We also added NOAA-mapped smoke 300–900 km upwind of each city: it preceded 16 of 21 training arrival days, but the model's error didn't move (2.49 either way). Our guess: without 2023, the training years have only 2 bad days to learn from.

**Honesty notes:** one early scratch run looked at 2025 before we fixed our process; every choice since used 2022–2024 only. NOAA upgraded its model in May 2024, between our training and test years. Using the real weather instead of the forecast changes our error by only 0.01, so weather isn't leaking the answer. With 35 bad test days, catch counts are noisy; the average error is the steadier number.

## What we'd do next
- Train on more smoke seasons (2018–2021, from EPA and NOAA's forecast archive) so the model has enough smoke events to use the upwind signal we found.
- Forecast practice hours (3–6 PM) instead of the daily average, and test it with a real athletic director.

## Sources
- **Data:** [EPA AirData daily PM2.5 (88101)](https://aqs.epa.gov/aqsweb/airdata/download_files.html) · [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/) (bias-corrected, day-before 12Z run, nearest grid cell) · [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (Copernicus Atmosphere Monitoring Service global forecasts) · Open-Meteo [Historical Forecast](https://open-meteo.com/en/docs/historical-forecast-api) and [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) APIs · [NOAA HMS smoke polygons](https://www.ospo.noaa.gov/products/land/hms.html)
- **Libraries:** scikit-learn, pandas, NumPy, matplotlib, pyshp, eccodes, jupytext; Gradio and Plotly for the app
- **Starting point:** Veritas AI Project Briefs, suggested project 4.3.2
- **AI tools:** Claude (Anthropic), through Claude Code. It wrote most of the code (the data scripts, the model and evaluation notebook, and the Gradio app) and ran the experiments. Before the event it researched datasets and project ideas; during it, it checked which forecast archives were truly day-ahead and drafted this write-up and the video script, which we edited. We chose the track and project, picked which improvements to try from the options it proposed (an upwind-smoke feature, which we dropped, and the NOAA baseline), and read through all the code so we can explain it.
