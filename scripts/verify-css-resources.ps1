# Verify CSS Resources and Injection
# Purpose: Check all stylesheet files exist, are accessible, and properly referenced

param(
    [switch]$Verbose,
    [switch]$Fix
)

$ErrorActionPreference = "Continue"
$repoRoot = "c:\web-dev\github-repos\Evident"
$timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "CSS Resources Verification Report" -ForegroundColor Cyan
Write-Host "Time: $timestamp" -ForegroundColor Gray
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Define expected CSS files
$cssFiles = @(
    @{ src = "src/assets/css/tokens.css"; dest = "_site/assets/css/tokens.css"; desc = "Tokens" },
    @{ src = "assets/css/core.css"; dest = "_site/assets/css/core.css"; desc = "Core" },
    @{ src = "src/assets/css/tailwind.css"; dest = "_site/assets/css/style.css"; desc = "Tailwind/Style" }
)

# 1. Verify source files exist
Write-Host "[1] Checking SOURCE CSS FILES" -ForegroundColor Yellow
Write-Host ""

$sourceOk = $true
foreach ($file in $cssFiles) {
    $srcPath = Join-Path $repoRoot $file.src
    if (Test-Path $srcPath) {
        $size = (Get-Item $srcPath).Length
        $lines = @(Get-Content $srcPath).Count
        Write-Host "✓ $($file.desc)" -ForegroundColor Green
        if ($Verbose) {
            Write-Host "  Path: $($file.src)" -ForegroundColor Gray
            Write-Host "  Size: $($size) bytes, Lines: $lines" -ForegroundColor Gray
        }
    } else {
        Write-Host "✗ $($file.desc) - NOT FOUND" -ForegroundColor Red
        Write-Host "  Expected: $srcPath" -ForegroundColor Red
        $sourceOk = $false
    }
}
Write-Host ""

# 2. Verify destination files exist
Write-Host "[2] Checking DESTINATION CSS FILES (_site)" -ForegroundColor Yellow
Write-Host ""

$destOk = $true
foreach ($file in $cssFiles) {
    $destPath = Join-Path $repoRoot $file.dest
    if (Test-Path $destPath) {
        $size = (Get-Item $destPath).Length
        $lines = @(Get-Content $destPath).Count
        Write-Host "✓ $($file.desc)" -ForegroundColor Green
        if ($Verbose) {
            Write-Host "  Path: $($file.dest)" -ForegroundColor Gray
            Write-Host "  Size: $($size) bytes, Lines: $lines" -ForegroundColor Gray
        }
    } else {
        Write-Host "✗ $($file.desc) - MISSING FROM _site" -ForegroundColor Red
        Write-Host "  Expected: $destPath" -ForegroundColor Red
        $destOk = $false
    }
}
Write-Host ""

# 3. Verify layout references
Write-Host "[3] Checking HTML LAYOUT REFERENCES" -ForegroundColor Yellow
Write-Host ""

$layoutPath = Join-Path $repoRoot "_layouts\default.html"
if (Test-Path $layoutPath) {
    $layoutContent = Get-Content $layoutPath -Raw
    
    $cssReferences = @(
        "tokens.css",
        "core.css",
        "style.css"
    )
    
    $refOk = $true
    foreach ($ref in $cssReferences) {
        if ($layoutContent -match [regex]::Escape($ref)) {
            Write-Host "✓ Reference to '$ref' found" -ForegroundColor Green
        } else {
            Write-Host "✗ Reference to '$ref' NOT found" -ForegroundColor Red
            $refOk = $false
        }
    }
} else {
    Write-Host "✗ Layout file not found: $layoutPath" -ForegroundColor Red
    $refOk = $false
}
Write-Host ""

# 4. Verify assets/css directory structure
Write-Host "[4] Checking ASSETS/CSS DIRECTORY STRUCTURE" -ForegroundColor Yellow
Write-Host ""

$assetsCssPath = Join-Path $repoRoot "assets\css"
if (Test-Path $assetsCssPath) {
    Write-Host "✓ Directory exists: assets/css" -ForegroundColor Green
    $cssCount = @(Get-ChildItem $assetsCssPath -Filter "*.css" -Recurse).Count
    Write-Host "  Found $cssCount .css files (including subdirectories)" -ForegroundColor Gray
    
    if ($Verbose) {
        Get-ChildItem $assetsCssPath -Filter "*.css" -Recurse | ForEach-Object {
            Write-Host "  - $($_.FullName.Replace($repoRoot, ''))" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "✗ Directory not found: assets/css" -ForegroundColor Red
}
Write-Host ""

# 5. Verify _site/assets/css directory structure
Write-Host "[5] Checking _site/ASSETS/CSS OUTPUT" -ForegroundColor Yellow
Write-Host ""

$siteAssetsCssPath = Join-Path $repoRoot "_site\assets\css"
if (Test-Path $siteAssetsCssPath) {
    Write-Host "✓ Directory exists: _site/assets/css" -ForegroundColor Green
    $files = @(Get-ChildItem $siteAssetsCssPath -Filter "*.css")
    Write-Host "  Found $($files.Count) .css files:" -ForegroundColor Gray
    foreach ($file in $files) {
        $size = $file.Length / 1KB
        Write-Host "  - $($file.Name) ($([math]::Round($size, 2)) KB)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ Directory not found: _site/assets/css" -ForegroundColor Red
}
Write-Host ""

# 6. Summary
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

if ($sourceOk -and $destOk -and $refOk) {
    Write-Host "✓ All CSS resources verified successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Status: READY" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Issues detected:" -ForegroundColor Red
    if (-not $sourceOk) { Write-Host "  - Source CSS files missing or incomplete" -ForegroundColor Red }
    if (-not $destOk) { Write-Host "  - Destination CSS files missing or incomplete" -ForegroundColor Red }
    if (-not $refOk) { Write-Host "  - HTML references incomplete" -ForegroundColor Red }
    Write-Host ""
    Write-Host "Status: NEEDS ATTENTION" -ForegroundColor Red
    exit 1
}
