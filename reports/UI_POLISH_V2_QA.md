# UI polish v2 overnight verification

2026-11-14 19:47 UTC. Existing UI work at `1406b38` is retained. This follow-up is limited to the three requested UI tasks. The live deployment and scientific artifacts are unchanged.

## Visible changes in this follow-up

- The existing Harmonized / Raw baseline toggle and exact scope explanation now sit above the sidebar, visible on the first desktop and 390-pixel phone screen. One control remains; it preserves its existing state and URL behavior and is disabled during data/link hydration.
- Phone navigation uses two columns so all four tabs fit without page-wide horizontal scrolling.
- Rhythm chart labels, notes, caveats, map legends and selected-cell readouts have more readable phone sizing and wrapping. Wide tables scroll within their panels and accept keyboard focus.

Earlier `1406b38` changes retained in this PR include recoverable date and grid errors, exact calendar-week inspection and partial-week labels, scoped comparison CSVs, annual-grid pagination/search/daily-cell filtering, globe retry controls, and touch/keyboard seasonal inspection. Their original evidence remains in `reports/UI_CYCLE_QA.md`.

## Checks

- Independent real-asset checks decoded all seven national and 84 published cell series: 8,036 unique dates each, correct identities and nonempty finite values. All 42 rhythm country/stream/subset records have seven weekdays. No data regeneration was needed.
- Browser: all seven national calendars, one published daily grid per country and all seven validation tables load without alerts; a grid evidence drawer reports the selected cell correctly.
- Browser: `?view=rhythm` restores the selected tab; the lazy Earth view renders at phone width; no captured JavaScript errors.
- Browser at desktop and 390 pixels: scale toggle is visible on the first screen; switching to raw updates the pressed state and URL. Phone document width equals scroll width (375 CSS pixels after the vertical scrollbar).
- Browser: rhythm charts, caveats, robustness notes and exploratory map remain readable; selecting a map cell shows its existing numeric readout. ArrowRight scrolls the focused official-results table.
- Browser: Nepal calendar week 28 of 2024 retains unavailable weekly activity and the documented outage's missing daily estimates, rather than presenting a zero activity total.
- Source AST comparison against `1406b38` retains all existing App and RhythmView text/string/numeric literals. Only the visible UI label "Calendar reference scale" is added. Pipeline, public scientific data, model and official result files are unchanged.
- Shared web test discovery preserves the existing prechecks and all branch-specific tests when combined with the FRP feature. The runner matches that branch exactly.

Full Python/web/build checks are run after the commit; the external overnight check receipt records the final commit and result.

## Known limits

The rhythm country picker remains independent of the calendar country and is not persisted in shared URLs; `?view=rhythm` restores the tab, not its internal picker. This is existing behavior and was left unchanged under the bounded UI scope. Scientific wording corrections belong to the separate story-wording PR. Network/GPU failures were not artificially injected in this browser pass. This report does not claim the absence of every possible defect.
