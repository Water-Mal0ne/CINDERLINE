# Reproduce the key numbers

Everything below runs from committed scripts. Times are on a 32 GB Windows laptop.

## Software used

- Python 3.12.10, pandas 3.1.1, numpy 2.5.4, matplotlib 3.11.2, timezonefinder 9.2.0, pyarrow 26.0.1
- Node.js 24.22.1, npm 11.19.1 (web app; locked versions in `web/package-lock.json`)
- Install: `python -m pip install -r requirements.txt` (pyarrow is required for the parquet steps)

## 1. Harmonization (Layer 1)

The released seven-country model and its locked evaluation are reproduced by the streaming route (downloads the
official archives, several GB; see `pipeline/streaming/README.md`):

```powershell
python -m pipeline.streaming reproduce --output work/reproduced-seven --model-revision seven-country-v1 --baseline-commit 841998b
```

The Layer 1 review table is derived without refitting from the committed evaluation and published series:

```powershell
python -m pipeline.review.harmonization_review        # writes reports/review/
```

Expected (weekly, held-out 2020-2024, `reports/review/layer1_table.md`):

| Country | Selected | Weekly MAE (selected) | Bias | r |
|---|---|---:|---:|---:|
| Australia | B1 | 514.9 | +11.0% | 0.962 |
| Bangladesh | M1 | 12.1 | +6.8% | 0.921 |
| Brazil | B1 | 694.3 | -10.5% | 0.979 |
| Egypt | M1 | 4.3 | +51.7% | 0.729 |
| India | M1 | 337.9 | -2.4% | 0.930 |
| Nepal | M1 | 11.3 | -8.1% | 0.977 |
| United States | B1 | 390.8 | +1.7% | 0.905 |

Seeds: model calibration bootstrap 2841 (200 draws); ratio-trend bootstrap 2024 (2,000 draws).

## 2. Human rhythm (official pre-specified test)

Download the FIRMS country archives (MODIS and VIIRS S-NPP, 2013-2024, seven countries) into `data/` with the same
layout as `pipeline/download.py` (`data/{modis|viirs-snpp}/{year}/{sensor}_{year}_{Country}.csv`), then:

```powershell
python reference/kill_test.py data --label "REAL FIRMS DATA"     # about 15 minutes, about 16 GB RAM
```

Seed 42; 2,000 year-bootstrap draws; 5,000 null draws; Bonferroni over 21 tests. Expected
(`reports/official/kill_test_gate.json`, `kill_test_results.csv`):

- Decision: **pass** (United States 3/3 streams, Australia 3/3, Brazil 2/3; India, Nepal, Bangladesh, Egypt fail).
- US Sunday index: Terra 0.723 (95% CI 0.683-0.762), Aqua 0.667 (0.616-0.714), VIIRS 0.782 (0.753-0.810).
- Rows loaded 54,168,264; vegetation detections 46,765,553; static-source control 2,435,621.

Robustness checks and web payload:

```powershell
python -m pipeline.rhythm --from-saved reports/rhythm_results.json --official reports/official --output reports/rhythm_robustness
python -m pipeline.rhythm_web
```

Expected: US and Australia meet all robustness checks; Brazil fails the matched static control (Terra index 0.913,
adjusted p = 0.021).

## 3. Exploratory and review analyses

```powershell
python reference/rhythm_map.py data                     # per-cell map; seed 42, 20,000 null draws, BH 5%
python reference/rhythm_review.py data OUT_DIR          # B1/B2/B4/B5; seed 20261114 (200,000 draws), B5 seed 20261119
python reference/ne_india_states.py data rhythm_cells.csv ne_10m_admin_1_states_provinces.geojson OUT_DIR
python reference/ne_india_review.py data rhythm_cells.csv ne_10m_admin_1_states_provinces.geojson OUT_DIR
python -m pipeline.review.weekday_shapes
```

Natural Earth admin-1 boundaries: `ne_10m_admin_1_states_provinces.geojson` from
https://github.com/nvkelso/natural-earth-vector (public domain).

Expected: 492 significant VIIRS cells of 1,461 tested; northeast India 19 of 26 (14 of 21 cells mostly inside India);
200,000-draw Monte Carlo changes no significance call; Nepal planted 20% Saturday dip passes the country rule 12% of
the time.

## 4. Web app

```powershell
npm ci --prefix web
npm --prefix web test        # 30 tests
npm run build                # dist/, about 49.8 MiB
python -m pytest tests -q    # 67 tests
```
