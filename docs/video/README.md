# Video assets (demo voice-over kit)

The script is `docs/video-script.md`. Everything here was captured from the real app (`app/app.py` serving `app/index.html`) in a 1280×800 browser window on Nov 14, 2026.

## The produced video (what we submit)
The video we submit is built in `../video-project/` (next to this repo, not inside it, because its recordings and renders are large). It is 1:58.5, 1920×1080, 30 frames a second, H.264.
It shows a recording of the real app inside a window, with zooms and highlights on the numbers, between an animated opening, an animated "Does it work?" scene and a closing card. Captions and quiet music are part of the picture. We record the narration ourselves and mix it in. No AI voice.

| File in `../video-project/` | What it is |
|---|---|
| `renders/smokecheck-demo-music-only.mp4` | The whole video with captions and music, no voice. Read along with this |
| `renders/smokecheck-demo-picture.mp4` | The same picture with no sound, for the final mix |
| `assets/music/bed.wav` | The music, cut to length |
| `mix.sh` | Puts a narration recording on the video: `./mix.sh narration.m4a` writes `renders/smokecheck-demo-final.mp4` |
| `RECORDING-GUIDE.md`, `cue-sheet.md` | The lines, when each one starts, how to record, and how to change scene lengths |
| `CREDITS.md` | Music, fonts and tools to cite |

How it is made, in order:
1. **Record the app.** `capture/capture-app.mjs` is this folder's `capture.mjs` with two changes: it records at twice the pixels (2560×1600, so zooms stay sharp), in one take with a long hold after every click, and it writes `capture/meta.json` with the second of each click and the position of each number on the page. Same honesty notes as below: the cursor is drawn by the script and the city picker is set by the script. Start the app, then `APP=http://localhost:7863 node capture/capture-app.mjs`.
2. **Build the page.** The video is one HTML page, `index.html`, animated with GSAP. `node build.mjs` writes it from `timing.json` (how long each scene is), `capture/meta.json` (where to cut the recording, where to zoom) and the narration from `docs/video-script.md`. Captions are timed at 150 words a minute. The build stops if a scene is too short for its words, if the video would pass 2:00, or if the numbers in the recording differ from the script's.
3. **Render.** HyperFrames (`npx hyperframes render --quality high --output renders/smokecheck-demo-music-only.mp4`) opens the page in headless Chrome, draws all 3,555 frames and encodes them with the music. About five minutes.
4. **Strip the sound** for the mix: `ffmpeg -i renders/smokecheck-demo-music-only.mp4 -an -c:v copy renders/smokecheck-demo-picture.mp4`.
5. **Mix the voice.** `./mix.sh narration.m4a` levels the voice to -16 LUFS, plays the music 8 dB quieter and pushes it down further whenever the voice is speaking (ffmpeg `sidechaincompress`), and copies the picture untouched. A few seconds.

The music is "Deliberate Thought" by Kevin MacLeod (incompetech.com), Creative Commons Attribution 4.0. It must be credited wherever the video is posted.

The rest of this page is the older kit: stills and a plain silent screen recording. It is the backup if the produced video cannot be used.

## Files
| File | What it is |
|---|---|
| `01-tomorrow-live.png` | **Tomorrow** view, Minneapolis, as it was on Sat Nov 14: "Practice on Sunday, November 15", "OK TO PRACTICE OUTSIDE", smoke forecast 8.7, indoors above 32, "Forecast made Saturday at 1:35 PM". Live data, so the app will show other numbers on other days |
| `02-minneapolis-0731.png` | **2025 test run**, Minneapolis, Thursday, July 31, 2025: "MOVE PRACTICE INDOORS", smoke forecast 41.3, "RIGHT CALL", measured 69.1, NOAA's forecast 18.7 |
| `03-chicago-0731.png` | Chicago, same day: "OK TO PRACTICE OUTSIDE", smoke forecast 15.3, "MISSED A BAD DAY", measured 65.6, NOAA's forecast 13.7 |
| `04-chicago-0801.png` | Chicago, Friday, August 1, 2025: "MOVE PRACTICE INDOORS", smoke forecast 51.8, "RIGHT CALL", measured 45.5, NOAA's forecast 8.7 |
| `05-does-it-work.png` | **Does it work?** view: "26% LOWER ERROR THAN NOAA'S OFFICIAL FORECAST.", "Its warnings cost 127. Reading NOAA at 35 cost 123.", the four-row table, the "Weak spot" line (0 of 21) |
| `demo-silent.mp4` | Silent recording of the whole run sheet, 1:58, H.264, 1280×800, 30 frames a second. A yellow dot is the cursor |
| `capture.mjs` | The script that made all of the above |

## Timing of `demo-silent.mp4`
Video time is script time. The video starts at 0:00 of the script, so there is nothing to add.

| Time | On screen |
|---|---|
| 0:00 | Tomorrow view, Minneapolis (the Nov 14 forecast, 8.7). At 0:15 the cursor goes to "Smoke forecast", then to "Forecast made …" |
| 0:23 | Click **2025 test run**: Minneapolis, July 31. The cursor visits 41.3, NOAA's 18.7, measured 69.1, "RIGHT CALL" |
| 0:36 | Cursor at "Indoors above 32", then at "Line at 32" under the scale |
| 0:48 | City picker → Chicago: 15.3, measured 65.6, "MISSED A BAD DAY" |
| 1:03 | Click **›**: Friday, August 1. NOAA's 8.7, 51.8, measured 45.5 |
| 1:12 | Click **Does it work?**. At 1:29 the cursor goes to 2.36, then 3.20, then at 1:39 to the line with 127 and 123 |
| 1:44 | Cursor at the "Weak spot" line |
| 1:58 | End |

## How it was made
`capture.mjs` starts Google Chrome without a window (headless), opens the running app and drives it over Chrome's DevTools connection. It uses only Node (22 or newer), Chrome and ffmpeg. Nothing to install with npm.

```sh
python app/app.py                                               # in one terminal; the app is on http://localhost:7860
node docs/video/capture.mjs stills docs/video                   # the five PNGs
node docs/video/capture.mjs video  docs/video/demo-silent.mp4   # the video; takes two minutes, it records in real time
```
If the app is on another port: `APP=http://localhost:7863 node docs/video/capture.mjs …`.

- **Stills.** Each one opens a link the page understands (`#tomorrow//Minneapolis`, `#test/2025-07-31/Minneapolis`, `#test/2025-07-31/Chicago`, `#test/2025-08-01/Chicago`, `#results`), waits five seconds so the counting numbers and the letters have settled, and saves a screenshot. The city comes from the link. Chrome gets a new empty profile each run, so no remembered city can leak in.
- **Video.** The script opens `#tomorrow//Minneapolis`, then makes the run sheet's clicks at the run sheet's seconds: real mouse clicks on the tabs and the › button. Chrome sends a picture each time the page changes. The script repeats the last picture to fill a steady 30 frames a second and pipes them to ffmpeg (`libx264`, `-crf 21`).
- **Two things are not a real user.** Headless Chrome draws no mouse pointer, so the script adds the yellow dot. It also cannot draw the picker's drop-down list, so the script sets the picker to Chicago directly, which runs the same code as picking it. The list never shows in the video.
- **Do not use Chrome's one-line `--screenshot` with `--virtual-time-budget` for stills.** It fast-forwards the page's clock, and on smoke days it saved the picture without the "MOVE PRACTICE" line. The script waits in real time and does not have that problem.
- The video refuses to start if the Tomorrow view says "Updating…" or "Couldn't update.". Wait a minute and run it again.

## Recording the voice-over (pick one)

**A. Easiest: play it and record yourself.** Open `demo-silent.mp4` full screen. Start a screen recording with your mic on (QuickTime → File → New Screen Recording → Options → your microphone). Press play and start reading at once: the video and the script both start at 0:00. Stop at 1:58.
The Tomorrow view in the video is the Nov 14 forecast (Minneapolis, practice outside), and it says "Forecast made Saturday at 1:35 PM". So say "made today", not "made this evening", if you use this video and not the live app.

**B. Record audio only, then combine.** Record yourself reading the script (Voice Memos is fine, export as `.m4a`). Keep it under 1:58. Then, in this folder (needs ffmpeg: `brew install ffmpeg`):
```sh
ffmpeg -i demo-silent.mp4 -i voice.m4a -map 0:v -map 1:a -c:v copy -c:a aac -shortest smokecheck-demo.mp4
```
The picture is copied as it is, so this takes a second. `-shortest` stops at whichever ends first, voice or video. If your voice runs past 1:58 the end gets cut, so check the last line made it. Tested with a silent dummy track: the output is 1:58.

## Note
The submitted video should ideally show the **live app**: record your own screen clicking through the run sheet while you talk, so the Tomorrow view is that evening's real forecast. Use `demo-silent.mp4` to rehearse the pacing, and as a backup if a live take goes wrong.
