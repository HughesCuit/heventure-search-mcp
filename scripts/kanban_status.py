#!/usr/bin/env python3
"""Kanban board status monitor — reads ~/.hermes/kanban.db directly."""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

DB_PATH = os.path.expanduser("~/.hermes/kanban.db")


def now_utc():
    return datetime.now(timezone.utc)


def ts_to_datetime(ts):
    """Convert integer unix timestamp to datetime (UTC)."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        return None


def minutes_since(ts):
    """Return minutes since a unix timestamp, or None."""
    dt = ts_to_datetime(ts)
    if dt is None:
        return None
    delta = now_utc() - dt
    return round(delta.total_seconds() / 60, 1)


def get_tasks(conn):
    """Fetch all tasks rows."""
    cur = conn.execute(
        "SELECT id, title, body, assignee, status, priority, "
        "created_by, created_at, started_at, completed_at, tenant, "
        "workspace_kind, workspace_path, result, current_run_id "
        "FROM tasks"
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_blocked_events(conn, task_ids):
    """For blocked tasks, find the most recent block-reason event."""
    if not task_ids:
        return {}
    placeholders = ",".join("?" * len(task_ids))
    cur = conn.execute(
        f"SELECT task_id, payload FROM task_events "
        f"WHERE task_id IN ({placeholders}) AND kind LIKE '%block%' "
        f"ORDER BY created_at DESC",
        task_ids,
    )
    result = {}
    for task_id, payload in cur.fetchall():
        if task_id not in result:
            try:
                data = json.loads(payload) if payload else {}
            except Exception:
                data = {}
            result[task_id] = data.get("reason") or data.get("message") or ""
    return result


def get_recent_completions(conn, tasks):
    """Get tasks that completed most recently (up to 5), with summary from runs."""
    done = [t for t in tasks if t["status"] == "done" and t.get("completed_at")]
    done.sort(key=lambda t: t["completed_at"] or 0, reverse=True)

    completions = []
    for t in done[:5]:
        summary = (t.get("result") or "")[:200]
        # Try to get summary from the latest run if available
        if not summary and t.get("current_run_id"):
            try:
                run = conn.execute(
                    "SELECT summary FROM task_runs WHERE id = ?", (t["current_run_id"],)
                ).fetchone()
                if run and run[0]:
                    summary = run[0][:200]
            except Exception:
                pass
        completions.append({
            "id": t["id"],
            "title": t["title"],
            "summary": summary,
        })
    return completions


def main():
    if not os.path.exists(DB_PATH):
        print(json.dumps({
            "error": f"Database not found: {DB_PATH}",
            "total": 0,
            "by_status": {},
            "running_tasks": [],
            "blocked_tasks": [],
            "recent_completions": [],
        }))
        return 0

    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row

        tasks = get_tasks(conn)

        # Count by status
        by_status = {}
        for t in tasks:
            s = t["status"] or "unknown"
            by_status[s] = by_status.get(s, 0) + 1

        total = len(tasks)

        # Running tasks
        running = []
        for t in tasks:
            if t["status"] == "running":
                running.append({
                    "id": t["id"],
                    "title": t["title"],
                    "assignee": t.get("assignee") or "",
                    "age_minutes": minutes_since(t.get("started_at") or t.get("created_at")),
                })

        # Blocked tasks
        blocked_task_ids = [t["id"] for t in tasks if t["status"] == "blocked"]
        block_reasons = get_blocked_events(conn, blocked_task_ids)
        blocked = []
        for t in tasks:
            if t["status"] == "blocked":
                blocked.append({
                    "id": t["id"],
                    "title": t["title"],
                    "reason": block_reasons.get(t["id"], ""),
                })

        recent = get_recent_completions(conn, tasks)

        conn.close()

        result = {
            "total": total,
            "by_status": by_status,
            "running_tasks": running,
            "blocked_tasks": blocked,
            "recent_completions": recent,
        }
        print(json.dumps(result, indent=2))
        return 0

    except Exception as e:
        print(json.dumps({"error": str(e), "total": 0, "by_status": {},
                          "running_tasks": [], "blocked_tasks": [],
                          "recent_completions": []}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
