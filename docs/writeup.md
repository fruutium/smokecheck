# SmokeCheck: practice outside, or move indoors?

<!-- Numbers from data/metrics.json and data/predictions.csv (main 65b1456, Nov 14). Re-check every number against the final files before submitting.
     [Brackets] = still to fill. Must fit ONE page when exported. Lines marked FORM are reused word for word on the submission form.
     FORM, team details: Abhiddyu Chandiwal and Aiden Patel, both Jordan High School. Emails are typed on the form by us, not stored here. -->

**Track:** AI + Climate · **Team:** Abhiddyu Chandiwal and Aiden Patel

*SmokeCheck is a prototype and is not medical or health advice.*

**One-sentence pitch (FORM):** SmokeCheck helps a Midwest high-school athletic director who has to decide whether tomorrow's practice is safe outdoors on a wildfire-smoke day by taking their city and tomorrow's date and telling them "practice outside" or "move indoors", with the PM2.5 forecast behind the call.

## The problem
When wildfire smoke drifts over the Midwest, an athletic director has to decide the day before whether practice stays outside. On July 31, 2025, smoke reached Chicago overnight: the day before measured 12.4 µg/m³ of fine particles (PM2.5), and that day measured 65.7, almost twice the EPA's 24-hour limit of 35.

## What we built
SmokeCheck takes a city and a date and returns tomorrow's average PM2.5 forecast and a call. For example:

> Milwaukee, July 31, 2025 → **Move practice indoors.** SmokeCheck forecast 27.6 µg/m³, above its warning line of 24. Monitors measured 83.7.

It runs in our Colab notebook, with an optional Gradio app: a map of six cities, a slider across 2025, and the call.

## What we added (FORM)
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting from one station's history, we combine this city's EPA monitors, the five other Midwest cities, NOAA satellite smoke maps, the CAMS model estimate and the day-ahead weather forecast. We built it for one decision, indoor or outdoor practice, and test it on that decision: how many 2025 days above 35 µg/m³ each forecast warns about, and how many false alarms it raises.

## How it works
- **Data:** daily PM2.5 from EPA monitors in Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis is what we predict (7,470 city-days). Open-Meteo provides the CAMS estimate and weather forecasts; NOAA's HMS maps mark smoke plumes. **Open-Meteo air-quality values are model estimates, not measurements.**
- **Split:** train Aug 2022 – Dec 2024, test all of 2025 (2,190 city-days). Days are never shuffled.
- **Model:** the average of a Ridge regression and a gradient-boosted tree model (scikit-learn), both predicting the change from today's PM2.5.
- **Warning line:** each forecast warns above its own cut-off, chosen on 2022–2024 so that one missed bad day costs as much as 5 false alarms. SmokeCheck's is 24 µg/m³, not 35, because its forecasts run low on smoke days.

## Results (2025, never used in training or tuning)

| Forecast | Average error (µg/m³) | Warns above | Bad days caught (of 35) | False alarms |
|---|---|---|---|---|
| Persistence (tomorrow = today) | 3.40 | 37 | 12 | 19 |
| Climatology (usual for that city and month) | 4.33 | 19.5 | 0 | 0 |
| Raw CAMS estimate | 3.72 | 29.5 | 18 | 21 |
| **SmokeCheck** | **2.59** | 24 | 18 | 22 |

**Takeaway:** SmokeCheck's number is the closest every day, on clean days (2.24 vs 3.02 for persistence) and smoke days (8.63 vs 9.86). On warnings it only ties CAMS. CAMS has an unfair edge: Open-Meteo keeps no true day-ahead CAMS archive, so the archived value for a day already partly "sees" that day's smoke.

**Where it fails.** When smoke *arrives* (yesterday was fine, today is bad), SmokeCheck caught 6 of 21 days and CAMS 11 of 21. On July 31 in Chicago, SmokeCheck forecast 13.9 while CAMS said 34.3 and warned. Our model leans on today's readings, and those are still clean the day before smoke arrives. When smoke *lingers*, SmokeCheck caught 12 of 14 and CAMS 7 of 14: on August 1, CAMS said 19.1 while SmokeCheck said 54.8 (measured 45.5).

**Tried and dropped:** a tree model predicting the PM2.5 level directly caught 1 of 38 bad training days, because trees can't predict above values they have seen.

**Honesty notes:** NOAA's plume labels miss some smoke (12 of the 35 bad days had a light plume or none). One early scratch run looked at 2025 before we fixed our process; every choice after that used 2022–2024 only. Swapping in the real weather instead of the forecast changes the error by 0.01, so weather isn't leaking the answer.

## What we'd do next
- Catch smoke before it arrives: add NOAA-mapped smoke upwind of each city, chosen on training years only.
- Forecast practice hours (3–6 PM) instead of the daily average, and test it with a real athletic director.

## Sources
- **Data:** [EPA AirData daily PM2.5 (parameter 88101)](https://aqs.epa.gov/aqsweb/airdata/download_files.html) · [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api), carrying Copernicus Atmosphere Monitoring Service (CAMS) global atmospheric composition forecasts · Open-Meteo [Historical Forecast API](https://open-meteo.com/en/docs/historical-forecast-api) (training weather) and [Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) (day-ahead weather for 2025) · [NOAA Hazard Mapping System smoke polygons](https://www.ospo.noaa.gov/products/land/hms.html)
- **Libraries:** scikit-learn (`Ridge`, `StandardScaler`, `HistGradientBoostingRegressor`), pandas, NumPy, matplotlib, pyshp, jupytext; Gradio and Plotly for the app
- **Starting point:** Veritas AI Project Briefs, suggested project 4.3.2
- **AI tools:** Claude (Claude Code), used for [say exactly what: writing data-loading, model and app code, which we read and can explain; pre-event dataset research; drafting this write-up]
