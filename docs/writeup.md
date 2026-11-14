# SmokeCheck: practice outside, or move indoors?

<!-- DRAFT. Everything in [brackets] is waiting on a real number or a hub check. Nothing here is a result yet.
     Must fit ONE page when exported. Lines marked FORM are reused word for word on the submission form.
     FORM, team details: Abhiddyu Chandiwal and Aiden Patel, both Jordan High School. Emails are typed on the form by us, not stored here. -->

**Track:** AI + Climate · **Team:** Abhiddyu Chandiwal and Aiden Patel

*SmokeCheck is a prototype and is not medical or health advice.*

**One-sentence pitch (FORM):** SmokeCheck helps a Midwest high-school athletic director who has to decide whether tomorrow's practice is safe outdoors on a wildfire-smoke day by taking their city and tomorrow's date and telling them "practice outside" or "move indoors", with the PM2.5 forecast behind the call.

## The problem
When wildfire smoke drifts over the Midwest, a high-school athletic director has to decide the day before whether practice stays outside. The air-quality forecasts they can look up come from large-scale models that can miss how bad a smoke day gets in one city. A wrong "it's fine" puts [a few hundred] students outside breathing smoke; a wrong "move inside" cancels practice for nothing.

## What we built
SmokeCheck takes a city and a date and returns tomorrow's average fine-particle pollution (PM2.5) forecast and a verdict. For example:

> Chicago, Thursday July 31, 2025 → **[verdict].** SmokeCheck forecast [Y] µg/m³ (limit 35). The raw CAMS estimate said 34.3, just under the limit. Monitors measured 65.6.

It runs as a function in our Colab notebook, with an optional Gradio app: a map of six Midwest cities, a date slider across 2025, and the verdict.

## What we added (FORM)
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting PM2.5 from scratch, we take the CAMS air-quality model estimate from Open-Meteo and train a model to correct it with local EPA monitor readings. We built it for one user and one decision, an athletic director choosing indoor or outdoor practice, and we test it where that decision matters: on 2025 days above 35 µg/m³, counting missed warnings and false alarms against three simple forecasts.

<!-- HUB CHECKED (Nov 13): Open-Meteo has no true day-ahead CAMS archive. Say "CAMS estimate", never "day-ahead CAMS forecast". -->

## How it works
- **Data:** daily PM2.5 from EPA monitors ([source name], 7,476 city-days across Chicago, Milwaukee, Madison, Minneapolis, Detroit and St. Louis; EPA days are local standard time) is the truth we predict. Open-Meteo's air-quality API gives the CAMS PM2.5 estimate, and Open-Meteo weather gives wind and rain. **Open-Meteo air-quality values are model estimates, not measurements.** Cleaning: [how missing monitor days were handled].
- **A caveat on CAMS:** Open-Meteo keeps no archive of true day-ahead CAMS forecasts, so the CAMS history we use is short-range. That makes raw CAMS look better than a real day-ahead forecast would, so the comparison is tilted in CAMS's favor.
- **Split:** train Aug 4, 2022 – Dec 31, 2024, test all of 2025. Days are never shuffled, so the model never sees the future.
- **Model:** [model], trained to predict [the gap between CAMS and the monitors / tomorrow's PM2.5] from [features]. We chose it because [reason].
- **Decision rule:** forecast above 35 µg/m³ (the US EPA 24-hour standard) → "move indoors".

## Results (2025 test set, never used in training)
<!-- Baseline rows copied from data/metrics.json (main 1f73e73, Nov 13). Re-check every cell against the final metrics.json before submitting. -->

| Forecast | MAE (µg/m³) | Smoke days caught (of 35 city-days > 35) | False alarms |
|---|---|---|---|
| Baseline: persistence (tomorrow = today) | 3.40 | 14 | 21 |
| Baseline: climatology (typical value for that date) | 4.33 | 0 | 0 |
| Baseline: raw CAMS estimate | 3.72 | 10 | 4 |
| **SmokeCheck** | [ ] | [ ] | [ ] |

[One sentence: the main finding, whatever it turns out to be, including if we do not beat a baseline.]

**By city and by day type:** [where the model is better and worse: per city, smoke days vs clean days.]

**Why persistence isn't enough.** On July 31, 2025 smoke arrived in Chicago overnight: the day before measured 12.4, so "tomorrow = today" said the air was fine, and monitors measured 65.6. All three simple forecasts said "practice outside" that day (persistence 12.4, climatology 11.3, raw CAMS 34.3).

**Where it fails.** [One or two real test days it got wrong, with the numbers, and why we think so. Kit guess to verify: the first day smoke arrives, when yesterday's monitors were still clean.]

**What we tried and dropped.** [One thing, with its number, and why we dropped it.]

## What we'd do next
- [Forecast the practice hours (3–6 PM) instead of the daily average, since that is when students are outside.]
- [Try it with a real athletic director and ask whether a yes/no call or a number is more useful.]

## Sources
- **Data:** [EPA AirData daily PM2.5, link] · [Open-Meteo Air Quality API (CAMS global), link] · [Open-Meteo weather API, link]
- **Libraries:** [pandas, scikit-learn, LightGBM, Gradio, Plotly: keep only what we actually used]
- **Starting point:** Veritas AI Project Briefs, suggested project 4.3.2
- **AI tools:** Claude (Claude Code), used for [say exactly what: drafting data-loading and app code, which we read and can explain; pre-event research on datasets]. [Any others.]
