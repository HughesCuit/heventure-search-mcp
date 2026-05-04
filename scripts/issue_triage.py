#!/usr/bin/env python3
"""GitHub Issue triage: auto-filter, label, and classify incoming issues.

Three-layer filtering:
  Layer 1: Spam/malicious content detection (auto-close)
  Layer 2: Quality checks (needs-info label if incomplete)
  Layer 3: Ready for Kanban (add triaged label)

Usage:
    python3 issue_triage.py              # process all needs-triage issues
    python3 issue_triage.py --dry-run    # preview without changes
"""
import json
import os
import re
import sys
import urllib.request

REPO = "HughesCuit/heventure-search-mcp"
DRY_RUN = "--dry-run" in sys.argv

# ── Spam / malicious signals ────────────────────────────────────────────

SPAM_PATTERNS = [
    r"(?i)(buy|sell|discount|casino|viagra|crypto.?invest|earn.?money|free.?gift)",
    r"(?i)(phish|hack.?account|steal|credential|password.?dump)",
    r"https?://[^\s]+\.(ru|cn|tk|ml|ga|cf)/\S+",  # suspicious TLDs
    r"(?i)(telegram|whatsapp|wechat).{0,20}(group|channel|join)",
]
URL_PATTERN = re.compile(r"https?://\S+")
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
XSS_PATTERNS = [
    r"<script[^>]*>",
    r"javascript:",
    r"on\w+\s*=",
]


# ── Quality signals ─────────────────────────────────────────────────────

def check_spam(title: str, body: str) -> tuple[bool, str]:
    """Returns (is_spam, reason)."""
    text = f"{title} {body}"
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text):
            return True, f"Spam pattern: {pattern}"
    # XSS injection attempt
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text):
            return True, f"XSS pattern: {pattern}"
    # Too many URLs (link spam)
    urls = URL_PATTERN.findall(body)
    if len(urls) > 10:
        return True, f"Link spam: {len(urls)} URLs"
    return False, ""


def check_quality(title: str, body: str, labels: list[str]) -> tuple[bool, str]:
    """Returns (passes_quality, reason_if_not).
    
    Checks if the issue has enough information to be actionable.
    """
    # Title too short
    if len(title.strip()) < 5:
        return False, "Title too short (< 5 chars)"

    # Body too short (ignore code blocks)
    clean_body = CODE_BLOCK_PATTERN.sub("", body).strip()
    if len(clean_body) < 20:
        return False, "Description too short — please add more details"

    # Check if template was filled (bug report has specific sections)
    is_bug = any("bug" in l.lower() for l in labels)
    is_feature = any("enhancement" in l.lower() or "feature" in l.lower() for l in labels)

    if is_bug:
        # Bug reports should have reproduction steps
        has_repro = bool(re.search(
            r"(?i)(step|reproduc|to reproduce|how to|复现|步骤)",
            body
        ))
        if not has_repro:
            return False, "Bug report missing reproduction steps"

    if is_feature:
        # Feature requests should describe the problem
        has_problem = bool(re.search(
            r"(?i)(problem|frustrat|issue|want|need|希望|需求|问题)",
            body
        ))
        if not has_problem:
            return False, "Feature request missing problem statement"

    return True, ""


def classify_priority(title: str, body: str) -> str:
    """Suggest priority based on content signals."""
    text = f"{title} {body}".lower()

    # High priority signals
    high_signals = [
        r"(?i)(ssrf|xss|sql.?inject|security|vulnerability|漏洞|安全|crash|data.?loss)",
        r"(?i)(urgent|critical|blocking|阻塞|紧急|严重)",
    ]
    for pattern in high_signals:
        if re.search(pattern, text):
            return "high"

    # Low priority signals
    low_signals = [
        r"(?i)(typo|cosmetic|nice.?to.?have|minor|建议|优化|小问题)",
        r"(?i)(docs|documentation|readme|文档)",
    ]
    for pattern in low_signals:
        if re.search(pattern, text):
            return "low"

    return "medium"


# ── GitHub API ──────────────────────────────────────────────────────────

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
            "User-Agent": "issue-triage-bot",
            "Content-Type": "application/json",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def add_label(token: str, issue_number: int, label: str):
    """Add a label to an issue."""
    if DRY_RUN:
        print(f"    🔍 [DRY] Would add label '{label}' to #{issue_number}")
        return
    try:
        # Get current labels
        issue = github_api(f"/repos/{REPO}/issues/{issue_number}", token)
        current_labels = [l["name"] for l in issue.get("labels", [])]
        if label in current_labels:
            return
        new_labels = current_labels + [label]
        github_api(
            f"/repos/{REPO}/issues/{issue_number}",
            token, "PATCH", {"labels": new_labels}
        )
        print(f"    ✅ Added label '{label}' to #{issue_number}")
    except Exception as e:
        print(f"    ❌ Failed to add label to #{issue_number}: {e}")


def remove_label(token: str, issue_number: int, label: str):
    """Remove a label from an issue."""
    if DRY_RUN:
        print(f"    🔍 [DRY] Would remove label '{label}' from #{issue_number}")
        return
    try:
        github_api(
            f"/repos/{REPO}/issues/{issue_number}/labels/{label}",
            token, "DELETE"
        )
    except Exception:
        pass  # label might not exist


def close_issue(token: str, issue_number: int, reason: str):
    """Close an issue as spam."""
    if DRY_RUN:
        print(f"    🔍 [DRY] Would close #{issue_number} as spam: {reason}")
        return
    try:
        # Add spam label
        add_label(token, issue_number, "spam")
        # Close
        github_api(
            f"/repos/{REPO}/issues/{issue_number}",
            token, "PATCH", {"state": "closed", "state_reason": "not_planned"}
        )
        # Add comment
        github_api(
            f"/repos/{REPO}/issues/{issue_number}/comments",
            token, "POST", {
                "body": "🚫 This issue has been automatically closed as spam.\n\n"
                        f"**Reason:** {reason}\n\n"
                        "If this was a mistake, please open a new issue with proper details."
            }
        )
        print(f"    🚫 Closed #{issue_number} as spam: {reason}")
    except Exception as e:
        print(f"    ❌ Failed to close #{issue_number}: {e}")


def post_comment(token: str, issue_number: int, body: str):
    """Post a comment on an issue."""
    if DRY_RUN:
        print(f"    🔍 [DRY] Would comment on #{issue_number}")
        return
    try:
        github_api(
            f"/repos/{REPO}/issues/{issue_number}/comments",
            token, "POST", {"body": body}
        )
        print(f"    💬 Commented on #{issue_number}")
    except Exception as e:
        print(f"    ❌ Failed to comment on #{issue_number}: {e}")


# ── Main triage loop ───────────────────────────────────────────────────

def main():
    token = load_token()
    if not token:
        print("❌ GITHUB_TOKEN not found")
        sys.exit(1)

    print("=" * 60)
    print(f"🔍 Issue Triage {'(DRY RUN)' if DRY_RUN else ''}")
    print("=" * 60)

    # Fetch issues with needs-triage label
    try:
        issues = github_api(
            f"/repos/{REPO}/issues?state=open&labels=needs-triage&per_page=50",
            token
        )
        issues = [i for i in issues if "pull_request" not in i]
    except Exception as e:
        print(f"❌ Failed to fetch issues: {e}")
        sys.exit(1)

    if not issues:
        print("\n✅ No issues pending triage")
        return

    print(f"\n📋 Found {len(issues)} issues pending triage\n")

    stats = {"spam": 0, "needs_info": 0, "triaged": 0}

    for issue in issues:
        num = issue["number"]
        title = issue["title"]
        body = issue.get("body", "") or ""
        labels = [l["name"] for l in issue.get("labels", [])]

        print(f"#{num}: {title[:60]}")

        # Layer 1: Spam detection
        is_spam, spam_reason = check_spam(title, body)
        if is_spam:
            close_issue(token, num, spam_reason)
            stats["spam"] += 1
            continue

        # Layer 2: Quality check
        passes_quality, quality_reason = check_quality(title, body, labels)
        if not passes_quality:
            add_label(token, num, "needs-info")
            remove_label(token, num, "needs-triage")
            post_comment(
                token, num,
                f"👋 Thanks for opening this issue!\n\n"
                f"We need a bit more information to help:\n\n"
                f"**{quality_reason}**\n\n"
                f"Please update the issue description and remove the `needs-info` label "
                f"when you've added the requested details."
            )
            stats["needs_info"] += 1
            continue

        # Layer 3: Ready for Kanban
        priority = classify_priority(title, body)
        add_label(token, num, "triaged")
        add_label(token, num, f"priority:{priority}")
        remove_label(token, num, "needs-triage")
        stats["triaged"] += 1
        print(f"    ✅ Triaged (priority: {priority})")

    print(f"\n{'='*60}")
    print(f"📊 Triage complete:")
    print(f"   🚫 Spam closed: {stats['spam']}")
    print(f"   ❓ Needs info:  {stats['needs_info']}")
    print(f"   ✅ Triaged:     {stats['triaged']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
