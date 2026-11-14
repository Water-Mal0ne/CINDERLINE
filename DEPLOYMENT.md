# FIRETRACE deployment

Public application: https://firetrace-bhaktapur-2026.pages.dev/

Deployment snapshot: https://8cc6976f.firetrace-bhaktapur-2026.pages.dev/

Published on November 14, 2026 using Cloudflare Pages Direct Upload, Wrangler 4.162.0, project `firetrace-bhaktapur-2026`, production branch `main`. The initial deployment uploaded 11 static files. No Worker functions, paid compute, database, or storage service was provisioned. The scientific pipeline runs locally; the published application serves its precomputed results.

## Verified release

The current release was built from source commit `841998b` and deployed on November 14, 2026. All **39 public assets, 39,811,714 bytes**, returned HTTP 200 without authentication and matched their local build bytes by SHA-256 at 11:33 UTC. Machine-readable evidence is in `reports/deployment_verification.json`.

The release covers Nepal and the United States, 2003–2024, with a 15,118-cell 3D Earth heatmap, lazy daily-cell loading, four improved exploration sections and shareable evidence links. The optional rhythm module remains disabled because its release gate is `insufficient_data`. The initial 11-file snapshot remains at https://8a4097e6.firetrace-bhaktapur-2026.pages.dev/ for historical reference.

Public browser verification restored a United States daily-cell link with the raw scale, 2020 date range and week beginning 2020-09-30. Switching to the national harmonized view and using the global Earth control rendered correctly; the console showed no errors. The coordinator also checked local desktop/mobile controls, picking, orbit, year changes, exact-week evidence and keyboard focus recovery. Graphics-context loss was covered by source review and renderer tests, not forced on the live browser.

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
