import sqlite3
from raf_ai.config import Paths, discord_webhook_url
from raf_ai.db import connect, init_db
from raf_ai.ingest import ingest_all
from raf_ai.model import predict_and_store
from raf_ai.export import export_site_json
from raf_ai.notify import send_discord, build_summary_text

def main() -> None:
    paths = Paths()
    con = connect(paths.db_path)
    init_db(con)

    counts = ingest_all(con, paths.data_input)
    n_preds = predict_and_store(con)
    export_site_json(con, paths.site_data_out)

    # Discord optional
    wh = discord_webhook_url()
    if wh:
        # Use latest event by date
        cur = con.execute("SELECT event_name, slug FROM events ORDER BY event_date_utc DESC LIMIT 1;")
        row = cur.fetchone()
        if row:
            msg = build_summary_text(latest_event_name=row[0], latest_event_slug=row[1], base_url=None)
            send_discord(wh, msg)

    con.close()

    print("Pipeline complete.")
    print("Imported:", counts)
    print("Predictions generated:", n_preds)
    print("Site data:", paths.site_data_out)

if __name__ == "__main__":
    main()
