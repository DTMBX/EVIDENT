#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoSlug = "DTMBX/Evident"
$prs = @(53, 55, 56, 58, 59, 60, 61)
$maxRuns = 30

function Invoke-Gh([string[]]$Args) {
    $out = & gh @Args 2>&1
    $code = $LASTEXITCODE
    [pscustomobject]@{ Out = $out; Code = $code }
}

Write-Host "Checking gh authentication..."
$r = Invoke-Gh @("auth", "status")
if ($r.Code -ne 0) {
    Write-Error "gh not authenticated. Run: gh auth login"
    exit 1
}

Write-Host "Enabling repo auto-merge (best effort)..."
$r = Invoke-Gh @("api", "-X", "PATCH", "repos/$repoSlug", "-f", "allow_auto_merge=true")
if ($r.Code -ne 0) {
    Write-Warning ("Could not enable repo auto-merge (may be org policy / permissions). Details: {0}" -f ($r.Out -join "`n"))
}

foreach ($n in $prs) {
    Write-Host "`n---"
    Write-Host "Processing PR #$n"

    # PR guardrails
    $prJson = Invoke-Gh @("pr", "view", $n, "--repo", $repoSlug, "--json", "headRefName,isDraft,state,reviewDecision", "--jq", ".")
    if ($prJson.Code -ne 0) { Write-Warning "Cannot view PR #$n. Skipping."; continue }

    $pr = $prJson.Out | ConvertFrom-Json
    if ($pr.state -ne "OPEN") { Write-Host "PR #$n is not open ($($pr.state)). Skipping."; continue }
    if ($pr.isDraft) { Write-Host "PR #$n is draft. Skipping."; continue }

    $branch = $pr.headRefName
    Write-Host "Branch: $branch"

    # List runs (recent only)
    $runsRes = Invoke-Gh @("run", "list", "--repo", $repoSlug, "--branch", $branch, "--limit", $maxRuns.ToString(), "--json", "id,name,status,conclusion,htmlUrl")
    if ($runsRes.Code -ne 0) {
        Write-Warning ("Failed to list runs for {0}: {1}" -f $branch, ($runsRes.Out -join "`n"))
        continue
    }

    $runs = @()
    if ($runsRes.Out) { $runs = $runsRes.Out | ConvertFrom-Json }

    foreach ($run in $runs) {
        if ($run.conclusion -in @("failure", "cancelled", "timed_out")) {
            Write-Host "Rerunning: $($run.name) -> $($run.htmlUrl)"
            $rr = Invoke-Gh @("run", "rerun", $run.id.ToString(), "--repo", $repoSlug)
            if ($rr.Code -ne 0) {
                Write-Warning ("Rerun failed for run {0}: {1}" -f $run.id, ($rr.Out -join "`n"))
            }
        }
    }

    Write-Host "Scheduling auto-merge for PR #$n..."
    $m = Invoke-Gh @("pr", "merge", $n, "--repo", $repoSlug, "--squash", "--delete-branch", "--auto", "--body", "Auto-merge when checks pass (Node20 CI)")
    if ($m.Code -ne 0) {
        Write-Warning ("Auto-merge scheduling failed for PR #{0}: {1}" -f $n, ($m.Out -join "`n"))
    }
    else {
        Write-Host "Auto-merge scheduled for PR #$n"
    }
}
