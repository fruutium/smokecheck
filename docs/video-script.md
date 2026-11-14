# SmokeCheck video script (2:00 max)

<!-- Numbers from metrics.json / predictions.csv (main 2c71e03; every spoken number checked against predictions.csv). Re-check if the data changes.
     Screen recording with voice over, no editing needed. About 275 words of voiceover, roughly 1:55 at a brisk pace; trim the Aug 1 line first if it runs long. Read it aloud with a timer first. -->

**The one takeaway (same sentence in the video, the write-up and finals):**
> SmokeCheck's forecasts are closer than NOAA's official day-ahead forecast in every resample of 2025 (average error 2.58 vs 3.20). On the move-indoors call itself it's roughly even with NOAA, and it still misses smoke that arrives overnight.

## 1. The problem · 0:00–0:15
**Screen:** a plain title slide, "SmokeCheck: practice outside, or move indoors?" (any slide app), or skip it and start on the app with the card visible.
**Say:** "When wildfire smoke hits the Midwest, an athletic director decides the day before whether practice stays outside. Last July, Milwaukee's air hit more than twice the EPA limit, and NOAA's official forecast the day before said it would be fine."

## 2. The demo · 0:15–1:15
**Screen:** the app, opened on Milwaukee, July 31, 2025.
**Say:** "This is SmokeCheck. Milwaukee, July 31st, 2025, a day our model never saw. NOAA's official forecast said 13. SmokeCheck forecast 27 and says move practice indoors. Monitors measured 84."
**Do:** point at the warning-line sentence on the card.
**Say:** "It warns above 24 and a half, not 35, because its forecasts run low on smoke days. We set that line on 2022 to 2024, counting one missed smoke day as five false alarms."
**Do:** switch the city to Chicago.
**Say:** "Same day in Chicago, and here's where we fail. SmokeCheck said 14, and so did NOAA: practice outside. The air was 66. The smoke arrived overnight, and our model leans on today's readings, which were still clean."
**Do:** step the slider forward one day.
**Say:** "One day later the smoke is still there. NOAA says 9, fine. SmokeCheck says 54, move indoors. The air was 46."

## 3. How it works · 1:15–1:45
**Screen:** the "Does it work?" tab.
**Say:** "SmokeCheck combines EPA readings from the city and five neighbours, NOAA smoke maps, tomorrow's weather forecast and the CAMS model estimate, which is not a measurement. We trained on 2022 to 2024 and tested on 2025. Its average error is 2.6, against 3.2 for NOAA's official forecast and 3.4 for 'tomorrow equals today'. We resampled 2025 a thousand times, and SmokeCheck was closer in every one. On the move-indoors call, it's roughly even with NOAA and usually ahead of 'tomorrow equals today'."

## 4. Limits and next · 1:45–2:00
**Screen:** the "Where it fails" tab.
**Say:** "It still misses most days when smoke first arrives. The arrivals it caught were already hazy the day before. Next: more cities that get smoke, and a real athletic director."

## Run sheet (what to click, in order)
Do one silent practice run with these clicks, then record. Keep the browser window around 1280×800 so the card and the three boxes fit.
| Time | Click | Check on screen before speaking |
|---|---|---|
| 0:00 | Title slide (or the app) | |
| 0:15 | The app as it opens | Milwaukee · Thursday, July 31, 2025 · red "Move practice indoors" · NOAA 13.4 · SmokeCheck 26.8 · measured 83.7 |
| 0:35 | Hover over the sentence under "SmokeCheck forecasts 26.8" | "warns above 24.5 µg/m³, not 35" |
| 0:45 | City dropdown → Chicago | green "OK to practice outside" · SmokeCheck 13.7 · NOAA 13.7 · measured 65.6 · "Likely between 8.8 and 20.6" |
| 1:00 | Click the slider handle, press the right-arrow key once | Date box: Friday, August 1, 2025 · red · SmokeCheck 54.0 · NOAA 8.7 · measured 45.5 |
| 1:15 | Tab "Does it work?" | SmokeCheck row first: 2.58 average error |
| 1:45 | Tab "Where it fails" | the "Smoke arrival days are the weak spot" note |
| 2:00 | Stop | |

## Recording checklist
- [ ] Under 2:00 on a timer
- [ ] Every number said out loud matches the write-up table
- [ ] "CAMS is a model estimate, not a measurement" is said once
- [ ] Uploaded unlisted (YouTube) or Drive "anyone with the link", opened in a private window
