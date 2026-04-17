#!/usr/bin/env python3

from __future__ import annotations

import argparse
import configparser
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read Zulip messages via the REST API and reply with a text summary."
    )
    parser.add_argument(
        "--config-file",
        default="zuliprc",
        help="Path to a zuliprc file. Default: ./zuliprc",
    )
    parser.add_argument(
        "--channel",
        help="Only reply to this channel name.",
    )
    parser.add_argument(
        "--topic",
        help="Only reply to this topic. Requires --channel.",
    )
    return parser.parse_args()


def load_config(config_file: str) -> tuple[str, str, str]:
    path = Path(config_file)
    parser = configparser.ConfigParser()
    if not parser.read(path):
        raise SystemExit(f"設定ファイルを読めませんでした: {path}")

    if "api" not in parser:
        raise SystemExit(f"[api] セクションがありません: {path}")

    section = parser["api"]
    email = section.get("email", "").strip()
    api_key = section.get("key", "").strip()
    site = section.get("site", "").strip().rstrip("/")
    if not email or not api_key or not site:
        raise SystemExit("zuliprc の email / key / site をすべて設定してください。")
    return email, api_key, site


def summarize_text(text: str) -> str:
    normalized = text.strip()
    lines = [line for line in normalized.splitlines() if line.strip()]
    words = re.findall(r"[A-Za-z0-9_]+", normalized.lower())
    top_words = Counter(words).most_common(5)

    preview = normalized.replace("\n", " ")
    if len(preview) > 120:
        preview = preview[:117] + "..."

    top_words_text = ", ".join(
        f"`{word}` x {count}" for word, count in top_words
    ) or "英数字トークンなし"

    return "\n".join(
        [
            "テキストを読み取りました。",
            f"- 文字数: {len(normalized)}",
            f"- 行数: {len(lines)}",
            f"- 単語数: {len(words)}",
            f"- よく出る語: {top_words_text}",
            f"- 先頭プレビュー: `{preview or '(empty)'}`",
        ]
    )


class ZulipRestBot:
    def __init__(self, site: str, email: str, api_key: str) -> None:
        self.site = site
        self.email = email
        self.session = requests.Session()
        self.session.auth = (email, api_key)
        self.session.headers.update({"User-Agent": "zulip-text-reader-rest-demo/1.0"})

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: int = 90,
    ) -> dict[str, Any]:
        response = self.session.request(
            method=method,
            url=f"{self.site}{path}",
            params=params,
            data=data,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("result") != "success":
            raise RuntimeError(f"API error at {path}: {payload}")
        return payload

    def register_queue(self) -> tuple[str, int, int]:
        payload = self.request(
            "POST",
            "/api/v1/register",
            data={
                "event_types": json.dumps(["message"]),
                "all_public_streams": "true",
            },
        )
        return (
            payload["queue_id"],
            payload["last_event_id"],
            payload.get("event_queue_longpoll_timeout_seconds", 90),
        )

    def get_events(self, queue_id: str, last_event_id: int, timeout: int) -> dict[str, Any]:
        return self.request(
            "GET",
            "/api/v1/events",
            params={
                "queue_id": queue_id,
                "last_event_id": last_event_id,
            },
            timeout=timeout + 10,
        )

    def get_raw_message(self, message_id: int) -> dict[str, Any]:
        return self.request(
            "GET",
            f"/api/v1/messages/{message_id}",
            params={
                "apply_markdown": "false",
                "allow_empty_topic_name": "true",
            },
        )

    def send_reply(self, message: dict[str, Any], content: str) -> None:
        if message["type"] == "stream":
            self.request(
                "POST",
                "/api/v1/messages",
                data={
                    "type": "stream",
                    "to": message["display_recipient"],
                    "topic": message.get("topic") or message.get("subject") or "",
                    "content": content,
                },
            )
            return

        recipients = [
            user["email"]
            for user in message["display_recipient"]
            if user["email"] != self.email
        ]
        self.request(
            "POST",
            "/api/v1/messages",
            data={
                "type": "private",
                "to": json.dumps(recipients),
                "content": content,
            },
        )


def matches_filter(message: dict[str, Any], args: argparse.Namespace) -> bool:
    if message["type"] != "stream":
        return not args.channel and not args.topic

    if args.channel and message.get("display_recipient") != args.channel:
        return False

    topic = message.get("topic") or message.get("subject") or ""
    if args.topic and topic != args.topic:
        return False

    return True


def main() -> None:
    args = parse_args()
    if args.topic and not args.channel:
        raise SystemExit("--topic を使う場合は --channel も指定してください。")

    email, api_key, site = load_config(args.config_file)
    bot = ZulipRestBot(site=site, email=email, api_key=api_key)
    queue_id, last_event_id, longpoll_timeout = bot.register_queue()

    print("REST bot started. Waiting for messages...")

    while True:
        payload = bot.get_events(queue_id, last_event_id, longpoll_timeout)
        for event in payload.get("events", []):
            last_event_id = max(last_event_id, event["id"])
            if event.get("type") != "message":
                continue

            message = event["message"]
            if message.get("sender_email") == email:
                continue
            if not matches_filter(message, args):
                continue

            raw_message = bot.get_raw_message(message["id"])
            raw_content = raw_message.get("raw_content") or raw_message.get("content", "")
            summary = summarize_text(raw_content)
            response = (
                f"message_id={message['id']}\n"
                f"sender={message.get('sender_full_name', 'unknown')}\n\n"
                f"{summary}"
            )
            bot.send_reply(message, response)


if __name__ == "__main__":
    main()
