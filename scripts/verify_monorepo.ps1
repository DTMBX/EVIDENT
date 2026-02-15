#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Monorepo verification script.
.DESCRIPTION
    Validates npm workspaces, builds all apps, runs tests, and executes
    federation verification. Exit code 0 means all checks passed.
.EXAMPLE
    .\scripts\verify_monorepo.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot | Split-Path -Parent
Set-Location $root

$failed = $false

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  [PASS] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  [FAIL] $Message" -ForegroundColor Red
    $script:failed = $true
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor DarkGray
}

# Banner
Write-Host ""
Write-Host "  =============================================" -ForegroundColor Magenta
Write-Host "       Evident Monorepo Verification" -ForegroundColor Magenta
Write-Host "  =============================================" -ForegroundColor Magenta
Write-Host "  Root: $root"
Write-Host ""

# 1. Clean Install
Write-Section "1. Clean Install (npm ci)"
try {
    $ciOutput = & npm ci 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "npm ci completed successfully"
    } else {
        Write-Fail "npm ci failed"
        $ciOutput | Select-Object -Last 15 | ForEach-Object { Write-Host "     $_" }
    }
} catch {
    Write-Fail "npm ci threw exception: $_"
}

# 2. Build All Workspaces
Write-Section "2. Build All Workspaces"
try {
    $buildOutput = & npm run build:all 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "All workspace builds completed"
    } else {
        Write-Fail "Workspace build failed"
        $buildOutput | Select-Object -Last 20 | ForEach-Object { Write-Host "     $_" }
    }
} catch {
    Write-Fail "Build threw exception: $_"
}

# 3. Run Tests (if present)
Write-Section "3. Run Workspace Tests"
try {
    $testOutput = & npm run test:all 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "All workspace tests passed (or none configured)"
    } else {
        Write-Fail "Some tests failed"
        $testOutput | Select-Object -Last 15 | ForEach-Object { Write-Host "     $_" }
    }
} catch {
    Write-Fail "Tests threw exception: $_"
}

# 4. Federation Verification (if present)
Write-Section "4. Federation Verification"
$federationScript = Join-Path (Split-Path $root -Parent) "federation-verify.ps1"
if (Test-Path $federationScript) {
    Write-Info "Running: $federationScript"
    try {
        & $federationScript
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "federation-verify.ps1 passed"
        } else {
            Write-Fail "federation-verify.ps1 failed"
        }
    } catch {
        Write-Fail "federation-verify.ps1 threw exception: $_"
    }
} else {
    Write-Info "federation-verify.ps1 not found at $federationScript, skipping"
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($failed) {
    Write-Host "  Some checks FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  All checks PASSED" -ForegroundColor Green
    exit 0
}
