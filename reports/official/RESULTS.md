# FIRETRACE "human rhythm" kill test: results

Run on real NASA FIRMS data, 14 November 2026, with `kill_test.py` version 2. Chart: `kill_test.png`. Raw numbers: `kill_test_results.csv`, `kill_test_gate.json`, `kill_test_diagnostics.json`.

## Decision

**Sunday dip clear in the US and Australia, weaker in Brazil, and absent where the rest day is Friday or Saturday. Our pre-specified rule passed narrowly; a stricter version fails on Brazil on the 2002-2024 record.**

Brazil is suggestive rather than clear. Brazil's Terra industrial-source control dips on Sunday over 2002-2024, but the dip comes entirely from 2002-2007; over 2013-2024, the window fixed for the rest-day test, the control is flat. Brazil's Sunday dip is weaker on raw detections (VIIRS does not pass) but passes in all three satellites on new ignitions. Because of the 2002-2024 control, Brazil does not meet the stricter check (Terra index 0.913, adjusted p = 0.021); the official pre-specified result is unchanged (PASS).

The pre-specified test passes. The United States replication check passed, and two other countries (Australia and Brazil) passed. The rule needed the US plus at least two others.

There is one important limit on what this shows. All three passing countries have Sunday as their rest day. None of the countries that rest on a different day (Nepal on Saturday, Bangladesh and Egypt on Friday) passed. So the data show a Sunday dip in Sunday-rest countries, but they do not yet show the dip moving to whatever day a country rests on. See "Caveats" below.

## What was tested

Nature has no 7-day cycle. If satellite fire detections are lower on a country's local rest day, that is consistent with people scheduling their burning around the working week. Earl, Simmonds and Tapper (2015, Geophysical Research Letters) found a global Sunday minimum in MODIS data from 2001 to 2013. We repeated the idea per country, with the rest day for each country fixed before looking at the data:

| Country | Predicted rest day |
|---|---|
| United States, Australia, Brazil, India | Sunday |
| Nepal | Saturday |
| Bangladesh, Egypt | Friday |

Method in brief:

- Data: FIRMS country files, 2013 to 2024, for MODIS (Terra and Aqua satellites) and VIIRS S-NPP. 168 files, 54.2 million detections loaded.
- Vegetation fire detections only (FIRMS type 0). Low-confidence detections were dropped. Static sources such as gas flares and volcanoes (types 1 and 2) were kept apart as a negative control.
- Each detection's UTC time was converted to local time, so "Sunday" means Sunday where the fire was.
- Terra, Aqua and VIIRS were analysed separately. They watch many of the same fires, so agreement between them is corroboration, not three independent replications.
- For each year, the detection rate on each weekday was divided by the average day's rate. An index of 1.00 is an average day; 0.72 means 28% fewer detections than average.
- 95% confidence intervals come from resampling whole years. The p-value asks how often a randomly chosen weekday would look as low as the rest day. With 21 country-by-satellite tests, a result counted as significant only if p < 0.05 / 21 (about 0.0024) and the rest day was the lowest day of the week.
- A country passes if this holds in at least 2 of its 3 satellite streams.

## Numbers (all detections, day and night)

| Country | Satellite | Detections | Rest day | Rest-day index | 95% CI | Lowest day | p | Significant |
|---|---|---|---|---|---|---|---|---|
| United States | Terra | 635,163 | Sun | 0.723 | 0.683-0.762 | Sun | 0.0002 | yes |
| United States | Aqua | 716,325 | Sun | 0.667 | 0.616-0.714 | Sun | 0.0002 | yes |
| United States | VIIRS | 4,881,876 | Sun | 0.782 | 0.753-0.810 | Sun | 0.0002 | yes |
| Australia | Terra | 1,118,366 | Sun | 0.936 | 0.899-0.970 | Sun | 0.0018 | yes |
| Australia | Aqua | 1,560,421 | Sun | 0.890 | 0.856-0.918 | Sun | 0.0002 | yes |
| Australia | VIIRS | 12,176,521 | Sun | 0.937 | 0.917-0.955 | Sun | 0.0002 | yes |
| Brazil | Terra | 1,560,796 | Sun | 0.892 | 0.850-0.934 | Sun | 0.0002 | yes |
| Brazil | Aqua | 2,444,343 | Sun | 0.922 | 0.891-0.956 | Sun | 0.0002 | yes |
| Brazil | VIIRS | 15,090,238 | Sun | 0.941 | 0.917-0.967 | Mon | 0.0002 | no |
| India | Terra | 259,057 | Sun | 1.022 | 0.953-1.085 | Thu | 0.74 | no |
| India | Aqua | 630,552 | Sun | 0.949 | 0.872-1.038 | Sun | 0.13 | no |
| India | VIIRS | 5,048,853 | Sun | 1.003 | 0.977-1.035 | Thu | 0.59 | no |
| Nepal | Terra | 17,860 | Sat | 0.891 | 0.672-1.117 | Thu | 0.19 | no |
| Nepal | Aqua | 25,776 | Sat | 1.264 | 0.989-1.548 | Sun | 0.98 | no |
| Nepal | VIIRS | 339,021 | Sat | 1.015 | 0.913-1.124 | Thu | 0.61 | no |
| Bangladesh | Terra | 2,674 | Fri | 0.814 | 0.635-0.998 | Sun | 0.07 | no |
| Bangladesh | Aqua | 22,963 | Fri | 0.912 | 0.744-1.075 | Thu | 0.30 | no |
| Bangladesh | VIIRS | 105,174 | Fri | 0.727 | 0.643-0.821 | Fri | 0.0008 | yes |
| Egypt | Terra | 6,557 | Fri | 1.045 | 0.838-1.266 | Tue | 0.75 | no |
| Egypt | Aqua | 4,222 | Fri | 1.088 | 0.843-1.339 | Mon | 0.79 | no |
| Egypt | VIIRS | 118,795 | Fri | 1.036 | 0.978-1.089 | Sun | 0.98 | no |

0.0002 is the smallest p-value the test can produce with 5,000 random draws. Bangladesh Terra has 10 usable years; every other row has 12.

Per-country result:

| Country | Result | Streams significant |
|---|---|---|
| United States | pass (replication check) | 3 of 3 |
| Australia | pass | 3 of 3 |
| Brazil | pass | 2 of 3 |
| India | fail | 0 of 3 |
| Nepal | fail | 0 of 3 |
| Bangladesh | fail | 1 of 3 |
| Egypt | fail | 0 of 3 |

## Reading the numbers

The United States has by far the biggest dip: Sunday detections run 22% to 33% below an average day in all three satellites. Earl et al. reported a global Sunday minimum about 8% below Tuesday, so the US effect is much larger than their global average.

Australia and Brazil have smaller but very consistent Sunday dips, roughly 6% to 11% below average, with tight confidence intervals because there are millions of detections.

Brazil's VIIRS stream missed by a hair: Sunday is 0.941 and Monday is 0.933. In daytime-only VIIRS data Sunday is the lowest day (0.910). One possible reason is that VIIRS's night pass is around 1:30 am local time, so the Monday-night count partly reflects what was burning late on Sunday. That is a guess we have not tested.

India shows no Sunday dip in any stream.

Nepal shows no Saturday dip. Aqua shows Saturday as the highest day (1.264), but Terra and VIIRS do not agree, and Aqua's sample is small, so a Saturday rise is not established either.

Bangladesh VIIRS shows a significant Friday dip (0.727, the lowest day). The Bangladesh weekly pattern is odd, though: Saturday is 1.53 and Tuesday 1.33, far above average, and Sunday is almost as low as Friday (0.762). With about 9,000 VIIRS detections a year, a few large burning days could create this shape. Terra and Aqua do not confirm it.

Egypt shows no Friday dip.

Daytime-only results tell the same story. US Sunday is 0.63 to 0.66 in all three satellites, Australia 0.87 to 0.93, Brazil 0.89 to 0.91 (all three Brazil streams have Sunday lowest in daytime). Nepal, India and Egypt still show nothing; Bangladesh VIIRS Friday is 0.706.

## Daytime-only results (robustness view, not part of the gate)

A night detection can fall on the calendar day after a fire was lit (a fire lit on Saturday evening can still be burning at the 01:30 night overpass on Sunday). Restricting to daytime overpasses removes that spill-over. These results are a robustness view only; the gate uses all detections. Source: `reports/official/kill_test_results.csv`, subset `day`.

| Country | Stream | Rest day | All detections | Daytime only (95% CI) | Daytime lowest day | Daytime significant |
|---|---|---|---:|---|---|---|
| United States | Terra | Sun | 0.723 | 0.630 (0.596-0.661) | Sun | yes |
| United States | Aqua | Sun | 0.667 | 0.646 (0.592-0.695) | Sun | yes |
| United States | VIIRS | Sun | 0.782 | 0.657 (0.617-0.698) | Sun | yes |
| Australia | Terra | Sun | 0.936 | 0.926 (0.888-0.960) | Sun | yes |
| Australia | Aqua | Sun | 0.890 | 0.870 (0.828-0.907) | Sun | yes |
| Australia | VIIRS | Sun | 0.937 | 0.897 (0.867-0.927) | Sun | yes |
| Brazil | Terra | Sun | 0.892 | 0.894 (0.848-0.940) | Sun | yes |
| Brazil | Aqua | Sun | 0.922 | 0.909 (0.878-0.942) | Sun | yes |
| Brazil | VIIRS | Sun | 0.941 | 0.910 (0.883-0.938) | Sun | yes |
| India | Terra | Sun | 1.022 | 1.022 (0.921-1.128) | Thu | no |
| India | Aqua | Sun | 0.949 | 0.950 (0.872-1.042) | Sun | no |
| India | VIIRS | Sun | 1.003 | 0.988 (0.964-1.015) | Thu | no |
| Nepal | Terra | Sat | 0.891 | 0.876 (0.647-1.137) | Wed | no |
| Nepal | Aqua | Sat | 1.264 | 1.295 (1.005-1.621) | Sun | no |
| Nepal | VIIRS | Sat | 1.015 | 1.071 (1.002-1.139) | Thu | no |
| Bangladesh | Terra | Fri | 0.814 | 0.848 (0.533-1.183) | Sun | no |
| Bangladesh | Aqua | Fri | 0.912 | 0.913 (0.746-1.082) | Thu | no |
| Bangladesh | VIIRS | Fri | 0.727 | 0.706 (0.609-0.805) | Fri | yes |
| Egypt | Terra | Fri | 1.045 | 1.090 (0.825-1.395) | Tue | no |
| Egypt | Aqua | Fri | 1.088 | 1.138 (0.831-1.456) | Mon | no |
| Egypt | VIIRS | Fri | 1.036 | 0.981 (0.879-1.094) | Sun | no |

Daytime only, the Sunday dip is deeper in the US (0.63-0.66) and Australia; in Brazil it is about the same in Terra and deeper in Aqua and VIIRS, and Brazil's VIIRS stream has Sunday as its lowest day (it was Monday with night detections included). Nepal, India and Egypt still show no rest-day dip; Bangladesh VIIRS remains the only Friday dip.

## Negative control (static sources)

Gas flares, volcanoes and other static hot sources should not follow a rest day the way field burning does. Pooled across all seven countries, their weekday pattern is flat:

| Satellite | Detections | Largest deviation from average |
|---|---|---|
| Terra | 100,462 | 1.6% |
| Aqua | 83,690 | 2.4% |
| VIIRS | 2,251,469 | 1.7% |

This makes it unlikely that the Sunday dip comes from the satellites or the FIRMS processing behaving differently on some weekdays. (The control is pooled across countries and uses simple counts, not the year-by-year method, so it is a sanity check rather than a formal test.)

Per-country controls, rechecked with the same year-level method as the main test (robustness, not part of the gate):

- US volcano detections show a Sunday dip in VIIRS only (0.861), almost entirely from Kilauea and sensitive to the 2018 eruption year; Aqua and Alaska's volcanoes show none, and the larger US industrial-source control is flat in all three satellites over 2002-2024. A processing or satellite artifact would be expected to appear across satellites and source types, so we treat this as an unexplained single-volcano, single-satellite result and report it rather than discount it.
- Brazil's Terra industrial-source control dips on Sunday over 2002-2024, but the dip comes entirely from 2002-2007; over 2013-2024, the window fixed for the rest-day test, the control is flat. Brazil's Sunday dip is weaker on raw detections (VIIRS does not pass) but passes in all three satellites on new ignitions. Because of the 2002-2024 control, Brazil does not meet the stricter check (Terra index 0.913, adjusted p = 0.021); the official pre-specified result is unchanged (PASS).

Year-level recheck: `reports/review/controls/CONTROLS.md`.

## Data diagnostics

- Loaded: 54,168,264 detections from 168 files.
- After dropping low-confidence detections: 49,333,709.
- Vegetation fires (main analysis): 46,765,553. Static sources (control): 2,435,621.
- Invalid timestamps dropped: 0. Detections with no resolvable time zone: 0.
- Converting UTC to local time moved 15.8% of vegetation detections to a different calendar date (40.6% of static-source detections). This is why the local-time step matters: without it, about one detection in six would be assigned to the wrong weekday.

## Caveats

- A rest-day dip is consistent with people scheduling their burning. It does not prove who lit the fires or why.
- No dip, as in India, Nepal and Egypt, does not mean fires there are weather-driven. Burning may not follow the official week, many farmers may not take the official rest day, or the effect may be too small to see.
- All numbers are satellite detections of hot spots, not counts of fires. One fire can produce many detections, and small or cloud-covered fires produce none.
- The three passing countries share Sunday as the rest day. The strongest version of the claim, that the dip follows each country's own rest day, would need Friday or Saturday countries to pass too. Only Bangladesh VIIRS does, and its weekly pattern looks unusual. A worldwide Sunday effect of some unknown non-human origin is unlikely given the flat negative control, but this test cannot rule it out on its own.
- Terra, Aqua and VIIRS see many of the same fires. Three agreeing satellites are stronger than one, but they are not three independent experiments.
- We did not measure cloud cover or satellite coverage by weekday. Over 12 years a weekday bias in coverage seems unlikely, and the negative control would likely have shown it, but it is untested.
- Countries were treated as one unit. Large countries (US, Brazil, Australia, India) mix regions with very different burning practices.

## Where is the dip? (EXPLORATORY)

This section is exploratory. It was not part of the pre-specified test above, and the regional groupings below were drawn after looking at the maps. Script: `rhythm_map.py`. Outputs: `rhythm_cells.csv`, `rhythm_cells.geojson`, `rhythm_summary.json`, and one map per country, `rhythm_map_<Country>.png`.

We repeated the weekday analysis for every 1 x 1 degree grid cell in the four Sunday-rest countries that passed or nearly passed (United States, Brazil, Australia, India), with VIIRS for the map and Aqua as a check. Same cleaning, local time, complete years and year bootstrap as the main test. A cell was analysed only if it averaged at least 300 detections a year over 2013-2024 and had at least 8 usable years (a usable year has at least 140 detections in that cell). With hundreds of cells, some would look significant by chance, so we controlled the false discovery rate at 5% (Benjamini-Hochberg) across all VIIRS cells together, and separately across all Aqua cells. The null test used 20,000 draws instead of 5,000 so p-values were fine-grained enough for this correction.

VIIRS: 1,461 cells were analysed and 492 show a significant Sunday dip. In 453 of those, Sunday is also the lowest day of the week. None of these four countries share a border, so no cell is counted twice.

| Country | Cells analysed | Significant Sunday dip | Median Sunday index |
|---|---|---|---|
| United States | 269 | 181 | 0.647 |
| Brazil | 575 | 207 | 0.908 |
| Australia | 383 | 85 | 0.905 |
| India | 234 | 19 | 1.042 |

Where the dip is (VIIRS, median Sunday index of the cells in each area):

- United States: almost everywhere it has enough detections. The Southeast (south of 37 N, east of 95 W) has 87 of 100 cells significant, median 0.57. The inland Pacific Northwest (25 of 44, median 0.64) and California (12 of 24, median 0.64) also dip. Alaska has no cell with enough detections to analyse.
- Brazil: strongest in the south, south of 23 S (37 of 42 cells, median 0.57), and in the northeast (52 of 85, median 0.77). The Amazon interior (north of 10 S, west of 50 W) mostly does not dip: median 1.00, 18 of 122 cells significant.
- Australia: the southwest of Western Australia (17 of 27, median 0.59) and the southeast (39 of 85, median 0.79), plus Tasmania and part of the Top End. The northern savanna, north of 20 S, mostly does not dip (12 of 131 significant, median 0.96).
- India: all 19 significant cells are in the northeast, east of 89 E (19 of 26 cells, median 0.65). The rest of India shows no dip at all (0 of 208 significant, median 1.05). Five of the 26 northeast cells lie mostly outside India (their detections come from the Indian side of the border) and carry the deepest dips; using only the 21 cells mostly inside India, 14 are significant (median 0.717). The cause is unresolved (see `reports/review/NORTHEAST_INDIA_REVIEW.md`).

Where the opposite shows up: the test only looks for dips, so a Sunday rise can't be "significant" here. As a description, 76 VIIRS cells have a Sunday confidence interval entirely above 1.0. 48 of them are in India outside the northeast; Punjab and Haryana, for example, have a median of 1.10. Most of the others are in Brazil (20).

Does Aqua agree? Aqua sees far fewer fires, so only 409 cells pass the same 300-a-year threshold (20 in the US). Where both satellites have a value, their Sunday indices are strongly correlated (r = 0.86) and fall on the same side of 1.0 in 77% of cells. Of the 106 VIIRS-significant cells that also have Aqua data, 103 also show a Sunday index below 1 in Aqua, and 49 are significant in Aqua on their own. Aqua and VIIRS see many of the same fires, so this is corroboration, not independent replication.

Reading it: the national Sunday dips found in the main test are not spread evenly. They come from particular regions, mostly farm and pasture land and areas with prescribed burning (we have not overlaid land-cover data to check this). Regions dominated by large wildfire seasons or forest clearing frontiers, like Alaska, the northern Australian savanna and the Amazon interior, show little or none. A dip in a cell is consistent with people scheduling their burning there. It does not show who lit the fires, and a cell with no dip is not shown to be weather-driven.

Caveats specific to the map:

- Neighbouring cells share weather and farming practice, so a cluster of significant cells is one regional pattern, not many independent findings. The false-discovery correction remains valid when cells are positively correlated, but it doesn't make them independent.
- The 300-a-year threshold means the map only covers places with a lot of burning. Grey areas are not "no dip"; they are "not enough detections to tell".
- 1-degree cells are coarse (about 100 km); a cell can mix very different land uses.
- Area boundaries in the list above (for example "east of 89 E") were chosen by eye after seeing the maps, to describe them. They are not tests.

## Not done

- The exploratory comparison (step 6 of our plan) was only planned if the test failed or only the US passed. Since the test passed, it was not run as a separate section. The full weekday table for every country and stream is in `kill_test_results.csv` if we want to look at it.
- The festival-window analysis (Eid al-Fitr, Dashain) has not been run.
