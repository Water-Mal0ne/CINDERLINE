# FIRETRACE deployment

## Seven-country deployment

The `seven-country-v1` update is now deployed and verified. The user explicitly authorized this publication after the earlier stop-after-push checkpoint. Source remains in the private GitHub repository; the application is public.

Public application: https://firetrace-bhaktapur-2026.pages.dev/

Deployment snapshot: https://12b83479.firetrace-bhaktapur-2026.pages.dev/

Published on November 14, 2026 using Cloudflare Pages Direct Upload, Wrangler 4.162.0, project `firetrace-bhaktapur-2026`, production branch `main`. This release contains 115 static files. No Worker functions, paid compute, database, or storage service was provisioned. The scientific pipeline runs locally; the published application serves its precomputed results.

## Verified release

The current release was built from source commit `e71f2147ef08e77c14c23f43a946cff30c7d3c0b`. All **115 public assets, 51,977,020 bytes (49.57 MiB)**, returned HTTP 200 without authentication and matched their local build bytes by SHA-256 at 18:01 Nepal time on November 14, 2026. Machine-readable evidence is in `reports/deployment_verification.json`. The largest file is 12,999,487 bytes; both the 50 MiB site budget and 25 MiB individual-file limit pass.

The release covers Australia, Bangladesh, Brazil, Egypt, India, Nepal and the United States, 2003–2024. It includes 41,986 annual country-grid records, 84 detailed daily-cell series, deterministic border-cell rendering, four exploration sections and shareable evidence links. The optional rhythm module remains disabled because its release gate is `insufficient_data`. The prior two-country snapshot remains at https://8cc6976f.firetrace-bhaktapur-2026.pages.dev/ for historical reference.

Public browser verification exercised all seven countries: raw/harmonized switching and national peak-week evidence showed the correct country and scope. A United States cell link (`40.75:-123.50`, 2020, week beginning 2020-09-30) reopened with its dates and evidence intact. The card showed 134 VIIRS detections converted to 19.4 Aqua-equivalent activity, alongside 13 observed Aqua detections and the local-calibration limitation. The Earth rendered after year/region changes and viewport resizing. The evidence dialog fit a 390px viewport; final console checks returned no errors. Graphics-context loss was covered by source review and renderer tests, not forced on the live browser.

## Publish an update

From the repository root:

```powershell
npm ci --prefix web
npm run build
npx --yes wrangler@4.162.0 pages deploy dist --project-name firetrace-bhaktapur-2026 --branch main
```

If authentication has expired, run the following and complete authorization locally:

```powershell
npx --yes wrangler@4.162.0 login --scopes account:read user:read pages:write
```

Do not put credentials in source files. Wrangler's local cache is ignored by Git. Direct Upload deploys only when the command runs; committing source does not automatically update this site. The existing Pages project requires no `--force` flag.

## GitHub and coordinated updates

Source repository: https://github.com/Water-Mal0ne/FIRETRACE (private). The public application remains accessible on Cloudflare. Repository visibility is independent of site visibility.

After committing a change, `powershell -File scripts/publish.ps1` runs web tests, Python regressions and the production build, pushes the committed revision through the `github` remote, then deploys it to the existing Cloudflare project and verifies every public asset. Its latest verification report is saved under ignored `work/`. Authentication stays in the local GitHub/Cloudflare credential stores. A failed check prevents publication; a failed GitHub push prevents the subsequent deployment. This is an explicit publish command, not a background watcher or scheduled automation.

The earlier owner-private Sites preview is separate from this public Cloudflare application. Submission drafts now reference the public Pages URL. A judge-accessible source repository remains a team decision before submission.

Cloudflare documentation: [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/), [Pages limits](https://developers.cloudflare.com/pages/platform/limits/).
