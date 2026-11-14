# Rest-day test on new ignitions (review E1) - ROBUSTNESS ANALYSIS

Script: `python reference/ignition_test.py data OUT_DIR` (imports `kill_test.py` unchanged). An ignition event is a 0.25-degree cell with at least one detection on a local day and none on the previous day, per country and stream; the same weekday index, year bootstrap, 5,000-draw null test, Bonferroni (21 tests) and gate are applied. Not part of the official decision.

**Result: the Sunday dip is sharper on ignitions than on raw detections in the US and Brazil, about the same in Australia, and still absent in the Friday- and Saturday-rest countries.** The gate applied to ignitions passes (US 3/3, Australia 2/3, Brazil 3/3). On ignitions Brazil's VIIRS stream has Sunday as its lowest day; Australia's Terra stream does not (Saturday is lowest).

| Country | Stream | Ignition events | Rest day | Ignition index (95% CI) | Raw-detection index (official) | Lowest day | Significant |
|---|---|---:|---|---|---:|---|---|
| United States | Terra | 216,384 | Sun | 0.591 (0.571-0.611) | 0.723 | Sun | yes |
| United States | Aqua | 243,854 | Sun | 0.605 (0.563-0.653) | 0.667 | Sun | yes |
| United States | VIIRS | 824,170 | Sun | 0.695 (0.674-0.719) | 0.782 | Sun | yes |
| Australia | Terra | 204,251 | Sun | 0.919 (0.893-0.945) | 0.936 | Sat | no |
| Australia | Aqua | 287,917 | Sun | 0.878 (0.853-0.901) | 0.890 | Sun | yes |
| Australia | VIIRS | 521,430 | Sun | 0.909 (0.895-0.925) | 0.937 | Sun | yes |
| Brazil | Terra | 562,541 | Sun | 0.827 (0.803-0.853) | 0.892 | Sun | yes |
| Brazil | Aqua | 813,517 | Sun | 0.869 (0.853-0.885) | 0.922 | Sun | yes |
| Brazil | VIIRS | 1,811,242 | Sun | 0.803 (0.790-0.816) | 0.941 | Sun | yes |
| India | Terra | 131,737 | Sun | 1.024 (0.976-1.072) | 1.022 | Thu | no |
| India | Aqua | 196,781 | Sun | 0.989 (0.945-1.036) | 0.949 | Wed | no |
| India | VIIRS | 746,710 | Sun | 1.012 (0.991-1.032) | 1.003 | Wed | no |
| Nepal | Terra | 7,046 | Sat | 0.889 (0.694-1.101) | 0.891 | Sat | no |
| Nepal | Aqua | 10,409 | Sat | 1.182 (0.973-1.389) | 1.264 | Sun | no |
| Nepal | VIIRS | 26,996 | Sat | 1.045 (1.009-1.086) | 1.015 | Thu | no |
| Bangladesh | Terra | 1,535 | | insufficient data | 0.814 | | |
| Bangladesh | Aqua | 4,484 | Fri | 1.033 (0.818-1.269) | 0.912 | Thu | no |
| Bangladesh | VIIRS | 15,455 | Fri | 0.864 (0.818-0.909) | 0.727 | Fri | yes |
| Egypt | Terra | 4,598 | Fri | 0.978 (0.845-1.125) | 1.045 | Tue | no |
| Egypt | Aqua | 2,852 | Fri | 1.102 (0.879-1.329) | 1.088 | Mon | no |
| Egypt | VIIRS | 39,919 | Fri | 0.987 (0.946-1.024) | 1.036 | Sun | no |
