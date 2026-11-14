# Seven-country staging audit

Date: November 14, 2026. An independent checking agent reviewed the isolated phase-3 pipeline and artifacts. Production comparison: the Nepal/United States release committed as `841998b`. The audit made no production-code or production-data changes.

## Decision

The staged count, calibration, conversion, calendar and annual-globe results pass the numerical checks described below. The dictionary payload is lossless and fits the original 50 MiB static-site budget with the measured application assets. It is ready for frontend integration and final release testing.

This is not a browser or deployment sign-off. The actual frontend decoder now passes the full-artifact equality check below, including normalization of national `daily_compact` records. The final built site must be measured again: the current budget leaves only **455,471 bytes** of headroom. Seven-country globe interaction, region switching, sharing, exports and narrow-screen coverage labels still require browser verification after integration.

The optional weekly-rhythm claim remains disabled. Its final gate is **`insufficient_data`**, with **`production_allowed: false`**. The predefined statistical condition passes for the United States, Australia and Brazil, but Brazil's matched control is flagged; only Australia qualifies beyond the US. No threshold or selection rule was changed to obtain a passing result.

## Independent checks

| Check | Result |
|---|---|
| Staged regression suite | 6 tests passed |
| Baseline model | Existing B1/M1 ratios and country selections exactly equal |
| Baseline evaluation | CSV byte-for-byte identical |
| Baseline daily conversion | All 208,936 rows × 14 columns exactly equal, including bootstrap bounds |
| Baseline globe | Entire 15,118-cell JSON value structure exactly equal |
| Source inventory | 273 unique complete records; seven countries × MODIS 2001–2025 and VIIRS S-NPP 2012–2025 |
| New-country civil-time samples | 7 date-boundary, multi-zone and historical daylight-saving cases passed |
| Seven-country count reduction | National daily and all-cell annual totals exactly equal preparation counts for each country/year/stratum/stream |
| Detailed-cell selection | All 84 cell IDs agree with training-only activity ranks and tie order |
| Independent fit | Training B1 and all M1 ratios exactly equal the saved selection lock |
| Independent model choice | Independently computed 2018–2019 daily MAEs reproduce all seven choices; test metrics were not used |
| Converted series | 731,276 rows; valid nonnegative estimates and bounds, correct source years and model labels |
| Annual globe | All 41,986 centers and 154 country/year totals verified; maximum summation difference 6.17 × 10⁻⁹ |
| Original calendar payloads | 5,118,932 numerical comparisons passed with absolute serialization tolerance 5.00001 × 10⁻⁶ |
| Dictionary roundtrip | 91 tables / 731,276 rows / 108 files independently checked; original JSON values and number types preserved |
| Actual frontend decoder | Transpiled `web/src/loadData.ts`; `normalizePublishedData` and `decodeCell` passed Node `assert.deepStrictEqual` for all 91 tables / 731,276 records against the original artifacts |
| Canonical Python package | Reviewed every staged-to-`pipeline/streaming` diff; changes are package-relative imports and descriptive phase metadata. All 6 promoted tests passed |

The seven-country inventory represents **74,187,339 raw records and 67,934,899 cleaned detections**. Cleaning reports zero invalid timestamps and zero unresolved timezones. Confidence exclusions remain explicit. These are satellite detections, not independent fires.

The independently reproduced validation selections are B1 for Australia, Brazil and the United States; M1 for Bangladesh, Egypt, India and Nepal. The expanded global training ratio is **0.1450130601167073**. Adding countries legitimately changes that ratio and therefore creates a new model revision; previous two-country performance numbers must not be presented as metrics for the expanded model.

## Scientific and engineering review

The streaming representation preserves integer multiplicity in `n`. SQLite reduction adds keys across both chunks and annual UTC archives, including local-date boundaries; it does not treat summary rows as detections. Vegetation and static-control types remain separate. National totals use all vegetation cells, while detailed cell selection uses only 2013–2017 activity.

The fitter retains the original windows: training 2013–2017, validation 2018–2019, test 2020–2024. It writes every country's selection lock before running held-out evaluation. The conversion retains the 200 whole-training-year bootstrap draws. The exact baseline comparison independently checks that the memory-saving implementation preserves the established algorithm.

Coverage qualification requires adjacent complete UTC archives and explicit instrument commissioning limits. The seven-country series uses observed Aqua for 2003–2012 and converted VIIRS for 2013–2024. No Terra-to-Aqua bridge or observed satellite/cloud coverage is invented. Early Aqua bounds equal the archived count because no conversion is applied; that does not imply zero observation uncertainty.

The annual globe uses true 0.25-degree cell centers and the same eligible source and selected model as the national daily record. All seven regions' public calendar payloads retain the disabled rhythm gate. Daily dates, source strings, coverage statements and model labels match the saved conversion exactly. Cell filenames are portable, remain inside the data directory, and ICS exports contain proper CRLF without doubled carriage returns.

One adapter issue was found and fixed during review: `weighted_rhythm.run_counts` initially did not inherit synthetic provenance from count metadata or the manifest. It now preserves the production routine's override. A regression fixture that statistically passes the US-plus-two condition verifies that synthetic provenance still forces `production_allowed: false`. This did not change the verified real-data results.

## Packaging

| Artifact | Measured size |
|---|---:|
| Original-format projected static site | 133,213,075 bytes — exceeds budget |
| Dictionary-encoded data | 50,613,315 bytes |
| Dictionary site with measured maps and application assets | 51,973,329 bytes / 49.57 MiB |
| Original budget | 52,428,800 bytes / 50 MiB |
| Remaining headroom | 455,471 bytes |
| Largest file, unchanged globe JSON | 12,999,487 bytes — below the 25 MiB file limit |

The independent Python decoder checked column membership, unique columns, row widths and every dictionary index, then compared canonical JSON after decoding against the original artifacts. A separate Node audit loaded the actual frontend implementation by TypeScript transpilation and compared every normalized national object and decoded cell record with `assert.deepStrictEqual`. The tested loader source SHA-256 was `52cef0383eaf3267ebbf82f625219df6275bdaf87855e12c190a66a2f9251086`.

Numeric precision, nulls and provenance are unchanged. The globe, CSV and ICS exports are unchanged. All individual files are below 25 MiB. These are actual encoded-file sizes, not estimates of transfer compression.

## Final independent verification

After integration, the complete Python suite passed **61 tests**. All web suites, including 26 share-link cases, and TypeScript passed. The verifier against the actual seven-country `web/public/data` directory passed **5,119,422 numerical checks** and measured **51,128,009 data bytes**, including shared map assets. A filename-only credential-pattern scan checked 257 tracked and unignored text files and found no matches. This is a bounded pattern scan, not a guarantee against every credential format.

The additive scientific sensitivity report was separately reviewed and independently recalculated. All 14 grid rows and 28 bridge rows agreed across 266 metric comparisons; bridge ratios, whole-training-year bootstrap bounds and interval inclusion rates matched exactly. The protocol's model hash matched its input and its file preceded saved calculations. The grid selection used 2013–2017 and metrics used 2018–2019 over the same 12 coarse footprints and 48 fine children per country. The bridge fit used 2003–2007 and validation used 2008–2011. No 2020–2024 observations entered these calculations.

The sensitivity report correctly treats reused validation, coarsening effects and ratio-only calibration intervals as limitations. It does not qualify an early reconstruction or enable the disabled rhythm module. See `reports/FINAL_QUALITY.md` for the final verification record, reproduction limits and publication bookkeeping.

## Evidence locations

Frozen science and original payloads are under `work/phase3/seven-country-{evaluation,converted,rhythm,public}`. The compact candidate and its budget are under `work/phase3/seven-country-compact`. Source-manifest fingerprint: `4bf6e7635b6cb9b7437fb069e4afb4866c5347dd15d46549288686fb8b21edd7`.

Independent scripts and JSON results are under `work/phase3-audit`: `check_baseline.py`, `check_seven_counts.py`, `check_globe.py`, `check_public.py`, `check_codec.py` and `check_browser_codec.mjs`. They read staged artifacts and write only audit evidence. The audit checked actual files rather than relying only on the builder's equivalence reports. The canonical implementation has been packaged under `pipeline/streaming`; raw and intermediate staging data remain excluded from Git.
