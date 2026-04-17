# zulip-hackathon-api

Zulip bot の最小デモです。`text_reader_bot.py` は新着メッセージを読み取り、`raw_content` を取得して文字数・行数・頻出語を返します。
`text_reader_rest_bot.py` は同じ内容を Zulip REST API を直接叩いて実装した版です。

## 使える言語

Zulip bot は REST API を叩ける言語なら基本的に実装できます。
ただし、公式ドキュメント上で bot 開発支援が最も充実しているのは Python です。

- Python: 公式ライブラリ `zulip` があり、`call_on_each_message` のような bot 向け API を使えます。
- JavaScript / TypeScript: 公式ライブラリ `zulip-js` があります。
- それ以外: Go / Ruby / Rust などでも REST API を直接使えば実装できます。完成度はライブラリ次第です。

このリポジトリでは、最初に試しやすいように Python 版のデモを置いています。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp zuliprc.example zuliprc
```

`zuliprc` に bot のメールアドレス、API key、Zulip URL を入れてください。

## 実行

公式 Python ライブラリ版:

```bash
python3 text_reader_bot.py --config-file zuliprc
```

REST API 直叩き版:

```bash
python3 text_reader_rest_bot.py --config-file zuliprc
```

特定チャネル・トピックだけ監視する:

```bash
python3 text_reader_rest_bot.py --config-file zuliprc --channel general --topic demo
```

## 動作イメージ

メッセージを受けると、bot は次のような情報を返信します。

- message_id
- sender
- 文字数
- 行数
- 単語数
- 頻出語
- テキスト先頭のプレビュー

次に作る候補としては、要約 bot、翻訳 bot、議事録 bot、FAQ bot あたりが現実的です。

## REST API 版の実装内容

`text_reader_rest_bot.py` は次の API を直接使っています。

- `POST /api/v1/register`: message event を受ける queue を作る
- `GET /api/v1/events`: long polling で新着 event を受ける
- `GET /api/v1/messages/{message_id}`: `apply_markdown=false` で raw text を取る
- `POST /api/v1/messages`: 解析結果を返信する
