#!/usr/bin/env python3
"""
结构化运行记录写入工具。

用法：
  python3 write_run_log.py <type> <json_string>

  type: "review" | "improve"
  json_string: 完整的运行记录 JSON

审查 (review) JSON 格式：
{
  "date": "2026-04-30",
  "time": "17:02",
  "commits_today": 3,
  "commits_summary": "fix: target-version, feat: SKILL.md",
  "issues_created": [
    {"number": 14, "title": "...", "priority": "high"}
  ],
  "issues_closed": [
    {"number": 5, "reason": "已修复于 aeebba0"}
  ],
  "open_issues_total": 6,
  "ci_status": "green",
  "findings": ["server.py __version__ 不同步"]
}

改进 (improve) JSON 格式：
{
  "date": "2026-04-30",
  "time": "00:05",
  "issues_attempted": [
    {"number": 7, "title": "...", "status": "success", "commit": "f4d1816", "review": "pass"}
  ],
  "issues_skipped": [],
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

# cron job IDs → output directory
REVIEW_DIR = Path.home() / ".hermes/cron/output/e670c315a970"
IMPROVE_DIR = Path.home() / ".hermes/cron/output/bcf6ca804ccb"


def write_log(log_type: str, data: dict):
    if log_type == "review":
        out_dir = REVIEW_DIR
    elif log_type == "improve":
        out_dir = IMPROVE_DIR
    else:
        print(f"Unknown type: {log_type}", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名（与 cron 自动保存的 .md 同名）
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = out_dir / f"{ts}.structured.json"

    data["_schema_version"] = 1
    data["_type"] = log_type
    data["_generated_at"] = datetime.now().isoformat()

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Written: {out_file}")
    return out_file


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    log_type = sys.argv[1]
    json_str = sys.argv[2]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    write_log(log_type, data)
