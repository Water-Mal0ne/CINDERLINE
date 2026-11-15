# Detailed observed hotspots: data contract and scope

The first release covers **VIIRS S-NPP, all seven published countries, UTC acquisition year 2024**. The existing harmonized historical globe and its calibration, data files, source choices and calendar alignment are unchanged.

The new layer shows qualifying archived detections at their original coordinate precision. It does not claim an independently validated fine-resolution harmonization. Its 0.05-degree grid counts observations; it is not Aqua-equivalent activity, a fire perimeter, burned area, a density per square kilometre, or a count of distinct fires. Degree-cell ground area varies with latitude. Individual points locate satellite pixel centres. The nominal VIIRS footprint is 375 m, but actual scan/track dimensions vary and are supplied per observation in kilometres. The archive does not provide footprint orientation, so any display must not invent an exact rotated footprint polygon.

## Dates and gaps

The detailed layer's period is the **UTC acquisition month**, separate from the harmonized calendar's local civil dates and selected range. Timestamps retain the archive's acquisition-minute precision and are serialized as `YYYY-MM-DDTHH:MM:00Z`; the zero seconds do not imply sub-minute timing accuracy.

The detailed layer retains qualifying archived records on dates excluded from the harmonized calendar. That calendar's conservative local-date outage mask is not silently applied to UTC records. The index includes documented 2024 S-NPP outage intervals for context, with a visible-policy string explaining the distinction. Published raw detections, harmonized weekly/monthly values, and aligned annual values therefore need not add up to the same number.

`zero_record_dates` means there were no qualifying records in this country archive on that UTC date. It does **not** mean the satellite observed the entire country, that there were no fires, or that the day has verified missing satellite coverage. Cloud, overpass and detection coverage remain unknown. Low-confidence and non-vegetation records are excluded, not relabelled as observed absence. No interpolation, smoothing, coarse-cell subdivision, temporal gap filling, or cross-sensor pooling occurs.

## Source and quality

The generator reads the seven canonical 2024 VIIRS S-NPP CSV archives named in `reports/data_manifest.json`, requires complete status, verifies each SHA-256, and reconciles the source row count. All raw archives are read-only and are not copied into the public site.

Retained rows require S-NPP satellite identity, nominal/high confidence, presumed vegetation fire (`type == 0`), finite latitude/longitude within Earth bounds, and a valid acquisition time/date within 2024. Timestamp parsing reuses `pipeline.clean._utc_datetime`; the confidence rule matches the existing pipeline. Unknown types never become vegetation. The stricter source check prevents a different VIIRS platform from entering a nominal S-NPP product.

Coordinates are not rounded for export. Finite non-negative FRP is retained, including zero; unknown/invalid FRP is null. Scan/track must be finite positive dimensions or become null (unknown), without inventing a default footprint. Repeated source records are retained rather than deduplicated as if they represented independent fires. Source coordinates, time, sensor and confidence remain available for each displayed record.

## Public JSON contract

All files use schema `observations-v1`. Paths in descriptors are relative to `web/public/data`, such as `observations/Nepal/2024-04.json`. Descriptors contain a byte-exact SHA-256; clients must reject stale/mismatched files rather than combine incompatible data. Local source file paths never enter public JSON.

`observations/index.json` contains `sensor`, `year`, `time_basis`, `temporal_precision`, `grid_size`, `tile_size`, `columns`, interpretation/policy notes, and `countries`:

```text
countries: [{
  id, name, count,
  source: {url, sha256, rows},
  months: [{month, file, sha256, count, bytes, tile_count}]
}]
```

Every country lists all twelve months. Empty months are explicitly zero-record payloads, never missing files.

A month payload contains:

```text
schema, sensor, country, month, time_basis, grid_size, count, source_sha256,
grid: [[latitudeIndex, longitudeIndex, detectionCount], ...],
tiles: [{id, file, sha256, count, bounds, bytes}, ...],
daily_counts: [["2024-MM-DD", detectionCount], ...],
zero_record_dates: ["2024-MM-DD", ...]
```

Grid indices use mathematical decimal floor of the original coordinate divided by 0.05. This avoids binary floating division shifting exact negative or positive cell boundaries. Cell origins are `index * 0.05`; counts are computed from source positions, not harmonized grid values. Exact +90/+180 boundary points are assigned to the final in-range cell without altering their coordinates.

Storage begins with 2-degree spatial tiles, then recursively splits dense tiles into quadrants until each has at most 8,000 records. Thus zooming into a smaller geographic area reduces requested data. Irreducibly coincident records are split into listed parts with identical bounds, never sampled away. Storage bounds are `[west, south, east, north]`; each point lies within those bounds, inclusive at the outer limits. Tile IDs are opaque, and clients must use the supplied bounds and descriptor paths.

A tile contains `schema`, `sensor`, `country`, `month`, `id`, `time_basis`, `count`, `bounds`, and:

```text
columns: ["lat", "lon", "utc", "confidence", "scan", "track", "frp", "daynight"]
rows: [[27.712345, 85.312345, "2024-04-01T07:12:00Z", "n", 0.42, 0.38, 4.2, "D"], ...]
```

Confidence is `n` or `h`; day/night is `D`, `N` or unknown `?`. A stable display identity is `country:month:tile.id:rowIndex`. Identity preserves duplicate acquisitions; it does not claim an identified fire event. Month grid sums, tile sums, daily sums and source-filtered month counts must agree exactly. Clients with a point budget must show a clear zoom-in instruction and retain the complete aggregate grid instead of silently omitting records.

## Reproduction and validation

From a Python environment with the repository requirements installed:

```powershell
python -m pipeline.review.observation_detail --manifest reports/data_manifest.json --output web/public/data/observations --receipt reports/observation-detail/generation.json
python -m pytest tests/test_observation_detail.py
```

The CLI requires a fresh output directory and preserves any existing export rather than deleting or overwriting it. For a reproduction beside the checked-in artifacts, choose a fresh ignored `work/` output directory and compare its index SHA-256. The manifest's original local source paths must exist; it is not necessary to download raw archives to use the site.

`generation.json` records archive row/quality diagnostics, retained counts, tiles, total bytes, maximum file size and index hash. The producer enforces the 25 MiB per-file limit and reserves space under Pages' 20,000-file limit. Individual source-hash and artifact-hash checks establish provenance and integrity, not observational completeness or scientific ground truth.

The initial real-data export contains **3,482,732 observations**, **8,866 JSON assets**, and **244,970,711 bytes**. The largest asset is **686,483 bytes**, below 1 MiB. These assets are fetched by selected country/month and visible spatial tiles, not all downloaded at startup. The build took 291.844 seconds on the development machine; this is an export duration, not a browser performance measurement.

| Country | Qualifying observed records | Point tiles |
| --- | ---: | ---: |
| Australia | 881,613 | 1,889 |
| Bangladesh | 6,877 | 74 |
| Brazil | 1,767,650 | 2,599 |
| Egypt | 7,931 | 246 |
| India | 382,884 | 1,051 |
| Nepal | 48,157 | 76 |
| United States | 387,620 | 2,846 |

Index SHA-256: `3379a22ad49bc0041721a1bc2b93bb71f2d0bfce95e8deefa60acf0879c0f2d6`.

The focused tests cover quality/platform/time exclusions; positive and negative exact grid boundaries; source coordinate precision; zero versus unknown FRP; unknown footprint dimensions; adaptive spatial subdivision; coincident/repeated records; polar/dateline bounds; count conservation; complete empty-month contracts; deliberate retention of records on calendar-excluded dates; and failed source hash/count/completeness checks.

NASA field definitions: [VIIRS active-fire attributes](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html). Existing outage sources and interpretation remain in `reports/review/OUTAGES.md` and `pipeline/review/no_observation.py`.
