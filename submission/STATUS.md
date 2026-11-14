# Submission draft status

## Prepared

- Harmonized calendar for all seven countries (Australia, Bangladesh, Brazil, Egypt, India, Nepal, United States), 2003-2024, deployed from commit `e71f214` and verified at the public Cloudflare URL (see `DEPLOYMENT.md`).
- Human rhythm: official pre-registered decision **pass** (US 3/3 streams, Australia 3/3, Brazil 2/3; India, Nepal, Bangladesh, Egypt fail), from `reference/kill_test.py`, outputs in `reports/official/`. Sunday-only caveat and Brazil static-control caveat are stated in the app, LIMITATIONS.md and these drafts.
- Robustness checks from the stricter 2002-2024 analysis: US and Australia meet all; Brazil's Terra matched static control is flagged (index 0.913, adjusted p = 0.021).
- Exploratory per-cell map, including the northeast India finding (19 of 26 cells significant after false-discovery correction; Aqua agrees). Per-state table and figure: `reports/official/exploratory_ne_india/`.
- Project page (under 500 words), seven-slide outline and demo script follow the two-act story: act 1 harmonization, act 2 human rhythm.
- The GitHub repository is public.

## Before submission

- **Merge PR #1 (`rhythm-integration`) and redeploy.** The live site was deployed from `e71f214` and does not yet include the Human rhythm tab.
- The northeast India text (religion shares from the Census of India 2011) is in PROJECT_PAGE.md, SLIDES.md, VIDEO_SCRIPT.md and the app; the team should review it.
- Verify the live event's submission fields, deadline (15 November 2026, 11:59 pm Nepal time) and media limits.
- Record and review the actual demo video from the deployed build.
- Team members must review the scientific interpretation and final text. These drafts have not been submitted or sent externally.
