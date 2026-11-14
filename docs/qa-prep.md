# SmokeCheck: finals Q&A prep

Sources: `metrics.json`, `predictions.csv`, notebook output, write-up, Decision Log. **(prep calc)** = computed for this doc from `predictions.csv` and not in the write-up, so say "we also checked". **Cost** = 5 × missed bad days + false alarms; lower is better. All numbers use scikit-learn 1.9.1, which the notebook pins.

## 30-second version
SmokeCheck forecasts tomorrow's daily PM2.5 for six Midwest cities, so a high-school athletic director knows the evening before whether practice should move indoors. It averages a Ridge regression and gradient-boosted trees. The inputs are all known by about 8 PM: monitor readings here, in the other five cities and in 14 more metros, this afternoon's reading, NOAA's own forecast for tomorrow, smoke maps, CAMS and the weather forecast. We train on Aug 2022 to Dec 2024 and test on 2025. The forecast is clearly more accurate than NOAA's official one: 26% lower error, 2.36 against 3.20, in every resample and every city. But its move-indoors warnings, at the line the training years gave it, were worse than just reading NOAA at 35 (cost 127 against 123), and it caught none of the 21 days when smoke first arrived. With only one big smoke event in training, the warning line can't be set reliably. That's the next thing to fix. The app also shows tonight's real forecast from live data, which hasn't been scored yet.

## 5 numbers to memorize
1. **2.36 vs 3.20**: our 2025 average error vs NOAA's, 26% lower. The gap is 0.83 (95% range 0.55–1.17), and we're better in all 1,000 week resamples and in every city. Lead with this.
2. **127 vs 123**: our warning cost at our line vs NOAA at the plain 35 line. We're worse, and ahead in only 42% of resamples. Against persistence (134) we're ahead in 93%.
3. **0 of 21**: arrival days caught, against 11 of 14 lingering days.
4. **27 to 32**: where our warning line really sits. On 2025 that range costs 117 to 127.
5. **2.58 → 2.36, 106 → 127**: our last model change. It made a better forecast with worse warnings, and we adopted it by a rule written down first.

## Questions

**1.**
- **Q:** How do you know it works?
- **Who answers:** Abhiddyu
- **A:** As a forecast, it clearly does. Average error is 2.36, against 3.20 for NOAA, 3.40 for "tomorrow equals today" and 4.33 for the usual value for that month. It's lowest in all six cities, and on smoke days it's 8.09 against NOAA's 10.82. As a warning it doesn't yet beat NOAA: cost 127, against NOAA's 123 at 35.
- **If they push:** "Raw CAMS costs 107 at its line, but Open-Meteo keeps no true day-ahead CAMS archive, so its value partly sees the day's smoke."

**2.**
- **Q:** NOAA already publishes a forecast. Why would anyone use yours?
- **Who answers:** Aiden
- **A:** We don't replace NOAA, we build on it: NOAA's forecast for tomorrow is one of our inputs, and our model learns how far to trust it next to the local readings. That cuts the error by 26%. On July 31 in Minneapolis, NOAA said 18.7, we said 41.3 ("move indoors"), and the air measured 69.1. Honestly, though, our warnings overall cost slightly more than reading NOAA at 35.
- **If they push:** "At their own lines, we caught 11 of 35 with 7 false alarms. NOAA at 35 caught 12 with 8. Day by day, 6 bad days were caught only by us, 7 only by NOAA, and 5 by both. All 7 of our false alarms came the day after a bad day." (prep calc)

**3.**
- **Q:** NOAA's own line of 52.5 looks tuned to make NOAA look bad.
- **Who answers:** Abhiddyu
- **A:** It came from the same rule on 2022–24 as everyone's. That's why our headline uses NOAA at the plain 35 line, where NOAA beats us, 123 to 127. Without picking any line, we're cheaper than NOAA at 71 of 101 lines. NOAA is cheaper at most lines from 28.5 to 43, including 35. (prep calc)
- **If they push:** "With hindsight, the best possible 2025 costs are 92 for us, 100 for CAMS, 106 for persistence and 118 for NOAA. That describes 2025 only, and 17.5, where our 92 comes from, is not our line."

**4.**
- **Q:** Your new model warns worse than the old one. Why adopt it?
- **Who answers:** Abhiddyu
- **A:** We wrote the rule down and committed it before building the three new inputs. Pick the variant with the lowest training-year error, and adopt it only if that error is at least 0.05 below 2.49 and its warning cost is at most 5 above 117. The winner had error 2.22 and cost 112, so we adopted it, and we ran 2025 only for that model. On 2025 it was better as a forecast (2.58 → 2.36) and worse as a warning (106 → 127), and we show both rows.
- **If they push:** "Picking the old model after seeing 2025 would be choosing on the test year. Most of the gain is from NOAA's forecast: shuffling it raises training error by 0.70."

**5.**
- **Q:** How did you set your warning line, and how stable is it?
- **Who answers:** Abhiddyu
- **A:** For every forecast, we reshuffle the 2022–24 days 200 times in whole weeks, find the cheapest line each time, and take the middle one. We set the line by a rule fixed before computing it, but the training years can't pin it down: it's somewhere between about 27 and 32. On 2025, a line of 27 would cost 117 and 32 costs 127. That's a range, not a choice.
- **If they push:** "With other random seeds, the line is 27–27.5 about half the time and 31.5–32 about 40%; our fixed seed 0 gives 32. An earlier, simpler rule jumped from 24 to 29.5 after a 0.005 rounding change, which is why we switched."
- **If they ask "why not just 35?":** "Every forecast runs low on bad days: we, NOAA and CAMS under-forecast them by 21 to 23 on average. One line of 35 would punish whichever forecast runs lowest, so each gets the same rule on 2022–24. At 35 we'd catch 9 of 35 with 5 false alarms." (prep calc)

**6.**
- **Q:** What breaks it?
- **Who answers:** Abhiddyu
- **A:** Arrival days, when today is clean and tomorrow is bad: we caught 0 of 21 (NOAA 2, the optimistic CAMS archive 11). On July 31 we said 15.3 for Chicago, where the air measured 65.6, and 28.1 for Milwaukee, where it measured 83.7. Both were below our line. The model leans on today's readings, which are still clean the day before smoke arrives.
- **If they push:** "When smoke lingers it works: we caught 11 of 14. On August 1 in Chicago we said 51.8, NOAA 8.7, and the air measured 45.5."

**7.**
- **Q:** Why is the afternoon reading fair?
- **Who answers:** Abhiddyu
- **A:** It's this city's average from 2 to 7 PM standard time, which is 3 to 8 PM in summer, so it's known by 8 PM. The call is made after that. It adds little: shuffling it raises training error by only 0.06.
- **If they push:** "The test uses EPA's checked archive. The live Tomorrow screen uses AirNow's feed, which is preliminary. On the 6 days of 2025 we compared, 35 of 36 city-days agreed within 1.5."

**8.**
- **Q:** Is anything leaking: weather, CAMS, NOAA's forecast?
- **Who answers:** Abhiddyu
- **A:** The weather isn't: the 2025 test uses the forecast actually made the day before, and swapping in real weather moves error only from 2.36 to 2.35. NOAA's forecast comes from its 6 AM Central run, published around noon the day before. Raw CAMS does partly leak, which is why we call it optimistic, and our model only uses today's CAMS. Two small gaps flatter us: "today" is a full-day average, and smoke maps use UTC days.
- **If they push:** "NOAA upgraded its model in May 2024, so most training rows have the older forecast. Our model learned how far to trust a forecast that has since changed."

**9.**
- **Q:** Did you ever look at 2025 while you were building?
- **Who answers:** Abhiddyu
- **A:** Yes, and the notebook's section 10 lists all 8 times. They include an early scratch run, scoring the baselines at 35 before fixing the 5:1 rule, seeing our model at two old lines, and picking the cities knowing 2025's smoky-day counts. We made NOAA our main comparison after scoring our model on 2025, and pinned scikit-learn 1.9.1 after seeing 17 caught instead of 18. Our last model change came after all of those, so 2025 isn't a perfectly untouched test.
- **If they push:** "Our training-year check hides one year at a time, so it sometimes trains on later years; that's only for choices. The clean fix is a fresh holdout year."

**10.**
- **Q:** Why does one miss cost 5 false alarms?
- **Who answers:** Aiden
- **A:** It's a judgement call. We fixed the 5:1 rule before scoring our model on 2025; we had already seen the baselines' 2025 numbers at a plain 35 line. Sending kids to run in smoke is much worse than an unneeded indoor practice, but if we cry wolf every week the athletic director stops listening.
- **If they push:** "We haven't asked a real athletic director yet. That's next."

**11.**
- **Q:** Why average Ridge and trees, and why predict the change from today?
- **Who answers:** Abhiddyu
- **A:** Trees can't predict above values they've seen: trees on the PM2.5 level caught 1 of 38 bad training days. So our trees predict the change from today, and today plus a big change can be large. Ridge predicts the level, since a weighted sum can already go beyond anything it has seen.
- **If they push:** "On the earlier model, training-year error was 2.69 for Ridge alone, 2.51 for trees alone and 2.49 for the average."

**12.**
- **Q:** Why did upwind smoke fail, and why not just add more years?
- **Who answers:** Abhiddyu
- **A:** Upwind smoke came before 16 of 21 training arrival days, against 17% of ordinary days, but training error was 2.49 with or without it. Adding 2018 to mid-2022 brought only 7 bad days, 3 of them smoke. Error fell (2.38 vs 2.49) but warning cost rose (115 vs 112), so by a rule written down first we kept the shorter history.
- **If they push:** "Shuffling the smoke maps raises error by 0.00, so the model barely uses smoke inputs."

**13.**
- **Q:** Why these six cities?
- **Who answers:** Abhiddyu
- **A:** We took the biggest Midwest metros with a full EPA record for 2022–2025 and the most 2025 days above 35: Milwaukee and Minneapolis 9 each, Madison and Detroit 6, Chicago 3, St. Louis 2. They run north to south, so smoke can be seen moving across the region. Honestly, those counts included 2025: the model never trained on it, but the cities were picked partly for being smoky that year.
- **If they push:** "Chicago has the most schools. Duluth, with 15 bad days, is now only in the input ring; adding it as a target is our next step."

**14.**
- **Q:** How sure are you, with only 35 bad days?
- **Who answers:** Abhiddyu
- **A:** On error, very sure. Resampling 2025's weeks 1,000 times, our gap is 0.83 to NOAA (95% range 0.55 to 1.17) and 1.05 to persistence (0.90 to 1.23), and we're better in every resample. On warnings, not at all: we're ahead of NOAA at 35 in only 42% of resamples, and of persistence in 93%. The 35 bad days fall on only 18 dates, so it's really a few smoke events.
- **If they push:** "We resample whole weeks with all six cities together, because smoke hits several cities at once."

**15.**
- **Q:** Why did you remove the uncertainty range from the app?
- **Who answers:** Abhiddyu
- **A:** Because it promised more than it gave. It was built to hold the measurement 8 days out of 10, and over all of 2025 it held 78.9%. But on bad days, the ones that matter, it held only 31%: in Chicago on July 31 it was 10.1 to 21.0, and the air measured 65.6. A coach would read that as "safe". The notebook still reports it, in section 7.
- **If they push:** "On smoke days it held 65%. A few ways of grouping were tried on 2025 before the rule was fixed; that's one of the 8 looks."

**16.**
- **Q:** Is the Tomorrow screen a real forecast? Where does the data come from and how fresh is it?
- **Who answers:** Aiden
- **A:** Yes. It's the model we tested, run on today's public data: AirNow's hourly monitor readings, NOAA's forecast and smoke map, and Open-Meteo for CAMS and tomorrow's weather. The app runs it by itself when the saved forecast is old, and the screen says when it was made. The 2 to 7 PM reading is complete about 8 PM Central. Before that it uses the day's readings so far and redoes the forecast every 30 minutes.
- **If they push:** "A run takes about a minute the first time, then about 15 seconds. If it fails, say with no internet, the page keeps the last forecast, says 'Couldn't update', and retries after 5 minutes."

**17.**
- **Q:** How do you know the live forecast is as good as your 2025 test?
- **Who answers:** Abhiddyu
- **A:** We don't yet. Live mode hasn't been scored, so we have no accuracy number for it. It's the same model and the same line of 32, frozen as tested, and the script stops unless it first reproduces our 2025 forecasts. The input is what differs: AirNow's preliminary readings instead of EPA's final archive, and before about 8 PM today's readings are only partial.
- **If they push:** "We checked our AirNow averages against EPA's archive on 6 days of 2025: 35 of 36 city-days were within 1.5. The exception was Minneapolis on July 30, 3.3 higher: AirNow has only the continuous monitors, and EPA also averages in filter samples that read lower that day. That checks the input, not the forecast."

**18.**
- **Q:** How does the page work?
- **Who answers:** Aiden
- **A:** It's one HTML file and a small Python server, FastAPI. The browser asks Python for JSON: tomorrow's forecast, one day of the 2025 test run, or the results table. Python answers with the same functions that make the calls, so the page never makes a forecast or a call itself. It only draws. One number, the PM2.5 forecast, sets the sky: clear dusk blue when the air is clean, orange-brown haze on a smoke day.
- **If they push:** "A function called `haze` turns the forecast into a number from 0 to 1: 0 at a PM2.5 of 4 or less, 0.5 at the warning line, 1 at 60 or more. The CSS mixes the sky's colours from that number."

**19.**
- **Q:** Did you write the front end yourselves? What is from a library?
- **Who answers:** Aiden
- **A:** Claude built it with us: it made several mockups, we chose between them, and it built the page from our pick. It's plain HTML, CSS and JavaScript in one file, no React. One library, GSAP, runs the motion. The fonts, Big Shoulders Display and Schibsted Grotesk, come from Google Fonts. Three effects are based on React Bits and rebuilt in plain JavaScript: letters that blur in, a light that follows the pointer, and the drifting smoke bands. The rest is hand-written, and we've read all of it.
- **If they push:** "React Bits' Aurora uses a WebGL shader; ours is two sine waves on a tiny canvas that CSS stretches and blurs. If GSAP doesn't load, or someone asks for less motion, the page sets the final values straight away."

**20.**
- **Q:** Who would actually use this, and what changes for them?
- **Who answers:** Aiden
- **A:** A Midwest high-school athletic director opens the Tomorrow screen after 8 PM and gets one call for their city, "OK to practice outside" or "move practice indoors", with the smoke forecast under it. Today the forecast part is the improvement: it's closer to what actually happens than NOAA's. The alarm isn't good enough yet: 11 of 35 bad days caught, slightly worse than reading NOAA at 35, and it misses smoke arriving overnight. It's a prototype, not health advice, and it forecasts the daily average, not practice hours.
- **If they push:** "We haven't tested it with a real athletic director yet."

**21.**
- **Q:** What would you do with another month?
- **Who answers:** Aiden
- **A:** Set the warning line on more smoke events, for example by adding smoky cities such as Duluth as targets, so it isn't decided by one 2023 event. Then work on arrival days, test it with a real athletic director, and score a fresh holdout year we haven't looked at. We'd also save every evening's live forecast and score it against what was measured.

**22.**
- **Q:** What did Claude do, and what did you do?
- **Who answers:** Aiden, then Abhiddyu
- **A:** Claude, through Claude Code, wrote most of the code (data scripts, notebook, the web app and its page design, built from mockups we chose between), ran the experiments, checked which forecast archives were truly day-ahead, and drafted the write-up and video script, which we edited. We chose the track and project, picked which improvements to try (upwind smoke, dropped; the NOAA baseline; the three new inputs), and read all the code. Ask us about any line.
- **If they push:** Be ready to walk through `add_features` (why everything is `shift(1)`, and why NOAA's forecast isn't shifted), `fit` and `predict`, and `best_cut_off` without notes. For the page: `live_view` in `app/app.py` and `haze` in `app/index.html`.

## Notes
- **Live mode has no accuracy number.** Never give one. Say "it hasn't been scored" and give the AirNow check: 35 of 36 city-days within 1.5.
- **Rounding:** Chicago Jul 31 is 65.6 (EPA mean 65.648). Say "about 66" out loud.
- **Decision Log:** don't quote the 11:10 PM baselines (one 35 line for everyone) or older model numbers without saying "earlier model".
