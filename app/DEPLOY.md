# Deploying SmokeCheck as a Hugging Face Space

Nothing here has been run against Hugging Face yet. Creating the Space is public and needs a human yes.

## What gets uploaded

`bash app/build_space.sh` builds `app/.space_build/`, which is git-ignored:

```
README.md              <- app/space/README.md (Space settings in the YAML header + description and sources)
app.py                 <- app/app.py
requirements.txt       <- app/requirements.txt (gradio==6.32.0, pandas==3.1.1, plotly==7.1.0)
data/predictions.csv   <- data/predictions.csv
data/metrics.json      <- data/metrics.json
```

The YAML header sets `sdk: gradio`, `sdk_version: "6.32.0"` (same as the pin) and `python_version: "3.12"`.
The Python version matters: pandas 3.1.1 needs Python 3.11 or newer, and Spaces default to 3.10.

## Morning commands

Run from the worktree root (`smokecheck-aiden/`). The Hugging Face token is already stored on this Mac.

```bash
bash app/build_space.sh                      # rebuild from the current app and data; uploads nothing
.venv/bin/python app/test_app.py             # should print "all checks passed"

hf auth whoami                               # must say fruutium; if not: hf auth switch
hf repos create fruutium/smokecheck --type space --sdk gradio --public
hf upload fruutium/smokecheck app/.space_build . --repo-type space --commit-message "SmokeCheck demo app"
```

The Space is then at https://huggingface.co/spaces/fruutium/smokecheck. The first build takes a few minutes.

To update it later, run `bash app/build_space.sh` and the same `hf upload` line again.

Web UI instead of the CLI: huggingface.co → New → Space, owner `fruutium`, name `smokecheck`, SDK Gradio,
public. Then use "Files → Add file → Upload files" to add the five files above, keeping `data/` as a folder.

**If `hf repos create` fails with HTTP 402:** the `huggingface_hub` docs say Gradio Spaces on the free
cpu-basic hardware may need a paid subscription. Stop there; paying or changing hardware is a human decision.

## Check it logged out

Open the Space link in a private (incognito) window:

1. The status badge says **Running**. If it says build or runtime error, open the **Logs** tab first; a
   Python-version or pip error usually means the YAML header was changed.
2. The default view is **Milwaukee, Thursday, July 31, 2025**: red "Move practice indoors", SmokeCheck 26.8
   (cut-off 24.5), NOAA 13.4 (no warning, cut-off 52.5), measured 83.7 (a bad day).
3. Change the city to Chicago and step the day slider once: Friday, August 1, 2025, SmokeCheck 54.0 warns.
4. The map draws the six city dots.
5. "Does it work?" and "Where it fails" both show tables.
6. The footer reads "Open-Meteo air-quality values are model estimates, not measurements. Prototype, not
   health advice."
7. The **Files** tab holds exactly the five files listed above. No tokens, notebooks or other data.

## Not decided yet

- **License.** The repo has no LICENSE file, so the Space README sets none. Add a `license:` line to
  `app/space/README.md` if the team picks one.
