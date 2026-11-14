# SmokeCheck video script (2:00 max)

<!-- DRAFT. [Brackets] wait on real numbers. Screen recording with voice over, no editing needed.
     About 260 words of voiceover = roughly 1:50 at a normal pace. Read it aloud with a timer before recording. -->

**The one takeaway (same sentence in the video, the write-up and finals):**
> [On 2025 smoke days, correcting the CAMS estimate with local monitors caught A of N unhealthy days; CAMS alone caught B, with C false alarms.]
> If we don't beat CAMS, the takeaway becomes that finding, said plainly.

## 1. The problem · 0:00–0:15
**Screen:** a plain title slide: "Practice outside, or move indoors?"
**Say:** "When wildfire smoke drifts over the Midwest, a high-school athletic director has to decide the day before whether practice stays outside. The forecasts they can look up come from big global models, and those can miss how bad one city gets."

## 2. The demo · 0:15–1:15
**Screen:** the app, opened on Chicago, [headline smoke day].
**Say:** "This is SmokeCheck. Pick a city and a day. Here's Chicago on [date], a day our model never saw in training."
**Do:** point at the verdict card.
**Say:** "SmokeCheck says move practice indoors: it forecast [Y] micrograms, over the limit of 35. The raw CAMS estimate said [X]. The monitors measured [Z]."
**Do:** drag the date slider back two days, then forward through the event.
**Say:** "Dragging through the week, you can watch the smoke arrive and the call change city by city."
**Do:** switch the city to [second city].
**Say:** "[Second city] on the same day: [verdict], and that was [right / wrong]."

## 3. How it works · 1:15–1:45
**Screen:** the "Does it work?" tab with the baseline table.
**Say:** "We don't forecast from scratch. We take the CAMS estimate from Open-Meteo, which is a model output, not a measurement, and train a model to correct it using EPA monitor readings and weather. We trained on 2022 to 2024 and tested on all of 2025. Against 'tomorrow equals today', SmokeCheck's error was [ ] versus [ ]. On the [N] days over the limit, it caught [A]; raw CAMS caught [B]. It raised [C] false alarms."

## 4. Limits and next · 1:45–2:00
**Screen:** the "Where it fails" tab.
**Say:** "It still misses [the main failure, in plain words]. Next we'd forecast the actual practice hours instead of the daily average, and test it with a real athletic director."

## Recording checklist
- [ ] Under 2:00 on a timer
- [ ] Every number said out loud matches the write-up table
- [ ] "Model estimate, not a measurement" is said once
- [ ] Uploaded unlisted (YouTube) or Drive "anyone with the link", opened in a private window
