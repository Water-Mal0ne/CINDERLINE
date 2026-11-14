# Submission draft status

## Prepared

- Harmonized calendar for all seven countries (Australia, Bangladesh, Brazil, Egypt, India, Nepal, United States), 2003-2024. The overnight brief identifies `main` at `290e756` as the deployed and verified safe baseline. Changes on `story-wording` are review-only and have not been deployed.
- Weekly Rhythm Index: official pre-specified decision **pass** (US 3/3 streams, Australia 3/3, Brazil 2/3; India, Nepal, Bangladesh, Egypt fail), from `reference/kill_test.py`, outputs in `reports/official/`. Sunday-only caveat and Brazil static-control caveat are stated in the app, LIMITATIONS.md and these drafts.
- Robustness checks from the stricter 2002-2024 analysis: US and Australia meet all; Brazil's Terra matched static control is flagged (index 0.913, adjusted p = 0.021), but the dip comes entirely from 2002-2007 and the control is flat over 2013-2024 (`reports/review/controls/CONTROLS.md`).
- Exploratory per-cell map, including the northeast India finding (19 of 26 cells significant after false-discovery correction, 14 of 21 cells mostly inside India; Aqua agrees). Per-state table and figure: `reports/official/exploratory_ne_india/`.
- Project page (under 500 words), seven-slide outline and demo script distinguish the two analyses. We reproduce a known weekly pattern in each satellite record separately. Independently, FIRETRACE tests whether its historical calendar survives a change of sensor and calibration.
- The GitHub repository is public.

## Before submission

- Review the overnight PRs before any merge or deployment. The existing safe site remains unchanged during this work.
- The northeast India text (no causal claim; census context only in METHODS.md) is in PROJECT_PAGE.md, SLIDES.md, VIDEO_SCRIPT.md and the app; the team should review it.
- Verify the live event's submission fields, deadline (15 November 2026, 11:59 pm Nepal time) and media limits.
- Record and review the actual demo video from the deployed build.
- Team members must review the scientific interpretation and final text. These drafts have not been submitted or sent externally.
