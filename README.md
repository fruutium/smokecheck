# SmokeCheck

Tomorrow's PM2.5 (fine-particle pollution) for six Midwest metro areas, so a high-school athletic director can
decide the evening before whether practice moves indoors on a wildfire-smoke day.

Veritas AI International High School Hackathon 2026 · Track: AI + Climate · starting point: suggested project 4.3.2
(next-day air quality forecast). Write-up: [`docs/writeup.md`](docs/writeup.md).

## Run it

- **Notebook (the main deliverable):** open [`smokecheck.ipynb`](smokecheck.ipynb) in Google Colab and choose
  Runtime → Run all. It needs no API keys or uploads, finishes in under a minute, and reads the small files in
  `data/`. Its first cell installs scikit-learn 1.9.1, the version our numbers come from.
- **App:** `pip install -r app/requirements.txt`, then `python app/app.py` from the repo folder.

## Results on the held-out test year (2025, six cities, 35 days above 35 µg/m³)

| Forecast | Average error (µg/m³) | Warns above | Bad days caught | False alarms | Cost (5 × missed + false alarms) |
|---|---|---|---|---|---|
| **SmokeCheck** | **2.36** | 32 | 11 | 7 | 127 |
| SmokeCheck before its second model change | 2.58 | 24.5 | 18 | 21 | 106 |
| NOAA's official day-ahead forecast (NAQFC) | 3.20 | 52.5 | 2 | 1 | 166 |
| NOAA at the plain 35 line | 3.20 | 35 | 12 | 8 | 123 |
| Persistence ("tomorrow = today") | 3.40 | 37 | 12 | 19 | 134 |
| Climatology (city-month average) | 4.33 | 19.5 | 0 | 0 | 175 |
| Raw CAMS archive (optimistic: it already "saw" the smoke) | 3.72 | 30 | 17 | 17 | 107 |

Each forecast's cut-off was set on the training years only (see the notebook, section 6). The average error is
the steady number. Warning counts depend on the cut-off, and the notebook shows them for every possible cut-off.

The second model change added three inputs (NOAA's forecast for tomorrow, a ring of 14 more metro areas, this
afternoon's reading). It was chosen by a rule fixed in advance on the training years (`compare_features.py`) and
then scored on 2025 once: the average error improved (2.58 to 2.36), but the warnings got worse (cost 106 to 127,
arrival days caught 6 to 0 of 21). The notebook, section 7, discusses it. 2025 had been looked at before this change.

## Data split

| Split | Dates | City-days | Days above 35 µg/m³ |
|---|---|---|---|
| Train | 2022-08-04 to 2024-12-31 | 5,286 | 38 |
| Test | 2025-01-01 to 2025-12-31 | 2,190 | 35 |

The split is by time and never shuffled. Every model choice and cut-off comes from the training years.

## Rebuild the data (optional, no API keys)

```bash
pip install -r requirements.txt
python fetch_data.py          # EPA readings + CAMS + weather -> data/daily.csv
python fetch_smoke.py         # NOAA smoke maps over each city -> data/smoke_days.csv
python fetch_dayahead.py      # 2025 weather forecast one day ahead -> data/weather_dayahead_2025.csv
python fetch_naqfc.py         # NOAA's day-ahead PM2.5 forecast -> data/naqfc_dayahead.csv (downloads about 3 GB)
python fetch_upwind_smoke.py  # smoke 300/600/900 km upwind (tried, not used) -> data/upwind_smoke.csv
python fetch_early.py         # 2018 to mid-2022 training days (tried, not used) -> data/daily_early.csv
python fetch_ring.py          # EPA readings in 14 more metro areas around the six -> data/ring_pm25.csv
python fetch_evening.py       # each city's 2-7 PM hourly reading -> data/evening_pm25.csv (downloads about 290 MB)
```

`compare_seasons.py` compares a model trained on 2018–2024 with ours on the training years. We didn't adopt it
(notebook, section 6). `compare_features.py` is the training-year comparison behind the second model change.

## Sources

- **US EPA AirData**, daily PM2.5 FRM/FEM (parameter 88101): https://aqs.epa.gov/aqsweb/airdata/download_files.html.
  We average all monitors in each metro area. Hourly PM2.5 (`hourly_88101_YYYY.zip`, same page) for the 2-7 PM reading.
- **NOAA National Air Quality Forecast Capability (NAQFC)**, bias-corrected 24-hour PM2.5, NOAA Open Data
  Dissemination on AWS: https://registry.opendata.aws/noaa-nws-naqfc-pds/
- **NOAA Hazard Mapping System** smoke polygons: https://www.ospo.noaa.gov/products/land/hms.html
- **Copernicus Atmosphere Monitoring Service (CAMS)** global atmospheric composition forecasts, via the
  **Open-Meteo Air Quality API**: https://open-meteo.com/en/docs/air-quality-api. Model estimates (about 45 km
  grid), not measurements.
- **Open-Meteo** Historical Forecast API and Previous Runs API (weather): https://open-meteo.com
- Libraries: pandas, NumPy, scikit-learn, matplotlib, pyshp, eccodes, jupytext, Gradio, Plotly.
- AI tools: Claude (Anthropic), through Claude Code; see the write-up for what it did.
