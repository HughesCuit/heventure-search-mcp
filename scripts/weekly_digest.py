#!/usr/bin/env python3
"""
每周流程复盘 — 多项目数据聚合脚本。

用法:
  python3 weekly_digest.py                     # 聚合所有项目
  python3 weekly_digest.py --project NAME      # 只聚合指定项目

读取 ~/.hermes/improve-loop/ 下各项目的 .structured.json，
输出统计摘要。LLM 拿这份摘要做决策。

输出格式: JSON（供 LLM 直接阅读）
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path.home() / ".hermes" / "improve-loop"
CUTOFF = datetime.now() - timedelta(days=7)


def find_all_projects() -> list[str]:
    """扫描所有项目目录"""
    if not BASE_DIR.exists():
        return []
    return [d.name for d in sorted(BASE_DIR.iterdir()) if d.is_dir()]


def load_structured(project: str, log_type: str) -> list[dict]:
    """加载最近 7 天的 .structured.json"""
    directory = BASE_DIR / project / log_type
    results = []
    if not directory.exists():
        return results
    for f in sorted(directory.glob("*.structured.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            ts = data.get("_generated_at", "")
            if ts:
                gen_time = datetime.fromisoformat(ts)
                if gen_time >= CUTOFF and data.get("_type") == log_type:
                    results.append(data)
        except (json.JSONDecodeError, ValueError):
            continue
    return results


def analyze_project(project: str) -> dict:
    """分析单个项目的数据"""
    reviews = load_structured(project, "review")
    improves = load_structured(project, "improve")

    # --- 审查统计 ---
    total_created = sum(len(r.get("issues_created", [])) for r in reviews)
    total_closed = sum(len(r.get("issues_closed", [])) for r in reviews)

    all_created_titles = []
    for r in reviews:
        for issue in r.get("issues_created", []):
            all_created_titles.append(issue.get("title", ""))

    # 关键词频率（检测重复模式）
    keywords = {}
    for title in all_created_titles:
        for word in title.split():
            if len(word) > 2:
                keywords[word] = keywords.get(word, 0) + 1
    repeated_keywords = {k: v for k, v in keywords.items() if v > 1}

    ci_green = sum(1 for r in reviews if r.get("ci_status") == "green")
    ci_red = sum(1 for r in reviews if r.get("ci_status") == "red")

    # --- 改进统计 ---
    total_attempted = 0
    total_success = 0
    total_failed = 0

    for r in improves:
        for item in r.get("issues_attempted", []):
            total_attempted += 1
            status = item.get("status", "")
            if status == "success":
                total_success += 1
            elif status == "failed":
                total_failed += 1

    ci_conclusions = [r.get("ci_conclusion", "unknown") for r in improves]
    ci_pass = sum(1 for c in ci_conclusions if c == "success")
    ci_fail = sum(1 for c in ci_conclusions if c == "failure")
    total_retries = sum(r.get("ci_retries", 0) for r in improves)

    success_rate = (total_success / total_attempted * 100) if total_attempted > 0 else 0

    return {
        "review_runs": len(reviews),
        "improve_runs": len(improves),
        "issues_created": total_created,
        "issues_closed": total_closed,
        "net_issue_change": total_created - total_closed,
        "success_rate": f"{success_rate:.0f}%",
        "ci_review_green": ci_green,
        "ci_review_red": ci_red,
        "ci_improve_pass": ci_pass,
        "ci_improve_fail": ci_fail,
        "ci_total_retries": total_retries,
        "repeated_keywords": repeated_keywords,
        "created_titles": all_created_titles,
    }


def main():
    # 解析参数
    target_project = None
    if "--project" in sys.argv:
        idx = sys.argv.index("--project")
        if idx + 1 < len(sys.argv):
            target_project = sys.argv[idx + 1]

    projects = [target_project] if target_project else find_all_projects()

    if not projects:
        print(
            json.dumps(
                {"note": "没有找到任何项目数据", "searched_path": str(BASE_DIR)},
                ensure_ascii=False,
            )
        )
        return

    all_stats = {}
    for project in projects:
        all_stats[project] = analyze_project(project)

    # 如果有多个项目，加一个汇总
    if len(projects) > 1:
        totals = {
            "total_projects": len(projects),
            "total_review_runs": sum(s["review_runs"] for s in all_stats.values()),
            "total_improve_runs": sum(s["improve_runs"] for s in all_stats.values()),
            "total_issues_created": sum(
                s["issues_created"] for s in all_stats.values()
            ),
            "total_issues_closed": sum(s["issues_closed"] for s in all_stats.values()),
        }
        output = {
            "period": f"{CUTOFF.strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}",
            "totals": totals,
            "projects": all_stats,
        }
    else:
        output = {
            "period": f"{CUTOFF.strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}",
            "project": projects[0],
            "stats": all_stats[projects[0]],
        }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
