# FIRETRACE deployment

Public application: https://firetrace-bhaktapur-2026.pages.dev/

Deployment snapshot: https://8a4097e6.firetrace-bhaktapur-2026.pages.dev/

Published on November 14, 2026 using Cloudflare Pages Direct Upload, Wrangler 4.162.0, project `firetrace-bhaktapur-2026`, production branch `main`. The initial deployment uploaded 11 static files. No Worker functions, paid compute, database, or storage service was provisioned. The scientific pipeline runs locally; the published application serves its precomputed results.

## Verified release

The initial 11-file release returned HTTP 200 without authentication and matched its local build bytes by SHA-256. The current source expands the real-data scope to Nepal and the United States, 2003–2024, with a 15,118-cell 3D Earth heatmap and lazy daily-cell loading. The optional rhythm module remains disabled because its release gate is `insufficient_data`. See the release verification record below for the current deployed revision.

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

After committing a change, `powershell -File scripts/publish.ps1` runs web tests, Python regressions and the production build, pushes the committed revision through the `github` remote, then deploys it to the existing Cloudflare project. Authentication stays in the local GitHub/Cloudflare credential stores. A failed check prevents publication; a failed GitHub push prevents the subsequent deployment. This is an explicit publish command, not a background watcher or scheduled automation.

The earlier owner-private Sites preview is separate from this public Cloudflare application. Submission drafts now reference the public Pages URL. A judge-accessible source repository remains a team decision before submission.

Cloudflare documentation: [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/), [Pages limits](https://developers.cloudflare.com/pages/platform/limits/).
