# Data and reproduction

The website runs from committed data files. Running it locally does not require downloading satellite archives or fitting a model. Reproducing the scientific outputs is a separate job, with larger inputs and checks that bind results to particular source files.

## Sources and versions

| Input | What the project uses | Record to inspect |
| --- | --- | --- |
| NASA FIRMS MODIS country archives | Separate Terra and Aqua detections, identified during cleaning | [Archive manifest](../reports/data_manifest.json), [downloader](../pipeline/download.py) |
| NASA FIRMS VIIRS country archives | Suomi-NPP detections for the released conversion and weekly-rhythm analysis | [Archive manifest](../reports/data_manifest.json), [model](../reports/harmonization_model.json) |
| NOAA-20 VIIRS archives | A separate transfer check, not an extra supplier in the released calendar | [NOAA-20 report](../reports/review/noaa20/NOAA20.md), [checker](../pipeline/review/noaa20_check.py) |
| Country and land outlines | Natural Earth geometry from `world-atlas` 2.0.2 | [Web dependency lock](../web/package-lock.json), [map preparation](../scripts/prepare-map.mjs) |
| State boundaries used in regional review | The Natural Earth admin-1 file named in the reproduction instructions | [REPRODUCE.md](../REPRODUCE.md) |

The manifest records the URL, archive year, row count, byte size and SHA-256 of each source file. Use those hashes as the source identity. The manifest does not provide one collection-version field that describes every MODIS and VIIRS archive; do not infer a uniform product version from the calendar year. A complete downloaded file also says nothing about cloud-free coverage of the country.

[Methods](../METHODS.md) records the source files' MODIS `version` field as `6.2` in 2013-2017, `6.03` in 2018-2022 and `61.03` in 2023-2024. These are the recorded collection/processing-source field values, not decimal software versions. The S-NPP VIIRS field is `2` throughout 2013-2024. Product processing changes cross the fitting and evaluation periods; the conversion does not isolate their effects.

The saved model revision is `seven-country-v1`, with baseline commit `841998b`. The model and public index carry the same archive fingerprint. The [locked-artifact receipt](../reports/LOCKED_ARTIFACTS.json) binds saved model-selection and evaluation artifacts to their bytes. Newly downloaded archive revisions may fail this identity check and must not silently inherit the old evaluation.

[REPRODUCE.md](../REPRODUCE.md) records Python 3.12.10, pandas 3.1.1, NumPy 2.5.4, matplotlib 3.11.2, timezonefinder 9.2.0, pyarrow 26.0.1, Node.js 24.22.1 and npm 11.19.1 for its run. These are recorded versions, not a claim that a fresh install will select them: [requirements.txt](../requirements.txt) specifies minimum Python-package versions. The web dependencies are pinned in [package-lock.json](../web/package-lock.json).

## Run the checked-in website

From the repository root:

```powershell
npm ci --prefix web
npm --prefix web run dev
```

Open the local URL printed by Vite. To inspect the production build:

```powershell
npm run build
npm --prefix web run preview
```

The root build prepares map files, runs TypeScript checks, builds `web/dist/`, then copies that output to `dist/`. It does not refit a model or deploy the site. The scripts are in [scripts/build.mjs](../scripts/build.mjs) and [web/package.json](../web/package.json).

## Working directories

| Path | Contents |
| --- | --- |
| `data/raw/` | Downloaded archives and their manifest; ignored by Git |
| `data/processed/` | Clean caches and processed tables; ignored by Git |
| `data/sample/` | Committed development samples and reduced analysis inputs |
| `work/` | Isolated reproductions, temporary counts and local verification receipts; ignored by Git |
| `reports/` | Frozen model, selection, evaluations and source identities |
| `reports/official/` | Official pre-specified weekly-rhythm outputs |
| `reports/review/` | Additional checks, including area reconciliation, FRP and 2025 continuity |
| `reports/calendar-confidence/` | Annual-calendar alignment and seasonal-panel verification |
| `web/public/data/` | Data the browser loads |
| `web/public/evidence/` | Downloadable evidence accompanying the app |
| `reference/` | Original analysis scripts used for the official and exploratory results |
| `tests/`, `web/tests/` | Python and browser-module tests |

The ignored directories are not missing website dependencies. They are needed only for the corresponding rebuild or source-level verification.

## Rebuild the baseline from archives

Create a Python environment and install the repository requirements:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
```

On a Unix shell, activate `.venv/bin/activate` instead. The commands below assume `python` refers to that environment.

The [exact-count route](../pipeline/streaming/README.md) can download archives and build an isolated baseline:

```powershell
python -m pipeline.streaming reproduce --output work/reproduced-seven --model-revision seven-country-v1 --baseline-commit 841998b --baseline-reports reports/releases/two-country-841998b
```

Its downloader requests the archive years defined in [reproduce.py](../pipeline/streaming/reproduce.py), including adjacent years needed to resolve local dates. The output directory must be new. The generated site is at `work/reproduced-seven/site/web/dist/`, and `REPRODUCTION.json` records whether its size checks passed. The command preserves the existing website and never deploys.

To reuse the original archives and saved evaluation instead of selecting models again:

```powershell
python -m pipeline.streaming reproduce --output work/locked-reproduction --source-manifest reports/data_manifest.json --locked-evaluation reports --model-revision seven-country-v1 --baseline-commit 841998b --baseline-reports reports/releases/two-country-841998b
```

The absolute archive paths in the manifest must exist on that machine. This is not a portable download list with paths automatically remapped. Hash mismatches must be investigated rather than bypassed.

The individual stages are also exposed. Here `data/raw/manifest.json` must describe all requested countries:

```powershell
python -m pipeline.download --countries Australia Bangladesh Brazil Egypt India Nepal United_States --years 2001 2025 --data-dir data/raw
python -m pipeline.streaming prepare --manifest data/raw/manifest.json --countries Australia Bangladesh Brazil Egypt India Nepal United_States --output work/prepared-seven
python -m pipeline.streaming build --preparations work/prepared-seven --expected-countries Australia Bangladesh Brazil Egypt India Nepal United_States --locked-evaluation reports --baseline-reports reports/releases/two-country-841998b --model-revision seven-country-v1 --baseline-commit 841998b --output work/baseline-build
```

Remove `--locked-evaluation reports` only when intentionally running model selection and evaluation again. A changed source snapshot is a new analysis revision, even if the command succeeds.

The baseline exporter predates several later features. It does not run the outage marker, area export, 2025 extension, final weekly-rhythm exporter, FRP exporter, seasonal payload exporter or annual correction builder. The following stages are needed for those outputs. Run mutating rebuilds in a separate checkout and compare their reports before replacing committed data. A successful baseline build alone does not reproduce every current panel.

The later scripts usually read `web/public/data/` and `reports/` in their checkout. They do not automatically discover the isolated baseline output. Before running them on a reproduction, stage the generated `pipeline/public/data/` (or `work/baseline-build/public/data/`) in that scratch checkout and verify that its frozen model and source snapshot match. Do not mix newly fitted coefficients with the old FRP or seasonal receipts; their hash checks should reject that combination. This staging and comparison is a release-review step, not an implemented one-command exporter.

## Apply calendar exclusions, then build area cells

On newly generated, unmarked daily payloads in the scratch checkout:

```powershell
python -m pipeline.review.no_observation --check-only
python -m pipeline.review.no_observation
```

The marker checks the pre-existing seasonal tables before writing. It refuses national files that are already marked. It must run before the 2025 extension, while the seasonal baseline still contains only the original historical years. See [the outage report](../reports/review/OUTAGES.md) and [the marker](../pipeline/review/no_observation.py).

Area commands take archive-root directories, not individual year directories. Replace the example root with a directory containing `modis/<year>/...csv` and `viirs-snpp/<year>/...csv`:

```powershell
$archiveRoot = "C:/path/to/archives"
python -m pipeline.area_cells count $archiveRoot --out work/area_counts --workers 12
python -m pipeline.area_cells build --counts work/area_counts --out web/public/data/area
```

Additional archive roots can follow `$archiveRoot`. The current selector reads MODIS 2002-2013 and VIIRS 2013-2025; the extra VIIRS year supplies local-date spill into the end of the historical record. This is more precise than the shorter archive range in [REPRODUCE.md](../REPRODUCE.md). The output itself covers 2003-2024.

Unlike the exact-count preparation stage, the area and extension counters reuse caches based on file modification times, not source hashes. Use fresh count directories for a source-level reproduction. Do not reuse one output directory across different archive snapshots, or supply duplicate archive filenames from several roots; their cache filenames can collide. Compare the source hashes with the release manifest separately.

The build uses the frozen national model and writes [reconciliation.csv](../reports/review/area/reconciliation.csv). The released files contain 41,736 cells, with monthly values stored in tenths of Aqua-reference-equivalent detections. The [area report](../reports/review/area/RECONCILIATION.md) records the country counts and sizes. Its largest monthly relative discrepancy is Egypt's 0.5647946% in January 2013; the released area input omitted the preceding VIIRS archive needed for eastern local-date spill. The command's year filter starts at 2013, so merely adding a 2012 file beside the inputs does not change that behavior. Local accuracy has not been validated.

Build area files before appending 2025 national rows. Their period and reconciliation target are the historical baseline, and outage-affected months are omitted in full.

## Append the 2025 daily extension

Use roots containing the 2024 and 2025 MODIS and VIIRS archives. A root already containing both years should appear only once:

```powershell
$extensionArchiveRoot = "C:/path/to/archives"
python -m pipeline.extend_2025 count $extensionArchiveRoot --out work/extend_2025
python -m pipeline.extend_2025 build --counts work/extend_2025 --dry-run
python -m pipeline.extend_2025 build --counts work/extend_2025
```

The builder requires unextended national and selected-cell files. It refuses a country that already contains 2025 rows; do not run it on the checked-in extended files. It appends 365 dates per country and selected daily cell with the frozen conversion. The calibration bounds are null because the training bootstrap is not rerun. The seasonal tables, anomaly flags and official evaluation remain unchanged. See [the implementation](../pipeline/extend_2025.py) and [extension receipt](../reports/review/extend2025/summary.json).

The outage and extension scripts update JSON, not the earlier static country CSV/ICS exports. For example, [United_States.csv](../web/public/data/United_States.csv) ends on 2024-12-31. The app's download controls generate files from the current loaded rows or selected guide year; use those for the current selection. `--dry-run` skips the extension's daily-file writes but still writes its continuity reports.

The [continuity table](../reports/review/extend2025/continuity_2025.csv) is the comparison target:

| Country | 2025 bias against Aqua | Weekly correlation |
| --- | ---: | ---: |
| Australia | +16.4% | 0.982 |
| Bangladesh | -6.6% | 0.987 |
| Brazil | -21.4% | 0.962 |
| Egypt | +50.0% | 0.305 |
| India | -11.1% | 0.942 |
| Nepal | -17.6% | 0.987 |
| United States | -7.0% | 0.845 |

These are continuity results beyond the original test period, not a new claim of validated accuracy. The [extension report](../reports/review/extend2025/CONTINUITY.md) documents the partial gap on 12 November 2025 and the missing next-archive spill at the western end of the year. The annual globe and custom-area files still stop at 2024; the selected daily-cell records do include 2025.

## Rebuild the weekly-rhythm and review outputs

The official script expects a root with `modis/<year>/...` and `viirs-snpp/<year>/...`, containing only the 2013-2024 archives for all seven countries. Its loader recursively reads CSVs without enforcing those study-year bounds. Reusing the larger baseline archive root would change the analysis. Prepare a separate root, as required by [REPRODUCE.md](../REPRODUCE.md):

```powershell
$rhythmArchiveRoot = "work/rhythm-archives"
python -m pipeline.download --countries Australia Bangladesh Brazil Egypt India Nepal United_States --years 2013 2024 --data-dir $rhythmArchiveRoot
python reference/kill_test.py $rhythmArchiveRoot --label "REAL FIRMS DATA"
```

Existing verified archives can be copied into that year-limited layout instead of downloaded again. The official script writes `kill_test_results.csv`, `kill_test_gate.json`, `kill_test_diagnostics.json` and its figure in the current working directory. Review those outputs before copying them into the scratch checkout's `reports/official/`. Keep the working-directory results CSV too: the new-active-cell script reads that exact filename.

The official [diagnostics](../reports/official/kill_test_diagnostics.json) record 54,168,264 loaded rows, 46,765,553 vegetation detections and 2,435,621 static-source control detections. The [gate](../reports/official/kill_test_gate.json) records a pass. Those numbers belong to that analysis scope; they should not be substituted for the baseline build's different source and year totals.

The supplementary commands are:

```powershell
python -m pipeline.review.harmonization_review
python reference/rhythm_map.py $rhythmArchiveRoot --out work/rhythm-map
python reference/rhythm_review.py $rhythmArchiveRoot work/rhythm-review
python reference/ignition_test.py $rhythmArchiveRoot work/new-active-cells
python -m pipeline.review.weekday_shapes
python -m pipeline.review.control_check $rhythmArchiveRoot --out work/control-review
python -m pipeline.review.noaa20_check C:/path/to/noaa20-archives
```

Review the regenerated map files before copying them into `reports/official/`, the new-active-cell outputs into `reports/review/ignitions/`, and the control outputs into `reports/review/controls/` in the scratch checkout. Passing the raw archive root to the control script is necessary to regenerate the Kilauea and Alaska location checks; without it, the script only reruns its count-table comparisons. It still reads the committed reduced counts and saved eligible-year lists for its longer-period tests.

The NOAA-20 root must contain `viirs-jpss1/<year>/...csv`; the checker requires all its specified years for a country. Regional review also requires the boundary file described in [REPRODUCE.md](../REPRODUCE.md):

```powershell
python reference/ne_india_states.py $rhythmArchiveRoot reports/official/rhythm_cells.csv C:/path/to/ne_10m_admin_1_states_provinces.geojson work/ne-india-states
python reference/ne_india_review.py $rhythmArchiveRoot reports/official/rhythm_cells.csv C:/path/to/ne_10m_admin_1_states_provinces.geojson work/ne-india-review
python reference/rhythm_map.py $rhythmArchiveRoot --countries Bangladesh --rest-day Sun --out work/bangladesh-sunday
python reference/rhythm_map.py $rhythmArchiveRoot --countries Bangladesh --rest-day Fri --out work/bangladesh-friday
```

The Bangladesh commands recreate the cell tables; the previously recorded hill-tract selection and interpretation remain in [its report](../reports/review/bangladesh_hills/RESULT.md). Copy reviewed regional outputs into their matching locations under `reports/official/` or `reports/review/` only after comparing them with that source report.

Once the reviewed official and supplemental inputs are in place, generate the browser payload:

```powershell
python -m pipeline.rhythm --from-saved reports/rhythm_results.json --official reports/official --output reports/rhythm_robustness
python -m pipeline.rhythm_web
```

The `--from-saved` step derives checks from an existing strict run; it does not recreate that run from the official table. The baseline builder produces its own `reports/rhythm_results.json`; compare it before replacing the scratch checkout's saved strict result. The browser exporter reads the reviewed map, control and new-active-cell files, so running it before those stages would package older evidence. These scripts have different input scopes and are not all independent fresh-archive reruns. Their source reports and [weekly-rhythm guide](04-weekly-rhythm.md) describe those dependencies.

## Rebuild the seasonal, FRP and annual-alignment payloads

The seasonal study can be rerun from its preserved sufficient statistics and checked independently:

```powershell
python -m pipeline.review.season_check
python scripts/verify_season_check.py
python -m pipeline.review.season_payload
python -m pipeline.review.season_payload --check
```

The last command checks byte-for-byte reproduction of `season-comparison.json`. It does not download or re-clean archives. Inputs and their identities are documented in [SEASON_CHECK.md](../reports/review/season/SEASON_CHECK.md).

FRP source-level reproduction needs the original clean cache, source archives and saved aggregation tree bound by the [source snapshot](../reports/review/frp/source_snapshot.json):

```powershell
$originalDataRoot = "C:/path/to/original-data-checkout"
python -m pipeline.review.frp_test --data-root $originalDataRoot
python scripts/verify_frp_test.py --data-root $originalDataRoot --report-dir reports/review/frp
python scripts/plot_frp_test.py --report-dir reports/review/frp
python -m pipeline.review.frp_test --publish-only
```

The independent receipt is required before publication. A new archive download alone is insufficient for this exact-cache provenance gate. If only the committed verified reports are available, `--publish-only` rebuilds the small public payload and evidence; it does not reproduce the original analysis. The available commands and limits are in [FRP_TEST.md](../reports/review/frp/FRP_TEST.md).

Annual alignment uses verified prepared counts, the frozen model and the published exclusion dates:

```powershell
python -m pipeline.review.calendar_alignment --preparations work/prepared-seven
python scripts/verify_calendar_alignment.py --preparations work/prepared-seven
```

Substitute the preparation directory from the matching source snapshot, or pass multiple preparation directories. The [alignment report](../reports/calendar-confidence/OUTAGE_ALIGNMENT.md) records 5,756 corrected cell-years, 154 national annual comparisons and 1,848 selected-cell annual comparisons. A mismatched archive fingerprint is an error, not permission to force the correction onto another globe.

## Test and build

```powershell
npm ci --prefix web
python -m pytest tests -q --basetemp .test-temp/reproduction -o cache_dir=.test-cache/reproduction
npm --prefix web test
python -m pipeline.review.season_payload --check
python scripts/verify_season_example.py --check
python scripts/build_submission_facts.py --check
npm run build
```

Use a dedicated temporary directory for each concurrent test run. The comments giving test counts in [REPRODUCE.md](../REPRODUCE.md) describe an earlier revision; read the result printed by the current runner. [The calendar-confidence receipt](../reports/calendar-confidence/VERIFICATION.md) records a later run, but is still a dated receipt rather than a permanent test-count promise.

`scripts/verify_payloads.py` additionally compares baseline public files with saved processed Parquet and evaluation files. Pass matching `--public-dir`, `--processed-dir` and `--evaluation` paths. It is not a substitute for the extension and outage-specific checks on subsequently changed daily payloads.

Before hosting, measure the actual `dist/`:

```powershell
$assets = Get-ChildItem -LiteralPath dist -Recurse -File
Test-Path -LiteralPath dist/index.html
($assets | Measure-Object -Property Length -Sum).Sum
$assets | Where-Object { $_.Length -gt 25MB } | Select-Object FullName, Length
```

The last command must return no files. The 25 MiB limit is per asset. The older streaming route also enforces its own 50 MiB total target and returns an error if that target is exceeded. That target is stricter than the expanded site's recorded size: the [calendar-confidence build receipt](../reports/calendar-confidence/VERIFICATION.md) records 65,734,368 bytes. Do not describe the old target as a Cloudflare total-site limit or substitute a past size for the current build measurement.

## Deploy a reviewed revision

The site is a static Cloudflare Pages application at [cinderline-spaceapps.pages.dev](https://cinderline-spaceapps.pages.dev/). Deployment is explicit. The commands here document the release procedure; they are not part of a local documentation or test run.

After review, build and tests, deploy the intended clean revision:

```powershell
npx --yes wrangler@4.162.0 pages deploy dist --project-name cinderline-spaceapps --branch main
python scripts/verify_deployment.py --url https://cinderline-spaceapps.pages.dev/ --dist dist --report work/latest_deployment_verification.json
```

If authentication has expired:

```powershell
npx --yes wrangler@4.162.0 login --scopes account:read user:read pages:write
```

Project creation is a one-time step for a new account/project, not a requirement for updating the existing project. See [DEPLOYMENT.md](../DEPLOYMENT.md) for that command. Its opening "not yet deployed" statement is historical; the committed [deployment verification receipt](../reports/deployment_verification.json) also describes the older release and must not be cited as verification of the current site.

The verification script compares every built asset with its HTTPS response by SHA-256. It does not exercise calendar selection, evidence, sharing, area drawing or WebGL. Check those flows in a fresh browser, at desktop and phone widths, after a release.

`scripts/publish.ps1` combines tests, build, Git push and deployment. Its default remote is `github` and its default branch is `main`. It checks for a clean working tree but does not verify that the checked-out branch matches its `Branch` argument: it builds the checkout while pushing the named branch. Check `git branch --show-current` and `git log -1` before using it, and require the checkout to be the intended release branch and commit. Do not use it for a review-only task or when a push or deployment has not been approved.
