# Reliability and exploration guidance

Additive components only. Existing scientific outputs, model choices, source data and scientific text were not edited by this task.

## Components

- `ReliabilityNotice` provides a visible scope statement and a native, initially closed evidence-limits disclosure. National weekly test numbers are selected by exact country, frozen model, split and aggregation. They never become local error estimates and are hidden for the raw scale. The peak-week metric is explicitly about the highest week, not displacement of a whole season.
- `recordAvailability` describes published daily values, not satellite observation exposure. It distinguishes numerical zero, missing values and missing day records; validates civil dates; handles leap years; respects inclusive selected dates; and prevents duplicate dates inflating availability. Missing or reversed calibration intervals are reported only for converted rows.
- Explicit `scope` values support national, cell, selected area and annual grid views. Monthly-area views must omit `rows`; monthly totals cannot stand in for daily observation coverage.
- Dates after 2024 receive a separate test-window note. Integrators can set `showPeriodNote={false}` where the existing 2025 warning already makes that fact visible.
- `ExplorationGuide` is a collapsed native disclosure with four callbacks: choose area, historical season, unusual weeks, evaluation. It changes no selections, inserts no tour overlay and preserves `ComparisonJourney`. Its copy does not assume that the old twelve-cell subset is the only area workflow.

## Integration contract

`ReliabilityNotice` requires `regionName`; optional props are `regionId`, `cellId`, `scope`, `model`, `evaluations`, `rows`, `start`, `end`, `mode`, `showPeriodNote`, and `onValidation`.

`ExplorationGuide` requires `regionName`, `onChooseArea`, `onSeason`, `onAnomalies`, and `onEvidence` (the latter should open evaluation; the guide text directs the user to a calendar square for week-specific evidence).

Parent owns `App.tsx` and `Globe.tsx` integration. No scientific confidence score or operational safety claim is created.

## Design direction

Product: compare historical satellite detections and inspect their support. Character: restrained, exact, readable. World: the existing graphite observation dashboard. Moments: the existing data plots; these additions provide context, not competing visuals. Signature: the selected area remains explicit.

The current interface is already polished. Additions use its neutral palette and typography, 4px spacing, small inline icons, native disclosure controls and 44px mobile targets. No animation, new asset or dependency is added.

## Verification

- `node --test tests/reliability.mjs`: **11 passed**. Includes all seven actual country metadata/evaluation matches, alternate candidate/split/scale isolation, invalid and leap dates, missing versus zero, duplicates, interval availability and dates beyond the frozen evaluation.
- `npm run typecheck`: initially passed with these new files. A subsequent integrated run encountered only the temporarily missing `SeasonComparison` import while another agent was writing that component; final integrated type checking belongs to the coordinator.
- Final integration must check native disclosure keyboard operation, mobile line wrapping, correct scope beside selected globe cells, the existing 2025 note without duplication, and guide callbacks reaching their intended sections.

Sources for new interpretation text: existing `METHODS.md`, `LIMITATIONS.md`, `pipeline/harmonize.py` and the unchanged public evaluation records. These components expose existing limits and metrics; they are not a new scientific evaluation.
