#!/usr/bin/env python3
"""Read GitHub issues from stdin (curl output), print sorted by priority."""

import json
import sys

issues = json.load(sys.stdin)
priority_map = {"high": 0, "medium": 1, "low": 2}


def sort_key(i):
    labels = [lb["name"] for lb in i["labels"] if lb["name"].startswith("priority:")]
    if labels:
        return priority_map.get(labels[0].split(":")[1], 2)
    return 2


for i in sorted(issues, key=sort_key):
    labels = ", ".join(lb["name"] for lb in i["labels"])
    body_preview = (i["body"] or "")[:120].replace("\n", " ")
    print(f"#{i['number']} [{i['state']}] ({labels}) {i['title']}")
    print(f"    {body_preview}...")
    print()
