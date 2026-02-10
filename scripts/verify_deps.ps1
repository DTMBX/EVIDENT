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

# ── Python version ─────────────────────────────────────────────────────────
Write-Host "`n» Python version" -ForegroundColor Yellow
try {
    Invoke-Expression "$Python -c `"import sys; print(sys.version)`""
} catch {
    Write-Warning "Python version check failed"
    $failed++
}

# ── smoke import: framework-agnostic (Flask or FastAPI) ────────────────────
Write-Host "`n» smoke import: web framework" -ForegroundColor Yellow
try {
    $smokeScript = @'
import importlib

def ok(name: str) -> bool:
    try:
        importlib.import_module(name)
        print(f"{name}: ok")
        return True
    except Exception as e:
        print(f"{name}: not available ({e.__class__.__name__})")
        return False

flask_ok = ok("flask")
fastapi_ok = ok("fastapi")

if not (flask_ok or fastapi_ok):
    raise SystemExit("Neither flask nor fastapi is importable. Base requirements are not coherent.")
'@
    $tmpFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.py'
    $smokeScript | Set-Content -Path $tmpFile -Encoding UTF8
    try {
        Invoke-Expression "$Python `"$tmpFile`"" 2>&1 | Write-Host
        if ($LASTEXITCODE -ne 0) { throw "smoke import failed" }
    } finally {
        Remove-Item $tmpFile -ErrorAction SilentlyContinue
    }
} catch {
    Write-Warning "framework smoke import failed: $_"
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
