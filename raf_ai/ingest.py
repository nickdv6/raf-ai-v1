from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd


def _detect_delimiter(header_line: str) -> str:
    candidates = [",", ";", "\t", "|"]
    counts = {d: header_line.count(d) for d in candidates}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def _read_csv(p: Path) -> pd.DataFrame:
    if not p.exists():
        raise FileNotFoundError(f"Missing input file: {p}")

    with p.open("r", encoding="utf-8-sig", errors="replace") as f:
        first_line = f.readline()

    delim = _detect_delimiter(first_line)
    df = pd.read_csv(p, sep=delim, encoding="utf-8-sig")

    # Normalize column names
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    return df


def ingest_all(con: sqlite3.Connection, input_dir: Path) -> dict[str, int]:
    """
    Idempotent ingest:
      - reads CSV inputs
      - validates schema
      - clears target tables in dependency order
      - inserts fresh data

    Note: We avoid explicit BEGIN/COMMIT SQL because pandas.to_sql()
    and sqlite3 connection settings can interact with autocommit behavior.
    """
    con.execute("PRAGMA foreign_keys = ON;")

    events = _read_csv(input_dir / "events.csv")
    bouts = _read_csv(input_dir / "bouts.csv")
    odds = _read_csv(input_dir / "odds.csv")
    outcomes = _read_csv(input_dir / "outcomes.csv")

    required_events = {"event_id", "slug", "event_name", "event_date_utc"}
    required_bouts = {"bout_id", "event_id", "bout_order", "fighter_a", "fighter_b"}
    required_odds = {"bout_id", "book", "odds_a_american", "odds_b_american", "odds_timestamp_utc"}
    required_out = {"bout_id", "winner"}

    for name, df, req in [
        ("events", events, required_events),
        ("bouts", bouts, required_bouts),
        ("odds", odds, required_odds),
        ("outcomes", outcomes, required_out),
    ]:
        missing = req - set(df.columns)
        if missing:
            raise ValueError(f"{name}.csv missing columns: {sorted(missing)}")

    try:
        # Clear in dependency order.
        con.execute("DELETE FROM odds;")
        con.execute("DELETE FROM outcomes;")
        con.execute("DELETE FROM predictions;")
        con.execute("DELETE FROM bouts;")
        con.execute("DELETE FROM events;")

        # Insert fresh
        events.to_sql("events", con, if_exists="append", index=False)
        bouts.to_sql("bouts", con, if_exists="append", index=False)
        odds.to_sql("odds", con, if_exists="append", index=False)
        outcomes.to_sql("outcomes", con, if_exists="append", index=False)

        con.commit()

    except Exception:
        # Roll back only if there is an active transaction
        if getattr(con, "in_transaction", False):
            con.rollback()
        raise

    return {
        "events": len(events),
        "bouts": len(bouts),
        "odds": len(odds),
        "outcomes": len(outcomes),
    }
