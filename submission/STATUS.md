# Submission package status

## Prepared

- Harmonized calendar for all seven countries (Australia, Bangladesh, Brazil, Egypt, India, Nepal, United States), 2003-2024. The overnight brief identifies `main` at `290e756` as the deployed and verified safe baseline. Changes on `story-wording` are review-only and have not been deployed.
- Weekly Rhythm Index: official pre-specified decision **pass** (US 3/3 streams, Australia 3/3, Brazil 2/3; India, Nepal, Bangladesh, Egypt fail), from `reference/kill_test.py`, outputs in `reports/official/`. Sunday-only caveat and Brazil static-control caveat are stated in the app, LIMITATIONS.md and these drafts.
- Robustness checks from the stricter 2002-2024 analysis: US and Australia meet all; Brazil's Terra matched static control is flagged (index 0.913, adjusted p = 0.021), but the dip comes entirely from 2002-2007 and the control is flat over 2013-2024 (`reports/review/controls/CONTROLS.md`).
- Exploratory per-cell map, including the northeast India finding (19 of 26 cells significant after false-discovery correction, 14 of 21 cells mostly inside India; Aqua agrees). Per-state table and figure: `reports/official/exploratory_ne_india/`.
- Project page (under 500 words), seven-slide PDF/PPTX, source slide text, short-video/live-pitch scripts, twenty judge answers, team briefing and submission checklist are prepared for human review. We reproduce a known weekly pattern in each satellite record separately. Independently, CINDERLINE tests whether its historical calendar survives a change of sensor and calibration.
- Reviewed FRP and common-date seasonal sensitivity evidence is packaged with pinned source commits, exact snapshots and independent verification receipts. New research and UI additions remain on separate PRs until approved; a submission document is not evidence that a feature has been deployed.
- The GitHub repository is public.

## Before submission

- Review the overnight PRs before any merge or deployment. The existing safe site remains unchanged during this work.
- Review the exploratory northeast India map and the failed Bangladesh prediction without assigning a cause.
- Verify the live event's submission fields, deadline (15 November 2026, 11:59 pm Nepal time) and media limits.
- Check the public seven-slide PDF as the demo, or record and time the optional short video from the approved build. A script is not a finished recording.
- Team members must review the scientific interpretation and final text. These drafts have not been submitted or sent externally.
