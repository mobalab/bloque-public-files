---
name: backlog-report
description: Fetch open Backlog tickets for target team members, classify each by the action needed, and post a summary to the project Slack channel with @ mentions. Run this when the PM wants a status sweep of outstanding tickets.
---

Generate a Backlog ticket status report for the target team members below and post it to Slack.

## Target members

| Name | Backlog assigneeId | Slack user ID |
|------|-------------------|---------------|
| 山田 | 1234567 | U12348D4A3H |

## Configuration

- **Backlog project ID**: 123456
- **Slack channel**: C123ABCDE45
- **Scripts directory**: `.claude/skills/backlog-report/scripts/`
- **Today's date**: use the current date

---

## Step 1 — Fetch open tickets

For each target member, call `mcp__bloque__backlog__get_issues` with:
- `assigneeId`: [<member's backlog assigneeId>]
- `projectId`: [123456]
- `count`: 100

Do **not** pass `statusId` — retrieve all statuses.

**Save the result** to a temp file, then filter it with the script:

```
# If the tool result was saved automatically to a file (result too large):
! python3 .claude/skills/backlog-report/scripts/filter_issues.py <path-to-saved-file>

# If the result is in context, write it to a temp file first:
# (use the Write tool to save to /tmp/backlog_issues.json, then:)
! python3 .claude/skills/backlog-report/scripts/filter_issues.py /tmp/backlog_issues.json
```

The script outputs a JSON array of open tickets. Use this list for Step 2.

---

## Step 2 — Read recent comments

For each open ticket from Step 1, call `mcp__bloque__backlog__get_issue_comments` with:
- `issueKey`: the ticket key (e.g. `FOO-123`)
- `count`: 3
- `order`: `"desc"`

Make all calls in parallel. If a ticket has no comments, proceed without them.

---

## Step 3 — Classify each ticket

Based on the ticket summary, description, and the most recent comments, assign each ticket to exactly one category:

1. **要返信** — A client or team member is waiting for a response from the assignee.
2. **担当者変更が必要（クライアントへ）** — The assignee has answered/completed their part, but the Backlog assignee has not been changed to the client who should act next.
3. **作業着手可能（開発者へアサイン）** — Ready to implement but needs to be (re)assigned to a developer.
4. **見積もり作成可能（開発者へアサイン）** — Needs an estimate; should be assigned to a developer.
5. **その他** — Genuinely in progress or does not fit the above.

---

## Step 4 — Build and post the Slack message

Write the classification results to `/tmp/classified.json` in this structure:

```json
{
  "member_name": "田中",
  "slack_user_id": "U1234D4A3H",
  "date": "<today's date>",
  "categories": {
    "要返信": [
      {"issueKey": "FOO-123", "summary": "チケット件名", "latest_comment": "最新コメントの要約（1行）"}
    ],
    "担当者変更が必要（クライアントへ）": [
      {"issueKey": "FOO-456", "summary": "チケット件名"}
    ],
    "作業着手可能（開発者へアサイン）": [],
    "見積もり作成可能（開発者へアサイン）": [],
    "その他": [
      {"issueKey": "FOO-789", "summary": "チケット件名", "note": "着手中"}
    ]
  }
}
```

Then generate the message:

```
! python3 .claude/skills/backlog-report/scripts/build_message.py /tmp/classified.json
```

Post the script's output to Slack by calling `mcp__bloque__slack__slack_send_message` with:
- `channel_id`: `C123ABCDE45`
- `message`: the script output
