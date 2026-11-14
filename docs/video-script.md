# SmokeCheck video script (2:00 max)

<!-- 268 words of voice-over, counted from the "Say:" lines below (about 300 when the numbers are read out in full).
     The run sheet ends at 1:58, so read at a brisk, steady 155 words a minute: about 1:55 with the clicks.
     Every number is checked against data/predictions.csv and data/metrics.json, and every on-screen string in the run sheet
     against the running app (commit e005d8a, Nov 14). Re-check both if the data or the page changes.
     One screen recording of the app with voice-over. No slides, no editing. Read it aloud with a timer first.
     If it runs long, cut the August 1 line (click the next-day arrow anyway, the screen tells that story). -->

**The one takeaway (same sentence in the video, the write-up and finals):**
> SmokeCheck's forecast is 26% more accurate than NOAA's official one, in every resample and every city. But its move-indoors warnings were slightly worse than just reading NOAA at 35, and it missed every day smoke first arrived.

## 1. The problem · 0:00–0:15
**Screen:** the app as it opens, on the **Tomorrow** tab, city Minneapolis. No clicks yet.
**Say:** "When wildfire smoke hits the Midwest, an athletic director decides the day before whether practice stays outside. In July 2025, Minneapolis's air hit almost twice the EPA limit. NOAA's official forecast said it would be fine."

## 2. The demo · 0:15–1:12
**Do:** point at "Smoke forecast", then at "Forecast made …".
**Say:** "This is SmokeCheck. This is tomorrow's real forecast for Minneapolis, made this evening from live readings. Practice outside."
*The last two words are the call on screen. Read what the page says that day: "Practice outside" or "Move practice indoors". The forecast number changes every day, so do not say it. If the "Forecast made" time is before evening, say "today" in place of "this evening".*

**Do:** click the **2025 test run** tab. The numbers take about two seconds to count up. The first sentence covers that.
**Say:** "To test it, we replay 2025, a year the model never saw. Minneapolis, July 31st. SmokeCheck forecast 41: move practice indoors. NOAA said 19. Monitors measured 69. Right call."

**Do:** point at "Indoors above 32".
**Say:** "The line is 32, not 35, because its forecasts run low on smoke days: we set it on 2022 to 2024, counting one missed smoke day as five false alarms."

**Do:** city picker, top right → **Chicago**.
**Say:** "Same day in Chicago, and here we fail. SmokeCheck said 15: practice outside. The air was 66. Missed a bad day. The smoke arrived overnight, and our model leans on today's readings."

**Do:** click the **›** button next to the date, once.
**Say:** "One day later the smoke is still there. NOAA says 9. SmokeCheck says 52: move indoors. The air was 46."

## 3. How it works · 1:12–1:44
**Do:** click the **Does it work?** tab.
**Say:** "It combines EPA readings from this city and 19 other Midwest metros, NOAA's own forecast, smoke maps, tomorrow's weather and the CAMS model estimate, which is not a measurement. We trained on 2022 to 2024 and tested on 2025. Its average error is 2.36, against NOAA's 3.2. It was closer in every city and every one of 1,000 resamples. But its move-indoors warnings were slightly worse than just reading NOAA at 35."

## 4. Limits and next · 1:44–1:58
**Do:** stay on the tab. Point at the "Weak spot" line.
**Say:** "It missed every day smoke first arrived. One big smoke year is not enough to set its warning line reliably. Next: more cities that get smoke, and a real athletic director."

## Run sheet (what to click, in order)
Do one silent practice run with these clicks, then record. `docs/video/demo-silent.mp4` is this run sheet, click for click, to rehearse against.
The page shows its headlines in capitals, so they are written that way here.

| Time | Click | Check on screen before speaking |
|---|---|---|
| 0:00 | Nothing. The app is open on the **Tomorrow** tab, picker (top right) on Minneapolis | "Minneapolis · Practice on [tomorrow's weekday and date]" · "OK TO PRACTICE OUTSIDE" (or "MOVE PRACTICE INDOORS") · "Smoke forecast [a number]" · "Indoors above 32" · "Forecast made [weekday] at [time]" · no "Updating…" after it |
| 0:15 | Point at "Smoke forecast", then "Forecast made …" | the same screen |
| 0:23 | Tab **2025 test run** | "Minneapolis · Thursday, July 31, 2025" · "MOVE PRACTICE INDOORS" · "Smoke forecast 41.3" · "Indoors above 32" · panel "WAS IT RIGHT?": "RIGHT CALL" · "Measured that day 69.1" · "A bad day" · "NOAA's forecast 18.7" |
| 0:36 | Point at "Indoors above 32", then at "Line at 32" under the scale | the same screen |
| 0:48 | City picker (top right) → **Chicago** | "Chicago · Thursday, July 31, 2025" · "OK TO PRACTICE OUTSIDE" · "Smoke forecast 15.3" · "MISSED A BAD DAY" · "Measured that day 65.6" · "NOAA's forecast 13.7" |
| 1:03 | The **›** button right of the date, once | "Chicago · Friday, August 1, 2025" · "MOVE PRACTICE INDOORS" · "Smoke forecast 51.8" · "RIGHT CALL" · "Measured that day 45.5" · "NOAA's forecast 8.7" |
| 1:12 | Tab **Does it work?** | "26% LOWER ERROR THAN NOAA'S OFFICIAL FORECAST." · "Its warnings cost 127. Reading NOAA at 35 cost 123. Lower is better." · row "SmokeCheck" 2.36 · row "NOAA's official forecast" 3.20 · row "NOAA's official forecast, read at 35" cost 123 |
| 1:44 | Point at the last line on the page | "Weak spot: it misses the day smoke first arrives (warned on 0 of 21 in 2025)." |
| 1:58 | Stop | |

Three things that can trip a take:
- **The app remembers the city.** After a take the picker is on Chicago and the day is August 1. Before every take, set the picker back to Minneapolis and reload the page. A reload goes back to the Tomorrow tab and to July 31.
- **Use the › button for the next day, not the arrow key.** Right after you pick a city, the keyboard is still on the picker, so the right-arrow key would act on the picker and not on the date.
- **"Updating…" on the Tomorrow tab.** Before about 8 PM Central the app remakes the forecast if it is more than 30 minutes old. That takes under a minute, and the number can change. Open the app, wait until "Updating…" is gone, then record.

## Recording checklist
- [ ] App running (`python app/app.py`, then http://127.0.0.1:7860), internet on. Only the Tomorrow tab needs it.
- [ ] Best after 8 PM Central: by then the afternoon readings are all in, and "made this evening" is true
- [ ] Browser window about 1280×800, zoom 100%, so the verdict, the numbers and the "Was it right?" panel fit without scrolling
- [ ] Picker on Minneapolis, page reloaded, no "Updating…" or "Couldn't update." on the Tomorrow tab
- [ ] Under 2:00 on a timer
- [ ] Every number said out loud matches the screen
- [ ] "the CAMS model estimate, which is not a measurement" is said once
- [ ] The takeaway's three facts are all said: more accurate than NOAA, warnings slightly worse than NOAA at 35, missed every arrival day
- [ ] Uploaded unlisted (YouTube) or Drive "anyone with the link", opened in a private window
