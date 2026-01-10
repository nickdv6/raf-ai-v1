import pandas as pd
from pathlib import Path
import sqlite3

def _detect_delimiter(header_line: str) -> str:
    candidates = [",", ";", "\t", "|"]
    counts = {d: header_line.count(d) for d in candidates}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","

def _read_csv(p: Path) -> pd.DataFrame:
    if not p.exists():
        raise FileNotFoundError(f"Missing input file: {p}")

    # Detect delimiter + strip BOM if present
    with p.open("r", encoding="utf-8-sig", errors="replace") as f:
        first_line = f.readline()

    delim = _detect_delimiter(first_line)
    df = pd.read_csv(p, sep=delim, encoding="utf-8-sig")

    # Normalize column names (strip whitespace + BOM artifacts)
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]

    return df

def ingest_all(con: sqlite3.Connection, input_dir: Path) -> dict[str, int]:
    events = _read_csv(input_dir / "events.csv")
    bouts = _read_csv(input_dir / "bouts.csv")
    odds = _read_csv(input_dir / "odds.csv")
    outcomes = _read_csv(input_dir / "outcomes.csv")

    # Basic validation (v1 schema)
    required_events = {"event_id", "slug", "event_name", "event_date_utc"}
    required_bouts  = {"bout_id", "event_id", "bout_order", "fighter_a", "fighter_b"}
    required_odds   = {"bout_id", "book", "odds_a_american", "odds_b_american", "odds_timestamp_utc"}
    required_out    = {"bout_id", "winner"}

    for name, df, req in [
        ("events", events, required_events),
        ("bouts", bouts, required_bouts),
        ("odds", odds, required_odds),
        ("outcomes", outcomes, required_out),
    ]:
        missing = req - set(df.columns)
        if missing:
            raise ValueError(f"{name}.csv missing columns: {sorted(missing)}")

    # Simple v1 approach: replace tables on each run
    events.to_sql("events", con, if_exists="replace", index=False)
    bouts.to_sql("bouts", con, if_exists="replace", index=False)
    odds.to_sql("odds", con, if_exists="replace", index=False)
    outcomes.to_sql("outcomes", con, if_exists="replace", index=False)

    con.commit()
    return {
        "events": len(events),
        "bouts": len(bouts),
        "odds": len(odds),
        "outcomes": len(outcomes),
    }
