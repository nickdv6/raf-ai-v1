from __future__ import annotations
import json
import urllib.request
from dataclasses import dataclass
from typing import Optional

@dataclass
class DiscordMessage:
    content: str

def send_discord(webhook_url: str, content: str) -> None:
    payload = json.dumps(DiscordMessage(content=content).__dict__).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp.read()

def build_summary_text(latest_event_name: str, latest_event_slug: str, base_url: str | None = None) -> str:
    url = f"{base_url}/events/{latest_event_slug}/" if base_url else f"/events/{latest_event_slug}/"
    return f"RAF model updated for **{latest_event_name}**.\nLatest card: {url}\n\n(Probabilities are informational only; no guarantees.)"
