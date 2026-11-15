# Content-first preview: scientific preservation review

Reviewed the `test/content-first-redesign` working tree against `7d390c4` on 2026-11-15. This is a source review; browser checks belong to the integration review.

## Scientific content

- No changes were found in `web/public/data`, analysis source, Python tests, or pipeline scripts.
- A TypeScript AST comparison of JSX text in App, Globe, ObservationControls, ObservationEarth, RhythmCellMap, RhythmView, and MonthCalendar found no removed scientific explanatory prose. Removed text was old marketing copy, navigation wording, and the “READ BEFORE INTERPRETING” label. “Calendar below” became “calendar” to match the separate Earth view.
- All sensor, calendar aggregation, season, anomaly, uncertainty, and calibration utilities remain unchanged. The review does not revalidate the underlying scientific method.
- The observed Earth layer retains its explicit non-harmonized, UTC, 2024-only labels and its distinction from local-date, outage-masked calendar values. Native hotspot evidence retains its original fields and warnings.
- Annual Earth totals retain the supplier-outage explanation, unknown coverage warning, and distinction between annual sums and omitted weekly/monthly bins. The selected-cell caveat remains beside its drill-down action.
- Weekly and monthly calendars retain no-observation and partial-bin handling. Monthly mode enables the existing after-2024 reliability notice; weekly mode retains the full frozen-model/2025 warning.
- Rhythm results retain the pre-specified decision, Sunday caveat, selected-country robustness note, exploratory status, correction methods, controls, and non-causal wording. Detailed robustness tables and longer limits now require explicit disclosure.

## Integration findings sent to the implementation team

1. **Season-guide keyboard focus:** the new journey effect calls `focus()` on `#seasonal-context`, but that section did not have a tabindex. The previous focus helper supplied it. The guide can therefore scroll without moving keyboard focus. Add a programmatic focus target before scrolling.
2. **Evidence-to-calendar destination:** the “Open a calendar week to inspect evidence” action only changes the top-level view. If Earth or Patterns was the last Explore subview, it returns there. Explicitly select the weekly calendar for this action.
3. **Sharing the selected subview:** newly introduced Calendar/Patterns/Earth, Weekly/Monthly, and pattern subviews were not in the share-link state at review time. A link labeled “Share this view” can reopen a different workspace. Serialize the new presentation state, or clearly limit the share contract to record filters. This is a presentation-state issue, not a data transformation.

## Resolution review

All three introduced navigation findings above were resolved in the final source review:

- `SeasonalContext` now has `tabIndex={-1}`, allowing the guide journey to transfer programmatic focus to its target.
- The evidence-page calendar action selects the weekly Calendar workspace before requesting focus. Its regression test passes after an Earth visit and an earlier Monthly selection.
- The presentation-only `workspaceNavigation.ts` helper now serializes Calendar/Patterns/Earth, Weekly/Monthly, and the selected pattern view. App initializes and restores that state on browser history navigation, includes it in share links, and resets it when resetting a shared view. The helper preserves scientific query parameters; component tests verify reload/history restoration alongside unchanged country, scale, and dates.

Independent test runs after the integration stabilized:

- 47 tests passed across app recovery/journeys, workspace navigation, seasonal baseline, exploration state, and exploration integration.
- 34 tests passed across workspace navigation, observation detail, globe recovery, and rhythm interaction. This is a separate overlapping suite, not 34 additional unique tests.

The new Earth workspace unmounts the WebGL components when another workspace is active. Existing cleanup code disposes demand render loops, controls, observers, event handlers, GPU resources, and pending requests. Both Earth renderers also retain document-visibility and intersection-based pausing. No newly hidden active WebGL loop was found in source.

Known pre-existing sharing limit: the observed-versus-harmonized Earth mode and independent observation month are not serialized; camera, selected annual cell, and Earth/table mode also reset. The new workspace choices themselves now restore. This review does not claim a complete Earth-camera or observation-state permalink.

No scientific source or data changes were made by this review. Browser layout, native-dialog interaction, device performance, and assistive-technology behavior require separate browser verification.
