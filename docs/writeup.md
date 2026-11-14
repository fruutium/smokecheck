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

> Chicago, [headline 2025 smoke day] → **Move practice indoors.** SmokeCheck forecast [Y] µg/m³ (limit 35). The raw CAMS estimate said [X]. Monitors measured [Z].

It runs as a function in our Colab notebook, with an optional Gradio app: a map of [N] Midwest cities, a date slider across 2025, and the verdict.

## What we added (FORM)
We started from suggested project 4.3.2 (next-day air quality forecast). Instead of forecasting PM2.5 from scratch, we take the CAMS air-quality model estimate from Open-Meteo and train a model to correct it with local EPA monitor readings. We built it for one user and one decision, an athletic director choosing indoor or outdoor practice, and we test it where that decision matters: on 2025 days above 35 µg/m³, counting missed warnings and false alarms against three simple forecasts.

<!-- HUB CHECK PENDING: is the CAMS archive a true day-ahead forecast or closer to an after-the-fact analysis?
     Until the hub confirms, say "CAMS estimate", never "day-ahead CAMS forecast". -->

## How it works
- **Data:** daily PM2.5 from EPA monitors ([source name], [N] days × [N] cities) is the truth we predict. Open-Meteo's air-quality API gives the CAMS PM2.5 estimate, and Open-Meteo weather gives wind and rain. **Open-Meteo air-quality values are model estimates, not measurements.** Cleaning: [how missing monitor days were handled].
- **Split:** train Aug 2022 – Dec 2024, test all of 2025. Days are never shuffled, so the model never sees the future.
- **Model:** [model], trained to predict [the gap between CAMS and the monitors / tomorrow's PM2.5] from [features]. We chose it because [reason].
- **Decision rule:** forecast above 35 µg/m³ (the US EPA 24-hour standard) → "move indoors".

## Results (2025 test set, never used in training)

| Forecast | MAE (µg/m³) | Smoke days caught (of [N] days > 35) | False alarms |
|---|---|---|---|
| Baseline: persistence (tomorrow = today) | [ ] | [ ] | [ ] |
| Baseline: climatology (typical value for that date) | [ ] | [ ] | [ ] |
| Baseline: raw CAMS estimate | [ ] | [ ] | [ ] |
| **SmokeCheck** | [ ] | [ ] | [ ] |

[One sentence: the main finding, whatever it turns out to be, including if we do not beat a baseline.]

**By city and by day type:** [where the model is better and worse: per city, smoke days vs clean days.]

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
