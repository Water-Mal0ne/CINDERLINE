# Where the US Sunday dip is strongest and weakest (review E9) - EXPLORATORY

Script: `python reference/us_cell_regions.py rhythm_cells.csv <Natural Earth admin-1> OUT_DIR`. US VIIRS 1-degree cells from the per-cell map, each assigned to the state with the largest share of its area and then to a region group fixed in the script. Numbers only; no causal claim.

| Region | Cells | Significant (BH 5%) | Median Sunday index | Range |
|---|---:|---:|---:|---|
| Southeast | 96 | 84 (88%) | 0.570 | 0.251-1.329 |
| Pacific coast | 57 | 31 (54%) | 0.635 | 0.374-1.202 |
| Southern Plains | 79 | 54 (68%) | 0.707 | 0.413-1.085 |
| Interior West | 30 | 11 (37%) | 0.772 | 0.461-1.143 |
| Alaska and Hawaii | 1 | 0 (0%) | 0.894 | 0.894-0.894 |
| Northern Plains and Midwest | 6 | 1 (17%) | 1.001 | 0.758-1.078 |

States with at least 3 cells, by median Sunday index (`e9_us_states_3plus_cells.csv`):

| State | Cells | Significant | Median |
|---|---:|---:|---:|
| Florida | 16 | 14 | 0.278 |
| Georgia | 14 | 14 | 0.437 |
| South Carolina | 6 | 6 | 0.475 |
| North Carolina | 6 | 6 | 0.482 |
| Alabama | 11 | 11 | 0.587 |
| Arkansas | 10 | 8 | 0.626 |
| Mississippi | 13 | 12 | 0.627 |
| Oregon | 21 | 14 | 0.631 |
| California | 24 | 12 | 0.641 |
| Texas | 39 | 32 | 0.683 |
| Kansas | 10 | 6 | 0.688 |
| Montana | 7 | 4 | 0.704 |
| Tennessee | 5 | 4 | 0.714 |
| Washington | 12 | 5 | 0.722 |
| Louisiana | 14 | 9 | 0.734 |
| Arizona | 8 | 3 | 0.751 |
| Idaho | 10 | 4 | 0.772 |
| Missouri | 14 | 9 | 0.772 |
| Oklahoma | 16 | 7 | 0.802 |
| New Mexico | 4 | 0 | 0.970 |
| North Dakota | 5 | 0 | 1.013 |

The dip is deepest in the southeastern states (Florida median 0.278, Georgia 0.437, the Carolinas about 0.48; 84 of 96 Southeast cells significant) and weakest in the Interior West (11 of 30 significant, median 0.772) and the northern plains (North Dakota 1.013, New Mexico 0.970).
