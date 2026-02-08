#!/usr/bin/env bash
set -euo pipefail

WORKDIR=$(pwd)
OUTDIR=".github/merge"
mkdir -p "$OUTDIR"
MERGE_REPORT="$OUTDIR/merge-report.json"
CONFLICTS_DIR="$OUTDIR/conflicts"
mkdir -p "$CONFLICTS_DIR"

timestamp() { date -u +%Y%m%dT%H%M%SZ; }

if ! command -v git >/dev/null 2>&1; then
  echo "git not available"
  exit 1
fi

echo "Fetching all remotes"
git fetch --all --prune --tags

# Detect primary branch
if git show-ref --verify --quiet refs/remotes/origin/main; then
  TARGET_A=main
elif git show-ref --verify --quiet refs/remotes/origin/master; then
  TARGET_A=master
else
  TARGET_A=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin | head -n1 | sed 's|origin/||')
fi

BACKUP_BRANCH="backup/pre-consolidation-$(timestamp)"
echo "Creating backup branch $BACKUP_BRANCH"
git checkout -B "$BACKUP_BRANCH" "origin/$TARGET_A"
git push origin "$BACKUP_BRANCH"

TEMP_MERGE="consolidation/temp-merge-$(timestamp)"
echo "Creating temp merge branch $TEMP_MERGE based on origin/$TARGET_A"
git checkout -B "$TEMP_MERGE" "origin/$TARGET_A"

echo "Enumerating remote branches"
branches=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin | sed 's|origin/||' | sort -u)

echo '[' > "$MERGE_REPORT"
first=true

for b in $branches; do
  # skip HEAD and main/master and deployment branches and internal consolidation
  case "$b" in
    HEAD|$TARGET_A|g8-pages|gh-pages|consolidation/*|backup/*|origin) continue ;;
  esac

  echo "Processing branch: $b"
  git fetch origin "$b" || true

  if git merge --no-commit --no-ff "origin/$b"; then
    msg="Merge origin/$b into $TEMP_MERGE (dry-run)"
    git commit -m "$msg" || true
    echo_record="{\"branch\":\"$b\",\"status\":\"clean\",\"message\":\"$msg\"}"
  else
    echo "Conflict detected merging origin/$b"
    git merge --abort || true

    # create a conflict branch for manual resolution
    conflict_branch="consolidation/conflicts/${b//\//-}-$(timestamp)"
    git checkout -B "$conflict_branch" "origin/$TARGET_A"
    git merge "origin/$b" || true

    # record conflict files
    conflict_files=$(git diff --name-only --diff-filter=U || true)
    echo "Conflict files for $b: $conflict_files"

    # stage and commit WIP so branch can be pushed for manual work
    git add -A || true
    git commit -m "WIP: manual conflict resolution for origin/$b" || true
    git push -u origin "$conflict_branch" || true

    # open a PR for manual resolution (requires gh)
    if command -v gh >/dev/null 2>&1; then
      pr_title="WIP: Resolve conflicts merging origin/$b into $TARGET_A"
      pr_body="Automated consolidation detected conflicts merging origin/$b into $TARGET_A.\n\nConflict files:\n$conflict_files\n\nBranch: $conflict_branch"
      gh pr create --title "$pr_title" --body "$pr_body" --base "$TARGET_A" --head "$conflict_branch" || true
    fi

    # save conflict metadata
    meta_file="$CONFLICTS_DIR/${b//\//-}.json"
    cat > "$meta_file" <<EOF
{
  "branch": "$b",
  "conflict_branch": "$conflict_branch",
  "conflict_files": "$(echo "$conflict_files" | sed 's/"/\\"/g')",
  "timestamp": "$(timestamp)"
}
EOF

    echo_record="{\"branch\":\"$b\",\"status\":\"conflict\",\"conflict_branch\":\"$conflict_branch\"}"
  fi

  if [ "$first" = true ]; then
    echo -n "$echo_record" >> "$MERGE_REPORT"
    first=false
  else
    echo -n ",\n$echo_record" >> "$MERGE_REPORT"
  fi

done

echo ']' >> "$MERGE_REPORT"

echo "Pushing temp merge backup branch: $TEMP_MERGE"
git push -u origin "$TEMP_MERGE" || true

echo "Merge dry-run complete. Report: $MERGE_REPORT"
