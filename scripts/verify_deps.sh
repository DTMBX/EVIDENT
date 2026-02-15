#!/usr/bin/env bash
# Evident Technologies -- dependency verification (Linux / CI)
set -euo pipefail

PY="${1:-python3.12}"
FAIL=0

echo ""
echo "=== Evident dep-verify (Linux / CI) ==="

# -- pip check --------------------------------------------------------------
echo ""
echo "> pip check"
$PY -m pip check || { echo "WARN: pip check failed"; FAIL=$((FAIL+1)); }

# -- ruff version -----------------------------------------------------------
echo ""
echo "> ruff version"
$PY -m ruff version || { echo "WARN: ruff not installed"; FAIL=$((FAIL+1)); }

# -- pytest collect ---------------------------------------------------------
echo ""
echo "> pytest --collect-only (quick)"
$PY -m pytest --collect-only -q 2>&1 | head -5 || { echo "WARN: pytest collect failed"; FAIL=$((FAIL+1)); }

# -- Python version ---------------------------------------------------------
echo ""
echo "> Python version"
$PY -c "import sys; print(sys.version)" || { echo "WARN: Python version check failed"; FAIL=$((FAIL+1)); }

# -- smoke import: framework-agnostic (Flask or FastAPI) --------------------
echo ""
echo "> smoke import: web framework"
$PY - <<'PY' || { echo "WARN: framework smoke import failed"; FAIL=$((FAIL+1)); }
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
PY

# -- summary ----------------------------------------------------------------
echo ""
if [ "$FAIL" -gt 0 ]; then
    echo "FAIL -- $FAIL check(s) failed."
    exit 1
else
    echo "ALL CHECKS PASSED"
    exit 0
fi
