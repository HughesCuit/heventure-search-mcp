#!/usr/bin/env python3
"""Kanban ↔ GitHub Issue bridge.

Commands:
    create   --kanban-id <id> --title "..." --body "..." [--labels "l1,l2"]
    close    --kanban-id <id> --issue-number <N> --summary "..."
    link     --kanban-id <id> --issue-number <N>
    list-stale [--days 7]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

REPO = "HughesCuit/heventure-search-mcp"
API = "https://api.github.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_token() -> str:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip()
    # fallback: environment
    return os.environ.get("GITHUB_TOKEN", "")


TOKEN = _load_token()
if not TOKEN:
    print(json.dumps({"error": "GITHUB_TOKEN not found in ~/.hermes/.env or env"}))
    sys.exit(1)

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "heventure-kanban-bridge",
}


def _request(method: str, path: str, data: dict | None = None) -> dict | list:
    """Make a GitHub API request and return parsed JSON."""
    url = f"{API}{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode() if exc.fp else ""
        print(json.dumps({
            "error": f"HTTP {exc.code}",
            "detail": err_body,
        }))
        sys.exit(1)


def _post_comment(issue_number: int, body: str) -> dict:
    return _request("POST", f"/repos/{REPO}/issues/{issue_number}/comments", {"body": body})


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace) -> None:
    """Create a GitHub Issue linked to a Kanban task."""
    body_text = f"**Kanban Task: {args.kanban_id}**\n\n{args.body}"
    payload: dict = {
        "title": args.title,
        "body": body_text,
    }
    if args.labels:
        payload["labels"] = [l.strip() for l in args.labels.split(",") if l.strip()]

    result = _request("POST", f"/repos/{REPO}/issues", payload)
    print(json.dumps({"issue_number": result["number"]}))


def cmd_close(args: argparse.Namespace) -> None:
    """Post a summary comment and close the Issue."""
    _post_comment(args.issue_number, f"### Kanban Task {args.kanban_id} — Completed\n\n{args.summary}")
    _request("PATCH", f"/repos/{REPO}/issues/{args.issue_number}", {"state": "closed"})
    print(json.dumps({"closed": True, "issue_number": args.issue_number}))


def cmd_link(args: argparse.Namespace) -> None:
    """Add a comment linking the Issue to a Kanban task."""
    _post_comment(args.issue_number, f"🔗 Linked to Kanban task `{args.kanban_id}`.")
    print(json.dumps({"linked": True, "issue_number": args.issue_number}))


def cmd_list_stale(args: argparse.Namespace) -> None:
    """List open auto-improve issues older than *days*."""
    since = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()
    path = (
        f"/repos/{REPO}/issues"
        f"?state=open&labels=auto-improve&since={since}&per_page=100"
    )
    issues = _request("GET", path)
    stale = [
        {
            "number": i["number"],
            "title": i["title"],
            "created_at": i["created_at"],
            "url": i["html_url"],
            "labels": [lb["name"] for lb in i.get("labels", [])],
        }
        for i in issues
        if i["created_at"] < since
    ]
    print(json.dumps(stale))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Kanban ↔ GitHub Issue bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create")
    p_create.add_argument("--kanban-id", required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--body", required=True)
    p_create.add_argument("--labels", default="")

    p_close = sub.add_parser("close")
    p_close.add_argument("--kanban-id", required=True)
    p_close.add_argument("--issue-number", type=int, required=True)
    p_close.add_argument("--summary", required=True)

    p_link = sub.add_parser("link")
    p_link.add_argument("--kanban-id", required=True)
    p_link.add_argument("--issue-number", type=int, required=True)

    p_stale = sub.add_parser("list-stale")
    p_stale.add_argument("--days", type=int, default=7)

    args = parser.parse_args()
    {"create": cmd_create, "close": cmd_close, "link": cmd_link, "list-stale": cmd_list_stale}[args.command](args)


if __name__ == "__main__":
    main()
