#!/usr/bin/env bash
set -euo pipefail

OUTDIR=".github/merge"
CI_DIR=".github/ci"
REPORT_FILE=".github/consolidation-report.json"
mkdir -p "$(dirname "$REPORT_FILE")"

timestamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

echo "Generating consolidation report"

cat > "$REPORT_FILE" <<EOF
{
  "generated_at": "$(timestamp)",
  "merge_report": $(jq -c . "$OUTDIR/merge-report.json" 2>/dev/null || echo '[]'),
  "conflicts": [
    $(jq -c '.[]' "$OUTDIR/conflicts"/*.json 2>/dev/null | paste -sd ',' - || echo '')
  ],
  "ci_runs": $(jq -c . "$CI_DIR/ci-runs.json" 2>/dev/null || echo '[]')
}
EOF

echo "Report written to $REPORT_FILE"
