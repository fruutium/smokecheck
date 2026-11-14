# SmokeCheck: finals Q&A prep

Sources: `metrics.json`, `predictions.csv`, notebook output, write-up, Decision Log. **(prep calc)** = computed for this doc from `predictions.csv` or a rerun of the notebook's models, not in the write-up, so say "we also checked". **Cost** = 5 × missed bad days + false alarms; lower is better. All numbers use scikit-learn 1.9.1, which the notebook pins.

## 30-second version
We forecast tomorrow's daily PM2.5 for six Midwest cities, so an athletic director knows the evening before whether practice should move indoors. We use only what's known that evening: monitor readings here and in five other cities, NOAA smoke maps, today's CAMS estimate and tomorrow's weather forecast. We average a Ridge regression and gradient-boosted trees, train on Aug 2022 to Dec 2024, and test once on all of 2025. Our average error is 19% lower than NOAA's official day-ahead forecast. For warnings, one missed bad day counts as 5 false alarms. Every forecast's warning line is the median cheapest line over 200 copies of 2022–24 resampled in whole weeks, so a tiny change in the data barely moves it. Our warnings cost 106, against NOAA's 123 at the plain 35 line. We still miss most days when smoke arrives overnight.

## 5 numbers to memorize
1. **2.58 vs 3.20**: our 2025 average error vs NOAA's (µg/m³, 2,190 city-days). 19% lower, no warning line involved.
2. **106 vs 123**: warning cost with lines set on 2022–24, us vs NOAA at the plain 35 line. Persistence 134, NOAA at its own line 166.
3. **102 / 106 / 118**: best possible 2025 cost in hindsight for us, persistence and NOAA. Ahead of NOAA, about even with persistence. Optimistic raw CAMS: 100.
4. **18 caught, 21 false alarms** at our line of 24.5. Always add NOAA at 35: 12 caught, 8 false alarms.
5. **6 of 21**: arrival days we caught, against 12 of 14 lingering days. Our weak spot.

## Questions

**1.**
- **Q:** How do you know it works and isn't just overfit?
- **Who answers:** Abhiddyu
- **A:** We scored all of 2025 once, after the final choices (Q8 has what we saw early). Average error: 2.58 for us, 3.20 for NOAA, 3.40 for "tomorrow equals today", 4.33 for the usual value for that month. It's lowest in all six cities, and on smoke days it's 8.63 against NOAA's 10.82. Warnings cost 106, against NOAA's 123 at 35.
- **If they push:** "Raw CAMS is about level with us, costing 107, and 100 in hindsight. But Open-Meteo keeps no true day-ahead CAMS archive, so its value partly sees the day's smoke."

**2.**
- **Q:** NOAA already publishes a forecast. Why would anyone use yours?
- **Who answers:** Aiden
- **A:** Our error is 19% lower, and our warnings cost 106 against NOAA's 123 at 35. NOAA rarely goes high enough on smoke days: on July 31, 2025 in Milwaukee it said 13.4 and the air measured 83.7, while we said 26.8, above our line: "move indoors". NOAA has fewer false alarms, so an athletic director could use both.
- **If they push:** "On arrival days we're both bad: 6 of 21 for us, 5 for NOAA at 35."

**3.**
- **Q:** NOAA's line of 52.5 looks tuned to make NOAA look bad.
- **Who answers:** Abhiddyu
- **A:** It came from the same rule on 2022–24 as everyone's line. That's why we also show NOAA at the plain 35 line, costing 123, and at its best line in hindsight, 25.5, costing 118. Both are worse than our 106, or 102 in hindsight.
- **If they push:** "Two caveats. NOAA's line was set mostly on its model from before the May 2024 upgrade, and its day covers 22 of EPA's 24 hours. And our cost is lower than NOAA's at every line up to 26.5 and tied at 27, but from 27.5 to about 46 NOAA's is lower at most lines." (prep calc)

**4.**
- **Q:** Your warning line changed during the weekend. Isn't that tuning on the test year?
- **Who answers:** Abhiddyu
- **A:** The old rule, take the single cheapest line on 2022–24, jumped from 24 to 29.5 when readings gained one decimal place (at most 0.005), because every line in between cost about the same. Honestly, we had already seen 2025 at both lines (18 caught and 22 false alarms, against 12 and 10). So we logged a new rule before computing it: the median cheapest line over 200 week-resampled copies. It gives 24.0 on old data and 24.5 on new, and 2025 was scored once.
- **If they push:** "The lesson: picking the single lowest point of a flat curve picks out noise."

**5.**
- **Q:** What breaks it?
- **Who answers:** Abhiddyu
- **A:** Arrival days, when today is clean and tomorrow is bad: we caught 6 of 21. On July 31 in Chicago we said 13.7, NOAA said 13.7, and the air measured 65.6, far above our range of 8.8 to 20.6. The day before, Minneapolis was already at 50.6 and NOAA had mapped a medium plume over Chicago, but the model leaned on Chicago's own clean reading.
- **If they push:** "36 of our 38 bad training days are from 2023, so it never learned to trust a smoky neighbour. When smoke lingers it works: on August 1 in Chicago we said 54.0, NOAA 8.7, and the air measured 45.5."

**6.**
- **Q:** Is tomorrow's weather leaking into your inputs?
- **Who answers:** Abhiddyu
- **A:** We had to train on near-real weather, because day-ahead forecasts aren't archived for 2022–2023. The 2025 test uses the forecast actually made the day before. Swapping in real weather moves error only from 2.58 to 2.57, with the same 18 caught and 21 false alarms.
- **If they push:** "Weather does matter: shuffling it on the held-out training years raises error by about 0.6, second only to this city's readings at about 1. So the tiny change means the day-ahead forecast is close to the real weather." (prep calc)

**7.**
- **Q:** Do your inputs, especially CAMS, really exist by the evening before?
- **Who answers:** Abhiddyu
- **A:** Tomorrow's raw CAMS doesn't, so we call that baseline optimistic: Open-Meteo's "previous day" CAMS values are empty for 2022–2025, and its history comes from runs that already see the smoke. Our model only uses today's CAMS. Two smaller gaps flatter us slightly: "today's reading" is the full-day average, though at 6 pm the last hours are missing, and NOAA's smoke maps use UTC days and can be finished late.
- **If they push:** "CAMS runs at 00Z and 12Z, so the runs covering today exist by the evening, but we didn't check the exact publication delay. Shuffling today's CAMS raises error by under 0.05 (prep calc), though dropping CAMS cut training arrival catches from 4 to 1 of 21. That's a hint, not proof."

**8.**
- **Q:** Did you ever look at 2025 while you were building?
- **Who answers:** Abhiddyu
- **A:** Yes, early, before training-only selection. An early commit scored the baselines on 2025 at a plain 35 line, and one scratch run tried tree models on 2025 with growing input sets, two losses, and warning at 35 vs 25 (error 2.1 to 3.5). That run is why the region and weather inputs were in our list from the start. The final choices (the Ridge-plus-trees average, absolute loss, the warning-line rule) came from training-year checks, though we'd seen 2025 at two old lines (Q4).
- **If they push:** "We disclose all of this. The clean fix is a fresh holdout year; Jan–May 2026 has partial EPA data and none for Minneapolis."

**9.**
- **Q:** Your training-years check trains on 2023 to predict 2022. Isn't that using the future?
- **Who answers:** Abhiddyu
- **A:** Yes. With only 2.4 years, training only forward leaves almost nothing, so we hid one whole year at a time. That's only for choices; the real test, 2025, comes after all training data.
- **If they push:** "It cost us too: with 2023 hidden, the other years have only 2 bad days."

**10.**
- **Q:** Why does one miss cost 5 false alarms? That number looks made up.
- **Who answers:** Aiden
- **A:** It's a judgement call, fixed before scoring our model on 2025 (we'd already seen the baselines at 35). Sending kids to run in smoke is much worse than an unneeded indoor practice, but if we cry wolf every week the athletic director stops listening.
- **If they push:** "At 3:1 our line would be 29.5, catching 12 with 10 false alarms. At 10:1 it would be 22.5, catching 19 with 25. We haven't asked a real athletic director yet." (prep calc)

**11.**
- **Q:** Why does each forecast get its own line? And why is yours 24.5, not 35?
- **Who answers:** Abhiddyu
- **A:** Every forecast runs low on bad days: on the 35 bad days, we, NOAA and CAMS under-forecast by 21 to 23 on average, and our median forecast was 25.1. One line of 35 would just punish whichever forecast runs lowest, so each gets the same rule on 2022–24. At 35 we'd catch only 9 of 35. (prep calc)
- **If they push:** "At 35 we'd have 5 false alarms; NOAA at 35 catches 12 with 8."

**12.**
- **Q:** Why average Ridge and trees, and why predict the change from today?
- **Who answers:** Abhiddyu
- **A:** Trees can't predict above values they've seen: trees on the PM2.5 level caught 1 of 38 bad training days. So our trees predict the change from today, and today plus a big change can be large. Ridge predicts the level, since a weighted sum can already go beyond anything it has seen.
- **If they push:** "Training-year error: Ridge alone 2.69, trees alone 2.51, the average 2.49."

**13.**
- **Q:** Why did the upwind smoke feature fail, and why not just add more years?
- **Who answers:** Abhiddyu
- **A:** The signal is real: upwind smoke came before 16 of 21 training arrival days, against 17% of ordinary days, but training error was 2.49 with or without it. Our guess: with 2023 hidden, too few bad days are left to learn from. Adding 2018 to mid-2022 brought only 7 bad days, 3 of them smoke; error fell a little but warning cost rose, so by a rule written down first we kept the current model and never scored the longer one on 2025.
- **If they push:** "Shuffling the smoke maps raises error by about 0.01 (prep calc), so the model barely uses them. More years was a weak test of the upwind idea."

**14.**
- **Q:** Why these six cities?
- **Who answers:** Abhiddyu
- **A:** We took the biggest Midwest metros with a full EPA record for 2022–2025 and the most 2025 days above 35: Milwaukee and Minneapolis 9 each, Madison and Detroit 6, Chicago 3, St. Louis 2. They run north to south, so we can see smoke move across the region; Chicago is the notebook's demo city because it has the most schools. Honestly, those counts included 2025: the model never trained on it, but the cities were picked partly for being smoky that year.
- **If they push:** "St. Louis is the southern city that rarely gets smoke. We skipped Duluth (15 bad days, but small), Grand Rapids and the Ohio cities to keep it to six."

**15.**
- **Q:** 21 false alarms against NOAA's 1. Isn't that worse for an athletic director?
- **Who answers:** Aiden
- **A:** NOAA's 1 comes at its own line, where it catches only 2 of 35. At 35 NOAA has 8 false alarms and catches 12, while we catch 18. Our 21 is under 4 per city per year, and 16 came the day after a bad day, when smoke cleared faster than expected (median reading 25.1). Honestly, in Chicago we caught 1 of 3 with 5 false alarms. (prep calc)
- **If they push:** "An athletic director who hates false alarms can raise our line. The cost is more misses."

**16.**
- **Q:** 35 bad days is tiny. Can you trust the catch counts?
- **Who answers:** Abhiddyu
- **A:** Not much. The 35 bad days fall on only 18 dates, 19 of them July 30 to August 5, so it's really a few smoke events. The steadier number is average error over 2,190 days, where we're best in every city. Against NOAA at 35, 11 bad days were caught only by us and 5 only by NOAA. (prep calc)
- **If they push:** "Those days aren't independent, so we don't claim a significance test."

**17.**
- **Q:** Does your forecast range mean anything on the days that matter?
- **Who answers:** Abhiddyu
- **A:** Each forecast gets an 80% range from the training years' misses, grouped by forecast level. In 2025 the measurement fell inside it on 79.6% of days, but only 37% of bad days and 62% of smoke days, because arrival days land above the range. On July 31 in Milwaukee it was 0 to 55, so on smoky-looking days the model does show it's unsure.
- **If they push:** "Before we fixed its rule, we tried 4 groupings on 2025. All gave 80–81% coverage, so that choice couldn't flatter it much."

**18.**
- **Q:** Who would actually use this, and what changes for them?
- **Who answers:** Aiden
- **A:** A Midwest high-school athletic director deciding the evening before. They get one call, "practice outside" or "move indoors", with the forecast and its range behind it. On July 31, 2025, it would have moved Milwaukee and Madison practices indoors (26.8 and 25.9) when NOAA said 13.4 and 15.6. It's a prototype, not health advice, and it forecasts the daily average, not practice hours.
- **If they push:** "We haven't tested it with a real athletic director yet. That's next."

**19.**
- **Q:** What would you do with another month?
- **Who answers:** Aiden
- **A:** Fix arrival days: try more years while keeping CAMS where it exists, since dropping CAMS hurt arrival catches. Forecast practice hours, 3–6 pm, not the daily average. Test it with a real athletic director, then score a fresh holdout year once.

**20.**
- **Q:** What did Claude do, and what did you do?
- **Who answers:** Aiden, then Abhiddyu
- **A:** Claude, through Claude Code, wrote most of the code (data scripts, notebook, Gradio app), ran the experiments, checked which forecast archives were truly day-ahead, and drafted the write-up and video script, which we edited. We chose the track and project, picked which improvements to try (upwind smoke, dropped, and the NOAA baseline), and read all the code. Ask us about any line.
- **If they push:** Be ready to walk through `add_features` (why everything is `shift(1)`), `fit` and `predict`, and `best_cut_off` (the 200 reshuffles) without notes.

## Notes
- **Rounding:** Chicago Jul 31 is 65.6 (EPA mean 65.648). Say "about 66" out loud.
- **Decision Log:** don't quote the 11:10 PM baselines (one 35 line for everyone) or 12:29 AM's "beats NOAA only up to about 25". The current curve gives 26.5.
