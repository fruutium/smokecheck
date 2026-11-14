# SmokeCheck: practice outside, or move indoors?

<!-- Numbers from data/metrics.json and data/predictions.csv (main 1fc892f, Nov 14; scikit-learn 1.9.1), all recomputed from predictions.csv. Re-check against the final files before submitting.
     Target: about one page (~650 words). Lines marked FORM are reused word for word on the submission form.
     FORM, team details: Abhiddyu Chandiwal and Aiden Patel. School and emails are typed on the form by us, not stored here.
     One-sentence pitch (FORM): SmokeCheck helps a Midwest high-school athletic director who has to decide whether tomorrow's practice is safe outdoors on a wildfire-smoke day by taking their city and tomorrow's date and telling them "practice outside" or "move indoors", with the PM2.5 forecast behind the call. -->

**Track:** AI + Climate · **Team:** Abhiddyu Chandiwal and Aiden Patel · *A prototype, not medical or health advice.*

## The problem
An athletic director decides the evening before whether practice stays outside. On July 31, 2025, Milwaukee's air reached 83.7 µg/m³ of fine particles (PM2.5), over twice the EPA's 24-hour limit of 35. NOAA's official forecast the day before said 13.4.

## What we built
SmokeCheck returns tomorrow's PM2.5 forecast for a city, an 80% likely range, and a call: *Milwaukee, July 31, 2025 → **Move practice indoors** (forecast 26.8, above SmokeCheck's warning line of 24.5; measured 83.7).*

## What we added
<!-- FORM: the paragraph below is reused word for word as the form's "What we added" answer. -->
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting from one station's history, we combine this city's EPA monitors, five other Midwest cities, NOAA satellite smoke maps, the CAMS model estimate and the day-ahead weather forecast. We judge it on the athletic director's decision, missed smoke days versus false alarms, against NOAA's official day-ahead forecast.

## How it works
- **Data:** daily EPA PM2.5 for Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis (7,476 city-days). Train Aug 2022 – Dec 2024; test all of 2025, never shuffled. **Open-Meteo air-quality values (CAMS) are model estimates, not measurements.**
- **Model:** the average of a Ridge regression (predicts tomorrow's PM2.5) and gradient-boosted trees (predict the change from today).
- **Warning lines:** a missed bad day (above 35) counts as 5 false alarms. Each forecast's line is the middle of the cheapest lines over 200 resampled copies of 2022–2024, a rule we fixed before computing it. SmokeCheck's is 24.5, but those years can't pin it down: other random seeds put it anywhere from about 24 to 29.

## Results (2025, 35 bad city-days)

| Forecast | Avg error (µg/m³) | Warns above | Caught | False alarms | Cost (5 per miss + 1 per false alarm) |
|---|---|---|---|---|---|
| **SmokeCheck** | **2.58** | 24.5 | 18 | 21 | **106** |
| NOAA day-ahead (NAQFC) | 3.20 | 52.5 | 2 | 1 | 166 |
| NOAA at the plain 35 line | 3.20 | 35 | 12 | 8 | 123 |
| Persistence (tomorrow = today) | 3.40 | 37 | 12 | 19 | 134 |
| Raw CAMS (optimistic*) | 3.72 | 30 | 17 | 17 | 107 |

**How sure are we?** Resampling 2025's weeks 1,000 times, SmokeCheck's average error beats NOAA's by 0.60 µg/m³ (95% range 0.27–0.98) and persistence's by 0.82, in every resample. On the move-indoors call it is roughly even with NOAA (ahead in 60% of resamples) and ahead of persistence in 94%. *Raw CAMS is optimistic: its archive isn't a true day-ahead forecast and partly "sees" the day's smoke.

**Where it fails.** When smoke *arrives* overnight, SmokeCheck caught only 6 of 21 days, and all 6 were already hazy the day before (19–34 µg/m³). It doesn't catch a jump from clean to smoky: on July 31 in Chicago it said 13.7, NOAA 13.7, and the air measured 65.6. Its 80% range held the real value on 79.6% of days but only 37% of bad days. When smoke *lingers*, it caught 12 of 14.

**Tried and dropped:** trees predicting the PM2.5 level (1 of 38 bad training days caught); smoke mapped 300–900 km upwind (no change in error); and adding 2018–2022 (lower error but higher warning cost on training years, so never scored on 2025).

**Honesty notes:** we looked at 2025 seven times before the final numbers (listed in the notebook's section 10): a scratch run of model variants; the baselines at a plain 35 line; our model at two old cut-offs (24 and 29.5); a few groupings of the range; choosing the cities; making NOAA the main comparison after scoring our model; and pinning scikit-learn after older versions gave 17 caught instead of 18.

## What we'd do next
Add more cities that get smoke, such as Duluth (more years added only 3 bad smoke days). Forecast practice hours (3–6 PM) and test SmokeCheck with a real athletic director.

## Sources
- **Data:** [EPA AirData daily PM2.5](https://aqs.epa.gov/aqsweb/airdata/download_files.html) · [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/) · [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (Copernicus Atmosphere Monitoring Service) · Open-Meteo [Historical Forecast](https://open-meteo.com/en/docs/historical-forecast-api) and [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) · [NOAA HMS smoke polygons](https://www.ospo.noaa.gov/products/land/hms.html)
- **Libraries:** scikit-learn 1.9.1, pandas, NumPy, matplotlib, pyshp, eccodes, jupytext, Gradio, Plotly · **Starting point:** Veritas AI suggested project 4.3.2
- **AI tools:** Claude (Anthropic), through Claude Code. It wrote most of the code (the data scripts, the model and evaluation notebook, and the Gradio app) and ran the experiments. Before the event it researched datasets and project ideas; during it, it checked which forecast archives were truly day-ahead and drafted this write-up and the video script, which we edited. We chose the track and project, picked which improvements to try from the options it proposed (an upwind-smoke feature, which we dropped, and the NOAA baseline), and read through all the code so we can explain it.
