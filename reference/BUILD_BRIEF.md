# CINDERLINE: build brief for Codex

You are building our team's entry for the NASA Space Apps Challenge 2026, challenge "Harmonization of MODIS and VIIRS Hot Spots". We are a team of six at the Kathmandu, Nepal local event. The hackathon runs 14-15 November 2026 and the submission is due 15 November, 11:59 pm Nepal time (UTC+05:45). Read this whole brief before writing code.

## 1. The challenge in one paragraph

NASA's FIRMS service publishes every satellite fire detection ("hotspot") as a row: lat, lon, date, time (UTC), satellite, confidence, fire radiative power (FRP), day/night. Two instruments did this job. MODIS (Terra since 2000, Aqua since 2002) has ~1 km pixels. VIIRS (Suomi-NPP since 2012) has 375 m pixels and detects many more small fires. Joining the two records naively makes fire activity appear to jump after 2012. The challenge asks for (1) a harmonized, consistent 2000-present record and (2) a web app with a "burning activity calendar" for a chosen area and dates, showing historical patterns, critical periods and unusual conditions. Users: fire managers, emergency planners, land managers.

## 2. What we are building

Product name: CINDERLINE. Two layers.

Layer 1, required and must be excellent: a harmonized MODIS-VIIRS record and calendar web app, with honest evaluation against baselines.

Layer 2, our signature: a "human rhythm" analysis. Natural fire has no 7-day cycle; human burning follows the work week. If a region's fire detections dip on its local rest day (Sunday in the US, Saturday in Nepal, Friday in Bangladesh and Egypt), that is a human fingerprint. A 2015 paper (Earl, Simmonds and Tapper, Geophysical Research Letters, doi:10.1002/2015GL066383) found weekly cycles in MODIS fires. Our new contribution is testing this in a harmonized MODIS+VIIRS record, per sensor, with each country's own rest day predicted in advance. Layer 2 ships only if the data supports it (see section 7). If it does not, the app still works without it.

Demo story, two acts:
1. "Did fire really increase, or did the camera get sharper?" The naive joined series (a constructed baseline) jumps when VIIRS arrives; the harmonized record, evaluated against baselines on held-out years, shows how much of the change survives a fair comparison. If a real change remains after harmonization, show that honestly; do not force a jump to disappear.
2. "Then we found a human rhythm in it." Weekday charts per country, rest day highlighted, with confidence intervals.

## 3. Hard rules

- Science over features. No AI chatbot, no 3D globe, no forecasting until sections 4-7 pass their acceptance checks.
- Never claim "true number of fires". Hotspot detections are not fires, and no detection is not proof of no fire (clouds, overpass gaps). Report results on a named reference scale ("MODIS-Aqua-equivalent detections").
- Never pool Terra, Aqua and VIIRS into one stream for analysis. Keep them separate; agreement between independent streams is evidence.
- Convert UTC acquisition time to local civil time (IANA zone, e.g. Asia/Kathmandu) before any weekday or date logic.
- Every number shown in the UI must be reproducible from a script in the repo.
- Anything produced from synthetic data must say "SYNTHETIC DATA" inside the figure itself, not only in the filename, and must be kept apart from real-data results.
- Space Apps rules: use at least one NASA source from the challenge Resources (FIRMS is). Keep a file AI_DISCLOSURE.md listing where AI was used (code generation by Codex, etc.). Do not use the NASA logo or imply NASA endorsement. Add "NASA does not endorse this project" in the footer.
- License the repo MIT. No secrets in the repo; FIRMS MAP_KEY (if used) goes in .env, with .env.example committed.

## 4. Data

Source: NASA FIRMS archive, yearly country CSV files.
URL pattern (verify spelling on https://firms.modaps.eosdis.nasa.gov/country/):
`https://firms.modaps.eosdis.nasa.gov/data/country/{sensor}/{year}/{sensor}_{year}_{Country}.csv`
with sensor in `modis`, `viirs-snpp`.

Regions (country files): United_States, Australia, Nepal, Bangladesh, Egypt, India, Brazil. Years: MODIS 2001-2025, VIIRS 2012-2025.

Important: if your sandbox has no internet, stop and tell the human. They will run `pipeline/download.py` on a laptop and commit the files or a processed parquet. The US files are large; start with Nepal and United_States.

Relevant columns. MODIS: latitude, longitude, brightness, acq_date, acq_time, satellite (Terra/Aqua or T/A), instrument, confidence (0-100), frp, daynight, type. VIIRS: bright_ti4, confidence (l/n/h), satellite N. type: 0 vegetation fire, 1 volcano, 2 other static land source, 3 offshore.

Cleaning: keep type 0 for the main analysis (keep type 1/2 aside as a negative control). Drop MODIS confidence < 30 and VIIRS confidence "l". Add columns: stream (Terra/Aqua/VIIRS), utc datetime, local datetime, local_date, weekday, year, country, grid cell id.

## 5. Harmonization method

Unit of analysis: grid cell x day x stream, using a 0.25 degree grid (also test 0.5). Variables per cell-day: detection count, fire-present flag, summed FRP, day/night counts.

Reference scale: MODIS Aqua, because Aqua and VIIRS S-NPP both cross at about 13:30 local time, making them the fairest pair. Terra (10:30 crossing) is reported separately.

Overlap period: 2012-2025 (both flying). Never split randomly by day; adjacent days are correlated.
- Training: 2013-2017. Validation (model choice and tuning only): 2018-2019, or rolling year-blocks inside 2013-2019.
- Test: 2020-2024, touched ONCE, after the model is chosen. Report every baseline on it too.

Pre-2002 bridge: Aqua starts mid-2002, so 2001-2002 values need a Terra-to-Aqua calibration fitted on 2003-2011 (both MODIS satellites flying, VIIRS not yet), validated on held-out years within that period. Mark these values as "reconstructed from Terra" with their own wider uncertainty. If the bridge validates badly, start the supported record at 2003 and say so.

Models, in order:
- B0 raw: MODIS counts up to 2011, VIIRS counts from 2012. Shows the fake jump.
- B1 single ratio: one global VIIRS-to-Aqua ratio from training years.
- M1 stratified ratio: separate ratios by region x day/night x FRP class (and land cover if cheap to add).
- M2 (optional): gradient boosting (LightGBM) predicting Aqua-equivalent cell-month counts from VIIRS features (counts by FRP class, day/night, month, region). Keep it only if it beats M1 on the VALIDATION years, never decided on test years.

Metrics on test years, per region, at monthly and weekly aggregation: bias (%), MAE, correlation, and peak-week error of the fire season (in weeks). Write results to `reports/harmonization_eval.csv` and a markdown summary. If the simple ratio wins, use it and say so.

Synthetic check: create a fake record with a known trend, apply a sensor switch (inflate detections ~4x from a chosen year), run the pipeline and show it recovers the trend. Save as `reports/synthetic_switch.png`.

Output: a harmonized daily series per region and per grid cell on the Aqua-equivalent scale, with an uncertainty band (from bootstrap over training years), a coverage flag (which streams contributed) and a source flag (observed Aqua / converted VIIRS / reconstructed from Terra). Missing coverage is not the same as zero detections: keep them distinct in data and UI.

## 6. Burning activity calendar

For any preset region (and any grid cell inside it):
- Calendar heatmap: rows = years, columns = weeks (or days), colour = harmonized activity.
- Typical season: weekly median with 10th-90th percentile band across years.
- Critical period: the weeks where the median exceeds a threshold (e.g. top 25% of the year's activity).
- Anomalies: week flagged when activity is above the 90th or below the 10th percentile of that week's history; show z-score.
- Evidence card on click (any week/month): which streams observed it, raw counts per stream, model used, harmonized value with uncertainty, anomaly status.
- Toggle: raw (B0) vs harmonized. This toggle is act 1 of the demo.
- Download: CSV of the shown series, and an .ics file of critical periods.

## 7. Human rhythm module

A tested reference implementation exists: `kill_test.py` in the repo root (provided by the team, already revised after review). Reuse it, do not rewrite its statistics:
- Local civil time via IANA zones (timezonefinder for multi-zone countries; no solar-time fallback). Invalid timestamps and unresolved zones are dropped and counted in a diagnostics file.
- Complete calendar years only. Per year, weekday rate = detections on that weekday / number of times that weekday occurs that year (52 or 53); index = rate / mean rate. Average across years; 95% CI by bootstrapping whole years.
- Null test that keeps seasonality and clustering: under no weekly effect the rest day is a random weekday each year; p-value from 5000 draws. Bonferroni correction across all country x stream tests.
- Predicted rest days are fixed in code before looking at results: United_States Sun, Australia Sun, Nepal Sat, Bangladesh Fri, Egypt Fri, India Sun, Brazil Sun.
- Report: index per weekday, lowest day, whether the rest-day CI upper bound is below 1.0, number of streams agreeing. Run for all detections and daytime only.
- Replication check: United_States should show a significant Sunday dip (the 2015 paper found one). If it does not, stop and report: investigate data, method and comparability with that study. It is not by itself proof of a bug.
- Negative control: type 1/2 detections (static sources) are kept in a separate branch, never deleted by cleaning, and analysed the same way; expect no weekly pattern.
- The three streams observe overlapping fires, so agreement is corroboration, not independent replication. Say so.
- Optional extension if time remains: festival effect. Align on Eid al-Fitr dates (Bangladesh, Egypt) and Dashain (Nepal); compare activity in the festival window against the same weeks of neighbouring years.

Gate: the script writes `kill_test_gate.json` with decision pass / fail / insufficient_data. A country passes only if its predicted rest day is the lowest weekday and significant after correction in at least two streams; a single available stream is never enough. The module appears in the app only if the decision is "pass" (US replication passes and at least two other countries pass). Otherwise show the results as a documented negative finding in the report.

App view: country selector, 7-bar weekday chart per stream with CI whiskers and the rest day highlighted, a one-line verdict, and a "why this matters" note worded carefully: a robust rest-day dip is evidence consistent with people scheduling their burning, which is useful context for fire managers. It does not by itself prove ignition cause, and the absence of a dip does not prove fires are weather-driven. Do not use it to classify regions or recommend prevention versus forecasting.

## 8. Architecture

- `pipeline/` Python 3.11: download, clean, grid, harmonize, evaluate, calendar, rhythm. pandas, numpy, pyarrow, scikit-learn, lightgbm (optional), timezonefinder, matplotlib.
- Pipeline writes precomputed static JSON per region to `web/public/data/` so the site needs no backend. Keep total data under ~50 MB.
- `web/` Vite + React + TypeScript, Recharts or visx for charts, MapLibre GL for the map (region outline and grid cell picker). Deploy to Vercel or GitHub Pages.
- `reports/` evaluation tables and figures. `tests/` pytest for cleaning, timezone conversion, weekday index and harmonization on synthetic data.
- One command reproduces everything: `make all` (or `python -m pipeline.run_all`).

Data contracts (so agents can work in parallel; agree these first):
- `data/processed/detections.parquet`: country, stream, utc, local, local_date, weekday, year, lat, lon, cell_id, frp, daynight, type, confidence.
- `data/processed/harmonized_{region}.parquet`: date, region, cell_id (or "ALL"), raw_terra, raw_aqua, raw_viirs, harmonized, lo, hi, coverage, model.
- `web/public/data/{region}.json`: { meta, daily: [...], weekly_climatology: [...], anomalies: [...], critical_periods: [...], rhythm: {...} | null, eval: {...} }.

## 9. Agent plan

Work as six parallel agents, then integrate. Each agent works in its own branch and folder, follows the data contracts above, and writes a short STATUS.md entry when done. Use small sample data (Nepal, 2019-2021) until the full files are available.

Agent 1, Data: `pipeline/download.py`, `pipeline/clean.py`, local time conversion, grid assignment, detections.parquet, plus a 5 MB sample in `data/sample/` for the other agents. Tests for UTC-to-local conversion (include a night detection that changes date).

Agent 2, Harmonization: B0, B1, M1, optional M2; train/test split by years; metrics; synthetic sensor-switch test; harmonized parquet with uncertainty and coverage.

Agent 3, Calendar and anomalies: weekly climatology, percentile bands, critical periods, anomaly flags, evidence-card payloads, CSV and .ics export; exports the region JSON.

Agent 4, Human rhythm: port `kill_test.py` into `pipeline/rhythm.py`, add the negative control, daytime-only variant and gate logic; optional festival analysis; rhythm block in the region JSON; figure `reports/rhythm.png`.

Agent 5, Web app: React app with region picker and map, calendar heatmap, raw vs harmonized toggle, typical-season chart, anomaly list, evidence card drawer, rhythm view, Methods page and Limitations page. Build against mock JSON matching the contract first, then real data. Accessible colours, mobile-friendly, loads in under 3 seconds.

Agent 6, Evaluation, QA and submission: pytest suite; check every number in the UI against `reports/`; write README (problem, method, results table, how to run), METHODS.md, LIMITATIONS.md, AI_DISCLOSURE.md; draft the Space Apps project page text (under 500 words), a 7-slide outline and a 30-second demo video script following the two-act story.

Integration (you, after the agents): merge, run `make all` end to end, fix contract mismatches, deploy, and produce a final checklist of what works, what is partial and what was cut.

## 10. Order of work and checkpoints

1. Data contracts and sample data (first 1 hour). Everyone else uses mocks meanwhile.
2. Kill test on real data: US + Nepal first. Report results to the humans immediately; they decide on Layer 2.
3. Harmonization with baselines and held-out evaluation.
4. Calendar and app working end to end for Nepal and the US.
5. Remaining regions, rhythm view (if gated in), polish.
6. Freeze features 6 hours before the deadline. Then only bug fixes, docs, deploy, video.

## 11. Definition of done

- Live URL with the raw/harmonized toggle working for every preset region.
- Harmonized record improves held-out agreement with the Aqua reference over the baselines, while keeping genuine changes over time and documenting remaining uncertainty. It is NOT required that any trend or 2012 discontinuity disappears.
- Evaluation table: the selected model and all baselines (B0, B1, M1, M2 if built) on the untouched 2020-2024 test years.
- Synthetic sensor-switch figure.
- Calendar with typical season, critical periods, anomalies, evidence cards and downloads.
- Rhythm results with `kill_test_gate.json`, diagnostics, the US replication check and the negative control (in the app if the gate passes, otherwise as a documented negative result).
- A data manifest: source URLs, years, streams, missing files.
- README, METHODS, LIMITATIONS, AI_DISCLOSURE, project page text, slide outline, video script.
- `make all` reproduces every figure from raw files.

When anything in this brief conflicts with the real data, trust the data, write down what you changed and why in DECISIONS.md, and tell the humans.
