# Judge Q&A: the hardest questions, with honest answers

Every number is from a committed report (path in brackets). "Detections" are satellite hotspot detections, not fires. Questions 8, 9, 15, 19 and 20 cite the source index at the end ([S..] codes).

We reproduce a known weekly pattern in each satellite record separately. Independently, FIRETRACE tests whether its historical calendar survives a change of sensor and calibration.

**1. Aqua flew the whole time. Why switch to converted VIIRS from 2013?**
The product tests continuity on Aqua's reference scale; it does not imply Aqua stopped observing. Requiring adjacent UTC archives for complete local years makes 2013 the first eligible VIIRS year in this snapshot, despite observations beginning in 2012. The release uses historical S-NPP data. NASA currently lists S-NPP coverage ending on 2 November 2026; NOAA-20 and NOAA-21 are separate, more recent VIIRS platforms, not substitutes silently added here. On held-out 2020-2024 weeks, converted VIIRS tracks Aqua with weekly r = 0.73-0.98 depending on country [METHODS.md, reports/review/layer1_table.md; NASA FIRMS product coverage: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html].

**2. Why the 375 m VIIRS product and not the 750 m one?**
The 375 m I-band product is the standard VIIRS active-fire product in the FIRMS country archive and is more sensitive to small fires. The 750 m product is not in the country archive; we did not compare the two [METHODS.md].

**3. Is the VIIRS-to-Aqua ratio stable, given Aqua's orbit drift?**
No country shows a trend distinguishable from zero over 2013-2024 (year bootstrap). But in the test years the ratio is 39% above training in Egypt and 10% above in the US, and the US weekly correlation falls from 0.97 (2020) to 0.74 (2024). We cannot separate orbit drift from real change [reports/review/ratio_trend.csv, LIMITATIONS.md].

**4. Does harmonization beat the naive join?**
Yes, by a wide margin, against Aqua on untouched 2020-2024 weeks: raw VIIRS (B0) is biased +357% to +3,136%; the selected model is within +/-11% except Egypt (+52%) [reports/review/layer1_table.md].

**5. How do we know the test years were not used to choose the model?**
Training 2013-2017, model choice on 2018-2019 validation MAE, test 2020-2024 evaluated once after the choice was locked [reports/selection_lock.json]. Recomputing the weekly test metrics from the published series reproduces the official numbers exactly [reports/review/layer1_reproduction_check.csv].

**6. What does the uncertainty band on a converted week mean?**
The evidence card lists daily conversion intervals; it does not sum them into a weekly confidence interval. Each converted daily interval is the 2.5-97.5 percentile range across 200 bootstrap refits of the conversion ratio over the five training years. It is not a 95% confidence interval for true detections; it ignores cloud, observation and day-to-day conversion error. Observed Aqua days need no conversion interval, which does not imply perfect observation [METHODS.md, web/src/App.tsx].

**7. Where does the harmonization fail?**
Egypt is biased high in every test year (+36% to +66%); Bangladesh 2022 fails (bias +114%, r 0.18); Brazil runs 10-14% low from 2021 [reports/review/HARMONIZATION_REVIEW.md]. The MODIS product version field also changes across the training, validation and test windows (6.2, 6.03, 61.03) [METHODS.md].

**8. Was the Sunday pattern already known, and is the result stable under the reported checks?**
Yes: Earl, Simmonds and Tapper reported weekly fire cycles in 2015. We reproduce a known association separately in raw satellite streams. Our contribution is an inspectable calendar with baseline comparisons, explicit failures, retrospective tests of count versus seasonal agreement, and the fixed count-versus-FRP comparison. We do not claim first discovery or promise a prize. The official country rule passes US 3/3, Australia 3/3 and Brazil 2/3 streams; India, Nepal, Bangladesh and Egypt do not pass. [S04, S10–S11, S13] The US Sunday dip is large (Sunday 22-33% below an average day in all three satellites) and stable: leaving out any one year never changes the lowest day. Re-running the null test with 200,000 draws instead of 5,000 changes no significance call [reports/review/RHYTHM_REVIEW.md].

**9. Was any of this preregistered?**
No. For the original rhythm gate, US and Nepal data were already in hand, and no Git record predates the first real-data run. For FRP, the local protocol was frozen before its first calculation, but Git receipt `92626ed2f76fc6ab1bcefa6254d49609b7c6b982` was created after the original result was known. It is an honest later record of the earlier local specification, not proof that the Git commit preceded results. Both use already-inspected historical records. [S12, S11]

**10. Brazil?**
Suggestive, not clear. Terra and Aqua pass; VIIRS does not (Sunday is not its lowest day in 11 of 12 leave-one-year-out runs). Brazil's Terra industrial-source control dips on Sunday over 2002-2024, but the dip comes entirely from 2002-2007; over 2013-2024, the window fixed for the rest-day test, the control is flat. Brazil's Sunday dip is weaker on raw detections (VIIRS does not pass) but passes in all three satellites on newly active grid cells: detections after a day without a detection, not verified ignitions. Because of the 2002-2024 control, Brazil does not meet the stricter check (Terra index 0.913, adjusted p = 0.021); the official pre-specified result is unchanged (PASS). [reports/review/controls/CONTROLS.md, reports/review/ignitions/IGNITIONS.md, reports/review/RHYTHM_REVIEW.md]

**11. Nepal shows nothing. Does that mean no human scheduling there?**
No. The country rule has low sensitivity in the reported simulation: with Nepal's real volume, a planted 20% Saturday dip passes only 12% of the time (VIIRS alone catches it 85% of the time). Nepal's real VIIRS Saturday index is 1.015. Simulation power does not itself rule out a 20% dip or establish the absence of scheduling; a 10% dip could be missed. These are conditional results for a specified observation/simulation model, not a classification of Nepal's fire causes. [reports/review/rhythm/b5_nepal_power.csv, reports/official/kill_test_results.csv]

**12. Does a Sunday dip prove people set the fires?**
No. A weekly association does not identify ignition cause. Supporting checks: the dip is sharper on newly active grid cells in the US (0.59-0.70) and Brazil; these are cells detected after a day without a detection, not verified ignitions. The US and Brazil industrial-source controls are flat over 2013-2024. A caveat: US volcano detections show a Sunday dip in VIIRS only (0.861), almost entirely from Kilauea and sensitive to the 2018 eruption year; Aqua and Alaska's volcanoes show none, and the larger US industrial-source control is flat in all three satellites over 2002-2024. These imperfect controls do not exclude every sampling or processing effect. The single-volcano, single-satellite result remains unexplained and visible. [reports/review/ignitions/IGNITIONS.md, reports/review/controls/CONTROLS.md]

**13. Punjab burns crop residue every year. Why no dip there?**
Punjab and Haryana cells show no weekly dip (median Sunday index 1.10, none significant); the rest of India outside the northeast is the same (0 of 201 cells mostly inside India significant, median 1.055). We report it as a null result and do not explain it [reports/review/NORTHEAST_INDIA_REVIEW.md].

**14. What explains the northeast India dip?**
Unresolved. It is consistent across time (Nagaland, Mizoram and Manipur cells below 1 in 12 of 12 years in VIIRS and Aqua) but partly a border effect: the five deepest cells lie mostly outside India; cells mostly inside India give 14 of 21 significant (median 0.717). A pre-committed out-of-sample prediction that Bangladesh's Chittagong Hill Tracts would show no Sunday dip failed in one of two cells [reports/review/NORTHEAST_INDIA_REVIEW.md, reports/review/bangladesh_hills/RESULT.md].

**15. Can I pick my own area, and can this forecast fire or replace alerts?**
Areas: the calendar covers national totals plus 12 daily grid cells per country; drawing an arbitrary area is not supported in this release (it would exceed the site's size budget). Forecasting: no. The calendar is historical and descriptive, complementary to near-real-time alert systems such as ICIMOD's, not a replacement [README.md]. Anomaly flags and exported ICS windows are descriptive references, not predictions, risk scores, emergency warnings or safe-burning advice. User impact and operational suitability have not been validated. NASA does not approve or endorse this conversion. [S08]

**16. What about satellite outages?**
The calendar masks outages of the stream supplying its value, plus flagged days with no detections in any of the seven countries: 38 days per country, all in 2022 and 2024, are marked "no observation" (grey) and excluded from typical-season statistics and anomaly flags. The documented Aqua outages fall in years supplied by converted VIIRS and therefore do not remove calendar values. Held-out evaluation and annual globe totals were not recomputed with these masks. [reports/review/OUTAGES.md]

**17. Does the conversion hold on another satellite?**
The reported four-country check (India, Australia and Brazil did not finish downloading) supports transfer to a second VIIRS platform, not independent ground-truth accuracy. NOAA-20 VIIRS, converted with the saved S-NPP-fitted model and no refitting, matches the released converted S-NPP series in the test years 2020-2024: United States +1.3% (weekly r 0.984), Nepal +0.6% (r 0.989), Bangladesh -0.5% (r 0.987), Egypt -2.6% (r 0.829). Egypt's high bias against Aqua persists with NOAA-20 (+47.7%); that shared discrepancy does not isolate its cause. The saved comparison still needs a strict common-date outage sensitivity, because a partly masked S-NPP week can be compared with a fuller NOAA-20 week. As a separate fourth rhythm stream, NOAA-20 also shows the US Sunday dip (0.832, p 0.0002). [reports/review/noaa20/NOAA20.md, pipeline/review/noaa20_check.py]

**18. Does a better annual total guarantee a better seasonal calendar?**
No. In the original retrospective, unmasked whole-year replacement experiment for India, comparing B1 with the frozen selected M1 across 2020-2024, mean absolute annual count error improves from **16.46% to 3.80%**, while monthly-share total-variation disagreement (**TV x100**) worsens from **13.59 to 16.29**. Both metrics use Aqua as the reference, not ground truth; this compares two conversions, not raw VIIRS with conversion. The original results are preserved in `reports/review/season/original_all_country_whole_year_comparison.csv`.

The direction survives both common-date outage masks. India's B1-to-M1 count error is **13.83% to 4.05%** with the primary mask and **13.94% to 4.51%** with one-day padding; seasonal TV worsens **12.31 to 15.57** and **12.28 to 15.42** respectively. Nepal's seasonal TV improves **13.82 to 5.75** and **13.79 to 5.69**. These compare totals and monthly shares over commonly retained dates, not reconstructed full-year activity. They are descriptive means of previously examined years, not new significance tests or guarantees for every cut/year. Sources: `reports/review/season/whole_year_comparison.csv`, `SEASON_CHECK.md` and independent verification. Reproduce with `python -m pipeline.review.season_check` and `python scripts/verify_season_check.py`. Production models and official results remain unchanged.

**19. What exactly passed in the count-versus-FRP test?**
“In US daytime observations from 2013-2024, the Sunday deficit was stronger in detection counts than in summed fire radiative power in MODIS Aqua and VIIRS S-NPP, under a pre-specified test.”

The same finite, nonnegative-FRP observations enter both measures. Aqua and S-NPP meet all fixed contrast and sensitivity criteria under both masks; Terra fails because its adjusted interval includes zero. Twelve year blocks drive uncertainty, not millions of independent detections. Independent recomputation passed. Summed FRP is sampled radiative power, not energy, emissions, burned area or distinct fire counts. The Git receipt is after the original result, as explained in question 9. [S11]

**20. What did AI do, and how can judges reproduce the work?**
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
