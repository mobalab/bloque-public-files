#!/usr/bin/env python3
"""freee の見積書一覧レスポンスを、Notion タスク DB 用の行データに正規化する。

使い方:
    python3 parse_quotes.py <freee-response.json> [more.json ...] [--since YYYY-MM-DD]

入力ファイルは以下のいずれかの形式:
  * freee_api_get のレスポンス:       {"quotations": [...]}
  * freee_api_bulk_get のレスポンス:  {"results": [{"data": {"quotations": [...]}}, ...]}
  * 見積書オブジェクトの配列そのもの
  * 上記いずれかをテキストとして含む MCP ツール結果のダンプ

標準出力に JSON 配列（古い順）を出力する:
    {
      "quote_id", "quotation_number", "quotation_date", "amount",  # 税抜
      "freee_url", "name", "backlog", "github_issue", "labels",
      "skip_new": bool,      # [失注]/[無効] なら true: 新しい行を作らない
      "warnings": [...]
    }

また、見つかった Backlog 課題キーの一覧を標準エラー出力に
"BACKLOG_KEYS: FOO-1 FOO-2 ..." の形で出力する（ステータスを取得する課題の一覧）。
"""
import argparse
import json
import re
import sys

PARTNER_ID = 12345678  # ACME Inc.（見積書を同期する取引先）
BACKLOG_PROJECT_KEY = "FOO"  # Backlog プロジェクトキー（FOO-123 の FOO）
FREEE_URL = "https://invoice.secure.freee.co.jp/reports/quotations/{id}"
SKIP_NEW_LABELS = {"失注", "無効"}  # 失注 / 無効

LABELS_RE = re.compile(r"^\s*((?:\[[^\]]*\]\s*)+)")
LABEL_RE = re.compile(r"\[([^\]]*)\]")
BACKLOG_RE = re.compile(rf"^({re.escape(BACKLOG_PROJECT_KEY)}-\d+)\s*")
ISSUE_RE = re.compile(r"#(\d+)\s*$")


def load_quotes(path):
    text = open(path, encoding="utf-8").read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        data = json.loads(text[start:])
    # MCP のダンプは [{"type": "text", "text": "..."}] で包まれていることがある
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        data = json.loads(data[0]["text"])
    if isinstance(data, list):
        return data
    if "quotations" in data:
        return data["quotations"]
    if "results" in data:
        out = []
        for r in data["results"]:
            out.extend((r.get("data") or {}).get("quotations", []))
        return out
    raise ValueError(f"{path}: 形式を認識できません")


def split_labels(s):
    m = LABELS_RE.match(s or "")
    if not m:
        return [], (s or "").strip()
    return LABEL_RE.findall(m.group(1)), s[m.end():].strip()


def parse(q):
    warnings = []
    subj_labels, subject = split_labels(q.get("subject") or "")
    memo_first = (q.get("memo") or "").splitlines()[0] if q.get("memo") else ""
    memo_labels, memo_rest = split_labels(memo_first)

    labels = list(dict.fromkeys(memo_labels + subj_labels))

    m = BACKLOG_RE.match(subject)
    backlog = m.group(1) if m else None
    name = subject[m.end():].strip() if m else subject
    if not backlog:
        mm = BACKLOG_RE.match(memo_rest)
        if mm:
            backlog = mm.group(1)
    if not backlog:
        warnings.append("件名/メモに Backlog 番号がありません")

    im = ISSUE_RE.search(memo_first)
    github_issue = int(im.group(1)) if im else None
    if github_issue is None:
        warnings.append("メモ1行目の末尾に GitHub issue 番号（#NNN）がありません")

    return {
        "quote_id": q["id"],
        "quotation_number": q.get("quotation_number"),
        "quotation_date": q.get("quotation_date"),
        "amount": q.get("amount_excluding_tax"),  # Notion の 金額 列は税抜金額
        "freee_url": FREEE_URL.format(id=q["id"]),
        "name": name,
        "backlog": backlog,
        "github_issue": github_issue,
        "labels": labels,
        "skip_new": bool(SKIP_NEW_LABELS & set(labels)),
        "warnings": warnings,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--since", help="YYYY-MM-DD 以降の日付の見積書のみ対象にする")
    args = ap.parse_args()

    seen = {}
    for f in args.files:
        for q in load_quotes(f):
            seen[q["id"]] = q
    rows = []
    for q in seen.values():
        if q.get("partner_id") not in (None, PARTNER_ID):
            continue
        if q.get("cancel_status") == "canceled":
            continue
        if args.since and (q.get("quotation_date") or "") < args.since:
            continue
        rows.append(parse(q))
    rows.sort(key=lambda r: (r["quotation_date"] or "", r["quotation_number"] or ""))
    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
    print()

    keys = sorted({r["backlog"] for r in rows if r["backlog"]},
                  key=lambda k: int(k.rsplit("-", 1)[1]))
    print("BACKLOG_KEYS: " + " ".join(keys), file=sys.stderr)


if __name__ == "__main__":
    main()
