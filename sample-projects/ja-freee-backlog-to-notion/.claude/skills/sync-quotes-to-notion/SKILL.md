---
name: sync-quotes-to-notion
description: >
  ACME Inc. 向けの freee の見積書を Notion の「Client tasks」データベースに同期し、各行の「状態」を
  紐づく Backlog 課題のステータスに揃える。新しい見積書ごとに行を追加し、既存行（見積書より先に GitHub issue
  で登録された行を含む）の空欄の列（Name, 金額, 見積書番号, freee, Backlog, GitHub issue）を補完し、
  「状態」を Backlog 課題の現在のステータスに更新する。タスク一覧、Notion のタスク DB、売上・作業項目シートを
  freee や Backlog から更新・同期してほしいと頼まれたときは必ず使うこと — 例:「Notionのタスク一覧を更新して」
  「見積書をNotionに反映」「Backlogのステータスを Notion に反映して」「sync quotes to Notion」—
  freee と明示されていなくても使う。
---

# sync-quotes-to-notion

Notion の「Client tasks」データベースを、freee の見積書および Backlog の課題と同期させます。

- **freee** は見積書由来の列（Name, 金額, 見積書番号, freee, Backlog, GitHub issue）の正となるデータです。
- **Backlog** は「状態」列の正となるデータです。Notion の「状態」の選択肢は Backlog プロジェクトのステータス名
  （例: 未対応 / 処理中 / 処理済み / 完了）と完全に一致している前提なので、ステータス名をそのままコピーします。
- それ以外の Notion の列（納品予定日, 備考）は手動で管理しているため、絶対に変更しないでください。

## 設定

| 項目 | 値 |
|---|---|
| freee company_id（Example Corp.） | `1234567` |
| freee partner_id（ACME Inc.） | `12345678` |
| Backlog プロジェクトキー | `FOO`（課題キーは `FOO-123` のような形式） |
| Notion データソース | `collection://12345678-90ab-cdef-1234-567890abcdef` |
| Notion ページ | https://app.notion.com/p/1234567890abcdef1234567890abcdef |
| スクリプト | `.claude/skills/sync-quotes-to-notion/scripts/`（このプロジェクトディレクトリから実行） |
| 作業用ディレクトリ | `/tmp/sync-quotes-to-notion/`（環境にセッション用の scratchpad がある場合はそちらを使い、以下のパスも読み替える） |

`scripts/parse_quotes.py` 冒頭の `PARTNER_ID` と `BACKLOG_PROJECT_KEY` は上の表と一致させてください。

## 列の対応

| Notion の列 | 種類 | 取得元 |
|---|---|---|
| Name | タイトル | freee の件名から、先頭の `[概算]` などのラベルと Backlog キー（`FOO-1689 `）を除いたもの |
| 金額 | 数値 | `amount_excluding_tax`（税抜）— `total_amount` ではない |
| 見積書番号 | テキスト | `quotation_number` |
| freee | URL | `https://invoice.secure.freee.co.jp/reports/quotations/{id}` |
| Backlog | テキスト | 件名の先頭にある Backlog キー（なければメモから） |
| GitHub issue | 数値 | メモ1行目の末尾にある `#NNN` |
| 状態 | セレクト/ステータス | 行に紐づく Backlog 課題の現在のステータス名 — **常に上書き** |
| GitHub URL / Backlog URL | 数式 | Notion が計算 — 書き込まない |
| 納品予定日 / 備考 | — | 手動管理 — 書き込まない |

これらはすべてスクリプトに実装されているので、自分でパースする必要はほとんどありません。

ラベルに関係なくすべての見積書を同期します — ラベルなし（交渉中）、`[概算]`、`[受注済み]`、`[パターン1]` など。
DB は見込みの作業も管理しているためです。例外は `[失注]` と `[無効]` のみです（手順5を参照）。これらは行を作成せず、
見積書由来の列も変更しませんが、既存の行がある場合は「状態」だけ Backlog から同期します。

以下の MCP ツール（`mcp__bloque__freee__*`, `mcp__bloque__backlog__*`, `mcp__bloque__notion__*`）は遅延読み込み
されている場合があります。最初に呼び出す前に ToolSearch（`select:<name>,<name>`）でスキーマを読み込んでください。

## 手順

### 1. 期間を決める

デフォルト: 直近3ヶ月の見積書（今日から3ヶ月前の日付を `YYYY-MM-DD` 形式で）。ユーザーが別の期間を指定した場合
（「6月以降」「全部」など）はそれに従います。

「状態」が更新されるのはこの期間内の見積書に紐づく行だけなので、期間を広げれば古い行の「状態」も更新されます。

### 2. freee から見積書を取得

```
mcp__bloque__freee__freee_api_get
  service: invoice
  path: /quotations            ← invoice サービスでは /api/1/ プレフィックスは不要
  query: {company_id: 1234567, partner_ids: "12345678", start_quotation_date: <since>, limit: 100}
```

API は古い順に返し、並び替えのオプションはありません。ちょうど100件返ってきた場合は `offset: 100` などで続きを取得します。

各レスポンスをスクリプト用のファイルにします:
- ツールの結果が大きすぎてファイルに保存された場合は、そのパスをそのまま使います。
- それ以外の場合（3ヶ月分なら通常こちら）は、見積書を `/tmp/sync-quotes-to-notion/freee-<n>.json` に
  `{"quotations": [...]}` の形で書き出します。スクリプトが読むフィールド — `id`, `quotation_number`,
  `quotation_date`, `subject`, `memo`, `amount_excluding_tax`, `cancel_status`, `partner_id` — だけを残し、
  `subject`/`memo` はラベル・全角スペース・改行も含めてそのままコピーしてください。

次に:

```bash
python3 .claude/skills/sync-quotes-to-notion/scripts/parse_quotes.py <file> [<file> ...] --since <since> \
  > /tmp/sync-quotes-to-notion/quotes.json
```

キャンセル済みの見積書と他の取引先の見積書を除外し、`[失注]`/`[無効]` の見積書に `skip_new: true` を付けます。
また、見つかった Backlog 課題キーを `BACKLOG_KEYS: FOO-1 FOO-2 ...` の形で標準エラー出力に出します — 手順3で使います。

### 3. Backlog から課題のステータスを取得

`BACKLOG_KEYS` の各キーについて、以下を（すべて並列で）呼び出します:

```
mcp__bloque__backlog__get_issue
  issueKey: <key>
```

結果を、キー → `status.name` の単純なマップとして `/tmp/sync-quotes-to-notion/statuses.json` に書き出します:

```json
{"FOO-1689": "処理中", "FOO-1702": "未対応"}
```

取得できないキー（削除・移動された課題など）は含めないでください — 計画に警告が出て、その行の「状態」は変更されません。

### 4. Notion の既存行を取得

すべての行を取得します（最近の行だけではありません — 古い行に期間内の見積書が入っていることがあるため）:

```
mcp__bloque__notion__notion-query-data-sources
  data: {
    data_source_urls: ["collection://12345678-90ab-cdef-1234-567890abcdef"],
    query: "SELECT id, url, createdTime, \"Name\", \"freee\", \"GitHub issue\", \"Backlog\", \"見積書番号\", \"金額\", \"状態\" FROM \"collection://12345678-90ab-cdef-1234-567890abcdef\""
  }
```

結果に `has_more: true` があれば、最後までページングします。結果がファイルに保存された場合はそのパスを使い、
そうでなければ `/tmp/sync-quotes-to-notion/rows.json` に `{"results": [...]}` の形で書き出します。列名が変更されて
クエリが失敗した場合は、`notion-fetch` でデータソースのスキーマを取得し直して調整してください — 列名を推測しないこと。

### 5. 計画を作成

```bash
python3 .claude/skills/sync-quotes-to-notion/scripts/plan_sync.py \
  /tmp/sync-quotes-to-notion/quotes.json /tmp/sync-quotes-to-notion/rows.json \
  --statuses /tmp/sync-quotes-to-notion/statuses.json \
  > /tmp/sync-quotes-to-notion/plan.json
```

照合の仕方（ユーザーに結果を説明できるように）:
1. `freee` の URL 内の見積書 ID で照合。
2. なければ、`freee` が**空**で `GitHub issue` が同じ行 — 見積書ができる前に登録されたタスク。
   1つの issue に複数の見積書（追加見積もり1, 2, …）があることが多いため、そのような行は最大1つの見積書（最も古いもの）
   だけが紐づき、残りの見積書にはそれぞれ新しい行が作られます。
3. 一致しなければ行を作成。

一致した行では、見積書由来の列は空欄だけを埋めます。空でない値が freee と異なる場合は `mismatches` に挙げ、変更しません
— ユーザーが意図的に Name を短くしたり修正したりしている可能性があるためです。

「状態」は別扱いで、常に Backlog が優先されます。新しい行には Backlog のステータスが入り、既存行の「状態」が Backlog と
異なる場合は更新されます。その変更はすべて `status_changes` に（`from` → `to` の形で）挙げられます。使う Backlog キーは、
行の `Backlog` 列が埋まっていればその値、なければ見積書のものです。

`[失注]`/`[無効]` の見積書は行を作成せず、見積書由来の列も変更しません。これらは `skipped` に挙げられます。既に行がある
場合は「状態」だけを同期します。

ユーザーがドライラン／プレビューを求めた場合はここで止め、計画を報告します（手順7。「〜します」ではなく「〜する予定です」という形で）。

それ以外で、計画が10行より多く作成する場合は、先に概要を見せて書き込む前に確認してください — 大量の作成は、意図より広い
期間を指定したか、Notion 上で行が移動・削除されたことを意味することが多く、間違って作られた何十行もの行を手で片付けるのは
大変です。少量（通常の毎週の実行）であればそのまま進めて構いません。

### 6. 反映

**作成** — 新しい行をすべて1回の呼び出しで（1回あたり最大100件）、古い順に:

```
mcp__bloque__notion__notion-create-pages
  parent: {type: "data_source_id", data_source_id: "12345678-90ab-cdef-1234-567890abcdef"}
  pages: [{properties: <plan.create[i].properties>}, ...]
```

計画内の `properties` は既に Notion が期待する形になっています（数値は数値、タイトルは `Name`、「状態」は選択肢の名前）。
ページ本文は追加しないでください。

**更新** — `plan.update` の各エントリごとに1回呼び出します:

```
mcp__bloque__notion__notion-update-page
  page_id: <page_id>
  command: update_properties
  properties: <properties>
```

Notion が「状態」の値を受け付けない場合、その Backlog ステータスに対応する選択肢が Notion にありません — 選択肢を自分で
作成・改名せず、ユーザーに報告してください。

### 7. 報告

日本語で簡潔に返信します。例:

```
Notion の Client tasks を更新しました（対象: 2026-08-18 以降の見積書 31件）
- 追加: 26件
- 空欄を補完: 1件（Q-20260901-00012 ← GitHub issue #123 の行に紐付け）
- 状態を Backlog から更新: 4件（FOO-1689 未対応 → 処理中, …）
- 変更なし: 1件
- スキップ（失注/無効）: 3件 — Q-20260805-00008, …
- 要確認:
  - Q-20260901-00012 の Name が freee と異なります（Notion: 「…」 / freee: 「…」）
  - Q-20261015-00027: 件名に Backlog 番号がありません
  - FOO-1712: Backlog のステータスを取得できなかったため、状態は変更していません
```

mismatch と警告はすべて含めてください — ユーザーが手で確認すべき項目です。`status_changes` のうち `page_url` がない
エントリは新規作成した行なので、個別には挙げず、既存行の変更だけを列挙してください。
