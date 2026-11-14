# SmokeCheck: finals talk outline (5:00 + Q&A)

<!-- Numbers from data/metrics.json and data/predictions.csv, checked by docs/finals/make_charts.py (its asserts fail if the data changes).
     The deck is docs/finals/deck.html: open it in Chrome, press Cmd+Ctrl+F for full screen, arrows / Space / PageDown to move, #N in the URL jumps to slide N.
     Charts: chart_error.svg, chart_cost.svg, chart_chicago_week.svg (rebuild: python docs/finals/make_charts.py). -->

**Speakers:** Aiden = user, impact, demo. Abhiddyu = data, model, evaluation.
**Total planned:** 4:50, leaving 10 seconds of slack. The demo gets 1:30, the results 1:30.

**The one takeaway** (the same sentence as the write-up and video):
> Against NOAA's official day-ahead forecast, SmokeCheck's error is 19% lower. Counting a missed smoke day as five false alarms, its decisions cost 106, against NOAA's 123 at the EPA's 35 line.

| # | Slide | Time | Clock at end | Speaker |
|---|---|---|---|---|
| 1 | SmokeCheck: practice outside, or move indoors? | 0:20 | 0:20 | Aiden |
| 2 | One decision, made the evening before | 0:15 | 0:35 | Aiden |
| 3 | Switch to the app (live demo) | 1:30 | 2:05 | Aiden |
| 4 | Backup: the demo, in three days | 0:00 (only if the demo fails) | | Aiden |
| 5 | How it works | 0:30 | 2:35 | Abhiddyu |
| 6 | 19% lower error than NOAA's official forecast | 0:25 | 3:00 | Abhiddyu |
| 7 | Warning cost: a missed bad day = 5 false alarms | 0:35 | 3:35 | Abhiddyu |
| 8 | Where it fails: smoke arriving overnight | 0:30 | 4:05 | Abhiddyu |
| 9 | What we learned: the cheapest line is noise | 0:25 | 4:30 | Abhiddyu |
| 10 | Why it matters, and what's next | 0:20 | 4:50 | Aiden |
| 11 | Sources | Q&A only | | either |

---

## 1. SmokeCheck: practice outside, or move indoors? · 0:20 · Aiden
**On screen:** 83.7 measured in Milwaukee on July 31, 2025, and NOAA's 13.4 forecast. EPA limit 35.
**Say:** "When wildfire smoke hits the Midwest, a high-school athletic director has to decide the evening before whether practice stays outside. On July 31, 2025, Milwaukee's air measured 83.7 micrograms of fine particles. That's more than twice the EPA's limit of 35. The day before, NOAA's official forecast said 13.4."

## 2. One decision, made the evening before · 0:15 · Aiden
**Say:** "SmokeCheck is built for that one decision. You give it a city and tomorrow's date. It says 'practice outside' or 'move indoors', and shows the PM2.5 forecast and a likely range behind the call. It covers six Midwest cities."

## 3. Switch to the app · 1:30 · Aiden (live demo)
**Before the talk:** have the app already open on Milwaukee, July 31, 2025, in a second window. Practice switching windows (Cmd+Tab) once.
**Do and say:**
1. **Milwaukee, Jul 31 (0:30).** "This is a day the model never saw. NOAA's official forecast said 13.4. SmokeCheck forecast 26.8. That's above its warning line of 24.5, so it says move practice indoors. The monitors measured 83.7." Point at the warning-line sentence: "It warns above 24.5, not 35, because forecasts run low on smoke days. We set that line on 2022 to 2024 only."
2. **City → Chicago (0:30).** "Same day in Chicago, and here we fail. SmokeCheck said 13.7, and so did NOAA: practice outside. The air measured about 66. The smoke arrived overnight. Our model leans on today's readings, and those were still clean."
3. **Slider → Aug 1 (0:20).** "One day later the smoke is still there. NOAA says 8.7, fine. SmokeCheck says 54, move indoors. The air measured 45.5."
4. **Back to the deck (0:10).** "So it catches smoke that lingers, but not smoke that's just arriving. Abhiddyu will show the numbers."

**If the demo fails** (the app won't load, freezes, or shows an error): don't debug it on stage. Say "Here are the same three days" and press the right arrow to slide 4. Talk through the three cards with the same lines as above, which takes about the same 1:30. If a recorded demo video is available, play it instead, starting at 0:15 and stopping at 1:15 (the demo section of `docs/video-script.md`).

## 4. Backup: the demo, in three days · 0:00 unless needed · Aiden
**Use only if the live demo fails.** It shows three cards with the same numbers as the app:
- Milwaukee, Jul 31: move indoors, 26.8 vs NOAA 13.4, measured 83.7.
- Chicago, Jul 31: practice outside, 13.7 (likely range 8.8 to 20.6) vs NOAA 13.7, measured 65.6.
- Chicago, Aug 1: move indoors, 54.0 vs NOAA 8.7, measured 45.5.

If the demo worked, press the right arrow twice from slide 3 to skip it.

## 5. How it works · 0:30 · Abhiddyu
**Say:** "We only use what's known the evening before. That's EPA monitor readings in this city and five others, NOAA's satellite smoke maps, today's CAMS estimate, and tomorrow's weather forecast. CAMS is a model estimate, not a measurement. The model averages two parts. A Ridge regression predicts tomorrow's level. Gradient-boosted trees predict the change from today, because trees can't predict values above anything they've seen. We trained on August 2022 to the end of 2024, and tested on all of 2025, once, in time order."

## 6. 19% lower error than NOAA's official forecast · 0:25 · Abhiddyu
**Say:** "Across 2,190 city-days in 2025, our average error is 2.58 micrograms. NOAA's official day-ahead forecast is 3.20, so we're 19% lower. 'Tomorrow equals today' is 3.40. Raw CAMS is 3.72, and that one is optimistic because its archive partly sees the day's smoke. This number doesn't depend on any warning line."

## 7. Warning cost: a missed bad day = 5 false alarms · 0:35 · Abhiddyu
**Say:** "An athletic director cares about the call, not the error. We count a missed bad day as five false alarms. Every forecast runs low on smoke days, so each one gets its own warning line, from the same rule, on the training years only. At its own line, SmokeCheck costs 106. NOAA at its own line costs 166, and at the plain 35 line it costs 123. But that's one year with 35 bad days. When we resample 2025's weeks, on the call we're roughly even with NOAA (ahead in 60% of resamples) and ahead of persistence in 94%. The error win is the solid one."

## 8. Where it fails: smoke arriving overnight · 0:30 · Abhiddyu
**On screen:** Chicago, July 27 to August 2, 2025, with measured, SmokeCheck and NOAA, the 35 line and the 24.5 line.
**Say:** "Here's that Chicago week. On July 31 the smoke arrived overnight. Both we and NOAA said 13.7, and the air hit about 66. When smoke arrives, we caught only 6 of 21 bad days, because the model leans on today's clean reading. When smoke lingers, we caught 12 of 14, like August 1. NOAA never forecast above 16 all week." (If asked about August 2: "That's a small false alarm. We said 27.8 and it measured 26.2.")

## 9. What we learned: the cheapest line is noise · 0:25 · Abhiddyu
**Say:** "Our first rule for the warning line was to take the single cheapest line on the training years. Then we stored the readings with one more decimal place, a change of at most 0.005, and the line jumped from 24 to 29.5. Many lines cost almost the same, so the minimum was picking out noise. We wrote down a new rule before running it. We make 200 copies of the training years by drawing whole weeks, find the cheapest line on each, and take the median. Every forecast gets the same rule. Ours came out at 24.5."

## 10. Why it matters, and what's next · 0:20 · Aiden
**Say:** "Against NOAA's official forecast, SmokeCheck's error is 19% lower, and its warnings cost 106 against NOAA's 123 at the EPA's 35 line. Next, we want more smoky cities to fix arrival days, a forecast for practice hours, 3 to 6 PM, and a test with a real athletic director. It's a prototype, not health advice. Thank you."

## 11. Sources · Q&A only
Leave this slide up during questions. Answers are in `docs/qa-prep.md`.

---

## Rehearsal checklist
- [ ] Run the whole talk twice on a timer, and keep it under 4:55.
- [ ] Time the demo alone. If it runs over 1:30, cut the warning-line sentence from stop 1 (slide 7 covers it).
- [ ] Practice the failure path once: slide 3 → slide 4, then talk through the cards.
- [ ] Open the deck from the repo folder so the three chart files load, and check slides 6 to 8 show their charts.
- [ ] Check every spoken number against the slide. Say "about 66" for 65.6 and "54" for 54.0.
