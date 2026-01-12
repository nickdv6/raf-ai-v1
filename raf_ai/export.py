import sqlite3
import pandas as pd
import json
from pathlib import Path


def export_site_json(con: sqlite3.Connection, out_path: Path) -> None:
    # latest prediction per bout
    pred = pd.read_sql_query(
        """
      SELECT p.*
      FROM predictions p
      JOIN (
        SELECT bout_id, MAX(run_timestamp_utc) AS max_ts
        FROM predictions
        GROUP BY bout_id
      ) m
      ON p.bout_id = m.bout_id AND p.run_timestamp_utc = m.max_ts;
    """,
        con,
    )

    events = pd.read_sql_query("SELECT * FROM events ORDER BY event_date_utc DESC;", con)
    bouts = pd.read_sql_query("SELECT * FROM bouts ORDER BY event_id, bout_order;", con)
    odds = pd.read_sql_query(
        """
      SELECT o.*
      FROM odds o
      JOIN (
        SELECT bout_id, MAX(odds_timestamp_utc) AS max_ts
        FROM odds
        GROUP BY bout_id
      ) m
      ON o.bout_id = m.bout_id AND o.odds_timestamp_utc = m.max_ts;
    """,
        con,
    )
    outcomes = pd.read_sql_query("SELECT * FROM outcomes;", con)

    pred = pred.set_index("bout_id", drop=False) if len(pred) else pred
    odds = odds.set_index("bout_id", drop=False) if len(odds) else odds
    outcomes = outcomes.set_index("bout_id", drop=False) if len(outcomes) else outcomes

    # Diagnostics: confidence distribution (overall + per event)
    overall_counts = {"High": 0, "Medium": 0, "Low": 0, "None": 0}
    per_event_counts: dict[str, dict[str, int]] = {}

    event_list = []
    for _, e in events.iterrows():
        e_id = e["event_id"]
        event_name = str(e.get("event_name"))
        per_event_counts[event_name] = {"High": 0, "Medium": 0, "Low": 0, "None": 0}

        event_bouts = bouts[bouts["event_id"] == e_id].copy()

        bout_list = []
        for _, b in event_bouts.iterrows():
            bout_id = b["bout_id"]
            p = pred.loc[bout_id] if len(pred) and bout_id in pred.index else None
            o = odds.loc[bout_id] if len(odds) and bout_id in odds.index else None
            out = outcomes.loc[bout_id] if len(outcomes) and bout_id in outcomes.index else None

            # Confidence diagnostic
            if p is None:
                overall_counts["None"] += 1
                per_event_counts[event_name]["None"] += 1
            else:
                c = str(p.get("confidence", "Low"))
                if c not in ("High", "Medium", "Low"):
                    c = "Low"
                overall_counts[c] += 1
                per_event_counts[event_name][c] += 1

            bout_list.append(
                {
                    "bout_id": bout_id,
                    "bout_order": int(b["bout_order"]),
                    "weight_class_lbs": None
                    if pd.isna(b.get("weight_class_lbs"))
                    else float(b["weight_class_lbs"]),
                    "fighter_a": b["fighter_a"],
                    "fighter_b": b["fighter_b"],
                    "prediction": None
                    if p is None
                    else {
                        "p_a": float(p["p_a"]),
                        "p_b": float(p["p_b"]),
                        "confidence": str(p["confidence"]),
                        "edge_a": None if pd.isna(p["edge_a"]) else float(p["edge_a"]),
                        "edge_b": None if pd.isna(p["edge_b"]) else float(p["edge_b"]),
                    },
                    "odds": None
                    if o is None
                    else {
                        "book": str(o["book"]),
                        "odds_a_american": int(o["odds_a_american"]),
                        "odds_b_american": int(o["odds_b_american"]),
                        "odds_timestamp_utc": str(o["odds_timestamp_utc"]),
                    },
                    "outcome": None
                    if out is None
                    else {
                        "winner": str(out["winner"]),
                        "method": None if pd.isna(out.get("method")) else str(out["method"]),
                        "recorded_timestamp_utc": None
                        if pd.isna(out.get("recorded_timestamp_utc"))
                        else str(out["recorded_timestamp_utc"]),
                    },
                }
            )

        event_list.append(
            {
                "event_id": e["event_id"],
                "slug": e["slug"],
                "event_name": e["event_name"],
                "event_date_utc": e["event_date_utc"],
                "location": None if pd.isna(e.get("location")) else e["location"],
                "bouts": bout_list,
            }
        )

    # Write JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"events": event_list}, indent=2), encoding="utf-8")

    # Print diagnostics (clean and readable)
    print("\nConfidence distribution (exported predictions):")
    print(
        f"  Overall — High: {overall_counts['High']}, Medium: {overall_counts['Medium']}, Low: {overall_counts['Low']}, None: {overall_counts['None']}"
    )
    for name, counts in per_event_counts.items():
        total = counts["High"] + counts["Medium"] + counts["Low"] + counts["None"]
        print(
            f"  {name} — High: {counts['High']}, Medium: {counts['Medium']}, Low: {counts['Low']}, None: {counts['None']} (Total: {total})"
        )
    print("")
