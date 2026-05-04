#!/usr/bin/env python3
"""Bidirectional Kanban ↔ GitHub Issues sync.

Direction 1: Kanban done → close matching GitHub Issues
Direction 2: GitHub open Issues → create Kanban tasks (with idempotency)

Usage:
    python3 kanban_github_sync.py [--dry-run]
"""
import json
import os
import sqlite3
import subprocess
import sys
import urllib.request

REPO = "HughesCuit/heventure-search-mcp"
BRIDGE = os.path.expanduser("~/heventure-search-mcp/scripts/kanban_gh_bridge.py")
DB = os.path.expanduser("~/.hermes/kanban.db")
DRY_RUN = "--dry-run" in sys.argv


# ── Helpers ──────────────────────────────────────────────────────────────

def load_token() -> str:
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("GITHUB_TOKEN", "")


def github_api(path: str, token: str, method: str = "GET", data: dict | None = None) -> dict | list:
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "kanban-github-sync",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def run_cmd(cmd: list[str]) -> dict:
    """Run a command and return parsed JSON output."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        return {"raw": result.stdout.strip(), "error": result.stderr.strip()}


def map_priority(labels: list[str]) -> int:
    """GitHub label → Kanban priority int (lower = higher priority)."""
    for l in labels:
        if "high" in l:
            return 1
        if "low" in l:
            return 9
    return 5  # default medium


def has_kanban_task(issue: dict, kanban_tasks: list[tuple]) -> str | None:
    """Check if a GitHub Issue already has a Kanban task. Returns task_id or None."""
    body = issue.get("body", "") or ""
    issue_title = issue["title"].lower()

    for kid, ktitle, kstatus in kanban_tasks:
        # Most reliable: task ID in Issue body
        if kid in body:
            return kid
        # Title substring match (case-insensitive)
        if kstatus not in ("archived",):
            if ktitle.lower() in issue_title or issue_title in ktitle.lower():
                return kid
    return None


# ── Direction 1: Kanban done → Close GitHub Issues ──────────────────────

def sync_kanban_done_to_github(conn: sqlite3.Connection, token: str) -> dict:
    """Find done Kanban tasks and close their matching GitHub Issues."""
    done_tasks = conn.execute(
        "SELECT id, title FROM tasks WHERE status='done'"
    ).fetchall()

    # Fetch open Issues once (not per task)
    try:
        issues = github_api(
            f"/repos/{REPO}/issues?state=open&per_page=100", token
        )
        issues = [i for i in issues if "pull_request" not in i]
    except Exception as e:
        print(f"  ⚠️ Failed to fetch issues: {e}")
        return {"closed": [], "done_checked": len(done_tasks)}

    closed = []
    for task_id, task_title in done_tasks:

        for issue in issues:
            body = issue.get("body", "") or ""
            if task_id in body:
                if DRY_RUN:
                    print(f"  🔍 [DRY] Would close #{issue['number']} for {task_id}")
                else:
                    try:
                        run_cmd([
                            "python3", BRIDGE, "close",
                            "--kanban-id", task_id,
                            "--issue-number", str(issue["number"]),
                            "--summary", f"Completed: {task_title}",
                        ])
                        print(f"  ✅ Closed #{issue['number']} for {task_id}")
                    except Exception as e:
                        print(f"  ❌ Failed to close #{issue['number']}: {e}")
                closed.append(issue["number"])
                break  # one Issue per task

    return {"closed": closed, "done_checked": len(done_tasks)}


# ── Direction 2: GitHub open Issues → Create Kanban tasks ────────────────

def sync_github_to_kanban(conn: sqlite3.Connection, token: str) -> dict:
    """Create Kanban tasks for open GitHub Issues that don't have one."""
    # Fetch open Issues
    try:
        issues = github_api(f"/repos/{REPO}/issues?state=open&per_page=100", token)
        issues = [i for i in issues if "pull_request" not in i]
    except Exception as e:
        print(f"  ⚠️ Failed to fetch issues: {e}")
        return {"created": 0, "skipped": 0, "total_issues": 0}

    # Get existing Kanban tasks (all non-archived)
    existing = conn.execute(
        "SELECT id, title, status FROM tasks WHERE status != 'archived'"
    ).fetchall()

    created = []
    skipped = []

    for issue in issues:
        labels = [l["name"] for l in issue.get("labels", [])]

        # Only sync issues that passed triage
        if "triaged" not in labels:
            skipped.append(issue["number"])
            continue

        if has_kanban_task(issue, existing):
            skipped.append(issue["number"])
            continue

        num = issue["number"]
        title = issue["title"]
        priority = map_priority(labels)
        body_text = issue.get("body", "") or ""
        kanban_body = (
            f"GitHub Issue: #{num}\n"
            f"https://github.com/{REPO}/issues/{num}\n\n"
            f"{body_text[:500]}"
        )

        if DRY_RUN:
            print(f"  🔍 [DRY] Would create task for #{num}: {title[:50]}")
            created.append(num)
            continue

        try:
            result = run_cmd([
                "hermes", "kanban", "create", title,
                "--body", kanban_body,
                "--assignee", "backend-eng",
                "--priority", str(priority),
                "--idempotency-key", f"gh-issue-{num}",
                "--json",
            ])
            task_id = result.get("id", result.get("task_id", "unknown"))

            # Link back to GitHub Issue
            if task_id and task_id != "unknown":
                run_cmd([
                    "python3", BRIDGE, "link",
                    "--kanban-id", task_id,
                    "--issue-number", str(num),
                ])

            # Subscribe to Discord notifications
            run_cmd([
                "hermes", "kanban", "notify-subscribe", task_id,
                "--platform", "discord",
                "--chat-id", "1492843034168000673",
            ])

            print(f"  ✅ Created {task_id} for #{num}: {title[:50]}")
            created.append(num)
        except Exception as e:
            print(f"  ❌ Failed to create task for #{num}: {e}")

    return {"created": len(created), "skipped": len(skipped), "total_issues": len(issues)}


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    token = load_token()
    if not token:
        print("❌ GITHUB_TOKEN not found")
        sys.exit(1)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print("=" * 60)
    print(f"🔄 Kanban ↔ GitHub Sync {'(DRY RUN)' if DRY_RUN else ''}")
    print("=" * 60)

    # Direction 1
    print("\n📤 Direction 1: Kanban done → Close GitHub Issues")
    r1 = sync_kanban_done_to_github(conn, token)
    print(f"   Checked {r1['done_checked']} done tasks, closed {len(r1['closed'])} Issues")

    # Direction 2
    print("\n📥 Direction 2: GitHub open Issues → Create Kanban tasks")
    r2 = sync_github_to_kanban(conn, token)
    print(f"   {r2['total_issues']} open Issues: {r2['created']} tasks created, {r2['skipped']} already synced")

    conn.close()

    # Summary
    total_ops = len(r1["closed"]) + r2["created"]
    print(f"\n{'='*60}")
    print(f"✅ Sync complete — {total_ops} operations performed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
