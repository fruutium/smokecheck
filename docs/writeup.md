# SmokeCheck: practice outside, or move indoors?

<!-- Numbers from data/metrics.json and data/predictions.csv (main 1fc892f, Nov 14; scikit-learn 1.9.1), all recomputed from predictions.csv. Re-check against the final files before submitting.
     Target: about one page (~650 words). Lines marked FORM are reused word for word on the submission form.
     FORM, team details: Abhiddyu Chandiwal and Aiden Patel, both Jordan High School. Emails are typed on the form by us, not stored here.
     One-sentence pitch (FORM): SmokeCheck helps a Midwest high-school athletic director who has to decide whether tomorrow's practice is safe outdoors on a wildfire-smoke day by taking their city and tomorrow's date and telling them "practice outside" or "move indoors", with the PM2.5 forecast behind the call. -->

**Track:** AI + Climate · **Team:** Abhiddyu Chandiwal and Aiden Patel · *A prototype, not medical or health advice.*

## The problem
An athletic director decides the evening before whether practice stays outside. On July 31, 2025, Milwaukee's air reached 83.7 µg/m³ of fine particles (PM2.5), over twice the EPA's 24-hour limit of 35. NOAA's official forecast the day before said 13.4.

## What we built
SmokeCheck returns tomorrow's PM2.5 forecast for a city, an 80% likely range, and a call: *Milwaukee, July 31, 2025 → **Move practice indoors** (forecast 26.8, above SmokeCheck's warning line of 24.5; measured 83.7).* It runs in our Colab notebook and an optional Gradio app.

## What we added (FORM)
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting from one station's history, we combine this city's EPA monitors, five other Midwest cities, NOAA satellite smoke maps, the CAMS model estimate and the day-ahead weather forecast. We judge it on the athletic director's decision, missed smoke days versus false alarms, against NOAA's official day-ahead forecast.

## How it works
- **Data:** daily EPA PM2.5 for Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis (7,476 city-days). Train Aug 2022 – Dec 2024; test all of 2025, never shuffled. **Open-Meteo air-quality values (CAMS) are model estimates, not measurements.**
- **Model:** the average of a Ridge regression (predicts tomorrow's PM2.5) and gradient-boosted trees (predict the change from today, since trees can't predict above values they've seen).
- **Warning lines:** a missed bad day (above 35) counts as 5 false alarms. Each forecast's line is the median best line over 200 resampled copies of 2022–2024 (whole weeks drawn at random). SmokeCheck's is 24.5 because it runs low on smoke days.

## Results (2025, 35 bad city-days)

| Forecast | Average error (µg/m³) | Warns above | Caught | False alarms | Cost (5 × misses + false alarms) |
|---|---|---|---|---|---|
| **SmokeCheck** | **2.58** | 24.5 | 18 | 21 | **106** |
| NOAA day-ahead (NAQFC) | 3.20 | 52.5 | 2 | 1 | 166 |
| NOAA at the plain 35 line | 3.20 | 35 | 12 | 8 | 123 |
| Persistence (tomorrow = today) | 3.40 | 37 | 12 | 19 | 134 |
| Raw CAMS (optimistic*) | 3.72 | 30 | 17 | 17 | 107 |

**Takeaway:** SmokeCheck's average error is 19% lower than NOAA's official forecast (2.58 vs 3.20). Its warnings cost 106 against NOAA's 123 at the plain 35 line. With the best line picked in hindsight for everyone, SmokeCheck costs 102, NOAA 118 and persistence 106, so on warnings we clearly beat NOAA but only tie "tomorrow = today". *Raw CAMS does best in hindsight (100), but Open-Meteo keeps no true day-ahead CAMS archive, so its value partly "sees" the day's smoke.

**Where it fails.** When smoke *arrives* overnight, SmokeCheck caught only 6 of 21 days. On July 31 in Chicago it said 13.7 (likely range 8.8–20.6), NOAA said 13.7, and the air measured 65.6. Our model leans on today's readings, which are still clean, and its range held the real value on 79.6% of 2025 days but only 37% of bad days. When smoke *lingers*, it caught 12 of 14: on August 1 in Chicago, NOAA said 8.7, SmokeCheck 54.0, and the air measured 45.5.

**Tried and dropped:** trees predicting the PM2.5 level (1 of 38 bad training days caught); smoke mapped 300–900 km upwind (no change in error); and training on 2018–2022 too, which lowered the error on training years but raised the warning cost, since those years add only 3 smoke days.

**Honesty notes:** before fixing our process we saw some 2025 results: the baselines at a plain 35 line, one scratch run of model variants, and our first warning rule (the single cheapest line on training) at both 24 and 29.5, after a 0.005 µg/m³ rounding change made it jump. We wrote the resampled rule down before computing it. The range tried 4 layouts on 2025 (all 80–81%). We picked the cities knowing their smoky-day counts, 2025 included.

## What we'd do next
- Add more cities that get smoke (for example Duluth), since more years added only 3 smoke days.
- Forecast practice hours (3–6 PM) and test it with a real athletic director.

## Sources
- **Data:** [EPA AirData daily PM2.5](https://aqs.epa.gov/aqsweb/airdata/download_files.html) · [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/) · [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (Copernicus Atmosphere Monitoring Service) · Open-Meteo [Historical Forecast](https://open-meteo.com/en/docs/historical-forecast-api) and [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) APIs · [NOAA HMS smoke polygons](https://www.ospo.noaa.gov/products/land/hms.html)
- **Libraries:** scikit-learn 1.9.1, pandas, NumPy, matplotlib, pyshp, eccodes, jupytext, Gradio, Plotly · **Starting point:** Veritas AI suggested project 4.3.2
- **AI tools:** Claude (Anthropic), through Claude Code. It wrote most of the code (the data scripts, the model and evaluation notebook, and the Gradio app) and ran the experiments. Before the event it researched datasets and project ideas; during it, it checked which forecast archives were truly day-ahead and drafted this write-up and the video script, which we edited. We chose the track and project, picked which improvements to try from the options it proposed (an upwind-smoke feature, which we dropped, and the NOAA baseline), and read through all the code so we can explain it.
