# SmokeCheck: practice outside, or move indoors?

<!-- Numbers from data/metrics.json and data/predictions.csv (main, Nov 14), with scikit-learn 1.9.1. Re-check every number against the final files before submitting.
     Target: about one page (~650 words). Lines marked FORM are reused word for word on the submission form.
     FORM, team details: Abhiddyu Chandiwal and Aiden Patel, both Jordan High School. Emails are typed on the form by us, not stored here.
     One-sentence pitch (FORM): SmokeCheck helps a Midwest high-school athletic director who has to decide whether tomorrow's practice is safe outdoors on a wildfire-smoke day by taking their city and tomorrow's date and telling them "practice outside" or "move indoors", with the PM2.5 forecast behind the call. -->

**Track:** AI + Climate · **Team:** Abhiddyu Chandiwal and Aiden Patel · *A prototype, not medical or health advice.*

## The problem
An athletic director decides the evening before whether practice stays outside. On July 31, 2025, Milwaukee's air reached 83.7 µg/m³ of fine particles (PM2.5), over twice the EPA's 24-hour limit of 35. NOAA's official forecast the day before said 13.4.

## What we built
SmokeCheck takes a city and a date and returns tomorrow's PM2.5 forecast and a call: *Milwaukee, July 31, 2025 → **Move practice indoors** (forecast 27.6, above SmokeCheck's warning line of 24; measured 83.7).* It runs in our Colab notebook and an optional Gradio app.

## What we added (FORM)
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting from one station's history, we combine this city's EPA monitors, five other Midwest cities, NOAA satellite smoke maps, the CAMS model estimate and the day-ahead weather forecast. We judge it on the athletic director's decision, missed smoke days versus false alarms, against NOAA's official day-ahead forecast.

## How it works
- **Data:** daily EPA PM2.5 for Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis (7,476 city-days). Train Aug 2022 – Dec 2024; test all of 2025, never shuffled. **Open-Meteo air-quality values (CAMS) are model estimates, not measurements.**
- **Model:** the average of a Ridge regression (predicts tomorrow's PM2.5) and gradient-boosted trees (predict the change from today, since trees can't predict above values they've seen).
- **Warning lines:** we count one missed bad day (above 35) as costly as 5 false alarms. Each forecast's line is chosen on 2022–2024 to minimise that cost. SmokeCheck's is 24 because it runs low on smoke days.

## Results (2025, 35 bad city-days)

| Forecast | Average error (µg/m³) | Warns above | Caught | False alarms | Cost (5 × misses + false alarms) |
|---|---|---|---|---|---|
| **SmokeCheck** | **2.59** | 24 | 18 | 22 | **107** |
| NOAA day-ahead (NAQFC) | 3.20 | 45 | 6 | 1 | 146 |
| NOAA at the plain 35 line | 3.20 | 35 | 12 | 8 | 123 |
| Persistence (tomorrow = today) | 3.40 | 37 | 12 | 19 | 134 |
| Raw CAMS (optimistic*) | 3.72 | 29.5 | 18 | 21 | 106 |

**Takeaway:** compared with the forecast an athletic director could really have looked up, SmokeCheck's error is 19% lower, and its decisions cost 107 against NOAA's 123 at the plain 35 line. Even NOAA's best possible line, picked with hindsight on 2025, costs 118. *Raw CAMS scores slightly better (106), but Open-Meteo keeps no true day-ahead CAMS archive, so its value already partly "sees" the day's smoke.

**Where it fails.** When smoke *arrives* overnight, SmokeCheck caught only 6 of 21 days (NOAA 4). On July 31 in Chicago it said 13.9 and NOAA 13.7, and the air measured 65.6. Our model leans on today's readings, which are still clean. When smoke *lingers*, it caught 12 of 14 (NOAA 2). On August 1 in Chicago, NOAA said 8.7, SmokeCheck 54.8, and the air measured 45.5.

**Tried and dropped:** trees predicting the PM2.5 level caught 1 of 38 bad training days. Smoke mapped 300–900 km upwind preceded 16 of 21 training arrival days, but didn't lower the error (2.49 either way). Our guess: without 2023 there are only 2 bad training days to learn from.

**Honesty notes:** we saw the baselines' 2025 numbers at a plain 35 line, and one early scratch run scored model variants on 2025, before we fixed the 5:1 rule and moved every choice to 2022–2024. We picked the six cities knowing their smoky-day counts, 2025 included. With 35 bad days, catch counts are noisy; the average error is steadier.

## What we'd do next
- Train on more smoke seasons (2018–2021) so the model can learn from the upwind smoke signal.
- Forecast practice hours (3–6 PM) and test it with a real athletic director.

## Sources
- **Data:** [EPA AirData daily PM2.5](https://aqs.epa.gov/aqsweb/airdata/download_files.html) · [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/) · [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (Copernicus Atmosphere Monitoring Service) · Open-Meteo [Historical Forecast](https://open-meteo.com/en/docs/historical-forecast-api) and [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) APIs · [NOAA HMS smoke polygons](https://www.ospo.noaa.gov/products/land/hms.html)
- **Libraries:** scikit-learn, pandas, NumPy, matplotlib, pyshp, eccodes, jupytext, Gradio, Plotly · **Starting point:** Veritas AI suggested project 4.3.2
- **AI tools:** Claude (Anthropic), through Claude Code. It wrote most of the code (the data scripts, the model and evaluation notebook, and the Gradio app) and ran the experiments. Before the event it researched datasets and project ideas; during it, it checked which forecast archives were truly day-ahead and drafted this write-up and the video script, which we edited. We chose the track and project, picked which improvements to try from the options it proposed (an upwind-smoke feature, which we dropped, and the NOAA baseline), and read through all the code so we can explain it.
