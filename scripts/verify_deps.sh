#!/usr/bin/env bash
# Evident Technologies — dependency verification (Linux / CI)
set -euo pipefail

PY="${1:-python3.12}"
FAIL=0

echo ""
echo "=== Evident dep-verify (Linux / CI) ==="

# ── pip check ──────────────────────────────────────────────────────────────
echo ""
echo "» pip check"
$PY -m pip check || { echo "WARN: pip check failed"; FAIL=$((FAIL+1)); }

# ── ruff version ───────────────────────────────────────────────────────────
echo ""
echo "» ruff version"
$PY -m ruff version || { echo "WARN: ruff not installed"; FAIL=$((FAIL+1)); }

# ── pytest collect ─────────────────────────────────────────────────────────
echo ""
echo "» pytest --collect-only (quick)"
$PY -m pytest --collect-only -q 2>&1 | head -5 || { echo "WARN: pytest collect failed"; FAIL=$((FAIL+1)); }

# ── smoke import: fastapi ──────────────────────────────────────────────────
echo ""
echo "» smoke import: fastapi"
$PY -c "import fastapi; print(f'fastapi {fastapi.__version__}')" || { echo "WARN: smoke import failed"; FAIL=$((FAIL+1)); }

# ── summary ────────────────────────────────────────────────────────────────
echo ""
if [ "$FAIL" -gt 0 ]; then
    echo "FAIL — $FAIL check(s) failed."
    exit 1
else
    echo "ALL CHECKS PASSED"
    exit 0
fi
