# Configure git to use repo hooks directory
Write-Host "Configuring git hooks..." -ForegroundColor Cyan

git config core.hooksPath .githooks

Write-Host "Done. Hooks path set to .githooks" -ForegroundColor Green
Write-Host "Run: python scripts/security/generate_key.py" -ForegroundColor Yellow
Write-Host "Optional check: python scripts/security/validate_encryption.py" -ForegroundColor Yellow
