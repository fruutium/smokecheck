# SmokeCheck

Next-day PM2.5 forecast for six Midwest metro areas, built to help a high-school athletic director decide
whether to hold practice outside or move it indoors on wildfire-smoke days.

Veritas AI International High School Hackathon 2026 · Track: AI + Climate · starting point: suggested project 4.3.2
(next-day air quality forecast). Work in progress: results and the write-up will be added here.

## Data split (locked in the first commit)

`data/daily.csv` has one row per city per day: Chicago, Milwaukee, Madison, Minneapolis, Detroit, St. Louis.

| Split | Dates | City-days | Days above 35 µg/m³ |
|---|---|---|---|
| Train | 2022-08-04 to 2024-12-31 | 5,286 | 38 |
| Test | 2025-01-01 to 2025-12-31 | 2,190 | 35 |

The split is by time and is never shuffled. The test year is only used for final scoring.

## Rebuild the data

```bash
pip install -r requirements.txt
python fetch_data.py
```

No API keys are needed.

## Data sources

- **Observed PM2.5:** US EPA AirData, daily summary files for PM2.5 FRM/FEM (parameter 88101),
  https://aqs.epa.gov/aqsweb/airdata/download_files.html. We average all monitors in each metro area.
- **CAMS model PM2.5:** Open-Meteo Air Quality API (CAMS global, about 45 km grid), https://open-meteo.com/en/docs/air-quality-api.
  These are model estimates, not measurements. The history is stitched from short-range model runs, so it is
  closer to the truth than a real day-ahead forecast would have been.
- **Weather:** Open-Meteo Historical Forecast API, https://open-meteo.com/en/docs/historical-forecast-api.
