---
title: SmokeCheck
emoji: 🌫️
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: "6.32.0"
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Next-day wildfire-smoke call for Midwest school practice
---

# SmokeCheck

For a Midwest high-school athletic director deciding the day before whether tomorrow's practice stays outside
or moves indoors on wildfire-smoke days. It replays every day of 2025 (the held-out test year) for six cities:
Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis.

The app only reads two files, `data/predictions.csv` and `data/metrics.json`. The model was trained and
evaluated in the project notebook; nothing is trained or downloaded here.

**Open-Meteo air-quality values are model estimates, not measurements. Prototype, not health advice.**

## Sources

- **US EPA AirData**, daily PM2.5 FRM/FEM (parameter 88101): https://aqs.epa.gov/aqsweb/airdata/download_files.html
- **NOAA National Air Quality Forecast Capability (NAQFC)**, bias-corrected 24-hour PM2.5, NOAA Open Data
  Dissemination on AWS: https://registry.opendata.aws/noaa-nws-naqfc-pds/
- **NOAA Hazard Mapping System** smoke polygons: https://www.ospo.noaa.gov/products/land/hms.html
- **Copernicus Atmosphere Monitoring Service (CAMS)** forecasts, via the **Open-Meteo Air Quality API**:
  https://open-meteo.com/en/docs/air-quality-api
- **Open-Meteo** Historical Forecast and Previous Runs APIs (weather): https://open-meteo.com
- Libraries used by this app: Gradio, pandas, Plotly.
- AI tools: Claude (Anthropic), through Claude Code.
