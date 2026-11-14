# Video assets (demo voiceover kit)

The script is `docs/video-script.md`. These files are captured from the real app (`app/app.py`, 1280×800 browser window).

## Files
| File | What it is |
|---|---|
| `01-milwaukee-0731.png` | App as it opens: Milwaukee, Jul 31 2025, red "Move practice indoors", NOAA 13.4 · SmokeCheck 26.8 · measured 83.7 |
| `02-chicago-0731.png` | Chicago, Jul 31: green "OK to practice outside", 13.7 · 13.7 · 65.6, "Likely between 8.8 and 20.6" |
| `03-chicago-0801.png` | Chicago, Aug 1: red, NOAA 8.7 · SmokeCheck 54.0 · measured 45.5 |
| `04-does-it-work.png` | "Does it work?" tab, SmokeCheck row first (2.58 average miss, cost 106; "NOAA at the plain 35 line" cost 123) |
| `05-where-it-fails.png` | "Where it fails" tab with the "Smoke arrival days are the weak spot" note |
| `demo-silent.mp4` | Silent screen recording of the demo, 1:44, H.264 1280×800. A yellow dot is the cursor. |

## Timing of `demo-silent.mp4`
Video 0:00 = script time 0:15 (section 2 starts). Add 0:15 to get the script's run-sheet time.

| Video | Script | On screen |
|---|---|---|
| 0:00 | 0:15 | Milwaukee, Jul 31. The cursor visits NOAA 13.4, SmokeCheck 26.8, measured 83.7 |
| 0:20 | 0:35 | Cursor under the "warns above 24.5, not 35" sentence |
| 0:29 | 0:44 | City dropdown → Chicago (green) |
| 0:45 | 1:00 | Slider one day forward → Friday, August 1 (red, 54.0) |
| 0:59 | 1:14 | "Does it work?" tab: SmokeCheck 2.58, NOAA 3.2, persistence 3.4, then cost 106 (SmokeCheck) and 123 (NOAA at the plain 35 line) |
| 1:29 | 1:44 | "Where it fails" tab, note outlined in yellow |
| 1:44 | 1:59 | End |

## Recording the voiceover (pick one)

**A. Easiest: play it and record yourself.** Open `demo-silent.mp4` full screen. Start a screen recording with your mic on (QuickTime → File → New Screen Recording → Options → your microphone). Read section 1 over the first frame, *then* press play when you reach "This is SmokeCheck". Stop at 2:00.

**B. Record audio only, then combine.** Record yourself reading the script (Voice Memos is fine, export as `.m4a`). Keep it under 1:59. Then, in this folder (needs ffmpeg: `brew install ffmpeg`):

Reading the whole script, section 1 included. This holds the first frame for 15 s while you read the intro:
```sh
ffmpeg -i demo-silent.mp4 -i voice.m4a -map 0:v -map 1:a -vf "tpad=start_duration=15:start_mode=clone" -c:v libx264 -crf 23 -pix_fmt yuv420p -c:a aac -shortest smokecheck-demo.mp4
```
Starting at "This is SmokeCheck" (skip section 1; faster, no re-encode):
```sh
ffmpeg -i demo-silent.mp4 -i voice.m4a -map 0:v -map 1:a -c:v copy -c:a aac -shortest smokecheck-demo.mp4
```
`-shortest` stops at whichever ends first, voice or video. If your voice runs long, the end gets cut, so check the last line made it. Both commands were tested with a silent dummy track: 1:59 and 1:44 outputs.

## Note
The submitted video should ideally show the **live app** (record your own screen clicking through the run sheet while you talk). Use `demo-silent.mp4` as a pacing guide to rehearse against, and as a backup if a live take goes wrong.
