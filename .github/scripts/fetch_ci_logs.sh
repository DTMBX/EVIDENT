#!/usr/bin/env bash
set -euo pipefail

CI_DIR=".github/ci"
LOG_DIR="$CI_DIR/logs"
mkdir -p "$LOG_DIR"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found; skipping CI log fetch"
  exit 0
fi

echo "Fetching recent workflow runs (limit 50)"
gh run list --limit 50 --json databaseId,headBranch,status,conclusion,createdAt > "$CI_DIR/ci-runs.json" || echo "gh run list failed"

if [ -s "$CI_DIR/ci-runs.json" ]; then
  ids=$(jq -r '.[].databaseId' "$CI_DIR/ci-runs.json" 2>/dev/null || true)
  for id in $ids; do
    echo "Downloading logs for run $id"
    gh run view "$id" --log > "$LOG_DIR/${id}.log" || echo "Failed to fetch logs for $id"
  done
else
  echo "No CI runs json created or empty"
fi

echo "CI logs saved to $LOG_DIR"
