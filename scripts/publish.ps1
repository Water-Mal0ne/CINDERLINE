param([string]$Remote = 'github', [string]$Branch = 'main')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    git remote get-url $Remote | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Configure the '$Remote' GitHub remote before publishing." }
    $changes = git status --porcelain
    if ($changes) { throw 'Commit the intended source changes before publishing so GitHub and Cloudflare identify the same revision.' }
    npm --prefix web test
    if ($LASTEXITCODE -ne 0) { throw 'Web verification failed.' }
    $projectPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Prepare the documented Python environment before publishing.' }
    & $projectPython -m pytest tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Scientific regression checks failed.' }
    node scripts/build.mjs
    if ($LASTEXITCODE -ne 0) { throw 'Production build failed.' }
    git push $Remote $Branch
    if ($LASTEXITCODE -ne 0) { throw 'GitHub upload failed; Cloudflare was not updated.' }
    npx --yes wrangler@4.162.0 pages deploy dist --project-name cinderline-spaceapps --branch $Branch
    if ($LASTEXITCODE -ne 0) { throw 'GitHub was updated, but Cloudflare deployment failed. Re-run after resolving the reported deployment error.' }
    & $projectPython scripts/verify_deployment.py --report work/latest_deployment_verification.json
    if ($LASTEXITCODE -ne 0) { throw 'Cloudflare accepted the deployment, but public asset verification failed. Inspect the verification report before calling the release complete.' }
    Write-Output 'Validated source pushed to GitHub and deployed to Cloudflare Pages.'
} finally {
    Pop-Location
}
