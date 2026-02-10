<#
.SYNOPSIS
    Verify Evident Technologies Python dependency stack.
.DESCRIPTION
    Runs pip check, ruff version, pytest discovery, and a quick smoke-import
    against the core framework module.  Exit 0 = healthy, Exit 1 = problem.
#>
param(
    [string]$Python = "py -3.12"
)

$ErrorActionPreference = "Stop"
$failed = 0

Write-Host "`n=== Evident dep-verify (Windows) ===" -ForegroundColor Cyan

# ── pip check ──────────────────────────────────────────────────────────────
Write-Host "`n» pip check" -ForegroundColor Yellow
try {
    Invoke-Expression "$Python -m pip check" | Out-String | Write-Host
} catch {
    Write-Warning "pip check failed: $_"
    $failed++
}

# ── ruff version ───────────────────────────────────────────────────────────
Write-Host "`n» ruff version" -ForegroundColor Yellow
try {
    Invoke-Expression "$Python -m ruff version" | Out-String | Write-Host
} catch {
    Write-Warning "ruff not installed"
    $failed++
}

# ── pytest collect ─────────────────────────────────────────────────────────
Write-Host "`n» pytest --collect-only (quick)" -ForegroundColor Yellow
try {
    Invoke-Expression "$Python -m pytest --collect-only -q 2>&1" | Select-Object -First 5 | Write-Host
} catch {
    Write-Warning "pytest collect failed"
    $failed++
}

# ── smoke import: fastapi ──────────────────────────────────────────────────
Write-Host "`n» smoke import: fastapi" -ForegroundColor Yellow
try {
    Invoke-Expression "$Python -c `"import fastapi; print(f'fastapi {fastapi.__version__}')`""
} catch {
    Write-Warning "smoke import failed"
    $failed++
}

# ── summary ────────────────────────────────────────────────────────────────
Write-Host ""
if ($failed -gt 0) {
    Write-Host "FAIL — $failed check(s) failed." -ForegroundColor Red
    exit 1
} else {
    Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
    exit 0
}
