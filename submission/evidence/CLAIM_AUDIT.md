# Submission numerical and source audit

**PASS for the authored Markdown package.** This audit checks existing facts and
claims; it does not add a scientific analysis or independently verify the external
NASA/Earl sources again. The root reviewer verified those primary sources and
provided their URLs and dates, retained in `source_manifest.json`.

The exact versions of the five authored documents, submission checklist and current
root AI disclosure are bound by normalized-LF
SHA-256 hashes in `document_checks.json`. Check the package from any checkout:

```sh
python scripts/build_submission_facts.py --check --audit-docs
```

The command validates 38 exact source hashes, reconciles the Layer 1 table with
the official locked evaluation, checks FRP/season approval receipts, reproduces
`facts.json` and `SOURCE_LEDGER.md`, and rejects changed document content or failed
word limits. It uses the Python standard library and the packaged evidence; other
branches and worktrees are unnecessary for this fact-extraction check. The
underlying scientific rerun commands belong to the pinned source branches.

## Delivery limits

| Item | Checked result |
|---|---|
| Slides | Exactly 7 |
| Title plus on-slide words | 17, 20, 26, 35, 25, 28, 22; all at most 40 |
| Speaker-note words | 70, 72, 77, 80, 78, 82, 81; all 60–90 |
| Project page | 419 words; under 500 |
| Judge questions | Exactly 1–20, in order |
| Short spoken script | 70 words; close to the requested approximately 75 |
| Live spoken pitch | 271 words; timing still requires rehearsal |
| Team briefing | 432 words |

The slide counts cover authored title and body text, not embedded chart labels or
production directions. Rendering and screenshot legibility are checked separately
by the deck reviewer. Written word counts cannot certify recording duration.

## Numerical checks

- **Held-out table:** Nepal B1/M1 weekly MAE 43.3/11.3 and biases +83.8%/−8.1%;
  Egypt selected MAE 4.3 and bias +51.7%. Units remain Aqua-reference-equivalent
  detections for MAE, with Aqua as reference rather than ground truth.
- **Stability:** reported Egypt/US test-versus-train ratio changes round to
  +39%/+10%; US selected weekly correlations round to 0.97 in 2020 and 0.74 in
  2024. Bangladesh 2022 selected bias/correlation round to +114%/0.18.
- **Evidence-card intervals:** Q6 matches `web/src/App.tsx` lines 91–92: the
  drawer displays each day's conversion bounds and explicitly does not sum them
  into a weekly confidence interval. Observed Aqua rows show no calibration
  interval; that is not a claim of perfect observation.
- **Official rhythm:** US 3/3, Australia 3/3 and Brazil 2/3 streams; India, Nepal,
  Bangladesh and Egypt do not pass. The separate new-cell robustness result is
  not substituted for this official result.
- **Nepal simulation:** the planted 20% Saturday dip yields 12% country pass and
  84.5% VIIRS significance over 200 simulations. Actual VIIRS Saturday index
  1.015 is kept separate from synthetic power.
- **Controls and geography:** VIIRS volcano Sunday index 0.861 matches the saved
  control, and removing Kilauea's 2018 detections removes corrected significance.
  The 0/201 outside-northeast and 14/21 mostly-inside-northeast cell statements
  match the review. The one-of-two failed Bangladesh prediction remains visible.
- **Outages:** 38 production dates per country are distinct from the retrospective
  common-date masks of 73 and 87. Known masks do not certify clear-sky coverage.
- **Season table:** all six India/Nepal rows match the independently verified
  whole-year summaries after rounding. The comparator is B1 versus selected M1;
  masked annual errors use retained-date totals. TV × 100 is monthly-share
  disagreement in points, not a percentage of actual fires.
- **FRP:** Aqua and S-NPP VIIRS pass both masks; Terra fails its adjusted interval
  criterion. The displayed contrast uses paired valid-FRP observations and twelve
  year blocks. It is separate from the official all-detection weekday indices.

## Claims and chronology

Questions 1–20 cover the requested sensor transition, resolution, drift,
uncertainty, prior weekly-cycle literature, causal limits, Brazil, Nepal,
Kilauea, preregistration distinction, failed Bangladesh prediction, Punjab null,
custom-area limits, historical scope and AI use. The quoted FRP conclusion is
bounded to US daytime observations and its pre-specified contrast.

The local FRP protocol preceded its first calculation; the Git receipt followed
the known result. Season diagnostics reuse previously examined years. NOAA-20
supports transfer between related products, not ground-truth accuracy, and its
strict common-date outage sensitivity remains pending. Summed snapshot FRP is
not energy, emissions, burned area or ignition cause. The package retains these
limits rather than treating a passing criterion as general validation.

The repository is currently PUBLIC according to the root reviewer's GitHub check;
the recorded check is in the manifest. A final logged-out access check, exact
video timing and human approval of the submission remain checklist items. No
branch merge or deployment is implied by inclusion of reviewed result snapshots.

## Submission fields and disclosure

The checklist covers the project title, short summary, demo link, final-project
link, detailed description, NASA/partner/other resources, AI use and personal
terms acceptance listed in the [Global Organizing Team answer](https://github.com/nasa/spaceapps/discussions/1858).
The [Navigator demo clarification](https://github.com/nasa/spaceapps/discussions/1991)
allows a presentation of at most seven slides or a video shorter than 30 seconds.
These sources were independently reopened for this audit on 14 November 2026 UTC.

The [local organizer listing](https://gdg.community.dev/events/details/google-gdg-kathmandu-presents-nasa-space-apps-challenge-2026-bhaktapur-local-event/)
supports Bhaktapur, Khwopa Engineering College and the 14–15 November event dates.
Its event end is 23:59 Nepal time; the checklist correctly asks the team to confirm
an earlier judging cutoff instead of assuming that event end guarantees a local
submission deadline. The 20:00 target is a team planning target. Actual team name,
six registered members, official project URL and any optional recorded-video URL
remain explicit placeholders; no identity or registration has been invented.

The checklist separates existing live links from future branch/main PDF links,
requires signed-out checks, and does not imply the final form or terms have been
submitted. Its AI statement matches the corrected root disclosure: real NASA
observations remain distinct from synthetic fixtures, and both historical gate
timing and the FRP after-result Git receipt are qualified. The immutable older
AI-disclosure snapshot remains exact historical evidence; the current corrected
disclosure and Q9 govern submission claims.
