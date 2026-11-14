# Northeast India follow-ups (review C1-C4) - EXPLORATORY

Data: REAL FIRMS DATA, VIIRS S-NPP (and Aqua) 2013-2024. Script: `python reference/ne_india_review.py data
rhythm_cells.csv <Natural Earth admin-1 GeoJSON> OUT_DIR`; outputs in `reports/review/northeast_india/`. Not part of
the pre-specified test; official results unchanged. No causal claim is made.

## C2. Border cells

Each India cell's land share inside India and inside each state was measured from a 25 x 25 grid of sample points
per 1-degree cell against Natural Earth admin-1 boundaries (`c2_india_cells_area_shares.csv`). A cell is "mostly
inside India" when at least 50% of its land is in India. FIRMS country files hold only detections inside India, so a
cross-border cell's detections all come from its Indian part.

| Group | Cells | Significant (BH 5%) | Median Sunday index |
|---|---:|---:|---:|
| Northeast (east of 89 E), mostly inside India | 21 | 14 | 0.717 |
| Northeast, mostly outside India (cross-border) | 5 | 5 | 0.383 |
| Rest of India, mostly inside India | 201 | 0 | 1.055 |

Cross-border northeast cells (India share of land): 22N 93E (11%), 26N 95E (25%), 23N 93E (39%), 24N 94E (42%),
22N 92E (48%). They carry the deepest dips (0.05-0.59), so earlier figures that pooled them overstated the depth of
the dip in cells that are mostly Indian. Seven cells outside the northeast are also mostly outside India (Pakistan,
Nepal and Bangladesh borders); none is significant.

## C3. Assam

Nine cells have Assam as their largest Indian state (`c3_assam_cells.csv`); eight are mostly Assam (at least 50% of
their Indian part). Of those eight, 5 are significant, median Sunday index 0.806. The four cells that are at least
95% Assam (plains) show a weaker, mixed result: 0.987, 0.817 (significant), 0.914 and 0.658 (significant). Assam's
deepest dip (0.454, 24N 92E) is in a cell whose Indian part is 39% Mizoram/Manipur.

## C1. Year by year, Nagaland, Mizoram and Manipur

Cells mostly inside India whose largest state is Nagaland, Mizoram or Manipur: 23N 92E (Mizoram), 24N 93E (Manipur),
25N 94E and 26N 94E (Nagaland). Pooled Sunday index per year (`c1_hill_states_yearly.csv`, `.png`):

- VIIRS: below 1 in **12 of 12** years (range 0.19-0.46, mean 0.35).
- Aqua: below 1 in **12 of 12** years (range 0.10-0.63, mean 0.30).

The dip is not driven by a few years.

## C4. Denominators

- All four Sunday-rest countries, VIIRS: 492 significant cells out of 1,461 tested (US 181 of 269, Brazil 207 of 575,
  Australia 85 of 383, India 19 of 234). Aqua: 52 of 409.
- Northeast India: 19 of 26 tested (14 of 21 mostly inside India, 5 of 5 cross-border).
- Northeast India per state (centroid assignment, `reports/official/exploratory_ne_india/`): see that table; two states
  rest on a single cell.
