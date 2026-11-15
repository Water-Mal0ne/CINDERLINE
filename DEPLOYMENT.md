# CINDERLINE deployment

## Planned deployment under the new name

**Planned public application:** https://cinderline-spaceapps.pages.dev/ (Cloudflare Pages project `cinderline-spaceapps`, production branch `main`). **Status: not yet deployed under this name.** Nothing in this repository deploys automatically.

The previous seven-country release was published on 14 November 2026 under the project's former name. It used Cloudflare Pages Direct Upload with Wrangler 4.162.0, from source commit `e71f2147ef08e77c14c23f43a946cff30c7d3c0b`. All 115 public assets (51,977,020 bytes) were verified by SHA-256 at 18:01 Nepal time; the record is `reports/deployment_verification.json`, which keeps the URL that was actually verified. That release predates the month calendar, area selection, 2025 extension, FRP panel and rename, so it is not the current product.

The current build is about 62.6 MiB in total, with every file under 25 MiB (largest `data/globe.json`, 12.40 MiB). Static hosting only: no Worker functions, paid compute, database or storage service.

## Publish an update

From the repository root:

```powershell
npm ci --prefix web
npm run build
# first deployment only: create the new Pages project
npx --yes wrangler@4.162.0 pages project create cinderline-spaceapps --production-branch main
npx --yes wrangler@4.162.0 pages deploy dist --project-name cinderline-spaceapps --branch main
python scripts/verify_deployment.py --url https://cinderline-spaceapps.pages.dev/ --dist dist
```

If authentication has expired, run the following and complete authorization locally:

```powershell
npx --yes wrangler@4.162.0 login --scopes account:read user:read pages:write
```

Do not put credentials in source files. Wrangler's local cache is ignored by Git. Direct Upload deploys only when the command runs; committing source does not automatically update this site. After the one-time `project create`, later deployments to the same project need no `--force` flag.

## GitHub and coordinated updates

Source repository: https://github.com/Water-Mal0ne/FIRETRACE (public; the repository keeps its original name). The public application remains accessible on Cloudflare. Repository visibility is independent of site visibility.

After committing a change, `powershell -File scripts/publish.ps1` runs web tests, Python regressions and the production build, pushes the committed revision through the `github` remote, then deploys it to the `cinderline-spaceapps` Cloudflare project (create it once first; see above) and verifies every public asset. Its latest verification report is saved under ignored `work/`. Authentication stays in the local GitHub/Cloudflare credential stores. A failed check prevents publication; a failed GitHub push prevents the subsequent deployment. This is an explicit publish command, not a background watcher or scheduled automation.

The earlier owner-private Sites preview is separate from this public Cloudflare application. Submission drafts now reference the public Pages URL. A judge-accessible source repository remains a team decision before submission.

Cloudflare documentation: [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/), [Pages limits](https://developers.cloudflare.com/pages/platform/limits/).
