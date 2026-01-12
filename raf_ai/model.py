from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd

MODEL_VERSION = "elo_v1"


def now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def american_to_implied_prob(odds: int) -> float:
    # Odds: -140 => 140/(140+100); +120 => 100/(120+100)
    if odds == 0:
        return np.nan
    if odds < 0:
        o = abs(odds)
        return o / (o + 100.0)
    return 100.0 / (odds + 100.0)


@dataclass
class EloConfig:
    k: float = 24.0
    base_rating: float = 1500.0


def expected_score(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / 400.0))


def confidence_label(p: float) -> str:
    # Confidence in terms of deviation from 0.5
    d = abs(p - 0.5)
    if d >= 0.18:
        return "High"
    if d >= 0.10:
        return "Medium"
    return "Low"


def build_elos_from_outcomes(con: sqlite3.Connection, cfg: EloConfig) -> dict[str, float]:
    # Iterate bouts in chronological order (by event_date, then bout_order), updating fighter ratings
    q = """
    SELECT e.event_date_utc, b.bout_order, b.fighter_a, b.fighter_b, o.winner
    FROM bouts b
    JOIN events e ON e.event_id = b.event_id
    LEFT JOIN outcomes o ON o.bout_id = b.bout_id
    ORDER BY e.event_date_utc ASC, b.bout_order ASC;
    """
    df = pd.read_sql_query(q, con)
    ratings: dict[str, float] = {}

    for _, row in df.iterrows():
        a = row["fighter_a"]
        b = row["fighter_b"]
        winner = row["winner"]

        r_a = ratings.get(a, cfg.base_rating)
        r_b = ratings.get(b, cfg.base_rating)

        p_a = expected_score(r_a, r_b)

        if pd.isna(winner):
            # No outcome yet: don't update ratings
            continue

        s_a = 1.0 if str(winner).upper() == "A" else 0.0
        s_b = 1.0 - s_a

        ratings[a] = r_a + cfg.k * (s_a - p_a)
        ratings[b] = r_b + cfg.k * (s_b - (1.0 - p_a))

    return ratings


def latest_odds_per_bout(con: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT o.*
    FROM odds o
    JOIN (
      SELECT bout_id, MAX(odds_timestamp_utc) AS max_ts
      FROM odds
      GROUP BY bout_id
    ) m
    ON o.bout_id = m.bout_id AND o.odds_timestamp_utc = m.max_ts;
    """
    return pd.read_sql_query(q, con)


def compute_confidence(p_a: float, edge_a: float, edge_b: float) -> str:
    """
    Confidence is derived from:
      1) model separation from 50/50 (abs(p_a - 0.5))
      2) strongest absolute edge vs market (max(abs(edge_a), abs(edge_b)))

    Tiers are deliberately conservative to avoid overstating confidence.
    """
    try:
        p_margin = abs(float(p_a) - 0.5)
        edge_abs = max(abs(float(edge_a)), abs(float(edge_b)))
    except Exception:
        return "Low"

    # High confidence: strong separation AND meaningful market disagreement
    if p_margin >= 0.10 and edge_abs >= 0.050:
        return "High"

    # Medium confidence: moderate separation AND moderate market disagreement
    if p_margin >= 0.06 and edge_abs >= 0.025:
        return "Medium"

    return "Low"


def predict_and_store(con: sqlite3.Connection) -> int:
    cfg = EloConfig()
    ratings = build_elos_from_outcomes(con, cfg)

    bouts = pd.read_sql_query(
        """
      SELECT b.bout_id, b.fighter_a, b.fighter_b
      FROM bouts b;
    """,
        con,
    )

    odds_latest = latest_odds_per_bout(con)
    odds_latest = odds_latest.set_index("bout_id") if len(odds_latest) else odds_latest

    run_ts = now_utc_iso()
    rows = []

    for _, r in bouts.iterrows():
        bout_id = r["bout_id"]
        a = r["fighter_a"]
        b = r["fighter_b"]

        r_a = ratings.get(a, cfg.base_rating)
        r_b = ratings.get(b, cfg.base_rating)

        p_a = expected_score(r_a, r_b)
        p_b = 1.0 - p_a

        implied_a = implied_b = edge_a = edge_b = None

        # Compute implied probabilities + edges if we have odds
        if len(odds_latest) and bout_id in odds_latest.index:
            od = odds_latest.loc[bout_id]
            implied_a = float(american_to_implied_prob(int(od["odds_a_american"])))
            implied_b = float(american_to_implied_prob(int(od["odds_b_american"])))

            # Guard against nan
            edge_a = float(p_a - implied_a) if implied_a == implied_a else None
            edge_b = float(p_b - implied_b) if implied_b == implied_b else None

        # Confidence: meaningful only when we have edges; otherwise fall back to p-only label
        if edge_a is not None and edge_b is not None:
            conf = compute_confidence(p_a, edge_a, edge_b)
        else:
            conf = confidence_label(p_a)

        rows.append(
            (
                bout_id,
                MODEL_VERSION,
                run_ts,
                float(p_a),
                float(p_b),
                conf,
                implied_a,
                implied_b,
                edge_a,
                edge_b,
            )
        )

    con.executemany(
        """
      INSERT OR REPLACE INTO predictions
      (bout_id, model_version, run_timestamp_utc, p_a, p_b, confidence, implied_p_a, implied_p_b, edge_a, edge_b)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """,
        rows,
    )
    con.commit()
    return len(rows)
