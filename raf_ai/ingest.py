import pandas as pd
from pathlib import Path

def _detect_delimiter(header_line: str) -> str:
    # Pick the delimiter that appears most in the header
    candidates = [",", ";", "\t", "|"]
    counts = {d: header_line.count(d) for d in candidates}
    best = max(counts, key=counts.get)
    # If none appear, default to comma
    return best if counts[best] > 0 else ","

def _read_csv(p: Path) -> pd.DataFrame:
    if not p.exists():
        raise FileNotFoundError(f"Missing input file: {p}")

    # Read first line to detect delimiter and handle encoding quirks
    with p.open("r", encoding="utf-8-sig", errors="replace") as f:
        first_line = f.readline()

    delim = _detect_delimiter(first_line)

    df = pd.read_csv(p, sep=delim, encoding="utf-8-sig")

    # Normalize column names (strip BOM, whitespace)
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]

    return df
