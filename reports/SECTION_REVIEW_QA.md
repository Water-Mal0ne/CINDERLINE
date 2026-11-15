# Section review and recovery QA

Reviewed 2026-11-15, starting from `cb54eac` on `ui-polish-v2`. This cycle preserves the scientific wording, values, captions, caveats and published data. It changes interaction, accessibility and recovery behavior. No merge or deployment is authorized by this review.

## Explore the record

- Monthly inspection now follows the selected calendar month when the date range changes, instead of following an array position. Changing country or spatial scope resets the selection; excluding the selected month clamps it to the available range.
- Opening and closing evidence no longer collapses an expanded unusual-observations list. Phone controls, seasonal controls and comparison labels have larger targets or text where needed.
- A globe selection requires a completed primary-pointer tap. Dragging away and back, additional pointers, cancellation, secondary clicks and releases without a matching press cannot accidentally select a cell. Listener cleanup and the existing demand-rendering behavior are preserved.
- The annual grid table is a labelled keyboard focus target. Phone pagination advanced from page 1 to page 2 of 13; focus remained on the named table group and the document had no horizontal overflow.

## Evidence and validation

- Explicit navigation brings the chosen workspace into view and focuses its main landmark. Before the fix, the held-out heading could be 635 pixels above the viewport after the comparison journey; after the fix it was visible at 206 pixels with the main landmark at 20 pixels.
- Held-out and daily evidence tables have named scroll regions, column headers and readable phone text. ArrowRight scrolled the held-out table at 390-pixel viewport width, without scrolling the whole page sideways.
- Index, country and cell failures offer a targeted retry. Malformed successful responses are rejected before rendering. Retrying clears only the affected data cache and requests a fresh response; older in-flight responses cannot refill the cache with stale data.
- A failed shared cell link retains its requested evidence week. Repairing the response and retrying restored Nepal cell `27.25:84.75`, week 1 of 2024, including its URL state. Deliberately leaving that view cancels the pending drawer.
- Choosing Methods while a shared-link country request was delayed by five seconds kept Methods open after the response arrived. The response no longer overrides a newer navigation choice or reopens an old drawer.

## Weekly Rhythm Index

- National analysis, exploratory cells and land outlines have recoverable, abort-safe loading with structural checks. Valid empty cell collections get an explicit empty state. If the usual initial country is absent, an available country is selected.
- Outline retry is independent of the scientific payload. With the cell endpoint deliberately failing, retrying a repaired outline retained all 234 India cells and the selected cell while loading the outline successfully.
- The exploratory map has one tab stop, visible selection and ArrowLeft/ArrowRight/Home/End navigation. Tab exits the map instead of traversing hundreds of cells. National and map country controls remain independent as before.
- All seven national country panels loaded without alerts. `?view=rhythm` restored the Rhythm view. The data validators preserve all shipped payloads without coercing or recomputing their values.

## Methods

- Process, Limitations and Data sources links provide direct navigation through the existing content. Their targets accept focus and remain visible below the scroll offset.
- Sidebar, footer and primary navigation use the same workspace navigation behavior. All 153 original App JSX text nodes remain verbatim; the four added labels are Process, Limitations, Data sources and Retry loading.

## Verification and limits

- Three implementation lanes were reviewed separately, followed by independent review of the App recovery logic and scientific-file diff. All 49 original Globe and 93 original Rhythm component JSX text blocks are retained.
- Added regressions exercise the real component handlers/effects, cache races, selection state, malformed-response recovery and map/globe input rules. The App navigation/retry tests were mutation-checked by disabling each guard in memory and observing its corresponding failure.
- The production build was checked locally at 1440 by 1000 and 390 by 844. All seven calendars exposed 1,166 week buttons and no alerts. Raw/harmonized switching, evidence closing/focus return, month selection, anomaly expansion and lazy WebGL rendering worked.
- Nepal week 28 of 2024 retained unavailable weekly activity and the distinction between the July 8 zero and the July 9-14 missing estimates. No observation was converted to zero by these UI changes.
- Fault tests used an external localhost server with response overrides; repository data files were never altered. Malformed index, country, cell and rhythm responses and independent outline failures were recovered in the browser. No errors were captured from the production preview. Earlier transient Vite errors during simultaneous source edits were absent from that final build.
- Browser proof images are saved outside the repository under `outputs/firetrace-section-review/screenshots/`. Full Python/web/build checks are required after this commit; the external check receipt records the exact commit and results.
- Physical multi-touch and a hardware out-and-back drag were not browser-tested; these paths are covered by the gesture-state unit tests. National/map country synchronization and Rhythm-country URL persistence were not added. The existing large lazy globe chunk warning remains. This cycle does not certify scientific accuracy or merge the separate scientific wording changes.
