"""Send a Telegram message (and optional files) via the Bot API.

  python scripts/notify_telegram.py --text-file msg.txt [--files a.pdf b.docx]
  python scripts/notify_telegram.py --text "本週無高度匹配"

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment.
Messages are sent as plain text (no parse_mode) so job titles with * or _ never break.
"""
import argparse
import os
import sys
from pathlib import Path

import requests

LIMIT = 4000  # Telegram caps messages at 4096 chars


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("--files", nargs="*", default=[])
    a = ap.parse_args()

    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("notify_telegram: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set")
    api = f"https://api.telegram.org/bot{token}"
    text = a.text if a.text else Path(a.text_file).read_text(encoding="utf-8")

    for i in range(0, len(text), LIMIT):
        r = requests.post(f"{api}/sendMessage",
                          data={"chat_id": chat, "text": text[i:i + LIMIT], "disable_web_page_preview": True},
                          timeout=30)
        if not r.ok:
            sys.exit(f"sendMessage failed: {r.status_code} {r.text[:200]}")
    for f in a.files:
        with open(f, "rb") as fh:
            r = requests.post(f"{api}/sendDocument", data={"chat_id": chat},
                              files={"document": (Path(f).name, fh)}, timeout=120)
        if not r.ok:
            sys.exit(f"sendDocument {f} failed: {r.status_code} {r.text[:200]}")
    print(f"sent: 1 message ({len(text)} chars), {len(a.files)} file(s)")


if __name__ == "__main__":
    main()
