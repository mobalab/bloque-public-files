#!/usr/bin/env python3
"""
Build a Slack message string from classified Backlog ticket data.

Input JSON structure (file path as arg, or stdin):
{
  "member_name": "山田",
  "slack_user_id": "U01234D4A3H",
  "date": "2026-06-08",
  "categories": {
    "要返信": [
      {"issueKey": "FOO-123", "summary": "...", "latest_comment": "..."}
    ],
    "担当者変更が必要（クライアントへ）": [
      {"issueKey": "FOO-456", "summary": "..."}
    ],
    "作業着手可能（開発者へアサイン）": [...],
    "見積もり作成可能（開発者へアサイン）": [...],
    "その他": [
      {"issueKey": "FOO-789", "summary": "...", "note": "着手中"}
    ]
  }
}

Usage:
    python3 build_message.py /path/to/classified.json
    cat classified.json | python3 build_message.py
"""

import json
import sys

BASE_URL = "https://foo.backlog.com/view"
MAX_CHARS = 5000

CATEGORY_ORDER = [
    "要返信",
    "担当者変更が必要（クライアントへ）",
    "作業着手可能（開発者へアサイン）",
    "見積もり作成可能（開発者へアサイン）",
    "その他",
]

CATEGORY_LABELS = {
    "要返信": "■ 要返信 (Need to reply)",
    "担当者変更が必要（クライアントへ）": "■ 担当者変更が必要（クライアントへ）",
    "作業着手可能（開発者へアサイン）": "■ 作業着手可能（開発者へアサイン）",
    "見積もり作成可能（開発者へアサイン）": "■ 見積もり作成可能（開発者へアサイン）",
    "その他": "■ その他",
}


def format_ticket_line(ticket, category):
    key = ticket["issueKey"]
    summary = ticket["summary"]
    url = f"{BASE_URL}/{key}"
    line = f"- [{key}]({url}) {summary}"
    if category == "要返信" and ticket.get("latest_comment"):
        line += f"\n　└ {ticket['latest_comment']}"
    elif ticket.get("note"):
        line += f"（{ticket['note']}）"
    return line


def build_sections(categories, other_count_only=False):
    lines = []
    for cat_key in CATEGORY_ORDER:
        tickets = categories.get(cat_key, [])
        if not tickets and not (cat_key == "その他" and other_count_only):
            continue
        label = CATEGORY_LABELS[cat_key]
        lines.append(f"**{label}**")
        if cat_key == "その他" and other_count_only:
            lines.append(f"- （{other_count_only}件 — 文字数制限のため省略）")
        else:
            for ticket in tickets:
                lines.append(format_ticket_line(ticket, cat_key))
        lines.append("")
    return lines


def build_message(data):
    slack_user_id = data["slack_user_id"]
    date = data["date"]
    categories = data["categories"]

    header = [f"<@{slack_user_id}> の未完了チケット状況レポート（{date}）", ""]
    body_lines = build_sections(categories)
    message = "\n".join(header + body_lines).rstrip()

    if len(message) <= MAX_CHARS:
        return message

    # Truncate: replace その他 with count summary first
    other_tickets = categories.get("その他", [])
    if other_tickets:
        reduced_categories = {k: v for k, v in categories.items() if k != "その他"}
        body_lines = build_sections(reduced_categories, other_count_only=len(other_tickets))
        message = "\n".join(header + body_lines).rstrip()

    return message[:MAX_CHARS]


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    print(build_message(data))


if __name__ == "__main__":
    main()
