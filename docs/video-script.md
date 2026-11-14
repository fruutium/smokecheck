# SmokeCheck video script (2:00 max)

<!-- Numbers from metrics.json / predictions.csv (main b6ac3e2). Re-check before recording.
     Screen recording with voice over, no editing needed. About 270 words of voiceover, roughly 1:55. Read it aloud with a timer first. -->

**The one takeaway (same sentence in the video, the write-up and finals):**
> Against NOAA's official day-ahead forecast, SmokeCheck's error is 19% lower and it warns on three times as many smoke days, at the price of more false alarms.

## 1. The problem · 0:00–0:15
**Screen:** a plain title slide: "Practice outside, or move indoors?"
**Say:** "When wildfire smoke drifts over the Midwest, a high-school athletic director has to decide the day before whether practice stays outside. Last July, Milwaukee's air hit more than twice the EPA limit, and NOAA's official forecast the day before said it would be fine."

## 2. The demo · 0:15–1:15
**Screen:** the app, opened on Milwaukee, July 31, 2025.
**Say:** "This is SmokeCheck. Pick a city and a day. Milwaukee, July 31st, 2025, a day our model never saw. NOAA's official forecast said 13. SmokeCheck forecast 28 and says move practice indoors. Monitors measured 84."
**Do:** point at the warning-line sentence on the card.
**Say:** "It warns above 24, not 35, because its forecasts run low on smoke days. We set that line on earlier years so one missed smoke day costs as much as five false alarms."
**Do:** switch the city to Chicago.
**Say:** "Same day in Chicago, and here's where we fail. SmokeCheck said 14, and so did NOAA: practice outside. The air was 66. The smoke arrived overnight, and our model leans on today's readings, which were still clean."
**Do:** step the slider forward one day.
**Say:** "One day later the smoke is still there. NOAA says 9, fine. SmokeCheck says 55, move indoors. The air was 46."

## 3. How it works · 1:15–1:45
**Screen:** the "Does it work?" tab.
**Say:** "SmokeCheck combines EPA monitor readings in the city and five neighbours, NOAA's satellite smoke map, tomorrow's weather forecast and the CAMS estimate, which is a model output, not a measurement. We trained on 2022 to 2024 and tested on all of 2025. Its average error is 2.6, against 3.2 for NOAA's official forecast and 3.4 for 'tomorrow equals today'. On the 35 bad days in 2025, it warned on 18; NOAA warned on 6. The price is 22 false alarms against NOAA's one."

## 4. Limits and next · 1:45–2:00
**Screen:** the "Where it fails" tab.
**Say:** "It still misses most days when smoke first arrives. Next, we'd add smoke mapped upwind of each city to catch it before it arrives, and test SmokeCheck with a real athletic director."

## Recording checklist
- [ ] Under 2:00 on a timer
- [ ] Every number said out loud matches the write-up table
- [ ] "Model output, not a measurement" is said once
- [ ] Uploaded unlisted (YouTube) or Drive "anyone with the link", opened in a private window
