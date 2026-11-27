# freee の見積書と Backlog の課題ステータスを Notion のタスク DB にまとめる

このサンプルは、2つの情報源から Notion のタスクデータベースを最新の状態に保ちます。

* **freee**（見積書）: 見積書ごとに1行作成し、件名・金額（税抜）・見積書番号・freee へのリンク・Backlog 課題キー・GitHub issue 番号を記入
* **Backlog**（課題）: 各行の「状態」列に、紐づく Backlog 課題の現在のステータスを反映

Notion 上で手動管理している列（納品予定日、備考）には一切触れません。また、見積書由来の値を意図的に書き換えている場合は、上書きせずに差分として報告します。

## 必要なもの

* Bloque アカウント
* freee アカウント（freee 請求書。見積書はここから取得します）
* Backlog アカウント、API キー
* Notion ワークスペースとタスク用データベース（後述）
* Claude Code

## 設定（初回のみ）

### Backlog の認証情報取得

以下のドキュメントに従って、Backlog API キーを取得してください。
[APIの設定 – Backlog ヘルプセンター](https://support-ja.backlog.com/hc/ja/articles/360035641754-API%E3%81%AE%E8%A8%AD%E5%AE%9A)

### Notion データベースの準備

以下の列を持つ Notion データベースを作成してください。列名を変更する場合は、`SKILL.md` と `scripts/plan_sync.py` もあわせて修正してください。

| 列名 | 種類 |
|---|---|
| Name | タイトル |
| 金額 | 数値 |
| 見積書番号 | テキスト |
| freee | URL |
| Backlog | テキスト |
| GitHub issue | 数値 |
| 状態 | セレクト または ステータス — **選択肢の名前を Backlog プロジェクトのステータス名と揃えてください**（例: 未対応 / 処理中 / 処理済み / 完了） |
| 納品予定日 / 備考 | 任意 — 手動管理用で、スキルからは書き込みません |

### Bloque 上で MCP サーバーの設定

1. もしまだでしたら、[Bloque](https://bloque.run) に登録してください
2. [サンプル用 Hub](https://bloque.run/to/demo/hub/f75e1ef7-84e3-4a89-ba2f-478347e7dbd7) の画面に行き、"Install Hub" をクリックします
3. [MCP サーバーの設定画面](https://bloque.run/mcp-servers)で、各サーバーの "Edit" ボタンを押して、"Configuration" タブから必要な情報を入力します:
    * Backlog: `BACKLOG_DOMAIN` には Backlogのドメイン名（`foo.backlog.jp` のような形式）を、`BACKLOG_API_KEY` には Backlog API キーの値を入力
    * freee: freee アカウントと連携
    * Notion: Notion ワークスペースと連携し、タスク用データベースへのアクセスを許可
4. [API Keys](https://bloque.run/api-keys) 画面に行き、API キーを作成、保存します

### プロジェクトディレクトリ

1. `.env.example` をコピーして `.env` を作成します
2. `.env` 内に Bloque API キーを記載します

### スキルの中のダミー値を書き換え

`SKILL.md` と `scripts/parse_quotes.py` の中にダミーの値が入っていますので、それらを自分のプロジェクト用に書き換えてください。

手動で書き換えても良いのですが、`skill-creator` スキルに以下のように指示して修正してもらうのも良いと思います。

```
/skill-creator sync-quotes-to-notion は他の人からもらったサンプルスキルです。スキル内部のダミーの値を自分のプロジェクト用に書き換えて使いたいので、必要な値を教えてください。
```

手動で書き換える場合は、`.claude/skills/sync-quotes-to-notion/SKILL.md` の22行目付近にある「設定」の表と、ファイル内で同じ値が出てくる箇所を修正してください。

* freee の company_id（`1234567`）: freee 上の自社の事業所 ID
* freee の partner_id（`12345678`）: 見積書を同期したい取引先の ID。`scripts/parse_quotes.py` の `PARTNER_ID` も修正
* Backlog のプロジェクトキー（`FOO`）: Backlog の課題キーの接頭辞。`scripts/parse_quotes.py` の `BACKLOG_PROJECT_KEY` も修正
* Notion のデータソース（`12345678-90ab-cdef-1234-567890abcdef`）とページ URL: タスク用データベースのもの（データベースのページを Claude に `notion-fetch` してもらうと `collection://...` の ID が分かります）

### freee の見積書の書き方

スキルは見積書からいくつかの決まりに沿って情報を読み取ります。見積書をこの形式で作成するか、`scripts/parse_quotes.py` を自分の運用に合わせて修正してください。

* 件名: 任意の `[ラベル]`、Backlog 課題キー、タイトルの順 — 例: `[概算] FOO-123 CSV エクスポート機能追加`
* メモ: 1行目の末尾に GitHub issue 番号 — 例: `#456`
* `[失注]` または `[無効]` ラベルの見積書は行を作成しません。既に行がある場合は「状態」だけを同期します

## 実際の使用

### 手動実行

手動で実行するには、Claude Code を起動し、 `sync-quotes-to-notion` スキルを呼び出します。
```
./claude-env.sh
/sync-quotes-to-notion
```

デフォルトでは直近3ヶ月の見積書が対象です。「6月以降の見積書を同期して」のように期間を指定したり、「Notion には書き込まずにプレビューだけして」のようにドライランを指示したりすることもできます。
