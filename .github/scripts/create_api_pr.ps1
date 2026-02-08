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
$mainRef = gh api repos/$repo/git/ref/heads/main --jq .object.sha
if (-not $mainRef) { Write-Host 'ERROR: could not get main sha'; exit 1 }
$mainSha = $mainRef
Write-Host "Main commit: $mainSha"
# Get main tree sha
$mainTree = gh api repos/$repo/git/commits/$mainSha --jq .tree.sha
if (-not $mainTree) { Write-Host 'ERROR: could not get main tree'; exit 2 }
Write-Host "Main tree: $mainTree"
$blobMap = @{}
foreach ($f in $files) {
    if (-not (Test-Path $f)) { Write-Host "ERROR: file not found: $f"; exit 3 }
    Write-Host "Creating blob for $f"
    $content = Get-Content -Raw -Encoding UTF8 $f
    $blobSha = gh api repos/$repo/git/blobs -f content="$content" -f encoding='utf-8' --jq .sha
    if (-not $blobSha) { Write-Host "ERROR: blob create failed for $f"; exit 4 }
    $blobMap[$f] = $blobSha
}
# Build tree JSON
$treeArray = @()
foreach ($kv in $blobMap.GetEnumerator()) {
    $treeArray += @{ path = $kv.Key; mode = '100644'; type = 'blob'; sha = $kv.Value }
}
$treeJson = $treeArray | ConvertTo-Json -Depth 10
Write-Host 'Creating tree'
$newTreeSha = gh api repos/$repo/git/trees -f tree="$treeJson" -f base_tree=$mainTree --jq .sha
if (-not $newTreeSha) { Write-Host 'ERROR: create tree failed'; exit 5 }
Write-Host "New tree: $newTreeSha"
# Create commit
$commitMsg = 'security: pin vulnerable deps + add pip-audit workflow'
$commitSha = gh api repos/$repo/git/commits -f message="$commitMsg" -f tree=$newTreeSha -f parents="[$mainSha]" --jq .sha
if (-not $commitSha) { Write-Host 'ERROR: commit create failed'; exit 6 }
Write-Host "Commit created: $commitSha"
# Create branch
Write-Host "Creating ref refs/heads/$branch"
$refResp = gh api repos/$repo/git/refs -f ref="refs/heads/$branch" -f sha=$commitSha -X POST 2>&1
Write-Host $refResp
# Create PR
Write-Host 'Creating PR'
$pr = gh api repos/$repo/pulls -f title='security: pin vulnerable deps + pip-audit' -f head=$branch -f base=main -f body='Pins pypdf, pdfminer.six, torch to secure versions and adds pip-audit workflow.' --jq .html_url 2>&1
Write-Host "PR: $pr"
Write-Host 'Done'
