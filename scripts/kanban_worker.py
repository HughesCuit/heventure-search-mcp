#!/usr/bin/env python3
"""
Kanban Worker Poller — 运行在 PC 上，自动从 Kanban 领任务并用 Claude Code 执行。

用法:
    python3 kanban_worker.py                          # 默认配置
    python3 kanban_worker.py --server 10.0.0.109      # 指定服务器
    python3 kanban_worker.py --poll-interval 60       # 每60秒轮询一次
    python3 kanban_worker.py --assignee pc-eng        # 指定领取哪个 agent 的任务
    python3 kanban_worker.py --dry-run                # 只看不干

环境变量:
    KANBAN_SERVER    服务器 IP (默认 10.0.0.109)
    KANBAN_PORT      Dashboard 端口 (默认 9119)
    KANBAN_ASSIGNEE  领取任务的 agent 名 (默认 pc-eng)
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_SERVER = os.environ.get("KANBAN_SERVER", "10.0.0.109")
DEFAULT_PORT = int(os.environ.get("KANBAN_PORT", "9119"))
DEFAULT_ASSIGNEE = os.environ.get("KANBAN_ASSIGNEE", "pc-eng")
DEFAULT_POLL_INTERVAL = 120  # seconds

API_BASE = "http://{server}:{port}/api/plugins/kanban"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("kanban-worker")

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def api_get(server: str, port: int, path: str) -> dict:
    """GET request to Kanban API."""
    url = f"{API_BASE.format(server=server, port=port)}{path}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def api_patch(server: str, port: int, path: str, body: dict) -> dict:
    """PATCH request to Kanban API."""
    url = f"{API_BASE.format(server=server, port=port)}{path}"
    data = json.dumps(body).encode()
    req = Request(
        url,
        data=data,
        method="PATCH",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def api_post(server: str, port: int, path: str, body: dict) -> dict:
    """POST request to Kanban API."""
    url = f"{API_BASE.format(server=server, port=port)}{path}"
    data = json.dumps(body).encode()
    req = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def find_task(server: str, port: int, assignee: str) -> dict | None:
    """Find the highest-priority ready task for this assignee."""
    board = api_get(server, port, "/board")
    candidates = []
    for col in board["columns"]:
        if col["name"] in ("ready", "todo"):
            for task in col["tasks"]:
                if task.get("assignee") == assignee:
                    candidates.append(task)
    if not candidates:
        return None
    # Sort by priority ASC (1=high first), then created_at ASC
    candidates.sort(key=lambda t: (t.get("priority", 99), t.get("created_at", 0)))
    return candidates[0]


def claim_task(server: str, port: int, task_id: str) -> bool:
    """Mark task as running (claim it)."""
    try:
        api_patch(server, port, f"/tasks/{task_id}", {"status": "running"})
        return True
    except (HTTPError, URLError) as e:
        log.error(f"Failed to claim {task_id}: {e}")
        return False


def complete_task(
    server: str, port: int, task_id: str, summary: str, metadata: dict = None
):
    """Mark task as done."""
    body = {"status": "done", "summary": summary}
    if metadata:
        body["metadata"] = metadata
    api_patch(server, port, f"/tasks/{task_id}", body)


def block_task(server: str, port: int, task_id: str, reason: str):
    """Mark task as blocked."""
    api_patch(
        server,
        port,
        f"/tasks/{task_id}",
        {
            "status": "blocked",
            "block_reason": reason,
        },
    )


def add_comment(server: str, port: int, task_id: str, body: str):
    """Add a comment to a task."""
    api_post(
        server,
        port,
        f"/tasks/{task_id}/comments",
        {
            "body": body,
            "author": "pc-eng",
        },
    )


def get_task_detail(server: str, port: int, task_id: str) -> dict:
    """Get full task detail."""
    return api_get(server, port, f"/tasks/{task_id}")


# ---------------------------------------------------------------------------
# Execution via Claude Code CLI
# ---------------------------------------------------------------------------


def execute_with_claude_code(task_body: str, workspace: str = None) -> tuple[bool, str]:
    """
    Execute a task using Claude Code CLI.
    Returns (success, output).
    """
    # Build the prompt for Claude Code
    prompt = f"""You are a backend engineer executing a Kanban task.

TASK:
{task_body}

INSTRUCTIONS:
1. Read the task carefully
2. Make the necessary code changes
3. Run tests to verify
4. Summarize what you did

Work in the current directory. Be concise and focused."""

    cmd = ["claude", "-p", prompt, "--output-format", "text"]

    work_dir = workspace or os.getcwd()
    log.info(f"Executing in {work_dir}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max
            cwd=work_dir,
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\n[STDERR]\n{result.stderr}"
            return False, output
        return True, output
    except subprocess.TimeoutExpired:
        return False, "Task timed out after 600 seconds"
    except FileNotFoundError:
        return False, "claude CLI not found — install it first"
    except Exception as e:
        return False, f"Execution error: {e}"


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run_once(
    server: str, port: int, assignee: str, dry_run: bool = False, workspace: str = None
) -> bool:
    """Poll once: find a task, claim it, execute it, report result.
    Returns True if a task was processed."""
    task = find_task(server, port, assignee)
    if not task:
        return False

    task_id = task["id"]
    title = task["title"]
    body = task.get("body", "")

    log.info(f"📋 Found task: {task_id[:12]} — {title}")

    if dry_run:
        log.info(f"[DRY RUN] Would execute: {title}")
        return True

    # Claim
    if not claim_task(server, port, task_id):
        log.warning(f"Could not claim {task_id} — another worker may have taken it")
        return False

    log.info(f"🔒 Claimed {task_id[:12]}")
    add_comment(
        server,
        port,
        task_id,
        f"pc-eng worker claimed this task at {time.strftime('%Y-%m-%d %H:%M:%S')}",
    )

    # Execute
    full_body = f"{title}\n\n{body}" if body else title
    log.info("⚡ Executing with Claude Code...")
    success, output = execute_with_claude_code(full_body, workspace)

    # Truncate output for summary
    summary = output[:2000] if output else "(no output)"

    if success:
        complete_task(
            server,
            port,
            task_id,
            summary=summary,
            metadata={
                "worker": "pc-eng",
                "executor": "claude-code",
                "duration_estimate": "auto",
            },
        )
        log.info(f"✅ Completed {task_id[:12]}")
    else:
        block_task(server, port, task_id, reason=f"Execution failed: {summary[:200]}")
        log.warning(f"🚫 Blocked {task_id[:12]}: {summary[:100]}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Kanban Worker Poller for PC")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Kanban server IP")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Kanban dashboard port"
    )
    parser.add_argument(
        "--assignee", default=DEFAULT_ASSIGNEE, help="Assignee to poll for"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help="Seconds between polls",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Find tasks but don't execute"
    )
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    parser.add_argument(
        "--workspace", default=None, help="Working directory for task execution"
    )
    args = parser.parse_args()

    log.info(
        f"🚀 Kanban Worker starting — server={args.server}:{args.port} assignee={args.assignee}"
    )
    log.info(f"   poll_interval={args.poll_interval}s dry_run={args.dry_run}")

    # Test connection
    try:
        board = api_get(args.server, args.port, "/board")
        total = sum(len(c["tasks"]) for c in board["columns"])
        log.info(f"   Connected! Board has {total} tasks")
    except Exception as e:
        log.error(f"   Cannot connect to Kanban: {e}")
        sys.exit(1)

    while True:
        try:
            processed = run_once(
                args.server,
                args.port,
                args.assignee,
                dry_run=args.dry_run,
                workspace=args.workspace,
            )
            if args.once:
                if not processed:
                    log.info("No tasks available")
                break

            if not processed:
                log.debug("No tasks — sleeping...")

        except KeyboardInterrupt:
            log.info("👋 Stopping worker")
            break
        except Exception as e:
            log.error(f"Error in poll cycle: {e}")

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
