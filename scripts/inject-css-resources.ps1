# CSS Resources Injection & Validation Script
# Purpose: Ensure CSS resources are properly built, copied, and injectable into the site

param(
    [switch]$Inject,
    [switch]$Validate,
    [switch]$Rebuild = $true
)

$ErrorActionPreference = "Stop"
$repoRoot = "c:\web-dev\github-repos\Evident"
$timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "CSS Resources Injection & Validation" -ForegroundColor Cyan
Write-Host "Time: $timestamp" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Helper function to check file integrity
function Test-FileIntegrity {
    param(
        [string]$Path,
        [string]$Description
    )
    
    if (-not (Test-Path $Path)) {
        Write-Host "✗ $Description NOT FOUND" -ForegroundColor Red
        return $false
    }
    
    $file = Get-Item $Path
    if ($file.Length -eq 0) {
        Write-Host "✗ $Description is EMPTY" -ForegroundColor Red
        return $false
    }
    
    $content = Get-Content $Path -Raw
    if ($null -eq $content -or $content.Trim().Length -eq 0) {
        Write-Host "✗ $Description has no valid content" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✓ $Description" -ForegroundColor Green
    return $true
}

# Step 1: Validate current state
Write-Host "[STEP 1] VALIDATING CURRENT STATE" -ForegroundColor Yellow
Write-Host ""

$validationPassed = $true

# Check source files
Write-Host "Source files:" -ForegroundColor Gray
$validationPassed = (Test-FileIntegrity "$repoRoot\src\assets\css\tokens.css" "tokens.css (source)") -and $validationPassed
$validationPassed = (Test-FileIntegrity "$repoRoot\assets\css\core.css" "core.css (source)") -and $validationPassed
$validationPassed = (Test-FileIntegrity "$repoRoot\src\assets\css\tailwind.css" "tailwind.css (source)") -and $validationPassed

Write-Host ""
Write-Host "Destination files:" -ForegroundColor Gray
$validationPassed = (Test-FileIntegrity "$repoRoot\_site\assets\css\tokens.css" "tokens.css (_site)") -and $validationPassed
$validationPassed = (Test-FileIntegrity "$repoRoot\_site\assets\css\core.css" "core.css (_site)") -and $validationPassed
$validationPassed = (Test-FileIntegrity "$repoRoot\_site\assets\css\style.css" "style.css (_site)") -and $validationPassed

Write-Host ""

if (-not $validationPassed) {
    Write-Host "⚠ Validation errors detected. Proceeding with rebuild..." -ForegroundColor Yellow
    $Rebuild = $true
}

# Step 2: Rebuild CSS if needed or requested
if ($Rebuild) {
    Write-Host "[STEP 2] REBUILDING CSS ASSETS" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        Write-Host "Running: npm run build:css" -ForegroundColor Gray
        Push-Location $repoRoot
        
        # Run the build command
        $output = & npm run build:css 2>&1
        
        # Display output
        $output | ForEach-Object {
            if ($_ -match "Copied|ERROR|error") {
                if ($_ -match "ERROR|error") {
                    Write-Host "  $($_)" -ForegroundColor Red
                } else {
                    Write-Host "  $($_)" -ForegroundColor Green
                }
            }
        }
        
        Pop-Location
        Write-Host "✓ CSS build completed" -ForegroundColor Green
    } catch {
        Write-Host "✗ CSS build failed: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[STEP 2] SKIPPING BUILD (validation passed)" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: Verify injection in HTML
Write-Host "[STEP 3] VERIFYING CSS INJECTION IN HTML" -ForegroundColor Yellow
Write-Host ""

$layoutPath = "$repoRoot\_layouts\default.html"
$layoutContent = Get-Content $layoutPath -Raw

$cssInjectionTests = @(
    @{ pattern = "tokens\.css"; desc = "tokens.css injection" },
    @{ pattern = "core\.css"; desc = "core.css injection" },
    @{ pattern = "style\.css"; desc = "style.css injection" }
)

$injectionOk = $true
foreach ($test in $cssInjectionTests) {
    if ($layoutContent -match [regex]::Escape($test.pattern)) {
        Write-Host "✓ $($test.desc) found in layout" -ForegroundColor Green
    } else {
        Write-Host "✗ $($test.desc) NOT found in layout" -ForegroundColor Red
        $injectionOk = $false
    }
}

Write-Host ""

# Step 4: Calculate checksums for verification
Write-Host "[STEP 4] CALCULATING FILE CHECKSUMS" -ForegroundColor Yellow
Write-Host ""

$files = @(
    "$repoRoot\_site\assets\css\tokens.css",
    "$repoRoot\_site\assets\css\core.css",
    "$repoRoot\_site\assets\css\style.css"
)

$checksums = @{}
foreach ($file in $files) {
    if (Test-Path $file) {
        $hash = (Get-FileHash $file -Algorithm SHA256).Hash.Substring(0, 16)
        $name = (Split-Path $file -Leaf)
        $checksums[$name] = $hash
        Write-Host "$($name.PadRight(20)) : $hash..." -ForegroundColor Gray
    }
}

Write-Host ""

# Final Summary
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "INJECTION SUMMARY" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

if ($validationPassed -and $injectionOk) {
    Write-Host "✓ CSS resources successfully injected and ready for deployment" -ForegroundColor Green
    Write-Host ""
    Write-Host "Injectable CSS files:" -ForegroundColor Gray
    Write-Host "  1. tokens.css  - Design tokens (CSS variables)" -ForegroundColor Gray
    Write-Host "  2. core.css    - Core base styles & resets" -ForegroundColor Gray
    Write-Host "  3. style.css   - Component & page styles" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Status: READY FOR DEPLOYMENT ✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠ Some issues were detected during injection verification" -ForegroundColor Yellow
    Write-Host ""
    if (-not $validationPassed) { Write-Host "  - File validation had issues" -ForegroundColor Yellow }
    if (-not $injectionOk) { Write-Host "  - HTML injection references incomplete" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Status: REVIEW RECOMMENDED" -ForegroundColor Yellow
    exit 1
}
