#!/usr/bin/env bash
#
# Refresh the news dashboard manually, on this machine.
#
#   ./refresh.sh              fetch today's news, rebuild, commit, push (updates the live site)
#   ./refresh.sh --no-push    same, but stop after the commit — nothing leaves your machine
#   ./refresh.sh --build-only re-render index.html from existing snapshots; fetches nothing
#
# The scheduled cloud routine does the same thing every morning at 10am. Running this by hand is
# safe alongside it: today's snapshot is simply rebuilt rather than duplicated, and if the routine
# pushed first, the push below rebases onto it.

set -euo pipefail

cd "$(dirname "$0")"

PUSH=1
BUILD_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --no-push)    PUSH=0 ;;
    --build-only) BUILD_ONLY=1 ;;
    -h|--help)    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }

if [ "$BUILD_ONLY" -eq 0 ]; then
  command -v claude >/dev/null || {
    echo "claude CLI not found. Install it, or use --build-only to re-render existing snapshots." >&2
    exit 1
  }

  echo "==> Fetching today's news (this takes a few minutes — it reads every article in full)"
  claude -p "Use the news-dashboard agent to run today's dashboard refresh. Follow .claude/agents/news-dashboard.md exactly. Do not commit or push; this script handles that."
fi

echo "==> Rebuilding index.html"
python3 build.py

if [ "$BUILD_ONLY" -eq 1 ]; then
  exit 0
fi

if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "==> Nothing changed — no new items today. Not committing."
  exit 0
fi

TODAY=$(date -u +%F)
COUNTS=$(python3 - "$TODAY" <<'PY'
import json, sys, pathlib
p = pathlib.Path("data") / (sys.argv[1] + ".json")
if not p.exists():
    print("no snapshot for today"); raise SystemExit
s = json.loads(p.read_text())["sections"]
print("%d actuarial, %d data science"
      % (len(s.get("actuarial", [])), len(s.get("data_science", []))))
PY
)

git add -A
git commit -q -m "News: $TODAY — $COUNTS"
echo "==> Committed: News: $TODAY — $COUNTS"

if [ "$PUSH" -eq 0 ]; then
  echo "==> Skipping push (--no-push). The live site is unchanged until you push."
  exit 0
fi

echo "==> Pushing"
git push -q origin main 2>/dev/null || {
  echo "==> Remote moved ahead; rebasing and retrying"
  git pull --rebase -q origin main
  python3 build.py
  git add -A
  git diff --cached --quiet || git commit -q --amend --no-edit
  git push -q origin main
}

echo "==> Done. Live in ~1 min: https://sean-shepherd.github.io/actuarial-ds-news-dashboard/"
