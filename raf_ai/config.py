from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Paths:
    root: Path = Path(__file__).resolve().parents[1]
    data_input: Path = root / "data" / "input"
    db_path: Path = root / "raf.sqlite"
    site_data_out: Path = root / "site" / "src" / "data" / "events.json"

def discord_webhook_url() -> str | None:
    return os.getenv("DISCORD_WEBHOOK_URL") or None
