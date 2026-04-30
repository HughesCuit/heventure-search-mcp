#!/usr/bin/env python3
"""
每周流程复盘 — 数据聚合脚本。

读取最近 7 天的 .structured.json 文件，输出统计摘要。
LLM 拿这份摘要做决策，不需要自己去读 markdown 报告。

用法: python3 weekly_digest.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

REVIEW_DIR = Path.home() / ".hermes/cron/output/e670c315a970"
IMPROVE_DIR = Path.home() / ".hermes/cron/output/bcf6ca804ccb"
CUTOFF = datetime.now() - timedelta(days=7)


def load_structured(directory: Path, log_type: str) -> list[dict]:
    """加载最近 7 天的 .structured.json"""
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


def analyze_reviews(reviews: list[dict]) -> dict:
    if not reviews:
        return {"total_runs": 0, "note": "最近7天无审查记录"}

    total_created = sum(len(r.get("issues_created", [])) for r in reviews)
    total_closed = sum(len(r.get("issues_closed", [])) for r in reviews)

    # 检测重复 issue 模式（标题关键词重叠）
    all_created_titles = []
    for r in reviews:
        for issue in r.get("issues_created", []):
            all_created_titles.append(issue.get("title", ""))

    # 简单关键词频率
    keywords = {}
    for title in all_created_titles:
        for word in title.split():
            if len(word) > 2:
                keywords[word] = keywords.get(word, 0) + 1
    repeated_keywords = {k: v for k, v in keywords.items() if v > 1}

    # CI 状态
    ci_green = sum(1 for r in reviews if r.get("ci_status") == "green")
    ci_red = sum(1 for r in reviews if r.get("ci_status") == "red")

    return {
        "total_runs": len(reviews),
        "total_issues_created": total_created,
        "total_issues_closed": total_closed,
        "net_change": total_created - total_closed,
        "ci_green_count": ci_green,
        "ci_red_count": ci_red,
        "created_titles": all_created_titles,
        "repeated_keywords": repeated_keywords,
    }


def analyze_improvements(improves: list[dict]) -> dict:
    if not improves:
        return {"total_runs": 0, "note": "最近7天无改进记录"}

    total_attempted = 0
    total_success = 0
    total_failed = 0
    total_skipped = 0
    all_attempted = []

    for r in improves:
        for item in r.get("issues_attempted", []):
            total_attempted += 1
            status = item.get("status", "")
            if status == "success":
                total_success += 1
            elif status == "failed":
                total_failed += 1
            elif status == "skipped":
                total_skipped += 1
            all_attempted.append(item)

        for item in r.get("issues_skipped", []):
            total_skipped += 1

    # CI 数据
    ci_conclusions = [r.get("ci_conclusion", "unknown") for r in improves]
    ci_pass = sum(1 for c in ci_conclusions if c == "success")
    ci_fail = sum(1 for c in ci_conclusions if c == "failure")
    total_retries = sum(r.get("ci_retries", 0) for r in improves)

    success_rate = (total_success / total_attempted * 100) if total_attempted > 0 else 0

    return {
        "total_runs": len(improves),
        "total_attempted": total_attempted,
        "total_success": total_success,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "success_rate": f"{success_rate:.0f}%",
        "ci_pass": ci_pass,
        "ci_fail": ci_fail,
        "total_ci_retries": total_retries,
        "attempted_details": all_attempted,
    }


def main():
    reviews = load_structured(REVIEW_DIR, "review")
    improves = load_structured(IMPROVE_DIR, "improve")

    review_stats = analyze_reviews(reviews)
    improve_stats = analyze_improvements(improves)

    output = {
        "period": f"{CUTOFF.strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}",
        "review": review_stats,
        "improvement": improve_stats,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
