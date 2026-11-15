# Section review: round two

15 November 2026, 09:25 Nepal time (UTC+05:45). Baseline: `4885399` on `ui-polish-v2`. Three implementation agents and the coordinator worked in separate file lanes, then reviewed one another's changes. No merge or deployment was performed.

## Explore the record

- Expanding unusual observations now focuses the first new result, including the final batch where the expansion button disappears. At phone width, expanding eight results to sixteen focused result nine; opening and closing its evidence drawer returned focus to that same result and retained all sixteen.
- Calendar boundary-arrow input now clears a competing hover preview even when the focused week cannot move. Moving the pointer toward the evidence action still retains the hovered week.
- Final desktop inspection found the month/date label wrapping inside a fixed-width column. A desktop-only intrinsic-width column now gives that label and its arrow controls enough room while the slider fills the remaining width; phone rules are unchanged.
- Isolated monthly and seasonal values, including zero, now get visible point marks. Missing values remain missing. Independent review additionally reproduced a monthly line spanning an entirely absent February; line segments and isolated markers now respect calendar-month adjacency, including December to January. Seasonal slots already preserve missing-week gaps in both lines and bands. Aggregation and exports are unchanged.

## Evidence and Methods

- A shared Rhythm or Methods URL now opens its requested page immediately, without depending on a successful calendar index or country response. The existing URL-validation rules and delayed-navigation revision guard remain intact.
- Methods anchor/history navigation after an index failure no longer leaves Retry loading permanently disabled. In the browser, a failed index still allowed Limitations navigation, then repaired successfully while keeping Methods selected.
- Existing evidence behavior was checked at phone width: named table regions, no page-wide horizontal overflow, and correct focus return from the drawer. Data sources navigation still focuses the target and exposes the real source link.

## Weekly Rhythm Index

- Country links in the verdict table expose their selected state and target. They focus and scroll the corresponding detail heading, including a repeated click on the same country. All seven headings reached about 20 pixels below the viewport top on a phone, without horizontal overflow.
- In-panel country and All detections / Daytime only controls retain their own focus and scroll position. The subset selector has explicit group semantics, and both results tables associate row and column headers with their values.
- Boundary keys restore the focused map cell's readout after hovering a different cell, even when the browser does not emit a new focus event.
- Browser fault injection independently confirmed that the Rhythm view remains available when the calendar index or country endpoint fails. National and map selections remain independent as before.

## Globe and grid table

- HTTP-200 malformed globe data now reaches the existing recoverable error panel rather than crashing during rendering. Retry invalidates only `globe.json` and fetches a fresh response. The browser recovered from an empty-object response into the real WebGL/table view.
- Compass directions bind numbers to the correct coordinate axis. For the real US cell at `18.875 N, 155.625 W`, the correct query returns one row; the reversed `155.625 N, 18.875 W` returns none. Free numeric and partial-coordinate searches remain supported.
- Selected-cell details survive switching between the grid table and 3D Earth, including the graphics fallback state. Country/data changes still clear the old selection. The browser retained the same US cell, including its recorded zero, across table/Earth/table changes.
- A nonmutating shape guard accepts the shipped 41,986-cell dataset unchanged and preserves null versus zero. The existing demand renderer, lazy load and scientific scales are retained.

## Evidence and boundaries

- New regressions were observed failing before the corresponding fixes. Focused suites cover real component events/effects and sparse data fixtures, rather than only static source checks.
- Independent source audits retain all 399 JSX text blocks across the seven changed views. Scientific data, models, pipeline, official results, captions and caveats are unchanged.
- Production preview checks use 1440 by 1000 and 390 by 844 viewports. Every country calendar loaded 1,166 week controls with no alerts after recovery. New sparse-chart cases are covered by component tests; they do not claim those gaps occur in the current national data.
- Screenshots, source-text audit and final post-commit test/build receipt are kept outside the repository in `outputs/firetrace-section-review-2/`. The full Python suite, full web suite with prechecks, TypeScript and build are run after the commit.
- Actual screen-reader speech and physical multi-touch remain untested. Rhythm-country URL persistence and national/map-country synchronization remain outside this round. The existing lazy globe chunk warning and previously documented future story/FRP branch conflicts remain. Scientific narrative corrections are still a separate unmerged PR.
