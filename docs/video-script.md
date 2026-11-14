# SmokeCheck video script (2:00 max)

<!-- Numbers from metrics.json / predictions.csv (main b6ac3e2). Re-check before recording.
     Screen recording with voice over, no editing needed. About 275 words of voiceover, roughly 1:55 at a brisk pace; trim the Aug 1 line first if it runs long. Read it aloud with a timer first. -->

**The one takeaway (same sentence in the video, the write-up and finals):**
> Against NOAA's official day-ahead forecast, SmokeCheck's error is 19% lower, and counting a missed smoke day as five false alarms, its decisions cost 107 against NOAA's 123.

## 1. The problem · 0:00–0:15
**Screen:** a plain title slide: "Practice outside, or move indoors?"
**Say:** "When wildfire smoke hits the Midwest, an athletic director decides the day before whether practice stays outside. Last July, Milwaukee's air hit more than twice the EPA limit, and NOAA's official forecast the day before said it would be fine."

## 2. The demo · 0:15–1:15
**Screen:** the app, opened on Milwaukee, July 31, 2025.
**Say:** "This is SmokeCheck. Milwaukee, July 31st, 2025, a day our model never saw. NOAA's official forecast said 13. SmokeCheck forecast 28 and says move practice indoors. Monitors measured 84."
**Do:** point at the warning-line sentence on the card.
**Say:** "It warns above 24, not 35, because its forecasts run low on smoke days. We set that line on earlier years so one missed smoke day costs as much as five false alarms."
**Do:** switch the city to Chicago.
**Say:** "Same day in Chicago, and here's where we fail. SmokeCheck said 14, and so did NOAA: practice outside. The air was 66. The smoke arrived overnight, and our model leans on today's readings, which were still clean."
**Do:** step the slider forward one day.
**Say:** "One day later the smoke is still there. NOAA says 9, fine. SmokeCheck says 55, move indoors. The air was 46."

## 3. How it works · 1:15–1:45
**Screen:** the "Does it work?" tab.
**Say:** "SmokeCheck combines EPA readings from the city and five neighbours, NOAA smoke maps, tomorrow's weather forecast and the CAMS model estimate, which is not a measurement. We trained on 2022 to 2024 and tested on 2025. Its average error is 2.6, against 3.2 for NOAA's official forecast and 3.4 for 'tomorrow equals today'. Counting a missed smoke day as five false alarms, SmokeCheck's calls cost 107 and NOAA's 123, or 118 even with hindsight."

## 4. Limits and next · 1:45–2:00
**Screen:** the "Where it fails" tab.
**Say:** "It still misses most days when smoke first arrives. Upwind smoke maps showed most of them coming, but with one big smoke year to learn from, the model couldn't use that. Next: more smoke seasons, and a real athletic director."

## Recording checklist
- [ ] Under 2:00 on a timer
- [ ] Every number said out loud matches the write-up table
- [ ] "CAMS is a model estimate, not a measurement" is said once
- [ ] Uploaded unlisted (YouTube) or Drive "anyone with the link", opened in a private window
