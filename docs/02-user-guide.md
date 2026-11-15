# User guide

Start with the [United States in 2024](https://cinderline-spaceapps.pages.dev/?v=1&region=United_States&start=2024-01-01&end=2024-12-31). Select "Explore the record", keep "Harmonized" selected and use "Whole region" for Spatial scope. The examples below were checked against the published app. Their values come from the committed [US data](../web/public/data/United_States.json), [seasonal comparison](../web/public/data/season-comparison.json), [rhythm data](../web/public/data/rhythm.json) and the source reports linked beside the relevant result.

The guide follows the page from top to bottom, then its other tabs. Several panels have their own study periods. A change in the main date range does not change every analysis on the page.

## Reference scale and sidebar

"Harmonized" displays Aqua-reference-equivalent detections: observed Aqua in the earlier record and converted VIIRS later. "Raw baseline" shows the deliberately unadjusted sensor switch. The latter helps expose the effect of changing instruments; it is not an alternative count of actual burning events. The monthly comparison keeps separate lines so that you can inspect the difference directly.

"Region" selects a country. "Spatial scope" offers its national total and the published daily grid cells. For the US, the sidebar says "12 training-period-selected cells displayed out of 15305 occupied cells; region total uses all cells." The 12 cells are a daily drill-down sample selected using training-period activity. They are not the only places included in the national calculation. Each is a 0.25-degree grid square; the small dot plot marks their centres, not individual detections. Empty parts of that plot say nothing about unselected cells. These counts and the selected IDs are in the [US metadata](../web/public/data/United_States.json).

"Start date" and "End date" limit the main calendar and comparison. "Use full available record" restores the published range. The calendar extends through 2025, but those converted observations use the frozen model beyond its validation period and have no calibration interval. Season statistics and anomaly flags still use the earlier record. The [continuity report](../reports/review/extend2025/CONTINUITY.md) explains this distinction.

"Observation streams" names Terra MODIS, Aqua MODIS and VIIRS. Its checkmarks are labels, not switches. The same burning event can appear in more than one stream, so adding those counts would not count unique events. "Evidence before conclusions" explains the limits of hotspots and missing observations; its "How to read this record" button opens Methods. A separate expandable guide with that same title sits below the country heading and provides shortcuts to area selection, the historical season, unusual weeks and evaluation.

The country heading includes "Export data" for the current daily selection. "Share this view" copies a link restoring the country, date range, daily grid cell, main tab, reference scale and open evidence week. The annual year follows the calendar end year, limited to the globe's available years. The link does not freeze the dataset or preserve the globe camera, selected annual cell, Earth/table preference, drawn area or individual panel controls. If clipboard access fails, the popup provides a link you can copy manually. See [the supported application state](../web/src/explorationIntegration.ts) and [share control](../web/src/ShareView.tsx).

## Weekly calendar

"Burning activity calendar" lays out calendar weeks across years. Dark cells indicate lower recorded activity and warmer cells indicate higher activity. Colours are scaled against the largest raw or harmonized weekly value in the selected dates and spatial scope, so check the numeric week preview before comparing screenshots from different selections. The bins begin on January 1, rather than following ISO week numbering. The short period at the end of a year stays visible but is not used as a full week in seasonal statistics.

Striped "no observation" cells mark unavailable periods. They are not zero detections. A week that contains an excluded date does not get presented as a fully observed weekly total. Hovering or focusing a square shows its date range, value and available-day count; selecting it opens evidence. An outline indicates interaction, not a separate peak-week designation, and a lower-edge marker identifies a partial week. Keyboard arrows move through the grid and Enter opens the focused week. The aggregation and missing-date rules are in [calendar.py](../pipeline/calendar.py), [the calendar utilities](../web/src/utils.ts) and [the calendar component](../web/src/App.tsx).

For the US selection, week 36 covers September 2-8, 2024 and has 3,259.5 Aqua-reference-equivalent detections. The "Peak observed week" summary below the instrument example identifies it as the busiest available week and provides "Inspect peak week". Week 28, July 8-14, is unavailable: only one daily estimate remains. This distinction prevents a supplier outage from looking like a quiet week. Both examples can be recomputed from [the daily rows](../web/public/data/United_States.json).

## Annual Earth

"Open the 3D Earth view" loads the map when needed. Drag to rotate, use the zoom controls and choose "Focus United States" to return to the selected country. "Grid table" provides exact values without relying on the map. Selecting a coloured cell exposes its annual value and, where a daily series exists, a route to that evidence.

Earth uses 0.25-degree annual Aqua-reference-equivalent totals with a fixed all-year logarithmic colour scale. The year control also changes the calendar date range. Earth ends in 2024 even if the calendar includes 2025. Its squares are aggregation cells, not sensor pixels, fire boundaries or burned area; zooming does not add spatial information. Uncoloured areas have no processed value, while the legend separately identifies recorded zero.

For 2024, the annual view retains 344 of 366 calendar dates and excludes 22 outage dates. A derived correction aligns annual values with the available daily record. Custom-area monthly totals use a different exclusion rule, described below. See the [annual alignment report](../reports/calendar-confidence/OUTAGE_ALIGNMENT.md), [globe data](../web/public/data/globe.json) and [alignment data](../web/public/data/calendar-alignment.json).

## Monthly calendar and history

"Monthly calendar" sums the published daily estimates by month. Rows are years; columns are months. A month containing a supplier outage is marked "No observation", even if it contains some usable days. A partial date-range selection is also marked separately. The busiest month and busiest fully observed year are chosen only from eligible displayed values; those labels describe the available records, not verified cloud-free coverage.

In the US 2024 view, September shows 8,318 Aqua-reference-equivalent detections, rounded for display. Selecting it updates "Month vs history". A range containing only 2024 has too few other years for a historical comparison. Use "Use full available record", then choose September and 2024 in this panel: the selected value is compared with a median of 5,580, a 10th-90th percentile range of 3,850-12,546 and 22 other eligible years. It lies inside that historical range. These values are calculated from [the US daily data](../web/public/data/United_States.json) by [monthStats.ts](../web/src/monthStats.ts).

The comparison excludes the selected year and removes outage, partial and missing months. It can include the 2025 extension when that year is in the displayed record; this is different from the fixed 2003-2024 seasonal baseline further down the page. "Download month calendar CSV" exports the monthly values and their availability status.

For the remaining 2024 examples, return Start date to 2024-01-01 and End date to 2024-12-31. This restores the worked example after the full-record history comparison.

## Custom area

"Choose your own area" loads country-wide monthly cell data after "Load United States area cells" is selected. Drag a rectangle on its map, or enter Latitude, Longitude and Radius (km), then select "Show this area". "Clear selection" removes the drawn selection. A circle and a rectangle are different inclusion rules; both select whole grid cells by their centres. Boundary cells are not clipped or weighted by covered area.

The result has its own monthly calendar and history comparison across the custom-area record, independent of the main Start date and End date. It uses the national conversion without a new local fit. This area selection does not turn the main weekly calendar into a daily series for that polygon. The custom-area record ends in 2024 and omits entire outage-affected months. Per-cell values are rounded, so its sums can differ from the annual globe, which retains available daily dates. See [the area contract](../web/src/areaSelection.ts), [area reconciliation](../reports/review/area/RECONCILIATION.md) and [area data](../web/public/data/area/United_States.json).

The panel currently says "2025 is national only". The precise limit is that custom-area monthly data stop in 2024: 2025 also exists for the selected daily-cell records in Spatial scope. That older label is recorded in the [documentation review notes](REVIEW_NOTES.md).

## One week across instruments

"One landscape. Two instruments. Different counts." chooses an illustrative high-activity week with comparable daily records in the current selection. For the US 2024 example it shows:

| Series, September 2-8 | Detections or reference-equivalent estimate |
| --- | ---: |
| Observed VIIRS | 22,477 |
| Converted VIIRS | 3,259.5 |
| Observed Aqua | 2,405 |

These are aggregate observations on the same dates, not matched overpasses. The difference between the converted value and Aqua remains visible. A chosen example is not an independent performance test. Values come from [the daily data](../web/public/data/United_States.json); selection behavior is in [ComparisonJourney.tsx](../web/src/ComparisonJourney.tsx).

"Compare the full record" moves to the monthly comparison. "Inspect this week" opens daily evidence. "Check held-out results" opens Evidence & validation. The summary strip beneath the example reports the sum of available values, the date range and the peak available week. Its total is not corrected for unobserved days.

## Instrument comparison

The instrument-comparison panel compares the Aqua-reference-equivalent record, observed Aqua and the raw sensor-switch baseline. "Focus on the Aqua scale" hides the raw-baseline line and rescales the chart to make the remaining lines easier to inspect; "Show raw baseline" restores it. Neither action changes the conversion or the downloaded values. The month selector, previous/next controls and "View monthly table" expose the actual sums; "Export comparison" downloads them.

For January 2024 in the US, the panel reports raw VIIRS 9,936, reference-equivalent 1,440.8 and observed Aqua 1,878, each with 31 available daily values. Day counts matter: a low monthly sum with fewer usable dates is not directly comparable with a full month. In the early period the harmonized line equals Aqua by construction, so their agreement there is not a validation result. These values and dates are in [the US data](../web/public/data/United_States.json).

## Season preservation

"Does the conversion preserve the season?" asks whether count agreement also preserves the distribution across months. Its Study period, Common retained dates and Monthly share/Detection counts controls are independent of the main calendar. It is a national retrospective comparison over 2020-2024, including when a daily cell is selected elsewhere.

With US, All five years and Primary exclusions, mean absolute total-count error is 589.0% for raw VIIRS and 4.8% for B1. Monthly-pattern disagreement is 12.9 points for both. B1 multiplies every count by one constant, so a whole-year replacement changes totals without changing monthly shares. "Selected B1" and "Simple conversion (B1)" therefore coincide. These numbers use the [published seasonal payload](../web/public/data/season-comparison.json) and [summary formulas](../web/src/seasonComparisonData.ts).

The error table averages each year's error equally. Its pattern score is total variation times 100, not a percentage of real burning events. "Inspect monthly values and retained dates" opens the numeric table; "Study limits and source" explains the shared outage mask. Exclusions padded by one day test sensitivity to the date boundaries. They do not establish cloud-free coverage.

## Seasonal context and calendar export

"The season behind the signal." describes the national 2003-2024 baseline. The line is the historical median for each complete seven-day bin; the band is its 10th-90th percentile range. Selecting a single daily cell elsewhere does not convert this into a local seasonal model.

For the US, week 34 has a median of 2,059 reference-equivalent detections and a range of 793.5-5,438.5 at displayed precision. In the 2024 date guide this is August 19-25. Use the slider or previous/next controls to inspect other weeks. These values are in `weekly_climatology` in [the US data](../web/public/data/United_States.json).

"Historical high-activity periods" groups weeks whose historical median reaches the project's seasonal threshold. "Add historical periods to calendar" downloads an `.ics` file with those windows translated into the selected year. It does not predict which days will have detections or send alerts. The threshold and export dates are defined in [calendar.py](../pipeline/calendar.py) and [SeasonalContext.tsx](../web/src/SeasonalContext.tsx).

## Unusual observations

"Unusual observations" lists complete weeks outside the historical 10th-90th percentile range for that week of the year. Each comparison leaves out the year being assessed. The US 2024 view has eight flagged weeks, four higher and four lower. The February 19 week has 2,292.2 reference-equivalent detections and a displayed z-score of +3.24. See `anomalies` in [the US data](../web/public/data/United_States.json).

A z-score is `(weekly value - historical mean) / historical standard deviation`. It measures deviation from that week's reference distribution; it is not a probability, severity rating or risk score. The flag itself uses percentile bounds, so a flagged week does not need to cross a particular z-score cutoff. Missing scores stay unavailable rather than becoming zero. The implementation is in [calendar.py](../pipeline/calendar.py).

Choose All, Higher activity or Lower activity, then sort by Newest first, Oldest first or Largest |z-score|. Selecting a row opens its weekly evidence. This is a national analysis: choosing a daily cell replaces the list with a request to select "Whole region". The list is limited to complete weeks within the selected date range and still uses harmonized values when the raw calendar comparison is selected. The 2025 extension has no newly generated anomaly flags.

## Weekly evidence drawer

A selected week opens "What each sensor detected", "How this estimate was made" and "Daily estimates". The US September example includes Terra 2,402, Aqua 2,405 and VIIRS 22,477. Its model is B1 and its source is converted VIIRS. The daily rows show the estimates and calibration intervals separately; the page does not add those intervals into a weekly confidence interval. All values are in [the US record](../web/public/data/United_States.json).

"Download daily CSV" and "Download evidence brief" preserve the selected evidence for inspection. "View 2024 on Earth (annual)" opens that year's map, not a map of the selected week's individual detections. Closing the drawer returns to the page. A source list or an archive label does not establish that every day was cloud-free.

## Evidence and validation

"Evidence & validation" opens "Let the baselines compete". The table retains B0, B1 and M1, validation and test periods, and weekly/monthly aggregations. Bias measures the overall signed count difference, MAE the mean absolute difference per period, and correlation whether the series rise and fall together. These are different measures; one good number does not replace the others.

For the US selected B1, the locked weekly test result is +1.7% bias, MAE 390.8 and correlation 0.905 over 2020-2024. Those values use a different aggregation and coverage treatment from the later season panel. Read [the Layer 1 table](../reports/review/layer1_table.md) and [harmonization guide](03-harmonization.md) before comparing them.

"Weekly pattern: see the 7-country test" links to the separate rhythm tab. "What every estimate carries" describes source observations, transformation and uncertainty. These are traceability categories, not extra validation scores.

## Weekly Rhythm Index

This tab has its own country selectors and uses each raw satellite stream separately. The calendar's harmonization did not reveal this pattern. The opening decision table reports the pre-specified country rule: US, Australia and Brazil pass; the other countries do not. The US passes in all three streams. Source: [official gate](../reports/official/kill_test_gate.json).

"Stricter checks on the passing countries" reports additional criteria without rewriting that decision. Brazil fails its long-window matched industrial-source control check. US VIIRS volcano detections have a separate unexplained Sunday pattern concentrated at Kilauea. Those qualifications matter even when the main country rule passes.

The weekday charts show detections on each weekday divided by an average day. The US All detections indices for Sunday are Terra 0.723, Aqua 0.667 and VIIRS 0.782. An Aqua index of 0.667 is about one-third below that stream's average day, not one-third fewer distinct events. Whiskers show year-bootstrap intervals; the orange weekday is the pre-specified comparison. "Daytime only" changes these charts. See [official stream results](../reports/official/kill_test_results.csv).

"Count the detections. Compare their power." is a separate fixed US daytime FRP study. The country and all/daytime controls above it do not change its scope. Aqua's Sunday count index is 0.644 and its FRP index is 0.815; two of the three streams meet the stated count-versus-FRP criteria. FRP is sampled radiative power, not burned area or total energy. "Read the values and test criteria", "What this comparison cannot establish" and "Protocol timing and reproducible evidence" expose the constraints. See [the FRP results](../reports/review/frp/FRP_TEST.md).

"Compare static heat sources" gives pooled control results. Its small deviations do not cancel a country-specific failure, which remains in the stricter-check table. "Where is the dip? One-degree cells" is exploratory and has its own country selector. Select a cell to inspect its values; blue denotes a lower Sunday index, while grey land can mean insufficient data. The northeast India cluster is descriptive and was delineated after inspection. Neither it nor the national weekday pattern identifies who caused a detection or why. The [weekly-rhythm guide](04-weekly-rhythm.md) covers the map thresholds, controls and unsuccessful predictions.

## Methods

"Methods" presents Process, Limitations and Data sources. "Keep the instruments separate" explains cleaning and civil dates; "Use Aqua as a reference" describes model comparison; "Let the evidence set the story" distinguishes simulation, conversion and raw-stream rhythm analyses. "What the record cannot tell you" lists the observation and inference limits. "Data sources" links the NASA FIRMS archive and shows the dataset generation timestamp, which is not a last-observed or live-update time.

For the formulas and full result tables, continue to [harmonization](03-harmonization.md). For exact rebuilding commands and the limits of the current reproduction workflow, use [data and reproduction](05-data-and-reproduction.md).
