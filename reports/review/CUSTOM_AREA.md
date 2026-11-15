# Custom area selection (review E4)

**Update, 15 November 2026: built on branch `area-of-interest`** (`pipeline/area_cells.py`, `web/src/AreaOfInterest.tsx`). It uses monthly per-cell series at 0.25 degrees, lazily loaded per country, with a drawn rectangle or a typed point and radius. Values use national calibration, and local accuracy has not been validated. See DECISIONS.md, "Area of interest". The original note follows.

## Original note: not built in that release

Stopped under the 30-minute rule. What it needs and why it does not fit tonight:

- The browser has national daily series plus 12 training-selected daily cells per country (84 series). A user-drawn
  area needs every cell's series; the full 0.25-degree set is 41,986 cells (only annual totals are shipped, in
  `globe.json`, 12.7 MB).
- Even a reduced version (weekly, 1-degree, 2013-2024 only, compact integers) is roughly 5-8 MB for seven countries.
  The built site is 49.8 MiB against the 50 MiB budget in DEPLOYMENT.md.
- The pre-2013 part of the record needs MODIS 2003-2012 archives, which are not on the analysis machine; the
  per-cell conversion would also have to be re-derived outside the locked streaming pipeline.

Design for a later release: (1) store weekly per-cell Aqua-reference-equivalent values on a 0.5-degree grid as a
lazily loaded binary file per country (uint16 counts with a per-country scale, about 0.5-1.5 MB each); (2) shrink
`globe.json` by the same binary encoding to stay under budget; (3) in the app, let the user brush a rectangle on the
country map, sum the selected cells client-side, and run the existing weekly climatology and leave-one-year-out
anomaly logic in the browser.
