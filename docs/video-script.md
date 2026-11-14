# SmokeCheck video script (2:00 max)

<!-- Numbers from metrics.json / predictions.csv (main 65b1456). Re-check before recording.
     Screen recording with voice over, no editing needed. About 270 words of voiceover, roughly 1:55. Read it aloud with a timer first. -->

**The one takeaway (same sentence in the video, the write-up and finals):**
> SmokeCheck's forecast is the closest every day, but on warnings it ties the CAMS model: it catches smoke that lingers, and CAMS catches smoke as it arrives.

## 1. The problem · 0:00–0:15
**Screen:** a plain title slide: "Practice outside, or move indoors?"
**Say:** "When wildfire smoke drifts over the Midwest, a high-school athletic director has to decide the day before whether practice stays outside. Last July, Chicago went from clean air to almost twice the EPA limit overnight."

## 2. The demo · 0:15–1:15
**Screen:** the app, opened on Milwaukee, July 31, 2025.
**Say:** "This is SmokeCheck. Pick a city and a day. Milwaukee, July 31st, 2025, a day our model never saw. SmokeCheck forecast 28 and says move practice indoors. Monitors measured 84, more than twice the limit."
**Do:** point at the warning-line sentence on the card.
**Say:** "It warns above 24, not 35, because its forecasts run low on smoke days. We set that line on earlier years so one missed smoke day costs as much as five false alarms."
**Do:** switch the city to Chicago.
**Say:** "Same day in Chicago, and here's where we fail. SmokeCheck said 14: practice outside. The CAMS model said 34 and warned. The air was 66. The smoke arrived overnight, and our model leans on today's readings, which were still clean."
**Do:** step the slider forward one day.
**Say:** "One day later it flips. CAMS says 19, fine. SmokeCheck says 55, move indoors. The air was 46."

## 3. How it works · 1:15–1:45
**Screen:** the "Does it work?" tab.
**Say:** "SmokeCheck combines EPA monitor readings in the city and five neighbours, NOAA's satellite smoke map, tomorrow's weather forecast and the CAMS estimate, which is a model output, not a measurement. We trained on 2022 to 2024 and tested on all of 2025. Its average error is 2.6, against 3.4 for 'tomorrow equals today' and 3.7 for CAMS. On the 35 bad days, it caught 18, the same as CAMS."

## 4. Limits and next · 1:45–2:00
**Screen:** the "Where it fails" tab.
**Say:** "It still misses most days when smoke first arrives. Next, we'd add smoke mapped upwind of each city to catch it before it arrives, and test SmokeCheck with a real athletic director."

## Recording checklist
- [ ] Under 2:00 on a timer
- [ ] Every number said out loud matches the write-up table
- [ ] "Model output, not a measurement" is said once
- [ ] Uploaded unlisted (YouTube) or Drive "anyone with the link", opened in a private window
