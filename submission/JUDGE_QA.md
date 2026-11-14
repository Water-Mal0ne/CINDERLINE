# Judge Q&A: the hardest questions, with honest answers

Every number is from a committed report (path in brackets). "Detections" are satellite hotspot detections, not fires.

We reproduce a known weekly pattern in each satellite record separately. Independently, FIRETRACE tests whether its historical calendar survives a change of sensor and calibration.

**1. Aqua flew the whole time. Why switch to converted VIIRS from 2013?**
So the record can continue after MODIS. Aqua is past its design life, its orbit drifted later in the early 2020s, and it had outages in 2020 and 2022; VIIRS continues on S-NPP, NOAA-20 and NOAA-21. The cost is shown, not hidden: on the held-out 2020-2024 weeks the converted series tracks Aqua with weekly r = 0.73-0.98 depending on country [reports/review/layer1_table.md], and the overlap charts show both series [reports/review/aqua_vs_converted_viirs_*.png].

**2. Why the 375 m VIIRS product and not the 750 m one?**
The 375 m I-band product is the standard VIIRS active-fire product in the FIRMS country archive and is more sensitive to small fires. The 750 m product is not in the country archive; we did not compare the two [METHODS.md].

**3. Is the VIIRS-to-Aqua ratio stable, given Aqua's orbit drift?**
No country shows a trend distinguishable from zero over 2013-2024 (year bootstrap). But in the test years the ratio is 39% above training in Egypt and 10% above in the US, and the US weekly correlation falls from 0.97 (2020) to 0.74 (2024). We cannot separate orbit drift from real change [reports/review/ratio_trend.csv, LIMITATIONS.md].

**4. Does harmonization beat the naive join?**
Yes, by a wide margin, against Aqua on untouched 2020-2024 weeks: raw VIIRS (B0) is biased +357% to +3,136%; the selected model is within +/-11% except Egypt (+52%) [reports/review/layer1_table.md].

**5. How do we know the test years were not used to choose the model?**
Training 2013-2017, model choice on 2018-2019 validation MAE, test 2020-2024 evaluated once after the choice was locked [reports/selection_lock.json]. Recomputing the weekly test metrics from the published series reproduces the official numbers exactly [reports/review/layer1_reproduction_check.csv].

**6. What does the uncertainty band on a converted week mean?**
It is the 2.5-97.5 percentile range across 200 bootstrap refits of the conversion ratio over the five training years. It is not a 95% confidence interval for true detections; it ignores cloud, observation and day-to-day conversion error [METHODS.md].

**7. Where does the harmonization fail?**
Egypt is biased high in every test year (+36% to +66%); Bangladesh 2022 fails (bias +114%, r 0.18); Brazil runs 10-14% low from 2021 [reports/review/HARMONIZATION_REVIEW.md]. The MODIS product version field also changes across the training, validation and test windows (6.2, 6.03, 61.03) [METHODS.md].

**8. Is the weekly-rhythm result stable under the reported checks?**
The US Sunday dip is large (Sunday 22-33% below an average day in all three satellites) and stable: leaving out any one year never changes the lowest day. Re-running the null test with 200,000 draws instead of 5,000 changes no significance call [reports/review/RHYTHM_REVIEW.md].

**9. Was the rule pre-registered?**
Pre-specified, not pre-registered. The rule and rest days were written before the data for five of the seven countries were downloaded, but after the US and Nepal data were in hand; no committed record predates the first real-data run [DECISIONS.md, gate timeline].

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

**15. Can I pick my own area, and can this forecast fire?**
Areas: the calendar covers national totals plus 12 daily grid cells per country; drawing an arbitrary area is not supported in this release (it would exceed the site's size budget). Forecasting: no. The calendar is historical and descriptive, complementary to near-real-time alert systems such as ICIMOD's, not a replacement [README.md].

**16. What about satellite outages?**
The calendar masks outages of the stream supplying its value, plus flagged days with no detections in any of the seven countries: 38 days per country, all in 2022 and 2024, are marked "no observation" (grey) and excluded from typical-season statistics and anomaly flags. The documented Aqua outages fall in years supplied by converted VIIRS and therefore do not remove calendar values. Held-out evaluation and annual globe totals were not recomputed with these masks. [reports/review/OUTAGES.md]

**17. Does the conversion hold on another satellite?**
The reported four-country check (India, Australia and Brazil did not finish downloading) supports transfer to a second VIIRS platform, not independent ground-truth accuracy. NOAA-20 VIIRS, converted with the saved S-NPP-fitted model and no refitting, matches the released converted S-NPP series in the test years 2020-2024: United States +1.3% (weekly r 0.984), Nepal +0.6% (r 0.989), Bangladesh -0.5% (r 0.987), Egypt -2.6% (r 0.829). Egypt's high bias against Aqua persists with NOAA-20 (+47.7%); that shared discrepancy does not isolate its cause. The saved comparison still needs a strict common-date outage sensitivity, because a partly masked S-NPP week can be compared with a fuller NOAA-20 week. As a separate fourth rhythm stream, NOAA-20 also shows the US Sunday dip (0.832, p 0.0002). [reports/review/noaa20/NOAA20.md, pipeline/review/noaa20_check.py]

**18. Does a better annual total guarantee a better seasonal calendar?**
No. In the original **retrospective, unmasked** whole-year replacement experiment for India, comparing the simple B1 conversion with the selected M1 conversion across 2020-2024, mean absolute annual count error improves from **16.46% to 3.80%**, while monthly-share total-variation disagreement (**TV x100**) worsens from **13.59 to 16.29**. Both metrics use Aqua as the reference, not ground truth. This compares two conversions, not raw VIIRS with conversion; it shows why count fit and seasonal shape must be checked separately. **The common-date outage sensitivity is pending Task 4; these original numbers must not be described as outage-adjusted.** Reproduce the original summary with `python scripts/verify_season_example.py --check`; retained source: `reports/review/season/original_whole_year_comparison.csv` (India/B1 and India/selected rows). The production model and official results are unchanged.
