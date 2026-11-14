# FIRETRACE

**Deployment status:** the seven-country update is live at [FIRETRACE](https://firetrace-bhaktapur-2026.pages.dev/). All 115 public assets and the seven-country browser workflows were verified on November 14, 2026. See `DEPLOYMENT.md`.

Compare satellite fire observations on a named reference scale, inspect historical seasons, and follow each displayed week back to its evidence.

FIRETRACE addresses **Harmonization of MODIS and VIIRS Hot Spots** with NASA FIRMS archives for **Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States**. The supported history is **2003–2024**: observed MODIS Aqua through 2012 and converted VIIRS S-NPP from 2013. Terra, Aqua and VIIRS remain separate during cleaning and evaluation. An Aqua-equivalent detection is an instrument-scale estimate, not the true number of fires.

## The working experience

Start with one observed week: compare the separate sensor counts, inspect the converted estimate and calibration bounds, open the held-out evaluation, then share a link that reopens the same evidence. This is the core demonstration; a trend does not have to disappear for the comparison to be useful.

- A 3D Earth shows **41,986** occupied 0.25-degree grid cells, annual history, a fixed all-year color scale and exact-value inspection. The renderer sleeps when idle or offscreen and provides a regional top-20 table fallback.
- The burning-activity calendar connects weekly history to raw/harmonized comparison, national seasonal patterns, historical unusual-period flags and evidence cards.
- National totals use all analyzed cells. **Twelve training-selected daily cells per country** load on demand: 84 detailed series, not arbitrary daily-area coverage.
- CSV exports preserve the selected series and provenance. ICS exports place historical high-activity windows into a selected year; they are not forecasts.
- Share links restore the region, dates, daily cell, page, scale and open evidence week. They use the current published data; camera position, annual globe-cell selection and Earth/table preference reset.

The release uses **273 verified annual archives**, **74,187,339 input rows** and **67,934,899 cleaned detections** including retained diagnostic-control types. It publishes **731,276 national and selected-cell daily rows**. Exact count reduction keeps processing bounded in memory, and a lossless dictionary format preserves every published daily value while fitting the static payload budget. See `DEPLOYMENT.md` for the actual verified live revision and final built size.

## Held-out results

B0 is uncalibrated VIIRS, B1 is a global training ratio, and M1 uses region/day-night/reported-FRP strata. Model selection uses **2018–2019 daily MAE**, after training on **2013–2017**. The table reports all three models on the **60 held-out months in 2020–2024**; these test results did not select the model. MAE measures agreement with archived Aqua detections, not ground-truth fire counts.

| Country | Selected | B0 monthly MAE | B1 monthly MAE | M1 monthly MAE | Selected bias |
|---|---|---:|---:|---:|---:|
| Australia | B1 | 68,780.72 | 2,003.27 | 3,167.65 | +11.04% |
| Bangladesh | M1 | 554.35 | 68.93 | 23.46 | +6.77% |
| Brazil | B1 | 97,241.05 | 2,282.61 | 3,597.51 | -10.49% |
| Egypt | M1 | 767.73 | 90.40 | 15.04 | +51.68% |
| India | M1 | 31,368.85 | 1,429.13 | 1,365.99 | -2.38% |
| Nepal | M1 | 2,474.43 | 182.52 | 30.24 | -8.11% |
| United States | B1 | 31,835.40 | 1,537.79 | 2,078.57 | +1.72% |

Egypt's selected model still has +51.68% test bias, and some countries retain substantial peak-season timing error. The simpler B1 wins validation in Australia, Brazil and the United States. The complete monthly/weekly evaluation remains in `reports/harmonization_eval.csv`; unfavorable results are retained.

The seven-country model is a distinct revision, `seven-country-v1`. Adding countries legitimately changes the global training ratio and M1 shrinkage target. Do not reuse the old two-country metric values for this release. The historical two-country implementation is preserved in Git at commit `841998b`; exact-count processing was checked against all of its daily values, bootstrap bounds and evaluation results before expansion.

## Human rhythm result

The official decision comes from the pre-specified test in `reference/kill_test.py`, run on real FIRMS data for the seven countries, 2013–2024 (outputs in `reports/official/`). The rule, fixed before the data were analysed: the United States replication check must pass and at least two other countries must pass, where a country passes if its predicted rest day is the lowest weekday and significant after Bonferroni correction in at least two of Terra, Aqua and VIIRS.

**Decision: pass.** The United States (3 of 3 streams), Australia (3 of 3) and Brazil (2 of 3) pass. India, Nepal, Bangladesh and Egypt do not. All three passing countries rest on Sunday; Friday- and Saturday-rest countries did not show a dip, so this does not show the dip following each country's own rest day. A dip is consistent with people scheduling their burning; it is not proof of cause.

The stricter seven-country release analysis (`pipeline/streaming/weighted_rhythm.py`: 2002–2024 MODIS and 2013–2024 VIIRS, upper bound below 1, matched per-country static-source controls) is reported as robustness checks next to the official decision and never changes it. The US and Australia meet all of them. Brazil's Terra static-source control also dips on Sunday (index 0.913, adjusted p = 0.021), so Brazil's vegetation-fire dip cannot be cleanly separated from weekly patterns in industrial heat sources. The control was clean on 2014-2023. The official pre-specified result is unchanged (PASS), but Brazil's support is weaker than the US and Australia.

The **Human rhythm** tab shows the official result, weekday charts per country and stream with 95% intervals, the robustness checks and an exploratory per-cell map. The map (`reference/rhythm_map.py`) is not part of the pre-specified test.

## Run the app

Requirements: Node.js 20+; Python 3.11+ for scientific reproduction. The committed precomputed data can run without downloading the original archives.

```powershell
npm ci --prefix web
npm --prefix web run dev
```

From the repository root, `npm run build` creates `dist`. Run web checks with `npm --prefix web test`.

## Reproduce the science

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pipeline.streaming reproduce --output work/reproduced-seven --model-revision seven-country-v1 --baseline-commit 841998b
```

Use `.venv/bin/python` on macOS/Linux. Run commands from the repository root. The reproduction command downloads official annual archives, prepares exact counts, generates the core scientific reports and compact data, then builds an isolated website. It requires a fresh output directory and never deploys or replaces the current application. Raw downloads require several GB; the guarded downloader retains a 10 GiB disk reserve. Existing verified archive paths can be reused through `--source-manifest`.

For separate preparation/build steps, multiple manifests or an already locked evaluation, see `pipeline/streaming/README.md`. `--locked-evaluation` verifies saved source/model identity and reuses the lock without reselection or another held-out evaluation. Cached preparations retain source/code hashes; original archives are referenced in place.

The supplemental grid/early-bridge experiments have their own prespecified protocol and outputs under `reports/scientific_validation/`. Run `python -m pipeline.validation.science_checks --help` for their preparation, analysis and model inputs. They are separate from the core reproduction command and do not retune the released model.

The original `python -m pipeline.run_all` route remains available for the smaller raw-record workflow. Its default scope is Nepal/US; it is not the seven-country release command. Explicit `--reuse-clean` keeps the cache's own source manifest, and `--reuse-analysis` checks input and code fingerprints. Newly downloaded archives must not be attached to older cached rows.

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m pipeline.run_all --synthetic
```

To rebuild the human-rhythm outputs from the annual archives (same folder layout as the downloader):

```powershell
python reference/kill_test.py data --label "REAL FIRMS DATA"     # official gate; copy outputs to reports/official/
python reference/rhythm_map.py data                            # exploratory per-cell map; copy to reports/official/
.\.venv\Scripts\python.exe -m pipeline.rhythm --from-saved reports/rhythm_results.json --official reports/official --output reports/rhythm_robustness
.\.venv\Scripts\python.exe -m pipeline.rhythm_web           # writes web/public/data/rhythm.json
```

Synthetic outputs stay separate under `reports/synthetic` and `work/synthetic-web-data`; the sensor-switch figure is visibly labeled synthetic.

## Inspect the evidence

| File | Meaning |
|---|---|
| `reports/data_manifest.json` | Official URLs, archive years, completion status and SHA-256 hashes |
| `reports/cleaning_diagnostics.json` | Filtering, civil-time and input/output counts |
| `reports/harmonization_model.json` | Ratios, country choices, model revision and uncertainty definition |
| `reports/selection_lock.json` | Training/validation choices frozen before held-out evaluation |
| `reports/harmonization_eval.csv` | All baselines and selected candidates on monthly/weekly held-out periods |
| `reports/official/kill_test_gate.json` | **Official** pre-specified rhythm decision (seven countries, 2013–2024) |
| `reports/official/kill_test_results.csv` | Official per-country, per-stream weekday estimates with per-day 95% intervals |
| `reports/official/RESULTS.md` | Plain-language write-up of the rhythm result and the exploratory map |
| `reports/rhythm_results.json`, `reports/kill_test_gate.json` | Stricter seven-country release analysis (2002–2024), used only for robustness checks |
| `reports/rhythm_robustness/robustness_checks.json` | Robustness checks derived from that analysis, next to the official decision |
| `reports/rhythm_robustness_2014_2023/` | Same stricter checks on 2014–2023 only (Brazil's control was clean there) |
| `reports/official/rhythm_cells.geojson` | Exploratory per-cell rest-day map (VIIRS, with Aqua check) |
| `reports/PHASE3_AUDIT.md` | Independent scientific, count and actual frontend-decoder checks |
| `reports/scientific_validation/SCIENTIFIC_SENSITIVITY.md` | Prespecified 0.25°/0.5° selected-cell sensitivity and early Terra-bridge feasibility |
| `reports/build_summary.json` | The built scope and data-size record |

## Scope and limits

Complete archives do not prove complete cloud-free satellite observation coverage. Zero archived detections and unknown observation exposure are different facts. Bootstrap bands describe calibration variability, not every observation uncertainty.

A prespecified 0.25°/0.5° selected-cell study was completed on 2018–2019 with frozen model ratios. It exposes large local errors, including US normalized monthly absolute error of 145.94% at 0.25° and 144.35% at 0.5°; national calibration does not establish cell accuracy. A separate Terra-bridge feasibility study improves count agreement but does not qualify a historical reconstruction or its total uncertainty. Neither study retunes the model or touches the 2020–2024 test metrics.

The release does **not** include a validated 2000–2002 Terra reconstruction, worldwide coverage, arbitrary-grid daily exploration or operational forecasting. National seasonality stays national when a cell is selected. The year-end partial week and other incomplete seven-day bins remain inspectable but do not enter seasonal/anomaly comparisons. See `METHODS.md`, `LIMITATIONS.md` and `DECISIONS.md`.

## Hosting and source

[Public application on Cloudflare Pages](https://firetrace-bhaktapur-2026.pages.dev/) · [Public source repository](https://github.com/Water-Mal0ne/FIRETRACE)

Cloudflare serves static assets; no paid compute or database was provisioned. `scripts/publish.ps1` checks, builds, pushes, deploys and verifies the public files. See `DEPLOYMENT.md` for release-specific evidence.

## Attribution

Data: [NASA FIRMS country archives](https://firms.modaps.eosdis.nasa.gov/country/). [Space Apps Navigator guidance](https://github.com/nasa/spaceapps/discussions/2016) supports selected-region implementations and prioritizing the harmonization method. Weekly-cycle context: [Earl, Simmonds and Tapper (2015)](https://doi.org/10.1002/2015GL066383).

Globe land and borders: public-domain [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) through world-atlas 2.0.2; rendering uses Three.js. Uncolored map areas are not observations of no fire. Software is MIT licensed; external data and dependencies retain their own terms. `AI_DISCLOSURE.md` records AI assistance.

**NASA does not endorse this project.**
