# Out-of-sample prediction: Chittagong Hill Tracts (review E2) - EXPLORATORY

Prediction committed before the analysis in commit `5adb21a90e781ce642b17c9aee9915a600c84dda` (14 Nov 2026 19:46 +0545):
"the Chittagong Hill Tracts ... will NOT show a significant Sunday dip, unlike India's northeastern hill states."

Method as committed: `reference/rhythm_map.py --countries Bangladesh --rest-day Sun` (VIIRS map, Aqua check, 1-degree
cells with >= 300 detections a year and >= 8 usable years, Benjamini-Hochberg 5% across Bangladesh cells). Natural
Earth admin-1 polygons for Bangladesh are divisions, not districts, so the committed fallback rule was used: cell
centroid east of 91.5 E and south of 23.5 N. Two cells qualify.

**Result: the prediction did not hold.**

| Cell (SW corner) | VIIRS Sunday index (95% CI) | VIIRS q | Aqua Sunday index | Aqua q | Lowest day (VIIRS) |
|---|---|---:|---:|---:|---|
| 21N 92E (Bandarban area) | **0.490 (0.407-0.570)** | **0.0004, significant** | **0.564, significant (q 0.020)** | | Sun |
| 22N 92E | 0.745 (0.610-0.890) | 0.089, not significant | 0.865, not significant | | Fri |

One of the two hill-tract cells has a significant Sunday dip in both VIIRS and Aqua. The other has no significant
Sunday dip; its lowest day is Friday, and with Friday as the tested day it is significant (0.652, q 0.011).
Outside the hill tracts, no Bangladesh cell has a significant Sunday dip; with Friday as the tested day, four
non-hill cells are significant (`tested_Fri/`).

Only two cells qualify, so this is a weak test either way. It is reported because it was pre-committed.
