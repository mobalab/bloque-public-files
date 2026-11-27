#!/usr/bin/env python3
"""パース済みの freee 見積書ごとに、Notion タスク DB で何をするかを決める。

使い方:
    python3 plan_sync.py <quotes.json> <notion-rows.json> [--statuses <backlog-statuses.json>]

quotes.json            parse_quotes.py の出力
notion-rows.json       notion-query-data-sources の SQL 結果（{"results": [...]}）
                       または行オブジェクトの配列。少なくとも url, freee, "GitHub issue",
                       Name, Backlog, 見積書番号, 金額, 状態 の列が必要。
backlog-statuses.json  （任意）{"FOO-123": "処理中", ...} — 各 Backlog 課題の現在の
                       ステータス名。値は get_issue の結果そのもの
                       （{"status": {"name": ...}, ...}）でもよい。

照合（見積書ごと、古い順）:
  1. freee URL の見積書 ID が同じ行
  2. なければ、freee 列が空で GitHub issue が同じ行（見積書より先に登録されたタスク）。
     1つの行は最大1回しか紐づかないため、1つの issue に複数の見積書がある場合は
     最も古いものだけが紐づく。[失注]/[無効] の見積書はこのフォールバックを使わない。

見積書由来の列: 一致した行は *空の* 列だけを埋める。空でない値が freee と異なる場合は
"mismatches" として報告し、変更しない（ユーザーが意図的に編集している可能性があるため）。

状態 列: Backlog を正とし、常に Backlog 課題の現在のステータスに合わせる — 新規行、
一致した行、[失注]/[無効] の見積書の既存行（この場合は 状態 のみ変更）のいずれも対象。
使う Backlog キーは、行の Backlog 列が埋まっていればその値、なければ見積書のもの。

出力 JSON:
  {"create": [{"quotation_number", "properties"}],
   "update": [{"page_id", "page_url", "quotation_number", "matched_by", "properties"}],
   "unchanged": [quotation_number, ...],
   "skipped": [{"quotation_number", "reason", "row_url"?}],
   "status_changes": [{"quotation_number", "backlog", "page_url"?, "from", "to"}],
   "mismatches": [{"page_url", "quotation_number", "column", "notion", "freee"}],
   "warnings": [{"quotation_number", "warning"}]}
"""
import argparse
import json
import re
import sys

QUOTE_ID_RE = re.compile(r"/quotations/(\d+)")
STATUS_COL = "状態"


def load_json(path):
    data = json.load(open(path, encoding="utf-8"))
    # MCP のダンプは [{"type": "text", "text": "..."}] で包まれていることがある
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        data = json.loads(data[0]["text"])
    return data


def load_rows(path):
    data = load_json(path)
    return data["results"] if isinstance(data, dict) else data


def load_statuses(path):
    if not path:
        return {}
    out = {}
    for key, v in load_json(path).items():
        if isinstance(v, dict):
            v = (v.get("status") or {}).get("name")
        if v:
            out[key] = v
    return out


def quote_id_of(url):
    m = QUOTE_ID_RE.search(url or "")
    return int(m.group(1)) if m else None


def blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def as_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def desired_properties(q):
    props = {
        "Name": q["name"],
        "freee": q["freee_url"],
        "見積書番号": q["quotation_number"],
        "金額": q["amount"],
        "Backlog": q["backlog"],
        "GitHub issue": q["github_issue"],
    }
    return {k: v for k, v in props.items() if v is not None and v != ""}


def same(col, notion_val, freee_val):
    if col in ("金額", "GitHub issue"):
        return as_int(notion_val) == as_int(freee_val)
    return str(notion_val).strip() == str(freee_val).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quotes")
    ap.add_argument("rows")
    ap.add_argument("--statuses", help="Backlog 課題キー -> ステータス名 の JSON マップ")
    args = ap.parse_args()

    quotes = json.load(open(args.quotes, encoding="utf-8"))
    rows = load_rows(args.rows)
    statuses = load_statuses(args.statuses)

    by_quote = {}
    for r in rows:
        qid = quote_id_of(r.get("freee"))
        if qid:
            by_quote[qid] = r
    unquoted_by_issue = {}
    for r in rows:
        if blank(r.get("freee")) and as_int(r.get("GitHub issue")) is not None:
            unquoted_by_issue.setdefault(as_int(r["GitHub issue"]), []).append(r)
    for lst in unquoted_by_issue.values():
        lst.sort(key=lambda r: r.get("createdTime") or "")

    plan = {k: [] for k in ("create", "update", "unchanged", "skipped",
                            "status_changes", "mismatches", "warnings")}
    missing_status = set()

    def status_for(q, row):
        """行に設定すべき Backlog ステータス（不明なら None）。"""
        key = (row or {}).get("Backlog")
        key = key.strip() if not blank(key) else q["backlog"]
        if not key or args.statuses is None:  # キーがない、またはステータス同期が指定されていない
            return key, None
        if key not in statuses:
            missing_status.add(key)
            return key, None
        return key, statuses[key]

    def page_id(row):
        return row.get("id") or row["url"].rstrip("/").split("/")[-1]

    for q in quotes:
        num = q["quotation_number"]
        for w in q.get("warnings", []):
            plan["warnings"].append({"quotation_number": num, "warning": w})

        row, matched_by = by_quote.get(q["quote_id"]), "freee"
        if row is None and not q["skip_new"] and q["github_issue"] is not None:
            cands = unquoted_by_issue.get(q["github_issue"]) or []
            if cands:
                row, matched_by = cands.pop(0), "GitHub issue"

        key, status = status_for(q, row)
        status_change = None
        if status is not None and (row is None or str(row.get(STATUS_COL) or "").strip() != status):
            status_change = {"quotation_number": num, "backlog": key,
                             **({"page_url": row["url"]} if row else {}),
                             "from": (row or {}).get(STATUS_COL), "to": status}

        if q["skip_new"]:
            label = "/".join(q["labels"])
            if row and status_change:
                reason = f"[{label}] — 見積書の列は同期せず、状態のみ Backlog から更新"
            elif row:
                reason = f"[{label}] — 見積書の列は同期しない"
            else:
                reason = f"[{label}] — 行は作成しない"
            plan["skipped"].append({
                "quotation_number": num, "reason": reason,
                **({"row_url": row["url"]} if row else {}),
            })
            if row and status_change:
                plan["status_changes"].append(status_change)
                plan["update"].append({
                    "page_id": page_id(row), "page_url": row["url"], "quotation_number": num,
                    "matched_by": matched_by, "properties": {STATUS_COL: status},
                })
            continue

        want = desired_properties(q)
        if row is None:
            if status is not None:
                want[STATUS_COL] = status
                plan["status_changes"].append(status_change)
            plan["create"].append({"quotation_number": num, "properties": want})
            continue

        fill = {}
        for col, val in want.items():
            cur = row.get(col)
            if blank(cur):
                fill[col] = val
            elif not same(col, cur, val):
                plan["mismatches"].append({
                    "page_url": row["url"], "quotation_number": num,
                    "column": col, "notion": cur, "freee": val,
                })
        if status_change:
            fill[STATUS_COL] = status
            plan["status_changes"].append(status_change)
        if fill:
            plan["update"].append({
                "page_id": page_id(row), "page_url": row["url"], "quotation_number": num,
                "matched_by": matched_by, "properties": fill,
            })
        else:
            plan["unchanged"].append(num)

    for key in sorted(missing_status):
        plan["warnings"].append({"quotation_number": None,
                                 "warning": f"{key} の Backlog ステータスがないため、状態は変更していません"})

    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
