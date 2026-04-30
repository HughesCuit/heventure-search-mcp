#!/usr/bin/env python3
"""
结构化运行记录写入工具（多项目版）。

用法:
  python3 write_run_log.py <project> <type> <json_string>

  project: 项目名称（如 heventure-search-mcp）
  type:    "review" | "improve"
  json_string: 完整的运行记录 JSON

日志存储位置: ~/.hermes/improve-loop/<project>/<type>/

审查 (review) JSON 格式:
{
  "date": "2026-04-30",
  "time": "17:02",
  "commits_today": 3,
  "commits_summary": "fix: ..., feat: ...",
  "issues_created": [{"number": 14, "title": "...", "priority": "high"}],
  "issues_closed": [{"number": 5, "reason": "..."}],
  "open_issues_total": 6,
  "ci_status": "green",
  "findings": ["..."]
}

改进 (improve) JSON 格式:
{
  "date": "2026-04-30",
  "time": "00:05",
  "issues_attempted": [{"number": 7, "title": "...", "status": "success", "commit": "abc1234", "review": "pass"}],
  "issues_skipped": [{"number": 8, "title": "...", "reason": "..."}],
  "push_status": "success",
  "ci_run_id": 25143464039,
  "ci_conclusion": "success",
  "ci_retries": 0
}
"""

import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path.home() / ".hermes" / "improve-loop"


def write_log(project: str, log_type: str, data: dict):
    if log_type not in ("review", "improve"):
        print(
            f"Unknown type: {log_type} (must be 'review' or 'improve')", file=sys.stderr
        )
        sys.exit(1)

    out_dir = BASE_DIR / project / log_type
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = out_dir / f"{ts}.structured.json"

    data["_schema_version"] = 1
    data["_type"] = log_type
    data["_project"] = project
    data["_generated_at"] = datetime.now().isoformat()

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Written: {out_file}")
    return out_file


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    log_type = sys.argv[2]
    json_str = sys.argv[3]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    write_log(project, log_type, data)
