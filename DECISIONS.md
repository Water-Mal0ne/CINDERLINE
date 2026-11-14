# Implementation decisions

## Scope and delivery

- The user requested continued implementation, distinct builder/checker/creative roles and successive independent reviews. Up to three agents work alongside the coordinator, with separate file ownership; additional roles rotate through those slots. The coordinator integrates and publishes tested changes.
- The implementation uses Python analysis and a static Vite/React/TypeScript application. The user's later explicit 3D Earth request overrides the original brief's no-3D preference. No chatbot, forecasts or ignition classifier was added.
- Nepal and the United States were built first. The historical phase-2 release at commit `841998b` contains a 76-archive snapshot, 10,142,672 cleaned records and 15,118 annual grid cells. Its selected models and evaluation are retained in Git rather than silently relabeled as seven-country results.
- The expanded release, `seven-country-v1`, includes Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States: 273 archives, 74,187,339 raw records, 67,934,899 cleaned detections, 41,986 annual cells and 731,276 national/detailed daily rows. All countries use the supported 2003–2024 local-year range.
- Worldwide expansion remains deferred. A complete seven-country manifest does not imply global observation coverage. [Space Apps Navigator guidance](https://github.com/nasa/spaceapps/discussions/2016) supports a selected-area implementation and emphasizes the harmonization method.
- National totals include all qualifying cells. Daily exploration contains 12 cells per country selected using training-period activity. All 41,986 contributing cells appear in the annual globe, but only 84 have daily drill-down. The accessible fallback lists the 20 highest-activity annual cells for a country/year.

## Exact-count processing and payloads

- The additive `pipeline.streaming` route cleans annual archives in bounded chunks, preserves exact count multiplicities and reduces repeated keys on disk. It never expands count rows back into individual detections. The original smaller raw-record `pipeline.run_all` route remains available; it is not the seven-country release command.
- Before changing country scope, independent checks reproduced the original two-country ratios, selections, evaluation CSV, all 208,936 daily rows, bootstrap bounds and annual globe values exactly. This establishes route equivalence for the same input snapshot.
- The new model legitimately refits the global B1 training ratio for seven countries, also changing M1's shrinkage target. Training, validation and test windows remain 2013–2017, 2018–2019 and 2020–2024. All country selections are frozen before held-out evaluation. Rebuilding presentation layers can reuse the saved, identity-checked lock rather than select/test again.
- The original seven-country static projection was 133,213,075 bytes. `column-dictionary-v1` reduces repeated daily fields without rounding, truncating dates, discarding cells or changing scientific values. The actual frontend decoder matched all 731,276 original records exactly. The projected site is 51,973,329 bytes (49.57 MiB); the final compiled build must remain under the 50 MiB target. CSV/ICS and the full annual globe are retained.
- Cached inputs retain their own source manifests and code hashes. Additional raw files do not silently join an earlier snapshot. Model revisions identify the calibration country scope and archive fingerprint.
- Geographic context comes from public-domain Natural Earth through world-atlas 2.0.2. Land and outlines are not FIRMS observations or satellite coverage masks.

## Final-night story review, 15 November 2026 Nepal time

- 2026-11-14 19:10 UTC: Work on the named feature branches and open reviewable PRs; preserve main at 290e756, the original UI backup, and the Workers migration worktree. Do not merge, deploy, log in, or rewrite history overnight.
- 2026-11-14 19:12 UTC: Treat the existing submission/ documents as the canonical slide, video, project-page, status and judge-Q&A paths; do not create duplicate root documents for names absent from this checkout.
- 2026-11-14 19:12 UTC: Describe rhythm as a separate analysis of original satellite streams, reproducing a known weekly pattern; do not imply harmonization discovered it or identified ignition causes.
- 2026-11-14 19:12 UTC: The India retrospective example compares the simple B1 conversion with selected M1, not raw VIIRS with conversion. Preserve its unmasked values and identify the pending common-date sensitivity separately; commit a reproduction script using the existing national sufficient statistics and frozen model.
- 2026-11-14 19:12 UTC: Use newly active grid cells for the recurrence proxy, not verified new ignitions; a nonsignificant country result does not establish absence of a pattern. Preserve every official number and gate decision.
- 2026-11-14 19:12 UTC: Distinguish NOAA-20 transfer corroboration from ground-truth validation, simulated power from exclusion of an effect, and calendar outage masking from unchanged model-evaluation and globe totals.
- 2026-11-14 19:12 UTC: The FRP contrast was already calculated before this overnight brief. Preserve the original timestamped protocol and hash; any new Git packaging commit must explicitly state that it follows the known result and cannot serve as a prior Git prediction.

- 2026-11-14 19:18 UTC: Independent review found residual overstatements in METHODS/LIMITATIONS and prior-timing language in README/slides; correct these in an additive follow-up commit, retain all numerical values, and rerun all checks. The initial build required sandbox escalation for esbuild file access; the same source built successfully without code changes.

- 2026-11-14 20:20 UTC: Preserve the original story-review section while moving it before scientific interpretation; mirror the corrected AI chronology and NOAA-20 transfer/coverage qualifications across story and submission, and synchronize the story season answer with the verified masked comparison. No scientific values, official decisions or historical protocol text change.

## Scientific interpretation

- A disappearing sensor-era jump is not a success criterion. Models are selected on validation daily MAE; genuine changes may remain. The simpler B1 is selected in Australia, Brazil and the United States; M1 is selected in Bangladesh, Egypt, India and Nepal.
- The raw display follows eligible source periods: Aqua in 2003–2012, VIIRS in 2013–2024. The 2013 transition follows archive eligibility; a forced 2012 switch must not manufacture a required discontinuity or missing baseline.
- The annual globe always uses the Aqua reference scale and a fixed all-year logarithmic color mapping. Raw/harmonized comparison controls do not convert the globe into a raw sensor-count map. Actual 0.25-degree grid centers and footprints are used; area-normalized density and burned area are not claimed.
- Every measurement is identified as satellite detections or an Aqua-equivalent estimate, not independent fires. Complete input archives do not prove cloud-free satellite observing exposure. Zero archived detections, unknown observation coverage and unprocessed geography remain distinct.
- Whole-training-year bootstrap bounds describe calibration uncertainty only. Equal conversion bounds on observed Aqua mean identity/no conversion, not perfect measurement certainty.
- The weekly research algorithm keeps per-stream analysis, IANA civil dates, weekday exposure adjustment, seeded year resampling, corrected tests and matched controls. The streaming route additionally enforces first complete instrument-year guards before archive/local-period qualification.
- The official rhythm decision is the gate pre-specified in `reference/kill_test.py` (pass: US 3/3 streams, Australia 3/3, Brazil 2/3). The stricter gate in `pipeline/rhythm.py` / `pipeline/streaming/weighted_rhythm.py` changed the pre-specified rule after the fact, so it is reported only as robustness checks next to the official decision. In the 2002–2024 release analysis, Brazil's matched static control is flagged; this is stated plainly in the app and LIMITATIONS.md. No threshold or control rule is relaxed or tightened to change the story.
- Agreement among instruments observing overlapping events is corroboration, not independent replication. Weekly associations do not establish ignition cause. Static controls can themselves follow human schedules; a nonsignificant control is not proof of no bias.
- Synthetic fixtures and figures are visibly labeled and kept separate. They cannot enable a real-data rhythm claim.
- Calendar weeks begin January 1. Seasonal/anomaly statistics require seven distinct observed dates in bins 1–52 and exclude the target year from its anomaly history. The final one- or two-day bin remains inspectable but is not compared with complete weeks. ICS windows describe historical seasonality, not forecasts.

## Partial scope retained explicitly

- No validated pre-Aqua Terra bridge or 2000–2002 reconstruction is included. The supported record begins in 2003; no 2000-present claim is made.
- A prespecified 0.25°/0.5° selected-cell diagnostic is complete on 2018–2019 with fixed model weights and training-only cell selection. National invariance is an arithmetic property; coarse-cell improvements do not establish spatial robustness. Large selected-cell US/Egypt errors remain explicit, and the product grid stays 0.25 degrees.
- An early Terra bridge was investigated using a 2003–2007 training block and separate 2008–2011 validation. It improves count agreement but leaves timing and reconstruction-uncertainty issues unresolved. No 2001–2002 series is added. Neither new check touches the 2020–2024 held-out metrics or retunes the production model.
- Arbitrary daily grid selection, worldwide data, land-cover stratification, the optional M2 model and festival analysis are not implemented.
- The shareable evidence journey is the working signature: one observed week, separate sensors, a named conversion, held-out validation and a reopenable link. The human rhythm view is a second act with its own tab; the evidence journey does not depend on it.
- Links reopen current published data rather than a frozen dataset version. Camera position, annual-cell selection and Earth/table preference are deliberately excluded and disclosed.
- The submission page, slide outline and video script are drafts. A finished recording and actual submission are separate tasks; their existence is not inferred from a script.

## Publication

- At the user's request, the public application uses free Cloudflare Pages. The initial private Sites preview remains separate. See `DEPLOYMENT.md` for the exact deployed revision rather than assuming the newest local data is already live.
- The GitHub repository is public so judges can read the source.
- Raw archives, caches, credentials, dependencies and the Python environment are excluded from Git. The repository contains reproducible analysis code, source manifests, processed static data and reviewable reports.

## Human rhythm integration (14 November 2026)
- Official decision = pre-specified `reference/kill_test.py`, seven countries, 2013–2024, outputs in `reports/official/`. Per-day 95% intervals were added to its CSV as an output-only change; all other numbers are byte-identical.
- Robustness checks are derived from the stricter seven-country release analysis (`reports/rhythm_results.json`, 2002–2024) with `python -m pipeline.rhythm --from-saved`, without re-estimating anything. The US and Australia meet all checks. Brazil fails the matched static-control check (Terra static-source index 0.913, adjusted p = 0.021); on 2014–2023 alone the same control was clean (`reports/rhythm_robustness_2014_2023/`). A year-level recheck shows the dip comes entirely from 2002-2007 and the control is flat over 2013-2024 (`reports/review/controls/CONTROLS.md`). The official result is unchanged.
- The human rhythm view is a standalone tab for all seven countries. The earlier locked per-region rhythm panel now links to it.
- The per-cell map is exploratory. A regional finding is featured only if it survives Benjamini-Hochberg correction and Aqua agrees; the northeast India boundary was drawn after viewing the map and is stated as such. No cultural or religious explanation is given in the app or docs.
- No Terra-to-Aqua bridge is used in the product; the supported calendar record starts in 2003.

## Gate timeline (review B6, 14 November 2026, Nepal time)

Why the word is "pre-specified", not "pre-registered": no committed record shows the gate rule before any real data were analysed.

- 15:27 - synthetic test of the kill test (`test/make_fake_data.py`, `kill_test_FAKE_DATA_example.png`; local file times).
- 15:30 - United States and Nepal FIRMS archives downloaded (local file times).
- 15:45 - the gate rule is written in the team's build brief (`FIRETRACE_codex_prompt.md`, section 7: rest days, two-stream rule, US plus two other countries). Local file time; the brief is not in this repository.
- 15:51 - first real-data result files of the kill test (US and Nepal, version 1 script) created in the analysis folder (local file times). The team brief to Claude Code lists these version-1 results.
- about 15:56 - version 2 of `kill_test.py` (writes `kill_test_gate.json`) last saved before the 7-country analysis; this modification time was observed at the start of the Claude Code session.
- 15:58 onward - Australia, Bangladesh, Brazil, Egypt and India archives downloaded (local file times), after the rule was written.
- 16:12 - first repository commit `94ba102` (EileyDeezNuts, Codex build): adds `reference/kill_test.py` (v2) together with US and Nepal real-data results, and `pipeline/rhythm.py` with the stricter gate (verified adjacent-year archives, upper bound below 1, matched per-country controls).
- about 17:10 - official 7-country run of `kill_test.py` (Rohit Poudel with Claude Code): decision pass.
- 17:56 - commit `e71f214` (EileyDeezNuts): stricter gate run on seven countries; Brazil's matched control flagged.
- 18:12-18:19 - commits `a062a19`, `a0be600` (Rohit Poudel with Claude Code): official outputs committed; stricter checks reported as robustness checks.

So the rule and rest days were fixed before the data for five of the seven countries were downloaded, but after the US and Nepal data were in hand and around the time the first US and Nepal results were produced. Local file times are not a committed record.

## Out-of-sample prediction: Bangladesh hills (review E2), written before the analysis

Prediction: the Chittagong Hill Tracts (hill shifting cultivation, communities mostly not Christian) will NOT show a significant Sunday dip, unlike India's northeastern hill states.

Test, fixed before running: the per-cell method of `reference/rhythm_map.py` (VIIRS for the map, Aqua as a check; 1-degree cells with at least 300 detections a year on average and 8 usable years; Benjamini-Hochberg at 5%) applied to Bangladesh with Sunday as the tested day. Cells are counted as Chittagong Hill Tracts if their centroid falls in Rangamati, Khagrachari or Bandarban districts, or otherwise if their centroid lies east of 91.5 E and south of 23.5 N. The prediction holds if no such cell has a significant Sunday dip. No Bangladesh per-cell result had been computed when this was committed.

Result (added after the analysis): the prediction did NOT hold. Of the two hill-tract cells, 21N 92E has a significant Sunday dip in VIIRS (0.490, q 0.0004) and Aqua (0.564, q 0.020); 22N 92E does not (0.745, q 0.089). The prediction was committed in `5adb21a90e781ce642b17c9aee9915a600c84dda`. See `reports/review/bangladesh_hills/RESULT.md`.
