Param()
$ErrorActionPreference = 'Stop'
$repo = 'DTMBX/EVIDENT'
$branch = 'security/pin-vulns-2026-02-08'
$files = @(
    '_backend/requirements-full.txt',
    '_backend/requirements-full-stack.txt',
    '_backend/requirements-ai.txt',
    '_backend/requirements-production.txt',
    '_backend/requirements-local-dev.txt',
    '_backend/requirements.txt',
    '.github/workflows/security-pip-audit.yml'
)
Write-Host "Repo: $repo Branch: $branch"
# Get main commit sha
$mainSha = gh api repos/$repo/git/ref/heads/main --jq .object.sha
if (-not $mainSha) { Write-Host 'ERROR: could not get main sha'; exit 1 }
Write-Host "Main commit: $mainSha"
# Create branch ref
Write-Host "Creating branch refs/heads/$branch"
$createRef = gh api repos/$repo/git/refs -f ref="refs/heads/$branch" -f sha=$mainSha -X POST 2>&1
Write-Host $createRef
# For each file, upload via Contents API
foreach ($f in $files) {
    if (-not (Test-Path $f)) { Write-Host "ERROR: file not found: $f"; exit 2 }
    Write-Host "Uploading $f to branch $branch"
    $raw = Get-Content -Raw -Encoding UTF8 $f
    $b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($raw))
    $resp = gh api repos/$repo/contents/$f -X PUT -f message="chore: update $f (security pins)" -f content=$b64 -f branch=$branch 2>&1
    Write-Host $resp
}
# Create PR
Write-Host 'Creating PR'
$pr = gh api repos/$repo/pulls -f title='security: pin vulnerable deps + pip-audit' -f head=$branch -f base=main -f body='Pins pypdf, pdfminer.six, torch to secure versions and adds pip-audit workflow.' --jq .html_url 2>&1
Write-Host "PR result: $pr"
