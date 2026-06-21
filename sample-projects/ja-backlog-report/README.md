# Backlog の未処理チケットを Slack に送信
## 必要なもの

* Bloque アカウント
* Baclkog アカウント、API key
* Slack アプリの clikent ID、client secret
* Claude Code

## 設定（初回のみ）
### Backlog 及び Slack の認証情報取得

以下のドキュメントに従って、Backlog API キーを取得してください。
[APIの設定 – Backlog ヘルプセンター](https://support-ja.backlog.com/hc/ja/articles/360035641754-API%E3%81%AE%E8%A8%AD%E5%AE%9A)

以下のドキュメントに従って、Bloque で使う Slack アプリを作成し、client ID と client secret を取得してください。
[Slackアプリを作成する | Bloque Documentation](https://docs.bloque.run/ja/docs/integrations/create-slack-app)

### Bloque 上で MCP サーバーの設定

1. もしまだでしたら、[Bloque](https://bloque.run) に登録してください
2. [サンプル用 Hub](https://bloque.run/to/kashima/hub/63697d9a-4e0d-4eef-99b9-cf753bf30abf) の画面に行き、"Install Hub" をクリックします
3. [MCP サーバーの設定画面](https://bloque.run/mcp-servers)で、各サーバーの "Edit" ボタンを押して、"Configuration" タブから必要な情報を入力します:
    * Backlog: `BACKLOG_DOMAIN` には Backlogのドメイン名（`foo.backlog.jp` のような形式）を、`BACKLOG_API_KEY` には Backlog API キーの値を入力
    * Slack: "Client ID" と "Client Secret" に、作成した Slack アプリの値を入力
4. [API Keys](https://bloque.run/api-keys) 画面に行き、API キーを作成、保存します

### プロジェクトディレクトリ

1. `.env.example` をコピーして `.env` を作成します
2. `.env` 内に Bloque API キーを記載します

### スキルの中のダミー値を書き換え

`SKILL.md` の中にダミーの値が入っていますので、それらを自分のプロジェクト用に書き換えてください。

手動で書き換えても良いのですが、`skill-creator` スキルに以下のように指示して修正してもらうのも良いと思います。

```
/skill-creator backlog-report は他の人からもらったサンプルスキルです。スキル内部のダミーの値を自分のプロジェクト用に書き換えて使いたいので、必要な値を教えてください。
```

手動で書き換える場合は以下の3点です。

* 12行目付近: 実際のユーザーに置き換えてください。複数人記載することも出来ます。
* 16行目: Backlog のプロジェクト ID
* 17行目と102行目: Slack のチャンネル ID


## 実際の使用

### 手動実行

手動で実行するには、Claude Code を起動し、 `backlog-report` スキルを呼び出します。
```
./claude-env.sh
/backlog-report
```

### 自動実行

定時実行するには、一番簡単なのは手元の PC などで cron を使う方法です。

もう少し管理された環境で実行したい場合の方法はいくつかありますが、GitHub Actions を使った方法を弊社エンジニアブログで紹介しています。GitHub アカウントを持っている人で新たなサーバー等は不要ですぐ使える方法です。
[Agent Skills を GitHub Actions 経由で定時実行し、野良化を防ぐ – もばらぶエンジニアブログ](https://engineering.mobalab.net/2026/06/18/run-agent-skills-from-github-actions/)
