# CINDERLINE atlas preview

This second redesign is isolated on `test/atlas-redesign`, based on `955332d`. It is intended only for the `atlas` branch of the separate Cloudflare Pages project `cinderline-ui-preview`. Do not merge, push or publish it to production without the user's next instruction.

## Presentation changes

- Desktop navigation becomes a left rail. Phones use a compact native disclosure. Each destination has one page heading.
- The monthly calendar is the fresh-arrival view. Existing query links keep their previous defaults; weekly evidence still opens the weekly view.
- Country and observation period occupy one compact toolbar. Secondary filters and CSV export sit inside Area & dates.
- Duplicate headings, navigation explanations, badges and promotional text are removed. Reading instructions live in named disclosures. Distinct scientific caveats and quantities remain intact.
- Earth puts the map beside its year and legend on wide screens. On phones, the year precedes the map and the legend follows it. Observation-layer distinctions and evidence remain available.
- Patterns, Weekly Rhythm Index, FRP, Evidence and Methods use readable chart/editorial layouts with fewer nested boxes.
- Legacy styles are explicitly layered. Relative typography, 24px base / 44px coarse-pointer calendar targets, control borders and keyboard selection are strengthened.
- Fonts are self-hosted with licenses and source hashes. A noscript fallback and tested-in-preview security-header policy are included.

## Verification before deployment

| Check | Result |
| --- | --- |
| Python | 112 passed |
| Web | 178 passed |
| TypeScript and root build | Passed |
| Data/science pipeline diff versus first preview | Empty |
| Seven countries at 320px | Loaded monthly tables without page-level horizontal overflow |
| Weekly evidence keyboard flow | Arrow navigation, Enter open, Escape close and focus return passed |
| Share panel at 320px | In bounds; copy feedback and manual URL shown |
| Custom area | US point/radius selection populated 2003–2024 monthly calendar |
| Weekly Rhythm Index / FRP | Country selection and US daytime FRP disclosure passed |
| Earth | Both layers reviewed; desktop map/sidebar and narrow layouts checked |
| Static output | 9,021 files; 310,977,010 bytes; largest 12,999,487 bytes; none over 25 MiB |

The build's existing lazy Globe bundle exceeds Vite's advisory 500 kB chunk threshold. It remains loaded on demand. Field Core Web Vitals, physical-phone gestures, OS text-scale settings, forced-colors runtime and a screen-reader user audit are not certified by these checks.

## Guide scope

[CHROME_GUIDES_V2.md](CHROME_GUIDES_V2.md) accounts for all 208 entries in the requested Chrome collection. It separates applicable requirements from optional recipes, experimental APIs and absent features. This is an implementation and verification record, not a claim of universal guideline compliance.

Public-preview asset verification, screenshots, response-header checks and production-boundary confirmation are saved in `work/atlas-preview` after deployment. The hosting-only `_headers` file is checked through response headers, not treated as a downloadable public asset.

## Introduction follow-up

The next review requested a first page that explains the project's central purpose. A dedicated Introduction now opens on a fresh URL, with the existing charcoal theme, a short harmonization explanation, the real selected-region conversion example and a primary link to the calendar. The example retains its selection/overpass caveat and identifies Aqua as a reference, not ground truth. It uses the existing comparison-week calculation without changing numbers or scientific data.

Introduction is also reachable from navigation and the brand link. Existing shared calendar, evidence and rhythm URLs keep their original destinations. The three example actions open the full instrument comparison, the actual week evidence and held-out results. Returning to Introduction preserves the current country, date and spatial selection; its example names that context. The monthly calendar remains the default detail reached from a fresh introduction.

Follow-up verification: 180 web tests passed, including first arrival, example actions, saved selection and history restoration. Browser checks covered 320px reflow, evidence close/focus return and all three evidence destinations. Source data and pipeline files remain unchanged. Public preview checks for this follow-up are recorded under `work/intro-preview`; production is not a deployment target.

## Home and seven-country examples

The subsequent review renamed Introduction to Home and requested a neater first page with country selection. Home now presents one compact explanation, a calendar action and a single comparison panel with a native Country selector. It uses a house icon, a quieter heading hierarchy and grouped actions. The existing calibration numbers, comparison-week selection and scientific caveat are unchanged.

All seven catalogue countries are available. The selector uses the application's existing country-loading flow, so the example, evidence and onward calendar share the same country. While loading, the old country's numbers are hidden. Failed loads show an unavailable state and allow selecting another country. Home preserves current calendar filters when revisited; selecting a different country loads that country's full region record, as in the calendar selector.

Fresh URLs use `workspace=home`. Previously saved `workspace=introduction` URLs remain valid and canonicalize to Home. Existing calendar and research links keep their destinations.

Verification: 183 web tests passed, including delayed country loading, failure recovery, evidence/calendar consistency and legacy URL handling. Browser checks exercised every country and its weekly evidence at 320px, with no page overflow or wrapped numeric values. The desktop and full mobile page were visually reviewed. Release receipts for this update are under `work/home-preview`. No production deployment, Git push or merge is authorized by this review.
