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
