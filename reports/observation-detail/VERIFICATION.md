# Finer observation layer verification

Initial verification of `feature/finer-observations`, based on main `cee2b56923fde55300c36af1c13facbb581fdedc`. At the time of these checks the work was local and had not been pushed, merged or deployed. The later integration incorporates documentation PR #18 without changing the scientific payloads; release status is tracked by the GitHub PR rather than this historical test receipt.

## Scope and data

All seven countries have all twelve UTC months of VIIRS S-NPP observations for 2024. The 3,482,732 retained records have been independently compared with their original archive rows, including duplicate multiplicity and every exported observation field. Monthly counts, 0.05-degree bins, daily counts, source and tile hashes, and tile bounds reconcile. See [DATA.md](DATA.md) and the independent [REVIEW.md](REVIEW.md).

Existing scientific payloads, calibration, historical harmonized values and annual alignment data are unchanged. The observed layer is separate: it retains source detections on calendar-excluded dates and uses UTC rather than local calendar dates. Its visible notice explains why the totals differ. No interpolation, spatial sampling or invented finer harmonization is used.

## Automated checks

| Check | Result |
|---|---|
| Full Python suite | 112 passed |
| Full web suite | 171 passed |
| TypeScript check and production build | Passed through `npm run build` |
| Production files | 9,003 |
| Production bytes | 310,740,011 |
| Largest production file | 12,999,487 bytes |
| Files above 25 MiB | 0 |
| `dist/index.html` | Present |

Commands were run from the worktree root:

```powershell
..\firetrace\.venv\Scripts\python.exe -B -m pytest -q -o cache_dir=work/pytest-cache --basetemp work/pytest-temp-observations
npm --prefix web test
npm run build
```

The first final-build attempt encountered a Windows filesystem-sandbox restriction in Vite's config loader. The same command passed with filesystem access; no code workaround was needed. Vite reports its existing large-chunk advisory for the lazily loaded Globe bundle (605.40 kB minified). This is not a build failure.

## Browser checks

Checked the local application at `http://127.0.0.1:5183/` on desktop and at a 390 x 844 browser viewport.

| Flow | Result |
|---|---|
| Open harmonized Earth and switch to observations | Passed; separate labels and controls |
| Load all seven country observation inventories | Passed |
| Change country while using May 2024 observations | Passed; layer and month remain selected |
| Zoom from 0.05-degree cells to native points | Passed on desktop and phone width |
| Select a rendered point and inspect evidence | Passed on desktop and phone width |
| Evidence timestamp, confidence, dimensions and FRP | Displayed; focus moves to evidence |
| Grid table to nearby records, inspect, clear, return to 3D | Passed |
| Nepal August 2024 empty month | Explicit no-qualifying-records state; old markers/evidence cleared |
| Repeated zoom at minimum distance and zoom out | Passed; Earth remains visible |
| Drag to rotate | Passed; drag does not select evidence |
| Return to harmonized overview | Passed; 0.25-degree annual scale remains separate |
| Browser console errors | None captured |

Browser testing found and fixed two integration issues: country loading reset the observation mode/month, and the phone canvas retained its desktop intrinsic width. The first is covered by a delayed-country integration test; the second was verified by the rendered canvas width matching its 307-pixel container at phone width.

Physical touch hardware and native two-finger pinch were not exercised. Existing automated gesture checks cover multi-pointer cancellation and tap/drag distinctions; browser checks cover phone-width buttons, selection and drag. Do not describe that as a physical-device performance test.

Local screenshots are in ignored `work/qa/desktop-observations.jpg` and `work/qa/phone-observations.jpg`. Data remains on demand: the complete static build size is not the initial browser download. Context coastlines do not become higher-resolution satellite imagery when zoomed.

## Integration after documentation PR 18

Merged documentation main `a4cb32e` into the feature branch without conflicts and added the separate observed-layer scope, usage, reproduction and contracts to the guide. No existing harmonized data file differs from that main revision.

The combined revision passed all 112 Python tests and 171 web tests. TypeScript and the production build passed again, producing the same bundle names and 310,740,011 total bytes across 9,003 files; no asset exceeds 25 MiB. Every monthly inventory and all 8,781 point-tile SHA-256 values were rechecked, with exact monthly grid/tile/daily count agreement for 3,482,732 observations. All 345 local documentation links resolve, and wording/punctuation checks pass.

The earlier desktop and phone-width checks apply to the unchanged application source and identical built bundles. Physical touchscreen testing remains unverified. This integration check does not deploy the site.
