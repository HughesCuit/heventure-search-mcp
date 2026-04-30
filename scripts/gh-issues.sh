#!/bin/bash
# GitHub Issues helper for heventure-search-mcp auto-improvement
# Usage: gh-issues.sh list                       — list open auto-improve issues
#        gh-issues.sh create "title" "body" "labels"  — create issue
#        gh-issues.sh close N                    — close issue N
#        gh-issues.sh comment N "text"           — comment on issue N

REPO="HughesCuit/heventure-search-mcp"

# Read GITHUB_TOKEN from .env (bypasses terminal masking)
GITHUB_TOKEN=$(grep '^GITHUB_TOKEN=' ~/.hermes/.env | head -1 | cut -d= -f2- | tr -d '\n\r' | tr -d '"')
BASE="https://api.github.com/repos/$REPO"

if [ -z "$GITHUB_TOKEN" ]; then
  echo "[ERROR] GITHUB_TOKEN not found"
  exit 1
fi

AUTH="Authorization: Bearer $GITHUB_TOKEN"
ACCEPT="Accept: application/vnd.github+json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "$1" in
  list)
    curl -s -H "$AUTH" -H "$ACCEPT" "$BASE/issues?labels=auto-improve&state=open&per_page=50" \
      | python3 "$SCRIPT_DIR/gh_list.py"
    ;;
  create)
    TITLE="$2"
    BODY="$3"
    LABELS="$4"
    curl -s -X POST -H "$AUTH" -H "$ACCEPT" "$BASE/issues" \
      -d "{\"title\": $(echo "$TITLE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))"), \"body\": $(echo "$BODY" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))"), \"labels\": [\"auto-improve\", $(echo "$LABELS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")]}"
    ;;
  close)
    NUM="$2"
    curl -s -X PATCH -H "$AUTH" -H "$ACCEPT" "$BASE/issues/$NUM" \
      -d '{"state": "closed", "state_reason": "completed"}'
    ;;
  comment)
    NUM="$2"
    TEXT="$3"
    curl -s -X POST -H "$AUTH" -H "$ACCEPT" "$BASE/issues/$NUM/comments" \
      -d "{\"body\": $(echo "$TEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")}"
    ;;
  *)
    echo "Usage: $0 {list|create|close|comment} [args]"
    exit 1
    ;;
esac
