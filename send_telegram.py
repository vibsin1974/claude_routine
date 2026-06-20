#!/usr/bin/env python3
"""Telegram 브리핑 발송 스크립트.

환경변수:
    Bot_Token: Telegram 봇 토큰
    Chat_ID:   발송 대상 채팅 ID

사용법:
    echo "브리핑 내용" | python send_telegram.py
    python send_telegram.py < briefing.txt
"""

import os
import sys
import json
import urllib.request
import urllib.error

MAX_LENGTH = 4000  # Telegram 메시지 최대 길이 (4096에서 여유분 확보)


def get_env(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        print(f"❌ 오류: 환경변수 '{key}'가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)
    return value


def send_message(token: str, chat_id: str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"❌ HTTP 오류 {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 네트워크 오류: {e.reason}", file=sys.stderr)
        sys.exit(1)


def split_message(text: str) -> list[str]:
    """4000자 초과 시 줄 단위로 분할."""
    if len(text) <= MAX_LENGTH:
        return [text]

    chunks = []
    current = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        if current_len + len(line) > MAX_LENGTH and current:
            chunks.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("".join(current))

    return chunks


def main():
    token = get_env("Bot_Token")
    chat_id = get_env("Chat_ID")

    text = sys.stdin.read().strip()
    if not text:
        print("❌ 오류: 브리핑 내용이 비어 있습니다.", file=sys.stderr)
        sys.exit(1)

    chunks = split_message(text)
    total = len(chunks)

    print(f"📤 Telegram 발송 시작 (총 {total}건)...")

    for i, chunk in enumerate(chunks, 1):
        result = send_message(token, chat_id, chunk)
        if result.get("ok"):
            print(f"  ✅ 메시지 {i}/{total} 발송 완료")
        else:
            print(f"  ❌ 메시지 {i}/{total} 발송 실패: {result}", file=sys.stderr)
            sys.exit(1)

    print(f"\n✅ Telegram 발송 성공 (메시지 {total}건)")
    print(f"📱 Chat ID: {chat_id}")


if __name__ == "__main__":
    main()
