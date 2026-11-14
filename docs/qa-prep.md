# SmokeCheck: finals Q&A prep

Sources: `metrics.json`, `predictions.csv`, notebook output, write-up, Decision Log. **(prep calc)** = computed from `predictions.csv` for this doc and not in the write-up, so say "we also checked". **Cost** = 5 × missed bad days + false alarms, and lower is better. All numbers use scikit-learn 1.9.1, which the notebook's install cell pins.

## 30-second version
We forecast tomorrow's daily PM2.5 for six Midwest cities, so an athletic director knows the evening before whether practice should move indoors. Inputs are only what's known that evening: monitor readings here and in five other cities, NOAA smoke maps, today's CAMS estimate and tomorrow's weather forecast. We average a Ridge regression and gradient-boosted trees, train on Aug 2022 to Dec 2024, and test once on all of 2025. Our average error is 19% lower than NOAA's official day-ahead forecast. For the warning, one missed bad day counts as much as 5 false alarms. For every forecast, we set its warning line by reshuffling the 2022–24 days 200 times in whole weeks, finding the cheapest line each time, and taking the middle one, so a tiny change in the data can't move it. Our warnings cost 106, against NOAA's 123 at the plain 35 line. We still miss most days when smoke arrives overnight.

## 5 numbers to memorize
1. **2.58 vs 3.20**: our average error in 2025 vs NOAA's, in µg/m³ over 2,190 city-days. That's 19% lower, and no warning line is involved.
2. **106 vs 123**: warning cost with lines set on 2022–24, us vs NOAA at the plain 35 line. Persistence costs 134, and NOAA at its own line 166.
3. **102 / 106 / 118**: the best possible 2025 cost, picked with hindsight, for us, persistence and NOAA. That's a clear win over NOAA and about even with persistence. Optimistic raw CAMS reaches 100.
4. **18 caught, 21 false alarms** at our line of 24.5. Always add NOAA at 35: 12 caught, 8 false alarms.
5. **6 of 21**: arrival days we caught, against 12 of 14 lingering days. This is our weak spot.

## Questions

**1.**
- **Q:** How do you know it works and isn't just overfit?
- **Who answers:** Abhiddyu
- **A:** We scored all of 2025 once and never used it for choices. Our average error is 2.58, against 3.20 for NOAA, 3.40 for "tomorrow equals today" and 4.33 for the usual value for that month. It's lowest in all six cities, and on smoke days it's 8.63 against NOAA's 10.82. Our warnings cost 106, against NOAA's 123 at 35.
- **If they push:** "Raw CAMS is about the same as us, costing 107, and 100 with hindsight. But Open-Meteo keeps no true day-ahead CAMS archive, so its value partly sees the day's smoke."

**2.**
- **Q:** NOAA already publishes a forecast. Why would anyone use yours?
- **Who answers:** Aiden
- **A:** Our error is 19% lower, and our warnings cost 106 against NOAA's 123 at the plain 35 line. NOAA's forecast rarely goes high enough on smoke days. On July 31, 2025 in Milwaukee it said 13.4 and the air measured 83.7, while we said 26.8, above our line: "move indoors". NOAA has fewer false alarms, so an athletic director could use both.
- **If they push:** "We caught 18 of 35 with 21 false alarms; NOAA at 35 caught 12 with 8. On arrival days we're both bad: 6 of 21 for us, 5 for NOAA at 35."

**3.**
- **Q:** NOAA's line of 52.5 looks tuned to make NOAA look bad.
- **Who answers:** Abhiddyu
- **A:** It came from the same rule on 2022–24 as everyone's line. That's why we compare with NOAA at the plain 35 line, where it costs 123, and its best line with hindsight, about 25.5, costs 118. Both are worse than our 106, or our 102 with hindsight.
- **If they push:** "Two caveats. NOAA's line was tuned mostly on its model from before the May 2024 upgrade, and its day covers 22 of EPA's 24 hours. Also, our cost is lower than NOAA's at every line up to about 26.5, but at most lines from 27 to about 46 NOAA's is lower." (prep calc)

**4.**
- **Q:** Your warning line changed during the weekend. Isn't that tuning on the test year?
- **Who answers:** Abhiddyu
- **A:** For every forecast, we set its warning line by reshuffling the 2022–24 days 200 times in whole weeks, finding the cheapest line each time, and taking the middle one, so a tiny change in the data can't move it. The old rule, take the single cheapest line, jumped from 24 to 29.5 when readings gained one decimal place (at most 0.005), because every line from 24 to 29.5 cost about the same. Honestly, we had already seen 2025 at both lines (18 caught and 22 false alarms, against 12 and 10). We logged the new rule before computing it; it gives 24.0 on old data and 24.5 on new, and 2025 was scored once.
- **If they push:** "The lesson: picking the single lowest point of a flat curve picks out noise."

**5.**
- **Q:** What breaks it?
- **Who answers:** Abhiddyu
- **A:** Arrival days, when today is clean and tomorrow is bad. We caught 6 of 21 of those. On July 31 in Chicago we said 13.7, NOAA said 13.7, and the air measured 65.6, far above our range of 8.8 to 20.6. The day before, Minneapolis was already at 50.6 and NOAA had mapped a medium plume over Chicago, but the model leaned on Chicago's own clean reading.
- **If they push:** "36 of our 38 bad training days are from 2023, so it never learned to trust a smoky neighbour. When smoke lingers it works: on August 1 in Chicago we said 54.0, NOAA 8.7, and the air measured 45.5."

**6.**
- **Q:** Is tomorrow's weather leaking into your inputs?
- **Who answers:** Abhiddyu
- **A:** We had to train on near-real weather, because day-ahead forecasts aren't archived for 2022–2023. The 2025 test uses the forecast actually made the day before. Swapping in real weather moves error only from 2.58 to 2.57, with the same 18 caught and 21 false alarms.
- **If they push:** "Weather does matter: we checked by shuffling inputs on the held-out years, and the weather forecast raised error by 0.65, second only to this city's readings at 0.98. So the tiny change means the day-ahead forecast is close to the real weather."

**7.**
- **Q:** Do your inputs, especially CAMS, really exist by the evening before?
- **Who answers:** Abhiddyu
- **A:** Tomorrow's raw CAMS doesn't, so we call that baseline optimistic: Open-Meteo's "previous day" CAMS values are empty for 2022–2025, and its history comes from runs that already see the smoke. Our model only uses today's CAMS. Two smaller gaps: "today's reading" is the full-day average, but at 6 pm the last hours are missing, and NOAA's smoke maps use UTC days and can be finished late, so we're slightly flattered.
- **If they push:** "CAMS runs at 00Z and 12Z, so the runs covering today exist by the evening, but we didn't check the exact publication delay. Shuffling today's CAMS raises error by only 0.03, though dropping CAMS cut training arrival catches from 4 to 1 of 21. That's a hint, not proof."

**8.**
- **Q:** Did you ever look at 2025 while you were building?
- **Who answers:** Abhiddyu
- **A:** Yes, early, before training-only selection. An early commit scored the baselines on 2025 at a plain 35 line, and one scratch run tried tree models on 2025 with growing input sets, two losses, and warning at 35 vs 25 (error 2.1 to 3.5). That run is why the region and weather inputs were in our list from the start. The final choices (the Ridge-plus-trees average, absolute loss, the warning-line rule) came from training-year checks.
- **If they push:** "We disclose all of this. The clean fix is a fresh holdout year. We rejected Jan–May 2026 because its EPA data is partial and missing for Minneapolis."

**9.**
- **Q:** Your training-years check trains on 2023 to predict 2022. Isn't that using the future?
- **Who answers:** Abhiddyu
- **A:** Yes. With only 2.4 years, training only forward leaves almost nothing, so we hid one whole year at a time. That's only for choices; the real test, 2025, comes after all training data.
- **If they push:** "It cost us too: when 2023 is hidden, the other years have only 2 bad days to learn from."

**10.**
- **Q:** Why does one miss cost 5 false alarms? That number looks made up.
- **Who answers:** Aiden
- **A:** It's a judgement call. We fixed the 5:1 rule before scoring our model on 2025; we had already seen the baselines' 2025 numbers at a plain 35 line. Sending kids to run in smoke is much worse than an unneeded indoor practice, but if we cry wolf every week the athletic director stops listening.
- **If they push:** "At 3:1 our line would be 29.5, catching 12 with 10 false alarms. At 10:1 it would be 22.5, catching 19 with 25. We haven't asked a real athletic director yet; that's next." (prep calc)

**11.**
- **Q:** Why does each forecast get its own line? And why is yours 24.5, not 35?
- **Who answers:** Abhiddyu
- **A:** Every forecast runs low on bad days: on the 35 bad days, we, NOAA and CAMS under-forecast by 21 to 23 on average, and our median forecast on those days was 25.1. A single line of 35 would just punish whichever forecast runs lowest, so each one gets the same rule on 2022–24. At 35, we'd catch only 9 of 35. (prep calc)
- **If they push:** "At 35 we'd have 5 false alarms; NOAA at 35 catches 12 with 8."

**12.**
- **Q:** Why average Ridge and trees, and why predict the change from today?
- **Who answers:** Abhiddyu
- **A:** Trees can't predict above values they've seen: trees on the PM2.5 level caught 1 of 38 bad training days. So the trees predict the change from today, and today plus a big change can be large. Ridge predicts the level, since a weighted sum can already go beyond anything it has seen.
- **If they push:** "Training-year error: Ridge alone 2.69, trees alone 2.51, average 2.49, and trees alone had far more false alarms."

**13.**
- **Q:** Why did the upwind smoke feature fail, and why not just add more years?
- **Who answers:** Abhiddyu
- **A:** The signal is real: upwind smoke came before 16 of 21 training arrival days, against 17% of ordinary days, but training error was 2.49 with or without it. Our guess: with 2023 hidden, too few bad days are left to learn from. Adding 2018 to mid-2022 brought only 7 bad days, 3 of them smoke; error fell a little but warning cost rose, so by a rule written down first we kept the current model.
- **If they push:** "Shuffling the smoke maps raises error by 0.00, so the model barely uses smoke inputs. More years was a weak test of the upwind idea."

**14.**
- **Q:** Why these six cities?
- **Who answers:** Abhiddyu
- **A:** We took the biggest Midwest metros with a full EPA record for 2022–2025 and the most 2025 days above 35: Milwaukee and Minneapolis 9 each, Madison and Detroit 6, Chicago 3, St. Louis 2. They run north to south, so we can see smoke move across the region, and Chicago is the headline because it has the most schools. Honestly, those counts included 2025: the model never trained on it, but the cities were picked partly for being smoky that year.
- **If they push:** "St. Louis is the southern city that rarely gets smoke. We skipped Duluth (15 bad days, but small), Grand Rapids and the Ohio cities to keep it to six."

**15.**
- **Q:** 21 false alarms against NOAA's 1. Isn't that worse for an athletic director?
- **Who answers:** Aiden
- **A:** NOAA's 1 false alarm comes at its own line, where it catches only 2 of 35. At the plain 35 line NOAA has 8 false alarms and catches 12, while we catch 18. Our 21 is under 4 per city per year, and 16 came the day after a bad day, when smoke cleared faster than expected, with a median reading of 25.6. Honestly, in Chicago we caught 1 of 3 with 5 false alarms. (prep calc)
- **If they push:** "An athletic director who hates false alarms can raise our line. The cost is more misses."

**16.**
- **Q:** 35 bad days is tiny. Can you trust the catch counts?
- **Who answers:** Abhiddyu
- **A:** Not much. The 35 bad days fall on only 18 dates, and 19 of them were July 30 to August 5, so it's really a few smoke events. The steadier number is average error over 2,190 days, where we're best in every city. Against NOAA at 35, 11 bad days were caught only by us and 5 only by NOAA. (prep calc)
- **If they push:** "Those days aren't independent, so we don't claim a significance test."

**17.**
- **Q:** Does your forecast range mean anything on the days that matter?
- **Who answers:** Abhiddyu
- **A:** Each forecast gets an 80% range, built from the training years' misses and grouped by forecast level. In 2025 the measurement fell inside it on 79.6% of days, but only 37% of bad days and 62% of smoke days, because arrival days land above the range. On July 31 in Milwaukee the range was 0 to 55, so on smoky-looking days the model does show it's unsure.
- **If they push:** "Before we fixed its rule, we tried 4 ways of grouping on 2025. All four gave 80–81% coverage, so that choice couldn't flatter it much."

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

## Write-up mismatches (status)
- **The write-up on this branch still has the old cut-off numbers:** line 24, 18 caught, 22 false alarms, cost 107; NOAA at 45 (6, 1, 146); CAMS at 29.5 (18, 21, 106); Milwaukee 27.6, Chicago 13.9 and 54.8; NOAA 4 arrival and 2 lingering. The current data gives 24.5 (18, 21, 106); NOAA at 52.5 (2, 1, 166); CAMS at 30 (17, 17, 107); 26.8, 13.7 and 54.0; NOAA 2 and 0. It also doesn't describe the new line rule.
- **More seasons:** the write-up's "next" step is more smoke seasons (2018–2021). The notebook already tried 2018–2024 and dropped it by a pre-written rule.
- **Rounding:** Chicago Jul 31 is 65.6 (EPA mean 65.648). Say "about 66" out loud.
- **Decision Log:** the 11:10 PM baseline numbers (one 35 line for everyone) are superseded. Don't quote them.
