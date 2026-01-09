import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  event_name TEXT NOT NULL,
  event_date_utc TEXT NOT NULL,
  location TEXT
);

CREATE TABLE IF NOT EXISTS bouts (
  bout_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  bout_order INTEGER NOT NULL,
  weight_class_lbs REAL,
  fighter_a TEXT NOT NULL,
  fighter_b TEXT NOT NULL,
  FOREIGN KEY(event_id) REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS odds (
  bout_id TEXT NOT NULL,
  book TEXT NOT NULL,
  odds_a_american INTEGER NOT NULL,
  odds_b_american INTEGER NOT NULL,
  odds_timestamp_utc TEXT NOT NULL,
  PRIMARY KEY (bout_id, book, odds_timestamp_utc),
  FOREIGN KEY(bout_id) REFERENCES bouts(bout_id)
);

CREATE TABLE IF NOT EXISTS outcomes (
  bout_id TEXT PRIMARY KEY,
  winner TEXT NOT NULL, -- 'A' or 'B'
  method TEXT,
  ended_round TEXT,
  ended_time TEXT,
  recorded_timestamp_utc TEXT,
  FOREIGN KEY(bout_id) REFERENCES bouts(bout_id)
);

-- Store model outputs per bout per run
CREATE TABLE IF NOT EXISTS predictions (
  bout_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  run_timestamp_utc TEXT NOT NULL,
  p_a REAL NOT NULL,
  p_b REAL NOT NULL,
  confidence TEXT NOT NULL,
  implied_p_a REAL,
  implied_p_b REAL,
  edge_a REAL,
  edge_b REAL,
  PRIMARY KEY (bout_id, model_version, run_timestamp_utc),
  FOREIGN KEY(bout_id) REFERENCES bouts(bout_id)
);
"""

def connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys=ON;")
    return con

def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    con.commit()
