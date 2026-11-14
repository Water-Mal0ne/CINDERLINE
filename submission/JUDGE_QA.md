# Judge Q&A — twenty hard questions

Hotspots are satellite detections, not distinct fires. Source IDs link to committed reports and scripts in the source index below. New FRP and common-date season results are preserved as source-commit snapshots under `submission/evidence/`; including them here does not merge their branches or deploy them.

We reproduce a known weekly pattern in each satellite record separately. Independently, FIRETRACE tests whether its historical calendar survives a change of sensor and calibration.

## 1. Aqua was still observing. Why switch to converted VIIRS in 2013?

The product deliberately tests continuity on Aqua's reference scale. In this snapshot, complete local years require the annual UTC archive and both adjacent archive years; that makes 2013 the first eligible VIIRS year despite observations beginning in 2012. The switch does not imply Aqua stopped. Later VIIRS platforms provide a route beyond MODIS, but this release uses historical S-NPP data. NASA currently lists S-NPP FIRMS coverage ending on 2 November 2026; we do not claim it continues today. [S01, S13]

## 2. Why VIIRS 375 m rather than 750 m?

We use the FIRMS 375 m active-fire detection product, which improves sensitivity to smaller hotspots relative to MODIS's 1 km product. We did not compare alternative VIIRS products or prove that finer resolution is always more accurate. Retrieved FRP also has its own algorithm and sampling limits; a 375 m detection is not a 375 m burned-area measurement. [S01, S13]

## 3. Is the conversion ratio stable, and what about US decline?

Not established as stable. The reported trend intervals include zero, but the test-period VIIRS/Aqua ratio is about 39% higher than training in Egypt and 10% higher in the US. US weekly correlation against Aqua falls from 0.97 in 2020 to 0.74 in 2024. Orbit, product, observation and actual activity changes are not separated by this analysis. We retain those diagnostics rather than treating a national average as permanent calibration. [S03]

## 4. How well does harmonization work, and where does it fail?

Against Aqua on held-out 2020–2024 weeks, Nepal's mean absolute error is 43.3 for B1 and 11.3 for selected M1. Egypt still has +51.7% selected bias. Bangladesh's 2022 weekly comparison is particularly poor: about +114% bias and correlation 0.18. These measure satellite-reference agreement, not accuracy against true fires. National fit does not establish local-cell accuracy or operational suitability. [S02–S03]

## 5. Were the test years used to choose the model?

The core model trains on 2013–2017, selects B1 or M1 by daily validation MAE on 2018–2019, and evaluates the locked choice on 2020–2024. B0 is a comparison baseline. The source lock and independent reproduction preserve those choices. Later season-preservation diagnostics deliberately reuse the already-examined test years and are labelled retrospective; they do not create a fresh holdout or retune the model. [S01–S02, S10]

## 6. What does the evidence-card uncertainty band mean?

The evidence card lists daily conversion intervals; it does not sum them into a weekly confidence interval. Converted daily estimates use the 2.5th–97.5th percentile range across 200 whole-training-year bootstrap refits of calibration ratios. This represents calibration variability over the training years, not uncertainty about true fires or all observation error: clouds, missed overpasses and day-to-day conversion error remain outside it. Observed Aqua days require no conversion interval; that does not imply perfect observation. [S01, S08]

## 7. Did a second satellite independently validate the conversion?

A separate NOAA-20 check transfers the saved S-NPP-fitted model without refitting in the US, Nepal, Bangladesh and Egypt. Its converted series broadly agrees with converted S-NPP, while Egypt's disagreement with Aqua persists. This supports transfer between related satellite products, not independent ground-truth validation or a diagnosis of the bias's cause. The comparison still needs its own strict common-date outage sensitivity; the new season test does not resolve that separate limitation. [S09]

## 8. Was the Sunday pattern already known, and what is new here?

Yes: Earl, Simmonds and Tapper reported weekly fire cycles in 2015. We reproduce a known association separately in raw satellite streams. Our contribution is an inspectable calendar with baseline comparisons, explicit failures, retrospective tests of count versus seasonal agreement, and the fixed count-versus-FRP comparison. We do not claim first discovery or promise a prize. The official country rule passes US 3/3, Australia 3/3 and Brazil 2/3 streams; India, Nepal, Bangladesh and Egypt do not pass. [S04, S10–S11, S13]

## 9. Was any of this preregistered?

No. For the original rhythm gate, US and Nepal data were already in hand, and no Git record predates the first real-data run. For FRP, the local protocol was frozen before its first calculation, but Git receipt `92626ed2f76fc6ab1bcefa6254d49609b7c6b982` was created after the original result was known. It is an honest later record of the earlier local specification, not proof that the Git commit preceded results. Both use already-inspected historical records. [S12, S11]

## 10. Why is Brazil qualified?

The official raw-detection rule passes Terra and Aqua, not VIIRS. A stricter industrial-source control flags a Sunday dip in Terra over 2002–2024; the recheck localizes it to 2002–2007, with no significant dip in the official 2013–2024 window. Brazil passes all three streams in the separate newly active grid-cell test. Such a cell has detections after a day without detections; it is not a verified ignition. Neither check erases the unfavorable evidence. [S06]

## 11. Does Nepal's failed country rule mean there is no weekly pattern?

No. In a simulation using Nepal's observed volume, a planted 20% Saturday dip passes the country rule only 12% of the time, while VIIRS alone is significant in 84.5% of simulations. That is conditional simulation power, not a measured real-world detection probability or proof of no pattern. Nepal's actual VIIRS Saturday index is 1.015; the country rule does not establish a dip. [S04–S05]

## 12. Can the Sunday dip identify human ignition, and what about Kilauea?

No: a weekday association identifies neither who burns nor why. Controls are imperfect. US volcanic detections have a VIIRS Sunday index of 0.861, largely from Kilauea; removing Kilauea's 2018 detections removes corrected significance. Aqua and the Alaska subset do not reproduce that significant Sunday result. This unexplained single-platform pattern cautions against dismissing all sampling effects. Industrial controls can themselves follow schedules, so even a control test is not a causal verdict. [S06]

## 13. Why is there no established dip in Punjab?

The reported Punjab/Haryana check has no significant weekly dip. More broadly, none of the 201 tested cells mostly inside India outside the northeast is significant. This is a null result under the specified sampling and tests, not proof of no human activity, a different fire cause, or a universal absence of weekly structure. We do not invent a cultural or weather explanation. [S07]

## 14. What explains northeast India, and did the Bangladesh prediction work?

The northeast map is exploratory and the cause remains unresolved. Restricting to cells mostly inside India leaves 14 significant cells out of 21; border geometry affects the deeper-looking pooled result. A separately pre-committed prediction of no Sunday dip in Bangladesh's Chittagong Hill Tracts failed: one of two eligible cells has a significant dip in both VIIRS and Aqua. With so few eligible cells it is a limited test, and the failed prediction stays visible. [S07]

## 15. Can users draw any area or interpret the globe as burned area?

No arbitrary-area daily selection is supported. The release has national series and 12 training-selected daily cells per country; national totals use all qualifying cells. The annual globe covers broader occupied cells, but its colors are converted observation totals on a fixed logarithmic scale. They are not burned area, area-normalized density, or proof of no fire in uncolored locations. National seasonal summaries remain national when a cell is selected. [S08]

## 16. How are outages and genuine zero observations handled?

The production calendar marks 38 VIIRS-supplied dates per country as “no observation,” from documented outages and previously flagged common zero-detection days. It preserves recorded source counts for inspection. These are distinct from retained dates with zero recorded detections. Official held-out metrics and annual globe totals were not recomputed with that mask. The separate season sensitivity removes the common Aqua/VIIRS union of 73 dates, then 87 with padding; those totals use only retained dates. None of these masks certifies complete clear-sky coverage. [S08, S10]

## 17. What exactly passed in the count-versus-FRP test?

“In US daytime observations from 2013-2024, the Sunday deficit was stronger in detection counts than in summed fire radiative power in MODIS Aqua and VIIRS S-NPP, under a pre-specified test.”

The same finite, nonnegative-FRP observations enter both measures. Aqua and S-NPP meet all fixed contrast and sensitivity criteria under both masks; Terra fails because its adjusted interval includes zero. Twelve year blocks drive uncertainty, not millions of independent detections. Independent recomputation passed. Summed FRP is sampled radiative power, not energy, emissions, burned area or distinct fire counts. The Git receipt is after the original result, as explained in question 9. [S11]

## 18. Does a better annual total guarantee a better seasonal calendar?

No. The **retrospective whole-year replacement control** compares simple B1 with selected M1, averaged equally over 2020–2024. India improves count agreement but worsens monthly-share TV against Aqua under the original calendar and both masks. Nepal's lower-TV direction also survives. These are descriptive means, not every-cut wins.

| Country / calendar | B1 → M1 absolute relative total error (%) | B1 → M1 monthly TV × 100 |
|---|---:|---:|
| India, original unmasked | 16.46 → 3.80 | 13.59 → 16.29 |
| India, primary common mask | 13.83 → 4.05 | 12.31 → 15.57 |
| India, padded common mask | 13.94 → 4.51 | 12.28 → 15.42 |
| Nepal, original unmasked | 83.34 → 7.91 | 14.55 → 4.51 |
| Nepal, primary common mask | 77.67 → 8.30 | 13.82 → 5.75 |
| Nepal, padded common mask | 76.74 → 8.06 | 13.79 → 5.69 |

Masked errors compare totals over **common retained dates**, not recovered complete-year totals. TV × 100 is monthly-pattern disagreement in points, not a percentage of fires misplaced. January whole-year controls are separate from the February–December artificial handover scenarios. No model was refitted. [S10]

## 19. Can FIRETRACE forecast fires or replace alerts?

No. It is a historical exploration prototype for comparing measurement records and inspecting seasons. Anomaly flags and exported ICS windows are descriptive references, not predictions, risk scores, emergency warnings or safe-burning advice. It may complement near-real-time monitoring, but user impact and operational suitability have not been validated. NASA does not approve or endorse this conversion. [S08]

## 20. What did AI do, and how can judges reproduce the work?

Codex and Claude Code assisted with analysis implementation, UI, testing, documentation and submission drafts. NASA FIRMS supplies the observations; synthetic fixtures are labelled and separate. The team must review all claims before submitting. Core commands and fixed model sources are in README/METHODS; season and FRP scripts, CSVs, input hashes and independent verification receipts are linked in the evidence ledger. Repository access must be confirmed for judges, and new branch results are not automatically deployed. [S01, S10–S12]

## Source index

The machine-readable evidence ledger and exact cross-branch source commits are in [SOURCE_LEDGER.md](evidence/SOURCE_LEDGER.md) and `evidence/source_manifest.json`. Those snapshots preserve reviewed results without implying their branches have merged.

- **S01 — Measurements, model and splits:** `METHODS.md`, `reports/harmonization_model.json`, `reports/selection_lock.json`; scripts `pipeline/harmonize.py`, `pipeline/streaming/prepared_runtime.py`.
- **S02 — Held-out error:** `reports/review/layer1_table.csv`, `layer1_table.md`, `layer1_reproduction_check.csv`, and `reports/harmonization_eval.csv`; script `pipeline/review/harmonization_review.py`.
- **S03 — Stability and failures:** `reports/review/ratio_trend.csv`, `layer1_per_year.csv`, `HARMONIZATION_REVIEW.md`, `LIMITATIONS.md`.
- **S04 — Official rhythm rule and results:** `reference/kill_test.py`, `reports/official/kill_test_gate.json`, `kill_test_results.csv`. Streams corroborate; they are not independent experiments.
- **S05 — Rhythm sensitivity and Nepal power:** `reports/review/RHYTHM_REVIEW.md`, `rhythm/b5_nepal_power.csv`; script `reference/rhythm_review.py`. The power experiment is synthetic, conditional on observed volume.
- **S06 — New-cell and control diagnostics:** `reference/ignition_test.py`, `reports/review/ignitions/IGNITIONS.md`, `e1_ignition_results.csv`; `pipeline/review/control_check.py`, `reports/review/controls/CONTROLS.md`. Legacy filenames use “ignition”; our interpretation does not treat those detections as verified ignitions.
- **S07 — Exploratory geography and failed prediction:** `reports/review/NORTHEAST_INDIA_REVIEW.md`, `reports/review/bangladesh_hills/RESULT.md`; scripts `reference/ne_india_review.py`, `reference/rhythm_map.py`.
- **S08 — Product scope, missing observations and limits:** `README.md`, `LIMITATIONS.md`, `reports/review/OUTAGES.md`, `no_observation_summary.json`, `CUSTOM_AREA.md`; script `pipeline/review/no_observation.py`.
- **S09 — NOAA-20:** `reports/review/noaa20/NOAA20.md`, `noaa20_conversion_check.csv`, `noaa20_rhythm_stream.csv`; script `pipeline/review/noaa20_check.py`.
- **S10 — Season sensitivity:** `submission/evidence/season/SEASON_CHECK.md`, `whole_year_comparison.csv`, `summary.json`, independent verification; source branch script `pipeline/review/season_check.py`, checker `scripts/verify_season_check.py`. Original six-row India/Nepal summary remains at `reports/review/season/original_whole_year_comparison.csv`.
- **S11 — Fixed FRP comparison:** `submission/evidence/frp/FRP_TEST.md`, `summary.csv`, original protocol and independent verification; source branch script `pipeline/review/frp_test.py`, checker `scripts/verify_frp_test.py`. The ledger pins the branch commit and distinguishes local protocol timing from the later Git receipt.
- **S12 — Chronology and assistance:** `DECISIONS.md`, `AI_DISCLOSURE.md`, and the FRP protocol receipt. The detailed chronology in question 9 qualifies any broad “before analysis” wording elsewhere.
- **S13 — Primary external context:** [NASA FIRMS notes](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php), [VIIRS product description](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html), and [Earl, Simmonds and Tapper (2015)](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2015GL066383). External facts were checked on 15 November 2026 Nepal time; they are source facts, not outputs of our analysis.
