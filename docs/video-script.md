# SmokeCheck video script (2:00 max)

<!-- 268 words of voice-over, counted from the "Say:" lines below (about 280 when the numbers are read out in full).
     This is now the script of a produced video, 1:58.5 long: a recording of the real app inside a window, with zooms and
     highlights, between an animated opening, an animated "Does it work?" scene and a closing card. Captions and quiet music are
     in the picture. The narration is recorded by us afterwards and mixed in (no AI voice).
     The project is in ../video-project (outside this repo): RECORDING-GUIDE.md there has the lines with their start times,
     and docs/video/README.md here says how the video is built and mixed.
     The captions move at 150 words a minute and the scenes have almost no spare time, so read at a brisk, steady pace.
     Every number is checked against data/predictions.csv and data/metrics.json, and every on-screen string against the
     running app (commit e005d8a, Nov 14). Re-check both if the data or the page changes.
     If a part runs long, make its scene longer in ../video-project/timing.json and rebuild (the video must stay under 2:00). -->

**The one takeaway (same sentence in the video, the write-up and finals):**
> SmokeCheck's forecast is 26% more accurate than NOAA's official one, in every resample and every city. But its move-indoors warnings were slightly worse than just reading NOAA at 35, and it missed every day smoke first arrived.

## 1. The problem · 0:00–0:15
**Screen:** animated opening, no app yet. A clear dusk sky fills with smoke under the words "Practice tomorrow: outside or indoors?". Then Minneapolis, July 31, 2025: "Measured in the air 69.1" on a bar that runs past the mark "EPA limit 35", and "NOAA's official forecast 18.7" below the limit.
**Say:** "When wildfire smoke hits the Midwest, an athletic director decides the day before whether practice stays outside. In July 2025, Minneapolis's air hit almost twice the EPA limit. NOAA's official forecast said it would be fine."

## 2. The demo · 0:15–1:09
**Screen (0:15):** the name SmokeCheck, then the real app in a window on the **Tomorrow** tab, Minneapolis. The picture zooms to "Smoke forecast", then highlights "Forecast made …", then the call.
**Say:** "This is SmokeCheck. This is tomorrow's real forecast for Minneapolis, made this evening from live readings. Practice outside."
*The last two words are the call on screen. Read what the page says that day: "Practice outside" or "Move practice indoors". The forecast number changes every day, so do not say it. If the "Forecast made" time is before evening, say "today" in place of "this evening".*
*The app recording in the produced video was made on Saturday, Nov 14 at 3:00 PM (forecast 8.7, practice outside), so for this video say "made today". The caption says "today" too.*

**Screen (0:22):** a real click on the **2025 test run** tab. The numbers count up for about two seconds, and the first sentence covers that. Then highlights on the date, on 41.3, and a zoom to the "Was it right?" panel: NOAA's 18.7, measured 69.1, "Right call".
**Say:** "To test it, we replay 2025, a year the model never saw. Minneapolis, July 31st. SmokeCheck forecast 41: move practice indoors. NOAA said 19. Monitors measured 69. Right call."

**Screen (0:35):** zoom to "Indoors above 32" with a highlight, then to the scale and "Line at 32". The left column adds "Set on 2022 to 2024" and "1 missed smoke day = 5 false alarms".
**Say:** "The line is 32, not 35, because its forecasts run low on smoke days: we set it on 2022 to 2024, counting one missed smoke day as five false alarms."

**Screen (0:48):** the city picker changes to **Chicago**. Highlight on 15.3, then a zoom to the panel: measured 65.6 and "Missed a bad day", held as long as the Minneapolis win.
**Say:** "Same day in Chicago, and here we fail. SmokeCheck said 15: practice outside. The air was 66. Missed a bad day. The smoke arrived overnight, and our model leans on today's readings."

**Screen (1:01):** a real click on the **›** button next to the date. Highlights on NOAA's 8.7, then 51.8, then measured 45.5.
**Say:** "One day later the smoke is still there. NOAA says 9. SmokeCheck says 52: move indoors. The air was 46."

## 3. How it works · 1:09–1:42
**Screen:** animated, no app. The five inputs appear one by one as they are named and feed into SmokeCheck (the CAMS one is tagged "not a measurement"). Then four years: 2022 to 2024 "Trained", 2025 "Tested here, a year it never saw". Then two cards of the same size: "Forecast error" 2.36 against 3.20, "26% lower error", closer in every city and in all 1,000 resamples; and "Move-indoors warnings" cost 127 against 123 for just reading NOAA at 35, "Slightly worse".
**Say:** "It combines EPA readings from this city and 19 other Midwest metros, NOAA's own forecast, smoke maps, tomorrow's weather and the CAMS model estimate, which is not a measurement. We trained on 2022 to 2024 and tested on 2025. Its average error is 2.36, against NOAA's 3.2. It was closer in every city and every one of 1,000 resamples. But its move-indoors warnings were slightly worse than just reading NOAA at 35."

## 4. Limits and next · 1:42–1:55
**Screen:** the real app again, on the **Does it work?** tab. Zoom to the "Weak spot" line with a highlight, and "0 of 21 days smoke first arrived" in the left column. Then the whole results table, then the two next steps. From 1:55 to 1:58.5 the closing card, with no words: SmokeCheck, "Aiden Patel and Abhiddyu Chandiwal", `github.com/fruutium/smokecheck`, "A prototype, not medical or health advice."
**Say:** "It missed every day smoke first arrived. One big smoke year is not enough to set its warning line reliably. Next: more cities that get smoke, and a real athletic director."

## Run sheet (for a live screen recording: the backup plan)
The produced video does not need this: its clicks are already recorded. Use it only if you record your own screen and not the produced video. Its times are the old ones, about three seconds later than the produced video from 1:03 on. `docs/video/demo-silent.mp4` is this run sheet, click for click.
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

## Recording checklist (the voice, for the produced video)
- [ ] Read along with `../video-project/renders/smokecheck-demo-music-only.mp4`, its sound off, in a quiet room (see `RECORDING-GUIDE.md` there)
- [ ] Finished before the closing card at 1:55
- [ ] Mixed with `./mix.sh narration.m4a`, and the result is under 2:00
- [ ] "Deliberate Thought" by Kevin MacLeod (CC BY 4.0) is credited in the video description and the write-up (`CREDITS.md` there)
- [ ] Every number said out loud matches the screen
- [ ] "the CAMS model estimate, which is not a measurement" is said once
- [ ] The takeaway's three facts are all said: more accurate than NOAA, warnings slightly worse than NOAA at 35, missed every arrival day
- [ ] Uploaded unlisted (YouTube) or Drive "anyone with the link", opened in a private window
