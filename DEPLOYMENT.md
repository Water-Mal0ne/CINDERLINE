# FIRETRACE deployment

Public application: https://firetrace-bhaktapur-2026.pages.dev/

Deployment snapshot: https://8a4097e6.firetrace-bhaktapur-2026.pages.dev/

Published on November 14, 2026 using Cloudflare Pages Direct Upload, Wrangler 4.162.0, project `firetrace-bhaktapur-2026`, production branch `main`. The initial deployment uploaded 11 static files. No Worker functions, paid compute, database, or storage service was provisioned. The scientific pipeline runs locally; the published application serves its precomputed results.

## Verified release

All 11 public files, including the homepage, scripts, stylesheet, datasets and downloadable exports, returned HTTP 200 without authentication and matched the corresponding local build bytes by SHA-256. The local application had already passed the Python and client checks, data-payload comparisons and browser interaction checks. Supported real-data scope is Nepal and the United States, 2013–2024; the optional rhythm module remains disabled because its release gate is `insufficient_data`.

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

The earlier owner-private Sites preview is separate from this public Cloudflare application. Submission drafts now reference the public Pages URL; a public source repository still needs to be supplied.

Cloudflare documentation: [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/), [Pages limits](https://developers.cloudflare.com/pages/platform/limits/).
