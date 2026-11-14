# SmokeCheck: finals Q&A prep

Sources: `metrics.json`, `predictions.csv`, notebook output, write-up, Decision Log. **(prep calc)** = computed from `predictions.csv` for this doc, not in the write-up; say "we also checked". **(recheck after more-seasons)** = changes if retrained with 2018–2021.

## 30-second version
We forecast tomorrow's daily PM2.5 for six Midwest cities, so an athletic director knows the evening before whether practice should move indoors. Inputs are only what's known that evening: today's monitor readings in this city and the other five, NOAA's smoke maps, today's CAMS estimate and tomorrow's weather forecast. Two models, Ridge and gradient-boosted trees, are averaged. We trained on Aug 2022 to Dec 2024 and tested once on all of 2025. Against NOAA's official day-ahead forecast, our average error is 19% lower and we warned on 18 of 35 bad days against NOAA's 6. We pay for that with 22 false alarms against NOAA's 1, and we still miss most days when smoke arrives overnight.

## 5 numbers to memorize (recheck after more-seasons)
1. **2.59 vs 3.20**: our average error in 2025 vs NOAA's, in µg/m³ over 2,190 city-days.
2. **18 vs 6 of 35**: bad days (above 35) each one warned on.
3. **22 vs 1**: false alarms. This is the price.
4. **24**: our warning line. It was set on 2022–2024 with one miss costing as much as 5 false alarms.
5. **6 of 21**: arrival days we caught, against 12 of 14 lingering days. This is our weak spot.

## Questions

**1.**
- **Q:** How do you know it works and isn't just overfit?
- **Who answers:** Abhiddyu
- **A:** We scored all of 2025 once, and never used it for choices. Our average error is 2.59, against 3.20 for NOAA, 3.40 for "tomorrow equals today" and 4.33 for the usual value for that month. It's lowest in all six cities, and on smoke days it's 8.63 against NOAA's 10.82. (recheck after more-seasons)
- **If they push:** "We tie the raw CAMS archive on catches, 18 and 18, and that archive partly sees the target day."

**2.**
- **Q:** NOAA already publishes a forecast. Why would anyone use yours?
- **Who answers:** Aiden
- **A:** NOAA's forecast rarely goes high enough on smoke days. On July 31, 2025 in Milwaukee it said 13.4; the air measured 83.7. We said 27.6, above our line: "move indoors". On days when smoke stayed for a second day, we warned on 12 of 14 and NOAA on 2. NOAA is far better at not crying wolf, so an athletic director could use both. (recheck after more-seasons)
- **If they push:** "When smoke arrives overnight we're both bad: we caught 6 of 21 of those days and NOAA caught 4."

**3.**
- **Q:** You gave NOAA a warning line of 45. Isn't that rigged against NOAA?
- **Who answers:** Abhiddyu
- **A:** Every forecast got the same rule: try lines from 10 to 45 on 2022–2024, keep the cheapest. NOAA's cost kept falling up to 45, our cap, because in training its forecasts above 35 were mostly false alarms (9 catches, 56 false alarms). We also gave NOAA its best possible line chosen with hindsight on 2025 itself. That line, 25.5, still costs 118 against our 107. Hindsight check only, never used for a choice. (prep calc; recheck after more-seasons)
- **If they push:** "Caveats: NOAA's line was tuned mostly on its pre-May-2024 model, and its day covers 22 of EPA's 24 hours. And at a plain 35 line NOAA catches 12 with 8 false alarms, beating our 9 with 6. We win at the lower line, not every line."

**4.**
- **Q:** What breaks it?
- **Who answers:** Abhiddyu
- **A:** Arrival days, when today is clean and tomorrow is bad. We caught 6 of 21 of those. On July 31 in Chicago we said 13.9, NOAA said 13.7, and the air measured 65.65. The day before, Chicago was 12.4, but Minneapolis was already at 50.6 and NOAA had mapped a medium plume over Chicago. The model still leaned on Chicago's own clean reading. (recheck after more-seasons)
- **If they push:** "36 of our 38 bad training days are from 2023, so it never learned to trust a smoky neighbour. More seasons is the fix."

**5.**
- **Q:** Is tomorrow's weather leaking into your inputs?
- **Who answers:** Abhiddyu
- **A:** We had to train on near-real weather, because day-ahead weather forecasts aren't archived for 2022–2023. The 2025 test, though, uses the weather forecast actually made the day before (Open-Meteo Previous Runs). Swapping in the real weather changes our error from 2.59 to 2.58, and we still catch 18 either way, so weather isn't carrying the answer.
- **If they push:** "That also tells us the model leans far more on today's readings than on the weather. [ask Abhiddyu: did we ever measure how much each input matters?]"

**6.**
- **Q:** CAMS is a model run with hindsight. Doesn't that leak?
- **Who answers:** Abhiddyu
- **A:** Yes for raw CAMS, which is why we label it "optimistic". Open-Meteo's "previous day" CAMS values are empty for 2022–2025, so its history is stitched from short-range runs that already see the smoke. Our model never uses tomorrow's CAMS, only today's value and how far off today's value was from the monitors.
- **If they push:** "Is today's CAMS really out by the evening? [ask Abhiddyu: when is the day's CAMS value published?]"

**7.**
- **Q:** Did you ever look at 2025 while you were building?
- **Who answers:** Abhiddyu
- **A:** Once, early on. A scratch run scored several feature sets on 2025, with error around 2.5–2.9 and 16 of 35 caught, before we had fixed our process. After that, every choice was made on the training years only, and 2025 was scored once at the end. We disclose this in the write-up. We can't un-see it, so the honest fix is a fresh holdout year.
- **If they push:** "[ask Abhiddyu: which feature sets the scratch run compared, and whether the final set was one of them.] We rejected Jan–May 2026 as a holdout because the EPA data is partial and missing for Minneapolis."

**8.**
- **Q:** Do your inputs really exist by the evening before?
- **Who answers:** Abhiddyu
- **A:** Mostly. Two gaps: "today's reading" is the full-day average, but at 6 pm the last hours are missing, and NOAA's smoke maps use UTC days and can be finished late. Both flatter us slightly.
- **If they push:** "Fix: use readings up to about 5 pm. We haven't measured the effect."

**9.**
- **Q:** Your training-years check trains on 2023 to predict 2022. Isn't that using the future?
- **Who answers:** Abhiddyu
- **A:** Yes. With only 2.4 years, training only forward leaves almost nothing before 2023, so we hid one whole year at a time. That check is only for choices; the real test, 2025, comes strictly after all training data.
- **If they push:** "It cost us too: when 2023 is hidden, the other years have only 2 bad days to learn from."

**10.**
- **Q:** Why does one miss cost 5 false alarms? That number looks made up.
- **Who answers:** Aiden
- **A:** It's a judgement call, fixed before we saw any results. Sending kids to run in smoke is much worse than an unneeded indoor practice, but if we cry wolf every week the athletic director stops listening. We also checked how sensitive it is. At 3:1 our line would be 28.5, catching 12 with 11 false alarms. At 10:1 it would be 22.5, catching 19 with 27. (prep calc; recheck after more-seasons)
- **If they push:** "We didn't ask a real athletic director. That's the first thing we'd do next."

**11.**
- **Q:** Why does each forecaster get its own line? And why is yours 24 and not 35?
- **Who answers:** Abhiddyu
- **A:** Every forecast runs low on bad days. On the 35 bad days, we, NOAA and CAMS all under-forecast by about 21–23 on average, and our median forecast on those days was 24.6. A single line of 35 would just punish whichever forecast runs lowest, so each one gets the same rule, tuned on 2022–2024. At 35, our 2025 result would be 9 catches and 6 false alarms. (prep calc; recheck after more-seasons)
- **If they push:** "On the training years, 24 costs 111 and 35 costs 127, so 24 was chosen before 2025."

**12.**
- **Q:** Why average Ridge and trees, and why predict the change from today?
- **Who answers:** Abhiddyu
- **A:** Trees can't predict above values they've seen: trees on the PM2.5 level had error 2.74 but caught 1 of 38 bad training days. So the trees predict the change from today, and today plus a big change can be large. Ridge predicts the level, since a weighted sum can already go beyond anything seen. Averaging pairs one that extrapolates with one that catches curved patterns. (recheck after more-seasons)
- **If they push:** "Ridge has today's reading as an input, so for Ridge, level or change is nearly the same model. [ask Abhiddyu: Ridge-alone and trees-alone numbers.]"

**13.**
- **Q:** Why did the upwind smoke feature fail if the signal is real?
- **Who answers:** Abhiddyu
- **A:** The signal is real: smoke 300–900 km upwind came before 16 of the 21 training arrival days, against 17% of ordinary days. But the training-years error was 2.49 with or without it. Our best guess is that when 2023 is hidden, only 2 bad days are left to learn from. We never scored it on 2025.
- **If they push:** "Tiny changes moved warning counts by a few days, so we wouldn't adopt it on that noise."

**14.**
- **Q:** Why these six cities?
- **Who answers:** Abhiddyu
- **A:** Chicago, our headline city, has only 3 bad days in 2025, which is too few to measure anything. Six metros give 35. Each city's target is the average of all its EPA monitors, and the other cities' readings act as an early signal, since smoke drifts across the Midwest.
- **If they push:** "[ask Abhiddyu: why these six specifically.] St. Louis is the weak spot, with only 2 bad test days."

**15.**
- **Q:** 22 false alarms against NOAA's 1. Isn't that worse for an athletic director?
- **Who answers:** Aiden
- **A:** It's under 4 per city per year, 21 of 22 in June–August. 16 came the day after a bad day, when smoke cleared faster than expected, and the median reading on those days was still 25. NOAA's 1 false alarm came with 29 missed bad days. Honestly, in Chicago we caught 1 of 3 with 6 false alarms. (prep calc; recheck after more-seasons)
- **If they push:** "Under our 5:1 rule we cost 107 and NOAA costs 146. An athletic director who hates false alarms can raise the line."

**16.**
- **Q:** 35 bad days is tiny. Can you trust the catch counts?
- **Who answers:** Abhiddyu
- **A:** Not much. The 35 bad days fall on only 18 dates, 19 of them July 30 to August 5: really a few smoke events. The steadier number is average error over 2,190 days, where we're best in every city. Day by day, 17 bad days were caught only by us and 5 only by NOAA. (prep calc; recheck after more-seasons)
- **If they push:** "Those days aren't independent, so we don't claim a significance test. More seasons is the fix."

**17.**
- **Q:** Who would actually use this, and what changes for them?
- **Who answers:** Aiden
- **A:** A Midwest high-school athletic director deciding the evening before. They get one call, "practice outside" or "move indoors", with the number behind it. Across 2025 it warned on three times as many bad days as NOAA's forecast, 18 against 6. It's a prototype, not health advice, and it forecasts the daily average, not practice hours.
- **If they push:** "We haven't tested it with a real athletic director yet. That's next."

**18.**
- **Q:** What would you do with another month?
- **Who answers:** Aiden
- **A:** Train on 2018–2021 smoke seasons (EPA and NOAA's archive) so the model has enough events to use the upwind signal on arrival days. Forecast practice hours, 3–6 pm, not the daily average. Test with a real athletic director, then score a fresh holdout year once.

**19.**
- **Q:** What did Claude do, and what did you do?
- **Who answers:** Aiden, then Abhiddyu
- **A:** Claude, through Claude Code, wrote most of the code (data scripts, the model and evaluation notebook, the Gradio app), ran the experiments, checked which forecast archives were truly day-ahead, and drafted the write-up and video script, which we edited. We chose the track and project, picked which improvements to try (the upwind feature, which we dropped, and the NOAA baseline), and read all the code. Ask us about any line.
- **If they push:** Be ready to walk through `add_features` (why everything is `shift(1)`), `fit` and `predict`, and `best_cut_off` without notes.

## Write-up mismatches (status)
- Fixed in the write-up: Ridge predicts the level and the trees predict the change; 7,476 city-days; the upwind reason is now "our guess".
- Rounding: Chicago Jul 31 is 65.65 in the data. Say "about 66" out loud; the write-up and app show 65.7.
- The Decision Log's 11:10 PM baseline numbers (one 35 line for everyone) are superseded. Don't quote them.
