#!/usr/bin/env python3
"""
Read a Backlog issues JSON (file path as arg, or stdin) and output
only open (non-completed) tickets as simplified JSON to stdout.

Usage:
    python3 filter_issues.py /path/to/issues.json
    cat issues.json | python3 filter_issues.py
"""

import json
import sys

COMPLETED_STATUSES = {"完了", "Closed", "Done", "closed", "done", "prodリリース済"}


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            issues = json.load(f)
    else:
        issues = json.load(sys.stdin)

    open_issues = []
    for issue in issues:
        status_name = issue.get("status", {}).get("name", "")
        if status_name in COMPLETED_STATUSES:
            continue
        open_issues.append({
            "issueKey": issue.get("issueKey", ""),
            "summary": issue.get("summary", ""),
            "status": status_name,
            "description": (issue.get("description") or "")[:300],
        })

    print(json.dumps(open_issues, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
